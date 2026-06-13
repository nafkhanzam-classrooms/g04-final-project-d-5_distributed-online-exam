import asyncio
import json
import socket
import time

async def send_udp_heartbeats(token: str, exam_id: int):
    """
    Background task untuk mengirimkan sinyal kehadiran secara periodik
    menggunakan UDP (User Datagram Protocol).
    """
    host = '127.0.0.1'
    port = 9001
    
    # Inisialisasi UDP Socket (SOCK_DGRAM)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("\n🚀 [UDP] Background task heartbeat dimulai...")
    try:
        while True:
            payload = {
                "action": "heartbeat",
                "token": token,
                "exam_id": exam_id,
                "timestamp": time.time()
            }
            
            # Object Serialization: Dict -> JSON -> Bytes
            message = json.dumps(payload).encode('utf-8')
            
            # Protokol UDP: Fire and Forget. 
            # Kita lempar data ke jaringan tanpa perlu melakukan koneksi (*connectionless*)
            udp_socket.sendto(message, (host, port))
            print(f"   -> 💓 [UDP] Heartbeat dikirim! (Timestamp: {payload['timestamp']:.2f})")
            
            # Beri jeda 5 detik untuk pengiriman berikutnya
            await asyncio.sleep(5)
            
    except asyncio.CancelledError:
        # Menangkap sinyal pembatalan saat ujian sudah selesai
        print("🛑 [UDP] Sinyal ujian selesai diterima. Menghentikan heartbeat.")
    finally:
        udp_socket.close()

async def tcp_client(token: str, exam_id: int):
    host = '127.0.0.1'
    port = 9000

    # ====================================================
    # MENJALANKAN BACKGROUND TASK
    # ====================================================
    # asyncio.create_task melepaskan fungsi UDP agar berjalan mandiri di latar belakang
    heartbeat_task = asyncio.create_task(send_udp_heartbeats(token, exam_id))

    print(f"🔄 Menghubungkan ke TCP Exam Server di {host}:{port}...")
    try:
        # Membuka koneksi TCP
        reader, writer = await asyncio.open_connection(host, port)
        print("✅ Berhasil terhubung ke server TCP ujian!")

        # --- TAHAP 1: MEMINTA SOAL ---
        req_payload = {
            "action": "request_questions",
            "token": token,
            "exam_id": exam_id
        }
        writer.write(json.dumps(req_payload).encode('utf-8'))
        await writer.drain()

        data = await reader.read(4096)
        response_json = json.loads(data.decode('utf-8'))
        print("📥 [TAHAP 1] Daftar soal berhasil diterima.")
        
        questions = response_json.get("questions", [])
        if not questions:
            print("❌ Tidak ada soal yang bisa dijawab.")
            writer.close()
            await writer.wait_closed()
            return

        first_question_id = questions[0]["question_id"]

        # --- SIMULASI BERPIKIR (Diperpanjang menjadi 12 Detik) ---
        print(f"\n⏳ Mahasiswa sedang membaca dan berpikir selama 12 detik...")
        print("👀 Perhatikan log: Background Task UDP akan tetap berjalan mandiri dan menembakkan paket setiap 5 detik!")
        await asyncio.sleep(12) 

        # --- TAHAP 2: MENGIRIM JAWABAN ---
        ans_payload = {
            "action": "submit_answer",
            "token": token,
            "exam_id": exam_id,
            "user_id": 1, 
            "question_id": first_question_id,
            "answer": "TCP"
        }
        
        print(f"\n📤 [TAHAP 2] Mengirim jawaban...")
        writer.write(json.dumps(ans_payload).encode('utf-8'))
        await writer.drain()

        # Menerima balasan yang berisi nilai
        data2 = await reader.read(4096)
        ans_response_json = json.loads(data2.decode('utf-8'))
        
        # ---> TAMBAHKAN BLOK PRINT INI <---
        print("\n📥 [TAHAP 2] Hasil Penilaian Diterima:")
        print(f"   • Status  : {ans_response_json.get('status')}")
        print(f"   • Benar?  : {ans_response_json.get('is_correct')}")
        print(f"   • Skor    : {ans_response_json.get('score')}")
        print(f"   • Feedback: {ans_response_json.get('feedback')}")
        # ----------------------------------

        # Menutup koneksi TCP secara elegan
        print("\n👋 Ujian selesai. Menutup koneksi TCP.")
        writer.close()
        await writer.wait_closed()

    except ConnectionRefusedError:
        print("❌ Koneksi TCP ditolak! Pastikan Exam Server berjalan.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan jaringan TCP: {e}")
    finally:
        # ====================================================
        # MEMBERSIHKAN BACKGROUND TASK
        # ====================================================
        # Kita harus mematikan task UDP secara manual agar tidak berjalan selamanya
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    print("=== 🎓 Simulasi Ujian DOES (TCP & UDP) ===")
    user_token = input("\n🔑 Paste Token JWT Anda di sini: ").strip()
    
    if user_token:
        asyncio.run(tcp_client(token=user_token, exam_id=1))
    else:
        print("❌ Token tidak boleh kosong.")