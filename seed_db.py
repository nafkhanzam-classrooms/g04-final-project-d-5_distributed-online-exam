from app.database import SessionLocal
from app.models import Question, Exam
from datetime import datetime, timedelta # <--- TAMBAHKAN INI
from app.models import Question, Exam, User # Tambahkan User

def seed_db():
    db = SessionLocal()
    try:
        # 1. Cek apakah Ujian (Exam) ID 1 sudah ada
        exam = db.query(Exam).filter(Exam.id == 1).first()
        if not exam:
            print("Membuat entri Ujian (Exam) ID 1...")
            
            # Mendefinisikan waktu mulai dan selesai
            sekarang = datetime.now()
            nanti = sekarang + timedelta(hours=2) # Ujian berlangsung 2 jam
            
            new_exam = Exam(
                id=1, 
                title="Ujian Pemrograman Jaringan",
                start_time=sekarang, 
                end_time=nanti      
            )
            db.add(new_exam)
            db.commit()
            print("✅ Ujian ID 1 berhasil dibuat.")
        
        # 2. Sekarang buat Soalnya
        existing_question = db.query(Question).filter(Question.id == 1).first()
        if not existing_question:
            print("Menyuntikkan soal ke dalam Ujian ID 1...")
            new_question = Question(
                exam_id=1,
                question_text="Sebutkan protokol pengiriman data yang menjamin data sampai tanpa cacat (Stateful)!",
                choices="-",
                correct_answer="TCP"
            )
            db.add(new_question)
            db.commit()
            print("✅ Soal nomor 1 berhasil disimpan.")
        else:
            print("ℹ️ Soal sudah ada.")
        
        # Tambahkan User ID 1 jika belum ada
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("Membuat User dummy ID 1...")
            new_user = User(id=1, username="mahasiswa_test", password_hash="hashed_password_dummy", role="STUDENT")
            db.add(new_user)
            db.commit()
            
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()