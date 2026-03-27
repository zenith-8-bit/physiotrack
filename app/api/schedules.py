from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ExerciseSchedule, PatientProfile, Exercise
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

class ExerciseItem(BaseModel):
    id: int
    name: str
    sets: int
    reps: int
    hold_seconds: Optional[int] = 0

class ScheduleCreate(BaseModel):
    patient_id: int
    schedule_data: Dict[str, List[Dict]]
    is_daily_template: bool = False

class ScheduleUpdate(BaseModel):
    schedule_data: Optional[Dict[str, List[Dict]]] = None
    is_active: Optional[str] = None

@router.get("/patient/{patient_id}")
def get_patient_schedule(patient_id: int, db: Session = Depends(get_db)):
    """Get current schedule for a patient"""
    try:
        schedule = db.query(ExerciseSchedule).filter(
            ExerciseSchedule.patient_id == patient_id,
            ExerciseSchedule.is_active == "true"
        ).order_by(ExerciseSchedule.updated_at.desc()).first()
        
        if not schedule:
            return {
                "id": None,
                "patient_id": patient_id,
                "schedule_data": {
                    "Mon": [], "Tue": [], "Wed": [], "Thu": [], 
                    "Fri": [], "Sat": [], "Sun": []
                },
                "is_daily_template": False,
                "created_at": None
            }
        
        return {
            "id": schedule.id,
            "patient_id": schedule.patient_id,
            "schedule_data": schedule.schedule_data or {},
            "is_daily_template": schedule.is_daily_template == "true",
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None
        }
    except Exception as e:
        print(f"Error in get_patient_schedule: {e}")
        return {
            "id": None,
            "patient_id": patient_id,
            "schedule_data": {
                "Mon": [], "Tue": [], "Wed": [], "Thu": [], 
                "Fri": [], "Sat": [], "Sun": []
            },
            "is_daily_template": False,
            "created_at": None,
            "error": str(e)
        }

@router.post("")
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create or update exercise schedule"""
    try:
        # Deactivate old schedules
        db.query(ExerciseSchedule).filter(
            ExerciseSchedule.patient_id == schedule.patient_id,
            ExerciseSchedule.is_active == "true"
        ).update({"is_active": "false"})
        
        # Create new schedule
        new_schedule = ExerciseSchedule(
            patient_id=schedule.patient_id,
            doctor_id=1,  # Default doctor ID
            schedule_data=schedule.schedule_data,
            is_daily_template="true" if schedule.is_daily_template else "false",
            is_active="true"
        )
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return {
            "id": new_schedule.id,
            "patient_id": new_schedule.patient_id,
            "schedule_data": new_schedule.schedule_data,
            "is_daily_template": new_schedule.is_daily_template == "true",
            "success": True,
            "message": "Schedule saved successfully"
        }
    except Exception as e:
        print(f"Error in create_schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save schedule: {str(e)}")

@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, update: ScheduleUpdate, db: Session = Depends(get_db)):
    """Update existing schedule"""
    try:
        schedule = db.query(ExerciseSchedule).filter(ExerciseSchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if update.schedule_data:
            schedule.schedule_data = update.schedule_data
        if update.is_active:
            schedule.is_active = update.is_active
        
        schedule.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "id": schedule.id,
            "success": True,
            "message": "Schedule updated successfully"
        }
    except Exception as e:
        print(f"Error in update_schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{schedule_id}")
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get schedule by ID"""
    try:
        schedule = db.query(ExerciseSchedule).filter(ExerciseSchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "id": schedule.id,
            "patient_id": schedule.patient_id,
            "schedule_data": schedule.schedule_data,
            "is_daily_template": schedule.is_daily_template == "true",
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat()
        }
    except Exception as e:
        print(f"Error in get_schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy-last-week/{patient_id}")
def copy_last_week(patient_id: int, db: Session = Depends(get_db)):
    """Copy last week's schedule"""
    try:
        last_schedule = db.query(ExerciseSchedule).filter(
            ExerciseSchedule.patient_id == patient_id
        ).order_by(ExerciseSchedule.created_at.desc()).first()
        
        if not last_schedule or not last_schedule.schedule_data:
            return {"success": False, "message": "No previous schedule found"}
        
        return {
            "success": True,
            "schedule_data": last_schedule.schedule_data,
            "message": "Last week's schedule loaded"
        }
    except Exception as e:
        print(f"Error in copy_last_week: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}