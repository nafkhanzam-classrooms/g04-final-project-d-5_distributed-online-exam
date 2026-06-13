from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    last_active = Column(DateTime, nullable=True)

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Relasi ke tabel Question (Satu ujian memiliki banyak soal)
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_text = Column(String(255), nullable=False)
    choices = Column(JSON, nullable=False)  # Menyimpan list pilihan seperti ["A", "B", "C", "D"]
    correct_answer = Column(String(255), nullable=False)

    # Relasi balik ke Exam
    exam = relationship("Exam", back_populates="questions")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    submitted_answer = Column(String(255), nullable=False)
    score = Column(Integer, nullable=True)