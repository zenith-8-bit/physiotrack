from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    diagnosis = Column(String)
    surgery_date = Column(DateTime, nullable=True)
    rehab_start_date = Column(DateTime, nullable=True)
    rehab_duration_weeks = Column(Integer, default=6)
    sessions_per_week = Column(Integer, default=3)
    clinical_notes = Column(Text, default="")
    assigned_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PatientProfile user_id={self.user_id}>"