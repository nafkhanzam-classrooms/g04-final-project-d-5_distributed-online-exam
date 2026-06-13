import grpc
from concurrent import futures
import grading_pb2
import grading_pb2_grpc

class GradingService(grading_pb2_grpc.GradingServiceServicer):
    def GradeSubmission(self, request, context):
        print(f"🔍 [GRADING] Memeriksa jawaban untuk User {request.user_id}, Soal {request.question_id}")
        
        correct_answer = "TCP"
        is_correct = (request.submitted_answer == correct_answer)
        score = 100 if is_correct else 0
        feedback = "Selamat, jawaban benar!" if is_correct else "Maaf, jawaban kurang tepat."

        # TAMBAHKAN PRINT INI UNTUK BUKTI
        print(f"✅ [GRADING] Selesai menilai. Mengirim balasan: Skor {score}")
        
        return grading_pb2.GradeResponse(
            is_correct=is_correct,
            score=score,
            feedback=feedback
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grading_pb2_grpc.add_GradingServiceServicer_to_server(GradingService(), server)
    server.add_insecure_port('[::]:50051')
    print("🎓 [GRADING SERVICE] Siap menerima permintaan di port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()