import customtkinter as ctk
import tkinter.messagebox as messagebox
import asyncio
import threading
import json
import socket
import time

# Set tema dasar
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ExamClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DOES - Student Exam Portal")
        self.geometry("600x400")
        self.resizable(False, False)

        self.user_token = ""
        self.exam_id = 1
        self.current_question_id = None
        
        # Variabel untuk sinkronisasi Thread UI dan Background
        self.answer_event = None
        self.user_answer = ""

        self.show_login_frame()

    # ==========================================
    # HALAMAN 1: LOGIN / INPUT TOKEN
    # ==========================================
    def show_login_frame(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(pady=40, padx=40, fill="both", expand=True)

        title_label = ctk.CTkLabel(self.login_frame, text="Selamat Datang di DOES", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(30, 10))

        subtitle_label = ctk.CTkLabel(self.login_frame, text="Silakan masukkan Token JWT Anda untuk memulai ujian", text_color="gray")
        subtitle_label.pack(pady=(0, 30))

        self.token_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Paste Token JWT di sini...", width=400)
        self.token_entry.pack(pady=10)

        connect_btn = ctk.CTkButton(self.login_frame, text="Mulai Ujian", command=self.start_connection)
        connect_btn.pack(pady=20)

    # ==========================================
    # HALAMAN 2: DASHBOARD UJIAN
    # ==========================================
    def show_exam_frame(self):
        if hasattr(self, 'login_frame'):
            self.login_frame.destroy()

        self.exam_frame = ctk.CTkFrame(self)
        self.exam_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.exam_frame, text="🟡 Menghubungkan ke Server...", text_color="orange", font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(pady=(10, 20))

        self.question_textbox = ctk.CTkTextbox(self.exam_frame, width=500, height=100)
        self.question_textbox.pack(pady=10)
        self.question_textbox.insert("0.0", "Menunggu soal dari server...")
        self.question_textbox.configure(state="disabled")

        self.answer_entry = ctk.CTkEntry(self.exam_frame, placeholder_text="Ketik jawaban Anda di sini...", width=300)
        self.answer_entry.pack(pady=20)

        self.submit_btn = ctk.CTkButton(self.exam_frame, text="Kirim Jawaban", command=self.submit_answer)
        self.submit_btn.pack(pady=10)

    # ==========================================
    # JEMBATAN UI & JARINGAN
    # ==========================================
    def start_connection(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Token tidak boleh kosong!")
            return
            
        self.user_token = token
        self.show_exam_frame()
        
        # ⚠️ PENTING: Jalankan jaringan di Background Thread agar UI tidak freeze
        threading.Thread(target=self.run_network_thread, daemon=True).start()

    def submit_answer(self):
        answer = self.answer_entry.get().strip()
        if not answer:
            messagebox.showwarning("Peringatan", "Jawaban tidak boleh kosong!")
            return

        # Simpan jawaban ke variabel
        self.user_answer = answer
        self.submit_btn.configure(state="disabled", text="Mengirim...")
        
        # Beri sinyal ke background thread untuk melanjutkan pengiriman
        if self.answer_event:
            self.answer_event.set()

    # Fungsi pembantu untuk mengupdate UI dari background thread dengan aman
    def safe_update_ui(self, func, *args):
        self.after(0, func, *args)

    def update_question_ui(self, q_id, q_text):
        self.current_question_id = q_id
        self.status_label.configure(text="🟢 Terhubung (Ujian Berlangsung)", text_color="green")
        self.question_textbox.configure(state="normal")
        self.question_textbox.delete("0.0", "end")
        self.question_textbox.insert("0.0", f"Soal No {q_id}:\n{q_text}")
        self.question_textbox.configure(state="disabled")

    def update_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    def show_final_result(self, is_correct, score, feedback):
        self.update_status("🔴 Ujian Selesai (Koneksi Ditutup)", "red")
        title = "Hasil Penilaian"
        msg = f"Status: Sukses\nSkor: {score}\nFeedback: {feedback}"
        # Tampilkan popup
        self.after(0, lambda: messagebox.showinfo(title, msg))

    # ==========================================
    # LOGIKA JARINGAN (BERJALAN DI BACKGROUND)
    # ==========================================
    def run_network_thread(self):
        """Membuat event loop baru khusus untuk thread ini"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.async_network_logic())
        loop.close()

    async def async_network_logic(self):
        host, tcp_port, udp_port = '127.0.0.1', 9000, 9001
        
        # 1. Jalankan UDP Heartbeat
        heartbeat_task = asyncio.create_task(self.send_udp_heartbeats(host, udp_port))
        
        try:
            # 2. Buka Koneksi TCP
            reader, writer = await asyncio.open_connection(host, tcp_port)
            
            # 3. Minta Soal
            req_payload = {"action": "request_questions", "token": self.user_token, "exam_id": self.exam_id}
            writer.write(json.dumps(req_payload).encode('utf-8'))
            await writer.drain()

            data = await reader.read(4096)
            response_json = json.loads(data.decode('utf-8'))
            questions = response_json.get("questions", [])
            
            if questions:
                q_id = questions[0]["question_id"]
                q_text = questions[0].get("question_text", "Pertanyaan tidak ditemukan.")
                
                # Update UI dengan soal asli dari server
                self.safe_update_ui(self.update_question_ui, q_id, q_text)
                
                # 4. Tunggu Mahasiswa Klik Tombol "Kirim"
                self.answer_event = asyncio.Event()
                await self.answer_event.wait() # <--- Menjeda eksekusi thread ini sampai UI mengirim sinyal
                
                # 5. Kirim Jawaban
                ans_payload = {
                    "action": "submit_answer",
                    "token": self.user_token,
                    "exam_id": self.exam_id,
                    "user_id": 1, 
                    "question_id": q_id,
                    "answer": self.user_answer
                }
                writer.write(json.dumps(ans_payload).encode('utf-8'))
                await writer.drain()

                # 6. Terima Hasil
                data2 = await reader.read(4096)
                ans_resp = json.loads(data2.decode('utf-8'))
                
                # Tampilkan skor asli ke UI
                self.safe_update_ui(self.show_final_result, ans_resp.get('is_correct'), ans_resp.get('score'), ans_resp.get('feedback'))

            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            self.safe_update_ui(self.update_status, f"❌ Error: {e}", "red")
            
        finally:
            # Matikan UDP saat selesai
            heartbeat_task.cancel()

    async def send_udp_heartbeats(self, host, port):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            while True:
                payload = {
                    "action": "heartbeat",
                    "token": self.user_token,
                    "exam_id": self.exam_id,
                    "timestamp": time.time()
                }
                udp_socket.sendto(json.dumps(payload).encode('utf-8'), (host, port))
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        finally:
            udp_socket.close()

if __name__ == "__main__":
    app = ExamClientGUI()
    app.mainloop()