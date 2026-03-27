from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import exercise as crud_exercise
from ..schemas.exercise import Exercise, ExerciseCreate, ExerciseUpdate

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

@router.get("/", response_model=list[Exercise])
def list_exercises(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all exercises"""
    exercises = crud_exercise.get_exercises(db, skip=skip, limit=limit)
    return exercises

@router.get("/{exercise_id}", response_model=Exercise)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Get exercise by ID"""
    exercise = crud_exercise.get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@router.get("/by-part/{body_part}", response_model=list[Exercise])
def get_exercises_by_part(body_part: str, db: Session = Depends(get_db)):
    """Get exercises by body part"""
    exercises = crud_exercise.get_exercises_by_body_part(db, body_part)
    return exercises

@router.post("/", response_model=Exercise)
def create_exercise(exercise: ExerciseCreate, db: Session = Depends(get_db)):
    """Create new exercise"""
    db_exercise = crud_exercise.get_exercise_by_name(db, exercise.name)
    if db_exercise:
        raise HTTPException(status_code=400, detail="Exercise already exists")
    return crud_exercise.create_exercise(db, exercise)

@router.put("/{exercise_id}", response_model=Exercise)
def update_exercise(exercise_id: int, exercise: ExerciseUpdate, db: Session = Depends(get_db)):
    """Update exercise"""
    db_exercise = crud_exercise.update_exercise(db, exercise_id, exercise)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return db_exercise

@router.delete("/{exercise_id}")
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Delete exercise"""
    db_exercise = crud_exercise.delete_exercise(db, exercise_id)
    if not db_exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {"message": "Exercise deleted"}