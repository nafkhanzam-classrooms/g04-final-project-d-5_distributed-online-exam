import socket
import json
import jwt
from datetime import datetime
from app.database import SessionLocal
from app.models import User

# ⚠️ PENTING: Sesuaikan SECRET_KEY dan ALGORITHM dengan 
# yang Anda gunakan di fungsi login FastAPI Anda (main.py)
SECRET_KEY = "7b3c9a4e2d1f8b6a5c0e9d8f7b6a5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
ALGORITHM = "HS256"

UDP_IP = "0.0.0.0"
UDP_PORT = 9001

def start_monitoring_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"🚀 [UDP MONITORING SERVER] Berjalan di port {UDP_PORT}...", flush=True)

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            payload = json.loads(data.decode('utf-8'))
            
            if payload.get("action") == "heartbeat":
                token = payload.get("token")
                
                # 1. Ekstrak identitas dari token
                try:
                    # Kita abaikan opsi kedaluwarsa (verify_exp=False) khusus untuk UDP 
                    # agar proses sangat ringan dan cepat.
                    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
                    username = decoded.get("sub") # Biasanya identitas disimpan di "sub"
                    
                    if username:
                        # 2. Buka database & update waktu aktif
                        db = SessionLocal()
                        try:
                            user = db.query(User).filter(User.username == username).first()
                            if user:
                                user.last_active = datetime.now()
                                db.commit()
                                print(f"💓 Heartbeat dari {username} dicatat pada {user.last_active.strftime('%H:%M:%S')}", flush=True)
                        finally:
                            db.close()
                except jwt.ExpiredSignatureError:
                    print("⚠️ Token heartbeat kedaluwarsa.", flush=True)
                except jwt.InvalidTokenError as e:
                    print(f"⚠️ Gagal membaca token: {e}", flush=True) # Sekarang akan mencetak alasan errornya
        except Exception as e:
            print(f"❌ Error sistem UDP: {e}", flush=True)

if __name__ == "__main__":
    start_monitoring_server()