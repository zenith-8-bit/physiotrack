from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

class TimelineEvent(BaseModel):
    patient_id: int
    exercise_name: str
    type: str = "prescribed"
    sets: int = 3
    reps: int = 10
    form_score: int = 85
    compliance_score: int = 90

@router.get("")
def get_timeline(db: Session = Depends(get_db)):
    """Get timeline events"""
    # TODO: Query from session logs
    return [
        {
            "id": 1,
            "patient_id": 1,
            "exercise_name": "Knee Flexion",
            "type": "prescribed",
            "sets": 3,
            "reps": 10,
            "form_score": 92,
            "compliance_score": 92,
            "created_at": "2025-03-27T09:14:00"
        }
    ]