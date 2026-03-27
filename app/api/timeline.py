from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import ExerciseSession, Exercise, PatientProfile, User

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

@router.get("")
def get_timeline(db: Session = Depends(get_db)):
    """Get timeline events with patient info"""
    sessions = db.query(ExerciseSession).order_by(desc(ExerciseSession.created_at)).limit(20).all()
    
    result = []
    for session in sessions:
        exercise = db.query(Exercise).filter(Exercise.id == session.exercise_id).first()
        patient = db.query(PatientProfile).filter(PatientProfile.id == session.patient_id).first()
        user = db.query(User).filter(User.id == patient.user_id).first() if patient else None
        
        if exercise and patient and user:
            result.append({
                "id": session.id,
                "patient_id": session.patient_id,
                "patient_name": user.name,
                "exercise_name": exercise.name,
                "exercise_id": exercise.id,
                "type": session.type,
                "sets": session.sets,
                "reps": session.reps,
                "form_score": int(session.form_score),
                "compliance_score": int(session.compliance_score),
                "notes": session.notes or "",
                "created_at": session.created_at.isoformat()
            })
    
    return result