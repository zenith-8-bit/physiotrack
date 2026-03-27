from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum
from . import Base

class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    qr_token = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.name} ({self.role})>"