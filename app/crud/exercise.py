from sqlalchemy.orm import Session
from ..models.exercise import Exercise
from ..schemas.exercise import ExerciseCreate, ExerciseUpdate

def get_exercise(db: Session, exercise_id: int):
    return db.query(Exercise).filter(Exercise.id == exercise_id).first()

def get_exercise_by_name(db: Session, name: str):
    return db.query(Exercise).filter(Exercise.name == name).first()

def get_exercises(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Exercise).offset(skip).limit(limit).all()

def get_exercises_by_body_part(db: Session, body_part: str):
    return db.query(Exercise).filter(Exercise.body_part == body_part).all()

def create_exercise(db: Session, exercise: ExerciseCreate):
    db_exercise = Exercise(**exercise.dict())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

def update_exercise(db: Session, exercise_id: int, exercise: ExerciseUpdate):
    db_exercise = get_exercise(db, exercise_id)
    if db_exercise:
        for key, value in exercise.dict(exclude_unset=True).items():
            setattr(db_exercise, key, value)
        db.commit()
        db.refresh(db_exercise)
    return db_exercise

def delete_exercise(db: Session, exercise_id: int):
    db_exercise = get_exercise(db, exercise_id)
    if db_exercise:
        db.delete(db_exercise)
        db.commit()
    return db_exercise