import asyncio
import json
import os
import sys
import grpc

# 1. Daftarkan Root Project (does/)
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Daftarkan langsung folder grading_service
grading_path = os.path.join(project_root, 'grading_service')
if grading_path not in sys.path:
    sys.path.insert(0, grading_path)

# Modul gRPC
from grading_service import grading_pb2
from grading_service import grading_pb2_grpc

# Modul Internal & Asinkron
from app import models
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# ==========================================
# SETUP DATABASE ASINKRON KHUSUS TCP SERVER
# ==========================================
ASYNC_DB_URL = "mysql+aiomysql://does_user:does_password@db:3306/does_db"

engine = create_async_engine(ASYNC_DB_URL, pool_size=20, max_overflow=50)
AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# ==========================================
# FUNGSI PEMROSESAN (FULL ASYNC)
# ==========================================
async def process_request_questions(payload: dict) -> dict:
    exam_id = int(payload.get("exam_id", 0))
    print(f"   [CCTV] Mencari soal untuk Exam ID: {exam_id}", flush=True)
    
    # Membuka sesi asinkron
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Question).filter(models.Question.exam_id == exam_id))
        soal = result.scalars().all()
        
        print(f"   [CCTV] Jumlah soal ditemukan: {len(soal)}", flush=True)
        
        if not soal:
            return {"questions": []}
            
        questions = [{"question_id": q.id, "question_text": q.question_text} for q in soal]
        return {"questions": questions}

async def process_submit_answer(payload: dict) -> dict:
    print("   [CCTV] 1. Memulai proses submit answer (ASYNC)...", flush=True)
    try:
        print("   [CCTV] 2. Membuka channel gRPC ke localhost:50051...", flush=True)
        # Menggunakan gRPC Asinkron (grpc.aio)
        async with grpc.aio.insecure_channel('grading-service:50051') as channel:
            stub = grading_pb2_grpc.GradingServiceStub(channel)
            
            print("   [CCTV] 3. Menembakkan data ke Grading Server...", flush=True)
            # AWAIT pada pemanggilan gRPC
            response = await stub.GradeSubmission(grading_pb2.GradeRequest(
                user_id=int(payload.get("user_id", 0)),
                question_id=int(payload.get("question_id", 0)),
                submitted_answer=payload.get("answer", "")
            ))
            
            print(f"   [CCTV] 4. Balasan gRPC diterima! Skor: {response.score}", flush=True)
            
            print("   [CCTV] 5. Membuka koneksi database MySQL (aiomysql)...", flush=True)
            # AWAIT pada operasi Database
            async with AsyncSessionLocal() as db:
                print("   [CCTV] 6. Menyiapkan model Answer untuk disimpan...", flush=True)
                new_answer = models.Answer(
                    user_id=int(payload.get("user_id")),
                    exam_id=int(payload.get("exam_id")),
                    question_id=int(payload.get("question_id")),
                    submitted_answer=payload.get("answer"),
                    score=int(payload.get("score", response.score))
                )
                db.add(new_answer)
                
                print("   [CCTV] 7. Melakukan await db.commit()...", flush=True)
                await db.commit()
                print("   [CCTV] 8. Commit berhasil!", flush=True)
                
            print("   [CCTV] 9. Mengembalikan respons ke mahasiswa.", flush=True)
            return {
                "status": "success", 
                "is_correct": response.is_correct, 
                "score": response.score,
                "feedback": response.feedback
            }
    except Exception as e:
        print(f"   [CCTV] ❌ ERROR FATAL DI PROSES SUBMIT: {e}", flush=True)
        return {"status": "error", "message": str(e)}

# ==========================================
# TCP SERVER CORE
# ==========================================
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"🔗 Koneksi baru dari {addr}", flush=True)
    
    try:
        while True:
            data = await reader.read(4096)
            if not data: break
            
            payload = json.loads(data.decode('utf-8'))
            action = payload.get("action")
            
            if action == "request_questions":
                # Langsung AWAIT, tidak perlu loop.run_in_executor lagi
                response = await process_request_questions(payload)
                
            elif action == "submit_answer":
                # Langsung AWAIT
                response = await process_submit_answer(payload)
                
            else:
                response = {"status": "error", "message": "Aksi tidak dikenal"}
            
            writer.write(json.dumps(response).encode('utf-8'))
            await writer.drain()
            
    except Exception as e:
        print(f"❌ Error pada client {addr}: {e}", flush=True)
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"👋 Koneksi {addr} ditutup.", flush=True)

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 9000)
    print("🚀 [TCP EXAM SERVER] Berjalan di port 9000 (FULL ASYNC)...", flush=True)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server dihentikan.", flush=True)