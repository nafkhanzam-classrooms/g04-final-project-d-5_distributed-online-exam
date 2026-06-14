import grpc
from concurrent import futures
import time
import grading_pb2
import grading_pb2_grpc
from sqlalchemy import create_engine, Table, MetaData, select

# Koneksi langsung ke database MySQL di dalam Docker container
DATABASE_URL = "mysql+pymysql://does_user:does_password@db:3306/does_db"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

class GradingService(grading_pb2_grpc.GradingServiceServicer):
    def GradeSubmission(self, request, context):
        print(f"[gRPC GRADER] Memproses penilaian untuk User ID: {request.user_id}, Question ID: {request.question_id}", flush=True)
        
        # Ambil input mahasiswa dan bersihkan dari spasi serta ubah ke huruf kecil
        submitted_answer = request.submitted_answer.strip().lower()
        
        is_correct = False
        score = 0
        feedback = "Jawaban Salah"

        try:
            # Ambil kunci jawaban secara dinamis dari tabel 'questions'
            with engine.connect() as connection:
                questions_table = Table('questions', metadata, autoload_with=engine)
                stmt = select(questions_table.c.correct_answer).where(questions_table.c.id == request.question_id)
                result = connection.execute(stmt).fetchone()

                if result:
                    correct_answer = str(result[0]).strip().lower()
                    print(f"[gRPC] Mencocokkan Kunci: '{correct_answer}' VS Input: '{submitted_answer}'", flush=True)

                    if submitted_answer == correct_answer:
                        is_correct = True
                        score = 100
                        feedback = "Jawaban Tepat! Skor Maksimal Berhasil Diraih."
                else:
                    feedback = "Error: ID Soal tidak ditemukan di database."

        except Exception as e:
            print(f"[gRPC ERROR] Kegagalan sistem database: {e}", flush=True)
            feedback = f"Error Sistem Grading: {str(e)}"

        return grading_pb2.GradeResponse(
            score=score,
            is_correct=is_correct,
            feedback=feedback
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grading_pb2_grpc.add_GradingServiceServicer_to_server(GradingService(), server)
    server.add_insecure_port('[::]:50051')
    print("🚀 [gRPC GRADING SERVER] Berjalan aktif di port 50051...", flush=True)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()