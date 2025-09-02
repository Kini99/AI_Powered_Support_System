from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    role: str
    user_id: str
    email: str
    session_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: str
    
    class Config:
        from_attributes = True