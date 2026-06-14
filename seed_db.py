from app.database import engine, Base, SessionLocal
from app import models
from datetime import datetime, timedelta
from app.security import get_password_hash #

# 1. Hapus dan buat ulang tabel (Agar bersih untuk demo)
print("🔄 Mereset tabel database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Waktu untuk simulasi (Mulai kemarin, selesai 7 hari lagi)
    waktu_mulai = datetime.now() - timedelta(days=1)
    waktu_selesai = datetime.now() + timedelta(days=7)

    # 2. Buat User Mahasiswa
    print("👤 Menambahkan data mahasiswa...")
    # Enkripsi kata sandi "123456"
    default_password = get_password_hash("123456") 
    
    student1 = models.User(username="student1", password_hash=default_password, role="STUDENT")
    student2 = models.User(username="student2", password_hash=default_password, role="STUDENT")
    
    db.add_all([student1, student2])
    db.commit()

    # 3. Buat Ujian 1 (Kuis Jaringan Dasar)
    print("📝 Menambahkan Kuis 1 dan soal-soalnya...")
    exam1 = models.Exam(
        title="Kuis 1: Jaringan & Protokol", 
        start_time=waktu_mulai, 
        end_time=waktu_selesai
    )
    db.add(exam1)
    db.commit()

    db.add_all([
        models.Question(exam_id=exam1.id, question_text="1. Protokol di Layer 4 (Transport) yang bersifat connectionless (tanpa jaminan pengiriman) adalah?", correct_answer="UDP", choices="[]"),
        models.Question(exam_id=exam1.id, question_text="2. Berapakah port default yang digunakan untuk layanan HTTP?", correct_answer="80", choices="[]"),
        models.Question(exam_id=exam1.id, question_text="3. Sistem yang berfungsi menerjemahkan nama domain menjadi alamat IP adalah?", correct_answer="DNS", choices="[]"),
        models.Question(exam_id=exam1.id, question_text="4. Alamat identitas fisik unik pada kartu jaringan komputer (NIC) disebut alamat?", correct_answer="MAC", choices="[]"),
        models.Question(exam_id=exam1.id, question_text="5. Protokol transfer hiperteks versi aman yang berjalan pada port 443 adalah?", correct_answer="HTTPS", choices="[]")
    ])

    # 4. Buat Ujian 2 (Kuis Arsitektur & Microservices)
    print("📝 Menambahkan Kuis 2 dan soal-soalnya...")
    exam2 = models.Exam(
        title="Kuis 2: Arsitektur Sistem Terdistribusi", 
        start_time=waktu_mulai, 
        end_time=waktu_selesai
    )
    db.add(exam2)
    db.commit()

    db.add_all([
        models.Question(exam_id=exam2.id, question_text="1. Format file yang paling umum digunakan untuk pertukaran data REST API selain XML adalah?", correct_answer="JSON", choices="[]"),
        models.Question(exam_id=exam2.id, question_text="2. Framework Remote Procedure Call buatan Google yang menggunakan protokol HTTP/2 adalah?", correct_answer="gRPC", choices="[]"),
        models.Question(exam_id=exam2.id, question_text="3. Pola arsitektur yang memecah aplikasi monolitik menjadi layanan-layanan kecil terisolasi disebut?", correct_answer="Microservices", choices="[]"),
        models.Question(exam_id=exam2.id, question_text="4. Platform virtualisasi level OS yang digunakan untuk membungkus aplikasi menjadi container adalah?", correct_answer="Docker", choices="[]"),
        models.Question(exam_id=exam2.id, question_text="5. Standar terbuka (RFC 7519) berbentuk token untuk mengamankan transmisi data web adalah?", correct_answer="JWT", choices="[]")
    ])

    db.commit()
    print("✅ SUKSES! Database berhasil disemai. Semua constraint terpenuhi.")

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
    db.rollback()
finally:
    db.close()