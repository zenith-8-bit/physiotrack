from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import patient as crud_patient, user as crud_user
from ..schemas.patient import PatientProfile, PatientProfileCreate

router = APIRouter(prefix="/api/patients", tags=["patients"])

@router.get("/{user_id}", response_model=PatientProfile)
def get_patient_profile(user_id: int, db: Session = Depends(get_db)):
    """Get patient profile"""
    patient = crud_patient.get_patient_profile(db, user_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient

@router.post("/", response_model=PatientProfile)
def create_patient_profile(patient: PatientProfileCreate, db: Session = Depends(get_db)):
    """Create patient profile"""
    # Check if user exists
    user = crud_user.get_user(db, patient.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if profile already exists
    existing_profile = crud_patient.get_patient_profile(db, patient.user_id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Patient profile already exists")
    
    return crud_patient.create_patient_profile(db, patient)

@router.get("/doctor/{doctor_id}")
def get_doctor_patients(doctor_id: int, db: Session = Depends(get_db)):
    """Get all patients assigned to a doctor"""
    patients = crud_patient.get_all_patients_for_doctor(db, doctor_id)
    return patients

@router.put("/{user_id}", response_model=PatientProfile)
def update_patient_profile(user_id: int, diagnosis: str = None, clinical_notes: str = None, db: Session = Depends(get_db)):
    """Update patient profile"""
    patient = crud_patient.update_patient_profile(
        db, user_id, 
        diagnosis=diagnosis, 
        clinical_notes=clinical_notes
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient