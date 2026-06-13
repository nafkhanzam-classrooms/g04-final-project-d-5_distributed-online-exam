[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/4SHtB1vz)
# 🚀 DOES (Distributed Online Examination System)

DOES adalah platform pelaksanaan ujian *online* berskala *Enterprise* yang dirancang menggunakan arsitektur **Microservices**. Proyek ini mendemonstrasikan keandalan sistem terdistribusi dalam menangani lonjakan koneksi (ribuan *request* serentak) menggunakan berbagai protokol jaringan yang dioptimalkan, *Asynchronous I/O*, dan TCP Load Balancing.

## 🛠️ Teknologi & Stack Utama
- **Bahasa:** Python 3.10+
- **Protokol:** TCP (Raw Sockets), UDP, HTTP/REST, gRPC (HTTP/2)
- **Framework:** FastAPI, Asyncio, SQLAlchemy, CustomTkinter (Frontend Desktop)
- **Database:** MySQL (dengan `aiomysql` untuk *Async DB Engine*)
- **Infrastruktur & Orkestrasi:** Docker, Docker Compose, Nginx (TCP Stream Load Balancer)

---

## 📂 Struktur Direktori & Penjelasan File

Berikut adalah bedah teknis dari setiap komponen dan *file* yang membangun sistem DOES:

### 1. Orkestrasi & Konfigurasi Infrastruktur
File-file ini bertugas mengatur bagaimana setiap *container* berjalan dan saling berkomunikasi.

* **`docker-compose.yml`**
  * Bertanggung jawab mendeploy 6 layanan/container terisolasi: `db` (MySQL), `auth-web` (FastAPI), `grading-service` (gRPC), `monitoring-server` (UDP), `exam-server` (TCP, 3 replicas), dan `nginx-lb` (Load Balancer).
* **`nginx.conf`**
  * Konfigurasi Nginx khusus untuk modul `stream` (TCP Layer 4). Membagi beban jaringan (Load Balancing) secara *round-robin* dari *port* 9000 ke 3 replika `exam-server` di *backend*.
* **`requirements.txt`**
  * Daftar seluruh pustaka Python yang dibutuhkan sistem (FastAPI, grpcio, SQLAlchemy, aiomysql, PyJWT, dll).

### 2. Modul Core FastAPI & Database (`/app`)
Berisi logika web server berbasis REST API untuk Manajemen Dosen dan Autentikasi Mahasiswa.

* **`app/main.py`**
  * *Entry point* FastAPI. Menyediakan *endpoint* dengan fitur CORS.
  * `create_exam()` & `create_question()`: *Endpoint* admin (Dosen) untuk menyuntikkan ujian dan soal ke MySQL.
  * `get_exam_results()`: Melakukan *query SQL Join* untuk mengambil nilai mahasiswa.
  * `monitor_students()`: Mengambil daftar mahasiswa dan membandingkan *timestamp* `last_active` untuk menentukan status Online/Offline.
* **`app/models.py`**
  * Definisi Skema Database (ORM SQLAlchemy). Terdiri dari kelas `User`, `Exam`, `Question`, dan `Answer`. Berisi relasi *Foreign Key* dan atribut krusial seperti `score` dan `last_active`.
* **`app/database.py`**
  * Konfigurasi *engine* sinkron (`pymysql`) khusus untuk digunakan oleh FastAPI dan *script seeding*.
* **`app/security.py`**
  * `create_access_token()`: Menghasilkan JSON Web Token (JWT) yang dienkripsi menggunakan kunci kriptografi SHA-256 sebagai "KTP" digital mahasiswa yang aman (Stateless Auth).

### 3. Core Microservices (Layanan Backend Terdistribusi)
Setiap file di bawah ini berjalan di dalam *container* Docker-nya masing-masing tanpa mengganggu satu sama lain.

* **`exam_server.py` (Asynchronous TCP Server)**
  * Menangani lalu lintas ujian menggunakan Raw TCP Sockets dan `asyncio` untuk performa *non-blocking* maksimal.
  * `process_request_questions(payload)`: Mengambil data soal dari MySQL secara asinkron (`aiomysql`).
  * `process_submit_answer(payload)`: Menerima jawaban, menembakkan *request* penilaian ke Grading Server (via gRPC), lalu menyimpan skor ke tabel `answers` (via `aiomysql.commit()`).
  * `handle_client(reader, writer)`: Mengelola siklus hidup koneksi TCP per mahasiswa.
  * `main()`: Menginisiasi TCP Server pada *port* 9000.
* **`monitoring_server.py` (UDP Server)**
  * Menangani *heartbeat* tanpa membebani antrean TCP.
  * `start_monitoring_server()`: Membuka *socket* UDP di *port* 9001. Membaca paket masuk, mendekode JWT tanpa verifikasi kedaluwarsa demi kecepatan, dan meng-update kolom `last_active` di tabel `users` MySQL.
* **`grading_service/grading.proto`**
  * *Blueprint* struktur pesan gRPC. Mendefinisikan tipe data biner `GradeRequest` dan `GradeResponse`.
* **`grading_service/grading_server.py`** (gRPC Server)
  * `GradeSubmission(request, context)`: Fungsi penilai (*Grader*). Menerima jawaban teks mahasiswa, mencocokkannya dengan *database* atau kunci internal, dan langsung mengembalikan skor integer beserta respons *feedback*.

### 4. Klien & Pengujian
Aplikasi antarmuka yang berada di luar Docker (dioperasikan di sisi pengguna/*host*).

* **`student_gui.py` (Aplikasi Mahasiswa)**
  * GUI Desktop modern menggunakan `customtkinter`.
  * *Fungsi Login*: Menghubungi HTTP FastAPI untuk mendapatkan Token JWT.
  * *Fungsi Heartbeat (Thread terpisah)*: Mengirim paket JWT via UDP ke port 9001 setiap 5 detik secara persisten.
  * *Fungsi TCP Client*: Membuat koneksi ke *port* 9000 (Nginx LB), meminta soal, merender UI ujian, dan mengirim payload jawaban saat disubmit.
* **`admin_dashboard.html` (Web Dosen)**
  * *Dashboard Single Page Application* (SPA) menggunakan Vanilla JavaScript dan Tailwind CSS (via CDN).
  * `fetchMonitoring()`: Melakukan HTTP GET secara *polling* (setiap 3 detik) ke FastAPI untuk merender indikator 🟢 Online atau 🔴 Offline mahasiswa.
  * `fetchResults()`: Melakukan HTTP GET untuk merender *leaderboard* nilai secara *live*.
* **`seed_db.py`**
  * *Script utilitas* untuk menyuntikkan ( *inject* ) data awal ke database bersih MySQL (mendaftarkan `User` dengan *role* STUDENT dan menyuntikkan `Exam` serta `Question`).
* **`stress_test.py` (Botnet Benchmarking)**
  * Penguji batas performa server berbasis *asyncio*.
  * `simulate_synthetic_student()`: Membuka koneksi TCP, meminta soal, dan mengirim jawaban dalam hitungan milidetik.
  * `main()`: Menjalankan konkurensi (misal: 1000 *tasks* sekaligus) dan menghitung rata-rata *latency/ping* server.

---

## 🏃‍♂️ Cara Menjalankan Sistem (Quickstart)

1. **Jalankan Docker Compose:**
   ```bash
   docker-compose up -d --build
