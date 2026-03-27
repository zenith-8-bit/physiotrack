from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Exercise

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

@router.get("")
def get_exercises(db: Session = Depends(get_db)):
    """Get all exercises"""
    exercises = db.query(Exercise).all()
    return [
        {
            "id": ex.id,
            "name": ex.name,
            "icon": ex.icon,
            "body_part": ex.body_part,
            "ml_model": ex.ml_model,
            "default_sets": ex.default_sets,
            "default_reps": ex.default_reps,
            "default_hold_seconds": ex.default_hold_seconds
        }
        for ex in exercises
    ]