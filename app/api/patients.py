from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import PatientProfile, User, Exercise, ExerciseSession
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/patients", tags=["patients"])

class PatientCreate(BaseModel):
    name: str
    phone: str
    email: str = None
    diagnosis: str = None
    status: str = "active"

class PatientUpdate(BaseModel):
    diagnosis: str = None
    status: str = None

@router.get("")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients with compliance scores"""
    patient_profiles = db.query(PatientProfile).all()
    result = []
    
    for profile in patient_profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()
        if not user:
            continue
        
        # Calculate compliance score
        sessions = db.query(ExerciseSession).filter(
            ExerciseSession.patient_id == profile.id
        ).all()
        avg_compliance = sum([s.compliance_score for s in sessions]) / len(sessions) if sessions else 0
        
        # Determine status
        if avg_compliance >= 80:
            status = "active"
        elif avg_compliance >= 50:
            status = "pending"
        else:
            status = "alert"
        
        # Last active
        last_session = db.query(ExerciseSession).filter(
            ExerciseSession.patient_id == profile.id
        ).order_by(ExerciseSession.created_at.desc()).first()
        
        last_active = "Never"
        if last_session:
            diff = datetime.utcnow() - last_session.created_at
            if diff.days == 0:
                last_active = "Today"
            elif diff.days == 1:
                last_active = "Yesterday"
            else:
                last_active = f"{diff.days} days ago"
        
        result.append({
            "id": profile.id,
            "user_id": user.id,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "diagnosis": profile.diagnosis or "Pending",
            "condition": profile.diagnosis or "No diagnosis",
            "status": status,
            "compliance_score": int(avg_compliance),
            "last_active": last_active,
            "linked_devices": 1,
            "assigned_doctor_id": profile.assigned_doctor_id
        })
    
    return result

@router.post("")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create new patient"""
    # Create user
    user = User(
        name=patient.name,
        phone=patient.phone,
        email=patient.email,
        role="patient"
    )
    db.add(user)
    db.flush()
    
    # Create patient profile
    profile = PatientProfile(
        user_id=user.id,
        diagnosis=patient.diagnosis,
        assigned_doctor_id=1  # Default to first doctor
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": user.id,
        "name": patient.name,
        "phone": patient.phone,
        "email": patient.email,
        "diagnosis": patient.diagnosis,
        "status": "active"
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
        "email": user.email if user else None,
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
    
    db.commit()
    return {"success": True, "patient_id": patient_id}