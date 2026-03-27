from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime
from . import Base

class ExerciseSession(Base):
    __tablename__ = "exercise_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    type = Column(String, default="prescribed")  # prescribed or self
    sets = Column(Integer, default=3)
    reps = Column(Integer, default=10)
    form_score = Column(Float, default=0)
    compliance_score = Column(Float, default=0)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)