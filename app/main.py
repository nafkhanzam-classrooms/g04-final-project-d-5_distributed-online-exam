import sys
print("--- STARTUP LOG: 1. Mulai membaca file main.py ---")

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
print("--- STARTUP LOG: 2. Import FastAPI & SQLAlchemy selesai ---")

from app.database import engine, Base, get_db
print("--- STARTUP LOG: 3. Import Database selesai ---")

from app import models, schemas
print("--- STARTUP LOG: 4. Import Models & Schemas selesai ---")

from app import security
print("--- STARTUP LOG: 5. Import Security (Bcrypt/JWT) selesai ---")

print("--- STARTUP LOG: 6. Membuat tabel database SQLite... ---")
# ==========================================
# PYDANTIC SCHEMAS UNTUK DOSEN
# ==========================================

class ExamCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime

class QuestionCreate(BaseModel):
    exam_id: int
    question_text: str
    choices: str = "-"
    correct_answer: str

class StudentResultResponse(BaseModel):
    username: str
    score: int
    submitted_answer: str

    class Config:
        from_attributes = True

class StudentMonitoringResponse(BaseModel):
    username: str
    status: str  # "Online" atau "Offline"
    last_active: Optional[str] = None
try:
    Base.metadata.create_all(bind=engine)
    print("--- STARTUP LOG: 7. Tabel database selesai dibuat ---")
except Exception as e:
    print(f"--- ERROR SAAT BIKIN DB: {e} ---")

app = FastAPI(title="DOES - Distributed Online Examination System")
print("--- STARTUP LOG: 8. Aplikasi FastAPI berhasil diinisialisasi ---")

# (Biarkan sisa kode endpoint Anda seperti @app.post("/auth/login") di bawah ini)

# Buat tabel otomatis jika belum ada (hanya untuk development)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DOES - Distributed Online Examination System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan semua domain (khusus untuk mode development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/auth/register")
def register(request: schemas.RegisterRequest, db: Session = Depends(get_db)):
    # Cek apakah username sudah digunakan
    existing_user = db.query(models.User).filter(models.User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    
    # Hash password sebelum disimpan ke database
    hashed_password = security.get_password_hash(request.password)
    
    # Buat objek user baru dan simpan
    new_user = models.User(
        username=request.username, 
        password_hash=hashed_password, 
        role=request.role
    )
    db.add(new_user)
    db.commit()
    
    return {"message": "User berhasil didaftarkan"}

@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Cari user di database
    user = db.query(models.User).filter(models.User.username == request.username).first()
    
    # Validasi username dan password
    if not user or not security.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
    # Generate Token
    access_token = security.create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id}
    )
    return {"token": access_token}

# ==========================================
# ENDPOINTS KHUSUS DOSEN / ADMIN
# ==========================================

# 1. Membuat Ujian Baru (Menggantikan langkah manual di seed_db)
@app.post("/admin/exams", status_code=status.HTTP_201_CREATED)
def create_exam(exam_data: ExamCreate, db: Session = Depends(get_db)):
    # Opsi Tambahan: Di sini Anda bisa memvalidasi token JWT 
    # dan memastikan user.role == "dosen"
    
    new_exam = models.Exam(
        title=exam_data.title,
        start_time=exam_data.start_time,
        end_time=exam_data.end_time
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return {"status": "success", "message": "Ujian berhasil dibuat", "exam_id": new_exam.id}


# 2. Menambahkan Soal ke Dalam Ujian
@app.post("/admin/questions", status_code=status.HTTP_201_CREATED)
def create_question(question_data: QuestionCreate, db: Session = Depends(get_db)):
    # Pastikan ujiannya ada dulu
    exam = db.query(models.Exam).filter(models.Exam.id == question_data.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Ujian (Exam) tidak ditemukan")

    new_question = models.Question(
        exam_id=question_data.exam_id,
        question_text=question_data.question_text,
        choices=question_data.choices,
        correct_answer=question_data.correct_answer
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return {"status": "success", "message": "Soal berhasil ditambahkan", "question_id": new_question.id}


# 3. Melihat Daftar Nilai Ujian Mahasiswa
@app.get("/admin/results/{exam_id}", response_model=List[StudentResultResponse])
def get_exam_results(exam_id: int, db: Session = Depends(get_db)):
    # Query untuk menggabungkan data Jawaban dengan nama Mahasiswa (User)
    results = db.query(
        models.User.username,
        models.Answer.score,
        models.Answer.submitted_answer
    ).join(models.Answer, models.User.id == models.Answer.user_id)\
     .filter(models.Answer.exam_id == exam_id).all()
     
    return results


# 4. Memantau Heartbeat / Status Live Mahasiswa
@app.get("/admin/monitoring/{exam_id}", response_model=List[StudentMonitoringResponse])
def monitor_students(exam_id: int, db: Session = Depends(get_db)):
    # Ambil semua user yang memiliki role "mahasiswa"
    students = db.query(models.User).filter(models.User.role == "STUDENT").all()
    
    monitoring_list = []
    sekarang = datetime.now()
    
    for student in students:
        # Logika Toleransi Batas Waktu Heartbeat (Contoh: 15 detik)
        # Jika kolom 'last_active' di model User Anda belum ada, 
        # kita berasumsi mahasiswa offline terlebih dahulu untuk saat ini.
        status_aktif = "Offline"
        waktu_str = "-"
        
        if hasattr(student, 'last_active') and student.last_active:
            selisih_waktu = (sekarang - student.last_active).total_seconds()
            waktu_str = student.last_active.strftime("%H:%M:%S")
            if selisih_waktu <= 15:  # Jika mengirim paket kurang dari 15 detik yang lalu
                status_aktif = "Online"
        
        monitoring_list.append({
            "username": student.username,
            "status": status_aktif,
            "last_active": waktu_str
        })
        
    return monitoring_list

@app.get("/profile", response_model=schemas.UserProfile)
def get_profile(token_data: dict = Depends(security.verify_token)):
    # Mengambil data langsung dari payload JWT yang sudah divalidasi
    return {
        "id": token_data.get("id"),
        "username": token_data.get("sub"),
        "role": token_data.get("role")
    }

@app.get("/exams", response_model=List[schemas.ExamResponse])
def get_exams(token_data: dict = Depends(security.verify_token), db: Session = Depends(get_db)):
    # Endpoint ini dilindungi oleh Depends(security.verify_token)
    exams = db.query(models.Exam).all()
    return exams