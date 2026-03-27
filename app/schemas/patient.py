from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PatientProfileBase(BaseModel):
    diagnosis: str
    rehab_duration_weeks: int = 6
    sessions_per_week: int = 3
    clinical_notes: Optional[str] = None

class PatientProfileCreate(PatientProfileBase):
    user_id: int
    assigned_doctor_id: Optional[int] = None

class PatientProfile(PatientProfileBase):
    id: int
    user_id: int
    assigned_doctor_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True