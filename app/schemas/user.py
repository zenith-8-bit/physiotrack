from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class UserCreate(UserBase):
    role: str = "patient"  # "doctor" or "patient"

class User(UserBase):
    id: int
    role: str
    qr_token: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserQRGenerate(BaseModel):
    qr_token: str
    qr_image_base64: str
    user: User