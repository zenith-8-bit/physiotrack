from sqlalchemy import Column, Integer, String, Text
from . import Base

class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    icon = Column(String)
    body_part = Column(String)
    description = Column(Text, default="")
    ml_model = Column(String)
    default_sets = Column(Integer, default=3)
    default_reps = Column(Integer, default=10)
    default_hold_seconds = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Exercise {self.name}>"