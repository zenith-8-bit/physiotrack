from pydantic import BaseModel
from typing import Optional

class ExerciseBase(BaseModel):
    name: str
    icon: str
    body_part: str
    description: Optional[str] = None
    ml_model: str
    default_sets: int = 3
    default_reps: int = 10
    default_hold_seconds: int = 0

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    body_part: Optional[str] = None
    description: Optional[str] = None
    ml_model: Optional[str] = None
    default_sets: Optional[int] = None
    default_reps: Optional[int] = None
    default_hold_seconds: Optional[int] = None

class Exercise(ExerciseBase):
    id: int
    
    class Config:
        from_attributes = True