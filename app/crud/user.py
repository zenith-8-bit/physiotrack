from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_qr_token(db: Session, qr_token: str):
    return db.query(User).filter(User.qr_token == qr_token).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_users_by_role(db: Session, role: str):
    return db.query(User).filter(User.role == role).all()

def create_user(db: Session, user: UserCreate, qr_token: str = None):
    db_user = User(
        name=user.name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        qr_token=qr_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_qr_token(db: Session, user_id: int, qr_token: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.qr_token = qr_token
        db.commit()
        db.refresh(db_user)
    return db_user