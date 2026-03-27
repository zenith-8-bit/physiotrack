from sqlalchemy.orm import Session
from ..models.patient import PatientProfile
from ..schemas.patient import PatientProfileCreate

def get_patient_profile(db: Session, user_id: int):
    return db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()

def create_patient_profile(db: Session, patient: PatientProfileCreate):
    db_patient = PatientProfile(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient_profile(db: Session, user_id: int, **kwargs):
    db_patient = get_patient_profile(db, user_id)
    if db_patient:
        for key, value in kwargs.items():
            setattr(db_patient, key, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient

def get_all_patients_for_doctor(db: Session, doctor_id: int):
    return db.query(PatientProfile).filter(PatientProfile.assigned_doctor_id == doctor_id).all()