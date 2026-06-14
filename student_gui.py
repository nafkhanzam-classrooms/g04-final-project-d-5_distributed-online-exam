import customtkinter as ctk
import socket
import json
import threading
import time
import requests
from tkinter import messagebox

# ==========================================
# KONFIGURASI JARINGAN & SERVER
# ==========================================
AUTH_URL = "http://localhost:8001/auth/login"
TCP_HOST = '127.0.0.1'
TCP_PORT = 9000
UDP_PORT = 9001

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class StudentApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DOES - Distributed Online Examination System")
        self.geometry("900x650")
        self.resizable(False, False)

        # Variabel State Aplikasi
        self.token = None
        self.username = None
        self.current_exam_id = None
        self.answer_entries = {}
        self.time_left = 600      
        self.timer_running = False

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        self.login_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dashboard_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.exam_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")

        self.build_login_frame()
        self.show_frame(self.login_frame)

    def show_frame(self, frame_to_show):
        for frame in (self.login_frame, self.dashboard_frame, self.exam_frame):
            frame.pack_forget()
        frame_to_show.pack(fill="both", expand=True)

    # ==========================================
    # HALAMAN 1: LOGIN
    # ==========================================
    def build_login_frame(self):
        card = ctk.CTkFrame(self.login_frame, width=400, height=450, corner_radius=15)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="Selamat Datang di DOES", font=("Arial", 24, "bold")).pack(pady=(40, 10))
        ctk.CTkLabel(card, text="Masuk untuk memulai ujian Anda", text_color="gray").pack(pady=(0, 30))

        self.entry_username = ctk.CTkEntry(card, placeholder_text="Username (misal: student1)", width=300, height=40)
        self.entry_username.pack(pady=10)

        self.entry_password = ctk.CTkEntry(card, placeholder_text="Password", width=300, height=40, show="*")
        self.entry_password.pack(pady=10)

        self.btn_login = ctk.CTkButton(card, text="LOGIN", width=300, height=45, font=("Arial", 14, "bold"), command=self.process_login)
        self.btn_login.pack(pady=30)

    def process_login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showwarning("Peringatan", "Username dan Password tidak boleh kosong!")
            return

        self.btn_login.configure(text="Memverifikasi...", state="disabled")
        self.update()

        try:
            payload = {"username": username, "password": password}
            response = requests.post(AUTH_URL, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.username = username
                
                threading.Thread(target=self.udp_heartbeat_loop, daemon=True).start()
                
                self.build_dashboard_frame()
                self.show_frame(self.dashboard_frame)
            else:
                messagebox.showerror("Akses Ditolak", "Username atau Password salah!")
        except Exception as e:
            messagebox.showerror("Error Koneksi", f"Gagal menghubungi Auth Server:\n{e}")
        finally:
            self.btn_login.configure(text="LOGIN", state="normal")

    # ==========================================
    # HALAMAN 2: DASHBOARD (Dengan Tombol Logout)
    # ==========================================
    def build_dashboard_frame(self):
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(self.dashboard_frame, height=80, corner_radius=0, fg_color="#1F497D")
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(header, text="DOES Dashboard", font=("Arial", 20, "bold"), text_color="white").pack(side="left", padx=30, pady=25)
        
        # Tombol LOGOUT ditaruh di sudut kanan header
        ctk.CTkButton(header, text="Logout", width=80, height=32, fg_color="#E74C3C", hover_color="#C0392B", font=("Arial", 12, "bold"), command=self.process_logout).pack(side="right", padx=30, pady=24)
        ctk.CTkLabel(header, text=f"👤 {self.username} | 🟢 Online ", font=("Arial", 14), text_color="#A3E4D7").pack(side="right", padx=5, pady=25)

        content = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=40)

        # FIXED FIX: 'mb' diganti dengan 'pady' untuk menghindari bad option error
        ctk.CTkLabel(content, text="Daftar Ujian Tersedia", font=("Arial", 22, "bold")).pack(anchor="w", pady=(0, 20))

        card1 = ctk.CTkFrame(content, fg_color="white", corner_radius=10, height=100)
        card1.pack(fill="x", pady=10)
        ctk.CTkLabel(card1, text="Kuis 1: Jaringan & Protokol", font=("Arial", 16, "bold"), text_color="black").pack(side="left", padx=20, pady=20)
        ctk.CTkButton(card1, text="Mulai Kerjakan", width=120, command=lambda: self.fetch_and_start_exam(1)).pack(side="right", padx=20, pady=20)

        card2 = ctk.CTkFrame(content, fg_color="white", corner_radius=10, height=100)
        card2.pack(fill="x", pady=10)
        ctk.CTkLabel(card2, text="Kuis 2: Arsitektur Sistem Terdistribusi", font=("Arial", 16, "bold"), text_color="black").pack(side="left", padx=20, pady=20)
        ctk.CTkButton(card2, text="Mulai Kerjakan", width=120, command=lambda: self.fetch_and_start_exam(2)).pack(side="right", padx=20, pady=20)

    def process_logout(self):
        """Fungsi untuk membersihkan session dan kembali ke login"""
        self.token = None
        self.username = None
        self.current_exam_id = None
        self.entry_username.delete(0, 'end')
        self.entry_password.delete(0, 'end')
        self.show_frame(self.login_frame)

    # ==========================================
    # HALAMAN 3: LAYAR UJIAN
    # ==========================================
    def fetch_and_start_exam(self, exam_id):
        self.current_exam_id = exam_id
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((TCP_HOST, TCP_PORT))
            
            payload = {"action": "request_questions", "token": self.token, "exam_id": exam_id}
            client_socket.sendall(json.dumps(payload).encode('utf-8'))
            
            response_data = client_socket.recv(4096)
            response = json.loads(response_data.decode('utf-8'))
            client_socket.close()

            questions = response.get("questions", [])
            if not questions:
                messagebox.showinfo("Info", "Soal belum tersedia untuk ujian ini.")
                return

            self.build_exam_frame(questions)
            self.show_frame(self.exam_frame)
            
            self.time_left = 600 
            self.timer_running = True
            self.update_timer()

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengambil soal dari server:\n{e}")

    def build_exam_frame(self, questions):
        for widget in self.exam_frame.winfo_children():
            widget.destroy()
        
        self.answer_entries.clear()

        header = ctk.CTkFrame(self.exam_frame, height=60, corner_radius=0)
        header.pack(fill="x", side="top")
        ctk.CTkLabel(header, text=f"Sedang Mengerjakan: Kuis {self.current_exam_id}", font=("Arial", 16, "bold")).pack(side="left", padx=20)
        
        self.lbl_timer = ctk.CTkLabel(header, text="⏳ Sisa Waktu: 10:00", font=("Arial", 16, "bold"), text_color="#E74C3C")
        self.lbl_timer.pack(side="right", padx=20)

        scroll_area = ctk.CTkScrollableFrame(self.exam_frame, fg_color="transparent")
        scroll_area.pack(fill="both", expand=True, padx=20, pady=20)

        for idx, q in enumerate(questions):
            card = ctk.CTkFrame(scroll_area, fg_color="white", corner_radius=8)
            card.pack(fill="x", pady=10, ipady=10)
            
            lbl_q = ctk.CTkLabel(card, text=q['question_text'], font=("Arial", 14), text_color="black", justify="left", wraplength=750)
            lbl_q.pack(anchor="w", padx=20, pady=(10, 5))
            
            entry_ans = ctk.CTkEntry(card, placeholder_text="Ketik jawaban singkat Anda di sini...", width=400)
            entry_ans.pack(anchor="w", padx=20, pady=(0, 10))
            
            self.answer_entries[q['question_id']] = entry_ans

        footer = ctk.CTkFrame(self.exam_frame, fg_color="transparent")
        footer.pack(fill="x", pady=10)
        
        self.btn_submit = ctk.CTkButton(footer, text="KIRIM JAWABAN", font=("Arial", 14, "bold"), width=200, height=45, fg_color="#27AE60", hover_color="#2ECC71", command=self.submit_exam)
        self.btn_submit.pack(pady=10)

    def update_timer(self):
        if self.timer_running and self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            self.lbl_timer.configure(text=f"⏳ Sisa Waktu: {mins:02d}:{secs:02d}")
            self.time_left -= 1
            self.after(1000, self.update_timer)
        elif self.time_left == 0 and self.timer_running:
            self.timer_running = False
            messagebox.showwarning("Waktu Habis!", "Waktu ujian telah habis. Jawaban akan dikirim secara otomatis.")
            self.submit_exam()

    def submit_exam(self):
        self.timer_running = False 
        self.btn_submit.configure(state="disabled", text="Memproses Penilaian...")
        self.update()

        total_score = 0
        total_questions = len(self.answer_entries)
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((TCP_HOST, TCP_PORT))

            user_id = 1 if self.username == "student1" else 2

            for q_id, entry in self.answer_entries.items():
                jawaban = entry.get().strip()
                
                payload = {
                    "action": "submit_answer",
                    "token": self.token,
                    "exam_id": self.current_exam_id,
                    "user_id": user_id,
                    "question_id": q_id,
                    "answer": jawaban
                }
                
                client_socket.sendall(json.dumps(payload).encode('utf-8'))
                
                resp_data = client_socket.recv(4096)
                if not resp_data: continue
                
                resp = json.loads(resp_data.decode('utf-8'))
                total_score += resp.get("score", 0)

            client_socket.close()

            final_score = total_score / total_questions if total_questions > 0 else 0
            messagebox.showinfo("Ujian Selesai 🎉", f"Seluruh jawaban berhasil dinilai oleh Grading Server.\n\nSkor Akhir Anda: {final_score:.0f} / 100")
            
            self.build_dashboard_frame()
            self.show_frame(self.dashboard_frame)

        except Exception as e:
            messagebox.showerror("Error TCP", f"Terjadi kesalahan saat mengirim jawaban:\n{e}")
        finally:
            self.btn_submit.configure(state="normal", text="KIRIM JAWABAN")

    def udp_heartbeat_loop(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while self.token is not None:
            try:
                payload = json.dumps({"action": "heartbeat", "token": self.token}).encode('utf-8')
                udp_socket.sendto(payload, (TCP_HOST, UDP_PORT))
                time.sleep(5)
            except Exception:
                break

if __name__ == "__main__":
    app = StudentApp()
    app.mainloop()