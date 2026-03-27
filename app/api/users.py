from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..crud import user as crud_user
from ..schemas.user import User, UserCreate, UserQRGenerate
from ..services.qr_service import generate_qr_code, generate_qr_token

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/", response_model=list[User])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users"""
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user"""
    db_user = crud_user.get_user_by_phone(db, user.phone)
    if db_user:
        raise HTTPException(status_code=400, detail="User with this phone already exists")
    return crud_user.create_user(db, user)

@router.get("/by-role/{role}", response_model=list[User])
def get_users_by_role(role: str, db: Session = Depends(get_db)):
    """Get users by role (doctor or patient)"""
    users = crud_user.get_users_by_role(db, role)
    return users

@router.post("/patient/register", response_model=UserQRGenerate)
def register_patient(name: str = Form(...), phone: str = Form(...), db: Session = Depends(get_db)):
    """
    Register a new patient and generate QR code for onboarding.
    """
    # Check if phone already exists
    existing_user = crud_user.get_user_by_phone(db, phone)
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Generate QR token
    qr_token = generate_qr_token()
    
    # Create user
    user_create = UserCreate(name=name, phone=phone, role="patient")
    db_user = crud_user.create_user(db, user_create, qr_token=qr_token)
    
    # Generate QR code
    qr_data = {
        "token": qr_token,
        "name": name,
        "phone": phone,
        "user_id": db_user.id,
        "type": "patient_onboarding"
    }
    qr_image = generate_qr_code(qr_data)
    
    return UserQRGenerate(
        qr_token=qr_token,
        qr_image_base64=qr_image,
        user=db_user
    )

@router.post("/patient/scan-qr")
def scan_patient_qr(qr_token: str = Form(...), db: Session = Depends(get_db)):
    """
    Patient scans QR code to link their device.
    """
    user = crud_user.get_user_by_qr_token(db, qr_token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid QR token")
    
    return {
        "success": True,
        "user_id": user.id,
        "name": user.name,
        "role": user.role
    }