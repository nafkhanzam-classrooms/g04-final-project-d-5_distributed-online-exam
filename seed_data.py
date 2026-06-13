from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
from app import models

def seed_database():
    # Pastikan semua tabel (termasuk tabel 'questions' yang baru) terbuat di SQLite
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Pengecekan sederhana agar tidak terjadi duplikasi data saat skrip dijalankan ulang
        if db.query(models.Exam).first():
            print("⚠️ Database sudah memiliki data ujian. Proses seeding dibatalkan.")
            return

        print("🚀 Memulai pengisian data ujian dan soal dummy...")

        # 1. Membuat Data Ujian Utama (Pemrograman Jaringan)
        exam_pj = models.Exam(
            title="Ujian Tengah Semester - Pemrograman Jaringan",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2)
        )
        db.add(exam_pj)
        db.flush()  # Mengambil ID dari exam_pj setelah dimasukkan ke antrean database

        # 2. Membuat Soal-soal untuk Ujian Pemrograman Jaringan
        q1 = models.Question(
            exam_id=exam_pj.id,
            question_text="Protokol manakah di bawah ini yang menyediakan komunikasi yang reliable, ordered, dan error-checked?",
            choices=["UDP", "TCP", "ICMP", "DNS"],
            correct_answer="TCP"
        )

        q2 = models.Question(
            exam_id=exam_pj.id,
            question_text="Apa komponen utama dalam Async Socket Programming di Python yang berfungsi mengelola jalurnya eksekusi coroutine?",
            choices=["Multi-threading", "Event Loop", "Process Pool", "Garbage Collector"],
            correct_answer="Event Loop"
        )

        q3 = models.Question(
            exam_id=exam_pj.id,
            question_text="Format serialization mana yang berbasis teks, ringan, dan paling umum digunakan untuk pertukaran data pada API modern?",
            choices=["Protocol Buffers", "XML", "JSON", "Java Serialization"],
            correct_answer="JSON"
        )

        db.add_all([q1, q2, q3])

        # 3. Membuat Data Ujian Tambahan sebagai Variasi
        exam_mat = models.Exam(
            title="Kuis 1 - Matematika Diskrit",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=1)
        )
        db.add(exam_mat)
        db.flush()

        q_mat1 = models.Question(
            exam_id=exam_mat.id,
            question_text="Jika p bernilai Benar dan q bernilai Salah, berapakah nilai kebenaran dari p AND q?",
            choices=["Benar", "Salah", "Tidak Terdefinisi", "Bisa Benar/Salah"],
            correct_answer="Salah"
        )
        db.add(q_mat1)

        # Commit semua transaksi ke dalam file SQLite
        db.commit()
        print("✅ Seeding berhasil! Data ujian dan soal dummy siap digunakan.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding gagal karena terjadi error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()