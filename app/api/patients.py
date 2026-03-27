from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PatientProfile, User, Exercise
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/patients", tags=["patients"])

class PatientCreate(BaseModel):
    name: str
    phone: str
    diagnosis: str = None
    status: str = "active"

class PatientUpdate(BaseModel):
    diagnosis: str = None
    status: str = None
    compliance_score: int = None

@router.get("")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients"""
    patients = db.query(PatientProfile).all()
    result = []
    for p in patients:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "name": user.name if user else "Unknown",
            "phone": user.phone if user else None,
            "email": user.email if user else None,
            "diagnosis": p.diagnosis,
            "condition": p.diagnosis or "Pending",
            "status": "active",
            "compliance_score": getattr(p, 'compliance_score', 75),
            "last_active": "Today",
            "linked_devices": 1,
            "assigned_doctor_id": p.assigned_doctor_id
        })
    return result

@router.post("")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create new patient"""
    # Create user first
    user = User(
        name=patient.name,
        phone=patient.phone,
        role="patient"
    )
    db.add(user)
    db.flush()
    
    # Create patient profile
    profile = PatientProfile(
        user_id=user.id,
        diagnosis=patient.diagnosis,
        assigned_doctor_id=1  # Default doctor
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": user.id,
        "name": patient.name,
        "phone": patient.phone,
        "diagnosis": patient.diagnosis,
        "status": patient.status
    }

@router.get("/{patient_id}")
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get patient by ID"""
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    user = db.query(User).filter(User.id == patient.user_id).first()
    return {
        "id": patient.id,
        "name": user.name if user else "Unknown",
        "phone": user.phone if user else None,
        "diagnosis": patient.diagnosis,
        "status": "active"
    }

@router.put("/{patient_id}")
def update_patient(patient_id: int, update: PatientUpdate, db: Session = Depends(get_db)):
    """Update patient"""
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    if update.diagnosis:
        patient.diagnosis = update.diagnosis
    if update.status:
        pass  # Update status logic
    
    db.commit()
    return {"success": True, "patient_id": patient_id}