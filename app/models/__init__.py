from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .exercise import Exercise
from .user import User
from .patient import PatientProfile

__all__ = ["Base", "Exercise", "User", "PatientProfile"]