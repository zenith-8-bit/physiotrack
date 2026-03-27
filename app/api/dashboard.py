from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import PatientProfile, User, ExerciseSession, Exercise
from datetime import datetime, timedelta
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

class DashboardStats(BaseModel):
    total_patients: int
    sessions_today: int
    avg_compliance: float
    total_alerts: int

class RecentActivity(BaseModel):
    patient_name: str
    patient_initials: str
    patient_color: str
    exercise_name: str
    exercise_type: str
    time: str

class WeeklyComplianceData(BaseModel):
    day: str
    prescribed_percentage: float
    self_initiated_percentage: float

class AlertItem(BaseModel):
    id: int
    patient_name: str
    alert_type: str
    message: str
    timestamp: str
    severity: str  # warning, danger, info

# ═══════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Total patients
        total_patients = db.query(func.count(PatientProfile.id)).scalar() or 0
        
        # Sessions today
        today = datetime.utcnow().date()
        sessions_today = db.query(func.count(ExerciseSession.id)).filter(
            func.date(ExerciseSession.created_at) == today
        ).scalar() or 0
        
        # Average compliance score (0-100)
        avg_compliance_query = db.query(func.avg(ExerciseSession.compliance_score)).scalar()
        avg_compliance = float(avg_compliance_query) if avg_compliance_query else 0
        avg_compliance = round(avg_compliance, 2)
        
        # Total alerts (compliance < 50 or form_score < 60)
        alerts_count = db.query(func.count(ExerciseSession.id)).filter(
            (ExerciseSession.compliance_score < 50) | (ExerciseSession.form_score < 60)
        ).scalar() or 0
        
        return {
            "total_patients": total_patients,
            "sessions_today": sessions_today,
            "avg_compliance": min(100, max(0, avg_compliance)),  # Clamp 0-100
            "total_alerts": alerts_count
        }
    except Exception as e:
        print(f"Error in get_dashboard_stats: {e}")
        return {
            "total_patients": 0,
            "sessions_today": 0,
            "avg_compliance": 0,
            "total_alerts": 0
        }

# ═══════════════════════════════════════════════════════════════
# RECENT ACTIVITY
# ═══════════════════════════════════════════════════════════════

@router.get("/recent-activity")
def get_recent_activity(limit: int = 4, db: Session = Depends(get_db)):
    """Get recent patient exercise sessions"""
    try:
        sessions = db.query(ExerciseSession).order_by(
            ExerciseSession.created_at.desc()
        ).limit(limit).all()
        
        activities = []
        for session in sessions:
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == session.patient_id
            ).first()
            user = db.query(User).filter(
                User.id == patient.user_id
            ).first() if patient else None
            exercise = db.query(Exercise).filter(
                Exercise.id == session.exercise_id
            ).first()
            
            if user and exercise:
                # Generate patient color based on ID
                colors = [
                    "linear-gradient(135deg,#1565c0,#42a5f5)",
                    "linear-gradient(135deg,#0d9488,#34d399)",
                    "linear-gradient(135deg,#dc2626,#fb923c)",
                    "linear-gradient(135deg,#7c3aed,#a78bfa)",
                    "linear-gradient(135deg,#0f3460,#1976d2)",
                    "linear-gradient(135deg,#be185d,#f472b6)"
                ]
                color = colors[patient.id % len(colors)]
                
                # Format time
                time_diff = datetime.utcnow() - session.created_at
                if time_diff.seconds < 60:
                    time_str = "Just now"
                elif time_diff.seconds < 3600:
                    mins = time_diff.seconds // 60
                    time_str = f"{mins}m ago"
                elif time_diff.days == 0:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours}h ago"
                else:
                    time_str = session.created_at.strftime("%H:%M")
                
                activities.append({
                    "patient_name": user.name,
                    "patient_initials": "".join([w[0].upper() for w in user.name.split()]),
                    "patient_color": color,
                    "exercise_name": exercise.name,
                    "exercise_type": session.type,  # prescribed or self
                    "time": time_str
                })
        
        return {"activities": activities, "count": len(activities)}
    except Exception as e:
        print(f"Error in get_recent_activity: {e}")
        return {"activities": [], "count": 0, "error": str(e)}

# ═══════════════════════════════���═══════════════════════════════
# WEEKLY COMPLIANCE
# ═══════════════════════════════════════════════════════════════

@router.get("/weekly-compliance")
def get_weekly_compliance(db: Session = Depends(get_db)):
    """Get weekly compliance data for last 7 days"""
    try:
        days_data = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i in range(7):
            target_date = datetime.utcnow().date() - timedelta(days=6-i)
            
            # Get prescribed exercises for this day
            prescribed_sessions = db.query(ExerciseSession).filter(
                func.date(ExerciseSession.created_at) == target_date,
                ExerciseSession.type == "prescribed"
            ).all()
            
            # Get self-initiated exercises for this day
            self_sessions = db.query(ExerciseSession).filter(
                func.date(ExerciseSession.created_at) == target_date,
                ExerciseSession.type == "self"
            ).all()
            
            # Calculate percentages
            prescribed_pct = 0
            self_pct = 0
            
            if prescribed_sessions:
                prescribed_pct = sum(s.compliance_score for s in prescribed_sessions) / len(prescribed_sessions)
            if self_sessions:
                self_pct = sum(s.compliance_score for s in self_sessions) / len(self_sessions)
            
            days_data.append({
                "day": day_names[i],
                "date": target_date.isoformat(),
                "prescribed_percentage": round(prescribed_pct, 2),
                "self_initiated_percentage": round(self_pct, 2),
                "prescribed_count": len(prescribed_sessions),
                "self_count": len(self_sessions)
            })
        
        return {"days": days_data}
    except Exception as e:
        print(f"Error in get_weekly_compliance: {e}")
        return {"days": [], "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# FLAGGED ALERTS
# ═══════════════════════════════════════════════════════════════

@router.get("/alerts")
def get_alerts(limit: int = 5, db: Session = Depends(get_db)):
    """Get flagged alerts for patients"""
    try:
        alerts = []
        
        # Get sessions with low compliance
        low_compliance = db.query(ExerciseSession).filter(
            ExerciseSession.compliance_score < 50
        ).order_by(ExerciseSession.created_at.desc()).limit(limit).all()
        
        for session in low_compliance:
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == session.patient_id
            ).first()
            user = db.query(User).filter(
                User.id == patient.user_id
            ).first() if patient else None
            
            if user:
                alerts.append({
                    "id": session.id,
                    "patient_name": user.name,
                    "alert_type": "compliance",
                    "message": f"Low compliance score: {session.compliance_score}%. Patient may need motivation boost.",
                    "timestamp": session.created_at.isoformat(),
                    "severity": "warning",
                    "details": f"{session.sets} sets × {session.reps} reps"
                })
        
        # Get sessions with poor form
        poor_form = db.query(ExerciseSession).filter(
            ExerciseSession.form_score < 60
        ).order_by(ExerciseSession.created_at.desc()).limit(limit).all()
        
        for session in poor_form:
            patient = db.query(PatientProfile).filter(
                PatientProfile.id == session.patient_id
            ).first()
            user = db.query(User).filter(
                User.id == patient.user_id
            ).first() if patient else None
            
            if user:
                alerts.append({
                    "id": session.id,
                    "patient_name": user.name,
                    "alert_type": "form",
                    "message": f"Incorrect form detected: Form score {session.form_score}%. Review exercise technique.",
                    "timestamp": session.created_at.isoformat(),
                    "severity": "danger",
                    "details": session.notes or "AI flagged for review"
                })
        
        # Sort by timestamp, most recent first
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"alerts": alerts[:limit], "count": len(alerts[:limit])}
    except Exception as e:
        print(f"Error in get_alerts: {e}")
        return {"alerts": [], "count": 0, "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# COMPLIANCE BY PATIENT
# ═══════════════════════════════════════════════════════════════

@router.get("/compliance-by-patient")
def get_compliance_by_patient(db: Session = Depends(get_db)):
    """Get compliance statistics grouped by patient"""
    try:
        patients = db.query(PatientProfile).all()
        
        patient_stats = []
        for patient in patients:
            user = db.query(User).filter(User.id == patient.user_id).first()
            
            sessions = db.query(ExerciseSession).filter(
                ExerciseSession.patient_id == patient.id
            ).all()
            
            if sessions:
                avg_compliance = sum(s.compliance_score for s in sessions) / len(sessions)
                avg_form = sum(s.form_score for s in sessions) / len(sessions)
                
                patient_stats.append({
                    "patient_id": patient.id,
                    "patient_name": user.name if user else "Unknown",
                    "compliance": round(avg_compliance, 2),
                    "form_score": round(avg_form, 2),
                    "sessions_count": len(sessions),
                    "status": "active" if avg_compliance > 75 else "alert" if avg_compliance < 50 else "pending"
                })
        
        # Sort by compliance
        patient_stats.sort(key=lambda x: x["compliance"], reverse=True)
        
        return {"patients": patient_stats}
    except Exception as e:
        print(f"Error in get_compliance_by_patient: {e}")
        return {"patients": [], "error": str(e)}

# ═══════════════════════════════════════════════════════════════
# MISSED SESSIONS
# ═══════════════════════════════════════════════════════════════

@router.get("/missed-sessions")
def get_missed_sessions(days: int = 7, db: Session = Depends(get_db)):
    """Get patients with missed sessions"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all patients
        all_patients = db.query(PatientProfile).all()
        
        missed = []
        for patient in all_patients:
            user = db.query(User).filter(User.id == patient.user_id).first()
            
            # Get last session
            last_session = db.query(ExerciseSession).filter(
                ExerciseSession.patient_id == patient.id
            ).order_by(ExerciseSession.created_at.desc()).first()
            
            if not last_session or last_session.created_at < cutoff_date:
                days_inactive = 0
                if last_session:
                    days_inactive = (datetime.utcnow() - last_session.created_at).days
                else:
                    days_inactive = days
                
                missed.append({
                    "patient_id": patient.id,
                    "patient_name": user.name if user else "Unknown",
                    "days_inactive": days_inactive,
                    "last_activity": last_session.created_at.isoformat() if last_session else None,
                    "severity": "danger" if days_inactive > 7 else "warning"
                })
        
        return {"missed": missed, "count": len(missed)}
    except Exception as e:
        print(f"Error in get_missed_sessions: {e}")
        return {"missed": [], "count": 0, "error": str(e)}