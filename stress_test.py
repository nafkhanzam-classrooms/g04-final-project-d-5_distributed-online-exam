import asyncio
import json
import time

# ⚠️ Ganti dengan Token JWT asli milik 'mahasiswa' Anda yang masih berlaku
VALID_TOKEN = "PASTE_TOKEN_JWT_ANDA_DI_SINI"

async def simulate_synthetic_student(bot_id):
    try:
        start_time = time.time()
        
        # 1. Buka Koneksi TCP ke Exam Server
        reader, writer = await asyncio.open_connection('127.0.0.1', 9000)

        # 2. Minta Soal
        req_payload = {"action": "request_questions", "token": VALID_TOKEN, "exam_id": 1}
        writer.write(json.dumps(req_payload).encode('utf-8'))
        await writer.drain()
        await reader.read(4096) # Abaikan isinya, kita hanya tes beban

        # 3. Langsung Tembak Jawaban
        ans_payload = {
            "action": "submit_answer",
            "token": VALID_TOKEN,
            "exam_id": 1,
            "user_id": 1, # Gunakan user 1 agar lolos Foreign Key
            "question_id": 1,
            "answer": f"TCP (Jawaban dari Bot {bot_id})"
        }
        writer.write(json.dumps(ans_payload).encode('utf-8'))
        await writer.drain()

        # 4. Tunggu hasil grading (gRPC)
        await reader.read(4096) 

        # Tutup koneksi
        writer.close()
        await writer.wait_closed()
        
        end_time = time.time()
        latency = end_time - start_time
        return True, latency
        
    except Exception as e:
        return False, str(e)

async def main():
    NUM_BOTS = 1000  # Mulai dari 100, lalu naikkan ke 500 atau 1000
    
    print(f"🚀 Mengerahkan {NUM_BOTS} user sintetis ke server...")
    start_total = time.time()
    
    # Jalankan semua bot secara serentak (concurrent)
    tasks = [simulate_synthetic_student(i) for i in range(NUM_BOTS)]
    results = await asyncio.gather(*tasks)
    
    end_total = time.time()
    
    # Rekap Hasil
    sukses = [r for r in results if r[0] == True]
    gagal = [r for r in results if r[0] == False]
    
    print("\n" + "="*30)
    print("📊 HASIL STRESS TEST")
    print("="*30)
    print(f"Total Bot      : {NUM_BOTS}")
    print(f"Waktu Total    : {end_total - start_total:.2f} detik")
    print(f"Berhasil (✅)  : {len(sukses)}")
    print(f"Gagal (❌)     : {len(gagal)}")
    
    if sukses:
        avg_latency = sum([r[1] for r in sukses]) / len(sukses)
        print(f"Rata-rata Ping : {avg_latency:.4f} detik per bot")
        
    if gagal:
        print("\nContoh Error:")
        print(gagal[0][1]) # Tampilkan 1 contoh alasan gagal

if __name__ == "__main__":
    asyncio.run(main())