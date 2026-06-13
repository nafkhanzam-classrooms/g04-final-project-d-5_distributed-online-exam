from pydantic import BaseModel
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str

class UserProfile(BaseModel):
    id: int
    username: str
    role: str

class ExamResponse(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "STUDENT"