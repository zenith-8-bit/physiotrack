"""
PhysioTrack — FastAPI Backend
Doctor Portal + Patient App API
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, date
from enum import Enum
import uuid
import hashlib
import hmac
import json
import time

# ──────────────────────────────────────────────
# APP INIT
# ──────────────────────────────────────────────

app = FastAPI(
    title="PhysioTrack API",
    description="AI-powered physiotherapy exercise tracking — Doctor Portal + Patient App backend",
    version="2.4.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ──────────────────────────────────────────────
# IN-MEMORY STORE (swap with DB in production)
# ──────────────────────────────────────────────

DB = {
    "doctors": {
        "DR001": {
            "id": "DR001",
            "name": "Dr. Ramesh Iyer",
            "specialisation": "Orthopaedics",
            "hospital": "Apollo Hospitals, Chennai",
            "reg_no": "TN-MCI-28441",
            "email": "ramesh.iyer@apollo.in",
            "password_hash": hashlib.sha256(b"demo1234").hexdigest(),
        }
    },
    "patients": {
        "PT001": {
            "id": "PT001",
            "doctor_id": "DR001",
            "first_name": "Suresh",
            "last_name": "Anand",
            "dob": "1985-03-12",
            "gender": "Male",
            "phone": "+919876543210",
            "email": "suresh@example.com",
            "diagnosis": "ACL Tear — Post-op Rehab",
            "surgery_date": "2025-02-10",
            "rehab_start": "2025-02-24",
            "rehab_duration_weeks": 12,
            "sessions_per_week": 5,
            "clinical_notes": "Post-op. Avoid weight bearing first 4 weeks.",
            "qr_token": "PT-XK9A2B",
            "status": "active",
            "created_at": "2025-02-24T10:00:00",
        }
    },
    "devices": {
        "DEV001": {"patient_id": "PT001", "device_model": "iPhone 13 Pro", "role": "primary", "linked_at": "2025-02-24T10:05:00", "last_seen": "2025-03-25T09:14:00"},
        "DEV002": {"patient_id": "PT001", "device_model": "OnePlus 9", "role": "sensor", "linked_at": "2025-02-25T08:00:00", "last_seen": "2025-03-25T09:14:00"},
    },
    "schedules": {},
    "sessions": [],
    "exercises": {
        "EX001": {"id": "EX001", "name": "Knee Flexion", "body_part": "Knee", "ml_model": "knee_flex_v2", "icon": "🦵"},
        "EX002": {"id": "EX002", "name": "Shoulder Roll", "body_part": "Shoulder", "ml_model": "shoulder_v1", "icon": "💪"},
        "EX003": {"id": "EX003", "name": "Hip Abduction", "body_part": "Hip", "ml_model": "hip_abd_v3", "icon": "🏃"},
        "EX004": {"id": "EX004", "name": "Wrist Curl", "body_part": "Wrist", "ml_model": "wrist_v1", "icon": "🤲"},
        "EX005": {"id": "EX005", "name": "Calf Raise", "body_part": "Ankle", "ml_model": "calf_v2", "icon": "🦶"},
        "EX006": {"id": "EX006", "name": "Wall Squat", "body_part": "Knee/Hip", "ml_model": "squat_v3", "icon": "🧱"},
        "EX007": {"id": "EX007", "name": "Back Extension", "body_part": "Back", "ml_model": "back_ext_v1", "icon": "🧘"},
        "EX008": {"id": "EX008", "name": "Straight Leg Raise", "body_part": "Knee", "ml_model": "slr_v2", "icon": "🦵"},
        "EX009": {"id": "EX009", "name": "Shoulder Abduction", "body_part": "Shoulder", "ml_model": "sh_abd_v2", "icon": "💪"},
        "EX010": {"id": "EX010", "name": "Bridge Exercise", "body_part": "Hip/Back", "ml_model": "bridge_v2", "icon": "🌉"},
        "EX011": {"id": "EX011", "name": "Ankle Circles", "body_part": "Ankle", "ml_model": "ankle_circ_v1", "icon": "🦶"},
        "EX012": {"id": "EX012", "name": "Neck Side Bend", "body_part": "Neck", "ml_model": "neck_v1", "icon": "🧑"},
    },
    "alerts": [],
    "tokens": {},  # token -> doctor_id
}

# ──────────────────────────────────────────────
# ENUMS & PYDANTIC MODELS
# ──────────────────────────────────────────────

class DeviceRole(str, Enum):
    primary = "primary"
    sensor = "sensor"

class SessionType(str, Enum):
    prescribed = "prescribed"
    self_initiated = "self"

class FormQuality(str, Enum):
    excellent = "Excellent"
    good = "Good"
    fair = "Fair"
    poor = "Poor"

class DayOfWeek(str, Enum):
    mon = "Mon"; tue = "Tue"; wed = "Wed"; thu = "Thu"
    fri = "Fri"; sat = "Sat"; sun = "Sun"

# ── Auth ──
class DoctorLoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    doctor_id: str
    doctor_name: str

# ── Doctor ──
class DoctorCreate(BaseModel):
    name: str
    specialisation: str
    hospital: str
    reg_no: str
    email: str
    password: str

# ── Patient ──
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    dob: str
    gender: Literal["Male", "Female", "Other"]
    phone: str
    email: Optional[str] = None
    diagnosis: str
    surgery_date: Optional[str] = None
    rehab_start: str
    rehab_duration_weeks: int = Field(default=8, ge=1, le=52)
    sessions_per_week: int = Field(default=5, ge=1, le=7)
    clinical_notes: Optional[str] = None

class PatientUpdate(BaseModel):
    clinical_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    rehab_duration_weeks: Optional[int] = None
    sessions_per_week: Optional[int] = None
    status: Optional[Literal["active", "inactive", "pending"]] = None

# ── Device ──
class DeviceLinkRequest(BaseModel):
    qr_token: str
    device_model: str
    os_version: Optional[str] = None
    app_version: Optional[str] = None

class DeviceRoleUpdate(BaseModel):
    role: DeviceRole

# ── Exercise ──
class ExerciseCreate(BaseModel):
    name: str
    body_part: str
    ml_model: str
    icon: Optional[str] = "💪"
    description: Optional[str] = None
    sensor_data_schema: Optional[dict] = None

# ── Schedule ──
class ScheduledExercise(BaseModel):
    exercise_id: str
    sets: int = Field(default=3, ge=1)
    reps: int = Field(default=10, ge=1)
    hold_seconds: int = Field(default=0, ge=0)
    notes_for_patient: Optional[str] = None

class WeekScheduleEntry(BaseModel):
    day: DayOfWeek
    exercises: List[ScheduledExercise]

class WeekSchedulePayload(BaseModel):
    patient_id: str
    schedule: List[WeekScheduleEntry]
    apply_same_daily: bool = False  # True = copy schedule[0] to all days

# ── Session ──
class RepData(BaseModel):
    rep_number: int
    correct: bool
    error_type: Optional[str] = None  # e.g. "inward_knee_collapse"
    sensor_values: Optional[dict] = None

class SessionReport(BaseModel):
    patient_id: str
    exercise_id: str
    device_id: str
    secondary_device_id: Optional[str] = None  # sensor phone
    session_type: SessionType
    sets_completed: int
    reps_data: List[RepData]
    form_quality: FormQuality
    duration_seconds: int
    distance_cm: Optional[float] = None  # for distance-based exercises
    notes: Optional[str] = None

class AgenticTriggerPayload(BaseModel):
    patient_id: str
    session_id: str
    error_types: List[str]
    device_available: bool  # whether secondary phone detected
    secondary_device_id: Optional[str] = None

# ── Alert ──
class Alert(BaseModel):
    patient_id: str
    alert_type: Literal["form_error", "missed_sessions", "device_switch", "compliance_drop"]
    message: str
    severity: Literal["low", "medium", "high"]

# ──────────────────────────────────────────────
# AUTH HELPERS
# ──────────────────────────────────────────────

def get_current_doctor(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    doctor_id = DB["tokens"].get(token)
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return doctor_id

def generate_token() -> str:
    return str(uuid.uuid4()).replace("-", "")

def generate_qr_token() -> str:
    return "PT-" + uuid.uuid4().hex[:6].upper()

# ──────────────────────────────────────────────
# ROOT
# ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    """Serve the web dashboard homepage."""
    return FileResponse("static/index.html")

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "db_patients": len(DB["patients"]), "db_exercises": len(DB["exercises"])}

# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def doctor_login(payload: DoctorLoginRequest):
    """Doctor portal login → returns bearer token."""
    doctor = next((d for d in DB["doctors"].values() if d["email"] == payload.email), None)
    if not doctor:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if doctor["password_hash"] != hashlib.sha256(payload.password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_token()
    DB["tokens"][token] = doctor["id"]
    return {"access_token": token, "doctor_id": doctor["id"], "doctor_name": doctor["name"]}

@app.post("/auth/logout", tags=["Auth"])
def doctor_logout(doctor_id: str = Depends(get_current_doctor), credentials: HTTPAuthorizationCredentials = Depends(security)):
    DB["tokens"].pop(credentials.credentials, None)
    return {"message": "Logged out"}

# ──────────────────────────────────────────────
# DOCTORS
# ──────────────────────────────────────────────

@app.post("/doctors/register", tags=["Doctors"], status_code=201)
def register_doctor(payload: DoctorCreate):
    """Register a new doctor account."""
    if any(d["email"] == payload.email for d in DB["doctors"].values()):
        raise HTTPException(status_code=409, detail="Email already registered")
    doc_id = "DR" + str(len(DB["doctors"]) + 1).zfill(3)
    DB["doctors"][doc_id] = {
        "id": doc_id,
        "name": payload.name,
        "specialisation": payload.specialisation,
        "hospital": payload.hospital,
        "reg_no": payload.reg_no,
        "email": payload.email,
        "password_hash": hashlib.sha256(payload.password.encode()).hexdigest(),
    }
    return {"doctor_id": doc_id, "message": "Doctor registered successfully"}

@app.get("/doctors/me", tags=["Doctors"])
def get_me(doctor_id: str = Depends(get_current_doctor)):
    doc = DB["doctors"].get(doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {k: v for k, v in doc.items() if k != "password_hash"}

# ──────────────────────────────────────────────
# PATIENTS
# ──────────────────────────────────────────────

@app.get("/patients", tags=["Patients"])
def list_patients(doctor_id: str = Depends(get_current_doctor)):
    """List all patients under the authenticated doctor."""
    pts = [p for p in DB["patients"].values() if p["doctor_id"] == doctor_id]
    return {"patients": pts, "count": len(pts)}

@app.post("/patients", tags=["Patients"], status_code=201)
def create_patient(payload: PatientCreate, background_tasks: BackgroundTasks, doctor_id: str = Depends(get_current_doctor)):
    """Register a new patient and generate QR onboarding token."""
    pt_id = "PT" + str(len(DB["patients"]) + 1).zfill(3)
    qr_token = generate_qr_token()
    DB["patients"][pt_id] = {
        "id": pt_id,
        "doctor_id": doctor_id,
        **payload.dict(),
        "qr_token": qr_token,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    # Background: generate QR payload (would write PNG in prod)
    background_tasks.add_task(_generate_qr_artifact, pt_id, qr_token)
    return {"patient_id": pt_id, "qr_token": qr_token, "message": "Patient registered. QR token ready."}

@app.get("/patients/{patient_id}", tags=["Patients"])
def get_patient(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    pt_devices = [d for d in DB["devices"].values() if d["patient_id"] == patient_id]
    return {**pt, "devices": pt_devices, "device_count": len(pt_devices)}

@app.patch("/patients/{patient_id}", tags=["Patients"])
def update_patient(patient_id: str, payload: PatientUpdate, doctor_id: str = Depends(get_current_doctor)):
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in payload.dict(exclude_none=True).items():
        pt[k] = v
    return {"message": "Patient updated", "patient": pt}

@app.delete("/patients/{patient_id}", tags=["Patients"])
def delete_patient(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    DB["patients"].pop(patient_id)
    return {"message": f"Patient {patient_id} removed"}

@app.post("/patients/{patient_id}/regenerate-qr", tags=["Patients"])
def regenerate_qr(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    """Invalidate old QR and generate a new onboarding token."""
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    new_token = generate_qr_token()
    pt["qr_token"] = new_token
    return {"patient_id": patient_id, "new_qr_token": new_token}

# ──────────────────────────────────────────────
# DEVICES  (multi-phone support)
# ──────────────────────────────────────────────

@app.post("/devices/link", tags=["Devices"], status_code=201)
def link_device(payload: DeviceLinkRequest):
    """
    Called by the PhysioTrack app when a patient scans the QR code.
    Multiple phones can call this with the same qr_token — all get linked.
    """
    patient = next((p for p in DB["patients"].values() if p["qr_token"] == payload.qr_token), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Invalid or expired QR token")

    existing_devices = [d for d in DB["devices"].values() if d["patient_id"] == patient["id"]]
    role = "primary" if not existing_devices else "sensor"

    dev_id = "DEV" + str(len(DB["devices"]) + 1).zfill(3)
    DB["devices"][dev_id] = {
        "device_id": dev_id,
        "patient_id": patient["id"],
        "device_model": payload.device_model,
        "os_version": payload.os_version,
        "app_version": payload.app_version,
        "role": role,
        "linked_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat(),
    }

    if patient["status"] == "pending":
        patient["status"] = "active"

    return {
        "device_id": dev_id,
        "patient_id": patient["id"],
        "role": role,
        "message": f"Device linked as {role}. {'Use as motion sensor.' if role=='sensor' else 'Primary UI device.'}"
    }

@app.get("/patients/{patient_id}/devices", tags=["Devices"])
def list_patient_devices(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Not found")
    devices = [d for d in DB["devices"].values() if d["patient_id"] == patient_id]
    return {"devices": devices, "count": len(devices)}

@app.patch("/devices/{device_id}/role", tags=["Devices"])
def update_device_role(device_id: str, payload: DeviceRoleUpdate, doctor_id: str = Depends(get_current_doctor)):
    """Promote/demote a device between primary and sensor role."""
    dev = DB["devices"].get(device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    dev["role"] = payload.role.value
    return {"message": f"Device {device_id} role updated to {payload.role.value}"}

@app.delete("/devices/{device_id}", tags=["Devices"])
def unlink_device(device_id: str, doctor_id: str = Depends(get_current_doctor)):
    if device_id not in DB["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    DB["devices"].pop(device_id)
    return {"message": "Device unlinked"}

# ──────────────────────────────────────────────
# EXERCISES
# ──────────────────────────────────────────────

@app.get("/exercises", tags=["Exercises"])
def list_exercises(body_part: Optional[str] = None):
    exs = list(DB["exercises"].values())
    if body_part:
        exs = [e for e in exs if body_part.lower() in e["body_part"].lower()]
    return {"exercises": exs, "count": len(exs)}

@app.post("/exercises", tags=["Exercises"], status_code=201)
def create_exercise(payload: ExerciseCreate, doctor_id: str = Depends(get_current_doctor)):
    ex_id = "EX" + str(len(DB["exercises"]) + 1).zfill(3)
    DB["exercises"][ex_id] = {"id": ex_id, **payload.dict()}
    return {"exercise_id": ex_id, "message": "Exercise added to library"}

@app.get("/exercises/{exercise_id}", tags=["Exercises"])
def get_exercise(exercise_id: str):
    ex = DB["exercises"].get(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ex

# ──────────────────────────────────────────────
# SCHEDULE
# ──────────────────────────────────────────────

@app.get("/patients/{patient_id}/schedule", tags=["Schedule"])
def get_schedule(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    """Get the weekly exercise schedule for a patient."""
    schedule = DB["schedules"].get(patient_id, {})
    return {"patient_id": patient_id, "schedule": schedule}

@app.put("/patients/{patient_id}/schedule", tags=["Schedule"])
def set_schedule(patient_id: str, payload: WeekSchedulePayload, doctor_id: str = Depends(get_current_doctor)):
    """
    Set or replace the weekly exercise schedule.
    If apply_same_daily=True, the first day's schedule is applied to all 7 days.
    """
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    if payload.apply_same_daily and payload.schedule:
        template = payload.schedule[0].exercises
        day_schedule = {day.value: [e.dict() for e in template] for day in DayOfWeek}
    else:
        day_schedule = {entry.day.value: [e.dict() for e in entry.exercises] for entry in payload.schedule}

    DB["schedules"][patient_id] = day_schedule
    return {"message": "Schedule saved", "patient_id": patient_id, "days": list(day_schedule.keys())}

@app.get("/patients/{patient_id}/schedule/today", tags=["Schedule"])
def get_todays_schedule(patient_id: str):
    """
    Called by the patient app on launch — returns today's prescribed exercises.
    No auth (patient-facing endpoint using device_id header in prod).
    """
    schedule = DB["schedules"].get(patient_id, {})
    today = datetime.utcnow().strftime("%a")  # Mon, Tue...
    todays = schedule.get(today, [])
    enriched = []
    for item in todays:
        ex = DB["exercises"].get(item.get("exercise_id"), {})
        enriched.append({**item, "exercise": ex})
    return {"patient_id": patient_id, "day": today, "exercises": enriched, "count": len(enriched)}

# ──────────────────────────────────────────────
# SESSIONS  (submitted by patient app)
# ──────────────────────────────────────────────

@app.post("/sessions", tags=["Sessions"], status_code=201)
def submit_session(payload: SessionReport, background_tasks: BackgroundTasks):
    """
    Patient app submits session data after exercise completes.
    ML model results, rep correctness, and sensor data come here.
    """
    session_id = "SES" + uuid.uuid4().hex[:8].upper()
    correct_reps = sum(1 for r in payload.reps_data if r.correct)
    total_reps = len(payload.reps_data)
    compliance_pct = round((correct_reps / total_reps * 100) if total_reps else 0, 1)

    error_types = list({r.error_type for r in payload.reps_data if not r.correct and r.error_type})

    session = {
        "session_id": session_id,
        **payload.dict(),
        "reps_data": [r.dict() for r in payload.reps_data],
        "correct_reps": correct_reps,
        "total_reps": total_reps,
        "compliance_pct": compliance_pct,
        "error_types": error_types,
        "recorded_at": datetime.utcnow().isoformat(),
    }
    DB["sessions"].append(session)

    # Trigger agentic response if errors detected
    if error_types:
        has_secondary = payload.secondary_device_id is not None
        background_tasks.add_task(
            _trigger_agentic_data_collection,
            AgenticTriggerPayload(
                patient_id=payload.patient_id,
                session_id=session_id,
                error_types=error_types,
                device_available=has_secondary,
                secondary_device_id=payload.secondary_device_id,
            )
        )

    return {"session_id": session_id, "compliance_pct": compliance_pct, "errors_detected": len(error_types)}

@app.get("/sessions", tags=["Sessions"])
def list_sessions(
    patient_id: Optional[str] = None,
    session_type: Optional[SessionType] = None,
    limit: int = 50,
    doctor_id: str = Depends(get_current_doctor)
):
    """Doctor view: all sessions, optionally filtered by patient or type."""
    sessions = DB["sessions"]
    if patient_id:
        sessions = [s for s in sessions if s["patient_id"] == patient_id]
    if session_type:
        sessions = [s for s in sessions if s["session_type"] == session_type]
    return {"sessions": sessions[-limit:], "count": len(sessions)}

@app.get("/sessions/{session_id}", tags=["Sessions"])
def get_session(session_id: str, doctor_id: str = Depends(get_current_doctor)):
    session = next((s for s in DB["sessions"] if s["session_id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# ──────────────────────────────────────────────
# TIMELINE (doctor-facing)
# ──────────────────────────────────────────────

@app.get("/timeline", tags=["Timeline"])
def get_timeline(
    patient_id: Optional[str] = None,
    days: int = 7,
    doctor_id: str = Depends(get_current_doctor)
):
    """
    Returns timeline events with type annotation:
    - prescribed → shown in purple
    - self → shown in blue
    """
    sessions = DB["sessions"]
    if patient_id:
        sessions = [s for s in sessions if s["patient_id"] == patient_id]

    timeline = []
    for s in sessions[-100:]:
        ex = DB["exercises"].get(s.get("exercise_id"), {})
        pt = DB["patients"].get(s.get("patient_id"), {})
        timeline.append({
            "session_id": s["session_id"],
            "patient_id": s["patient_id"],
            "patient_name": f"{pt.get('first_name','')} {pt.get('last_name','')}".strip(),
            "exercise_name": ex.get("name", "Unknown"),
            "exercise_icon": ex.get("icon", "💪"),
            "session_type": s["session_type"],
            "color": "#7c3aed" if s["session_type"] == "prescribed" else "#2196f3",
            "sets": s.get("sets_completed"),
            "correct_reps": s.get("correct_reps"),
            "total_reps": s.get("total_reps"),
            "compliance_pct": s.get("compliance_pct"),
            "form_quality": s.get("form_quality"),
            "error_types": s.get("error_types", []),
            "recorded_at": s.get("recorded_at"),
        })
    return {"timeline": sorted(timeline, key=lambda x: x["recorded_at"], reverse=True), "count": len(timeline)}

# ──────────────────────────────────────────────
# COMPLIANCE
# ──────────────────────────────────────────────

@app.get("/compliance/{patient_id}", tags=["Compliance"])
def get_compliance(patient_id: str, doctor_id: str = Depends(get_current_doctor)):
    """Compute compliance % for a patient."""
    pt = DB["patients"].get(patient_id)
    if not pt or pt["doctor_id"] != doctor_id:
        raise HTTPException(status_code=404, detail="Patient not found")

    sessions = [s for s in DB["sessions"] if s["patient_id"] == patient_id]
    prescribed = [s for s in sessions if s["session_type"] == "prescribed"]
    self_init = [s for s in sessions if s["session_type"] == "self"]

    avg_compliance = round(
        sum(s.get("compliance_pct", 0) for s in prescribed) / len(prescribed)
        if prescribed else 0, 1
    )
    return {
        "patient_id": patient_id,
        "total_sessions": len(sessions),
        "prescribed_sessions": len(prescribed),
        "self_initiated_sessions": len(self_init),
        "average_compliance_pct": avg_compliance,
        "missed_sessions": max(0, pt.get("sessions_per_week", 5) - len(prescribed)),
    }

# ──────────────────────────────────────────────
# ALERTS
# ──────────────────────────────────────────────

@app.get("/alerts", tags=["Alerts"])
def get_alerts(doctor_id: str = Depends(get_current_doctor)):
    """Fetch all alerts for the doctor's patients."""
    doctor_pt_ids = {p["id"] for p in DB["patients"].values() if p["doctor_id"] == doctor_id}
    alerts = [a for a in DB["alerts"] if a.get("patient_id") in doctor_pt_ids]
    return {"alerts": alerts, "count": len(alerts)}

@app.post("/alerts", tags=["Alerts"], status_code=201)
def create_alert(payload: Alert):
    """System/ML layer creates alerts (called internally or by sensor edge logic)."""
    alert = {
        "alert_id": "ALT" + uuid.uuid4().hex[:6].upper(),
        **payload.dict(),
        "created_at": datetime.utcnow().isoformat(),
        "resolved": False,
    }
    DB["alerts"].append(alert)
    return {"alert_id": alert["alert_id"], "message": "Alert created"}

@app.patch("/alerts/{alert_id}/resolve", tags=["Alerts"])
def resolve_alert(alert_id: str, doctor_id: str = Depends(get_current_doctor)):
    alert = next((a for a in DB["alerts"] if a["alert_id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert["resolved"] = True
    alert["resolved_at"] = datetime.utcnow().isoformat()
    return {"message": "Alert resolved"}

# ──────────────────────────────────────────────
# AGENTIC SENSOR TRIGGER
# ──────────────────────────────────────────────

@app.post("/sessions/agentic-trigger", tags=["Agentic"])
def agentic_trigger(payload: AgenticTriggerPayload, doctor_id: str = Depends(get_current_doctor)):
    """
    Manually trigger agentic data collection for a session with errors.
    Auto-called from session submission background task.
    """
    return _trigger_agentic_data_collection(payload)

def _trigger_agentic_data_collection(payload: AgenticTriggerPayload):
    """
    Agentic response logic:
    - If secondary device available → instruct it to switch to sensor-only mode and re-record
    - If no secondary device → halt exercise, send alert, request doctor review
    """
    result = {
        "session_id": payload.session_id,
        "error_types": payload.error_types,
        "action_taken": None,
        "instructions": [],
    }
    if payload.device_available and payload.secondary_device_id:
        result["action_taken"] = "secondary_sensor_activated"
        result["instructions"] = [
            f"Device {payload.secondary_device_id} switched to motion-sensor mode",
            "Re-recording next set with dual-sensor fusion",
            "Primary device continues camera + display",
        ]
        # Update device role
        dev = DB["devices"].get(payload.secondary_device_id)
        if dev:
            dev["role"] = "sensor"
    else:
        result["action_taken"] = "exercise_paused_alert_raised"
        result["instructions"] = [
            "No secondary sensor available",
            "Exercise flagged — doctor review required",
            "Push notification sent to patient to correct form",
        ]
        # Raise alert
        DB["alerts"].append({
            "alert_id": "ALT" + uuid.uuid4().hex[:6].upper(),
            "patient_id": payload.patient_id,
            "alert_type": "form_error",
            "message": f"Session {payload.session_id}: errors detected — {', '.join(payload.error_types)}. No sensor available.",
            "severity": "high",
            "created_at": datetime.utcnow().isoformat(),
            "resolved": False,
        })
    return result

def _generate_qr_artifact(patient_id: str, token: str):
    """Background task: in production, would render and store a QR PNG to S3."""
    print(f"[QR] Generated QR for {patient_id} → token: {token}")

# ──────────────────────────────────────────────
# PATIENT APP ENDPOINTS (no doctor auth)
# ──────────────────────────────────────────────

@app.get("/app/patient/{patient_id}/exercises", tags=["Patient App"])
def app_get_exercises(patient_id: str):
    """Patient app: get today's prescribed routine + exercise metadata."""
    schedule = DB["schedules"].get(patient_id, {})
    today = datetime.utcnow().strftime("%a")
    todays = schedule.get(today, [])
    enriched = []
    for item in todays:
        ex = DB["exercises"].get(item.get("exercise_id"), {})
        enriched.append({
            "exercise_id": item.get("exercise_id"),
            "name": ex.get("name"),
            "icon": ex.get("icon"),
            "body_part": ex.get("body_part"),
            "ml_model": ex.get("ml_model"),
            "sets": item.get("sets", 3),
            "reps": item.get("reps", 10),
            "hold_seconds": item.get("hold_seconds", 0),
            "notes": item.get("notes_for_patient"),
        })
    return {"day": today, "exercises": enriched}

@app.get("/app/patient/{patient_id}/progress", tags=["Patient App"])
def app_get_progress(patient_id: str):
    """Patient app: summary of progress for the account page."""
    sessions = [s for s in DB["sessions"] if s["patient_id"] == patient_id]
    return {
        "total_sessions": len(sessions),
        "prescribed_sessions": sum(1 for s in sessions if s["session_type"] == "prescribed"),
        "self_initiated": sum(1 for s in sessions if s["session_type"] == "self"),
        "avg_form": round(
            sum({"Excellent":4,"Good":3,"Fair":2,"Poor":1}.get(s.get("form_quality","Fair"),2) for s in sessions)
            / len(sessions) if sessions else 0, 2
        ),
        "streak_days": 0,  # compute from session dates in production
    }

# ──────────────────────────────────────────────
# DASHBOARD SUMMARY
# ──────────────────────────────────────────────

@app.get("/dashboard", tags=["Dashboard"])
def get_dashboard(doctor_id: str = Depends(get_current_doctor)):
    """Top-level dashboard stats for the doctor portal."""
    my_patients = [p for p in DB["patients"].values() if p["doctor_id"] == doctor_id]
    active = sum(1 for p in my_patients if p["status"] == "active")
    my_pt_ids = {p["id"] for p in my_patients}
    sessions_today = [
        s for s in DB["sessions"]
        if s["patient_id"] in my_pt_ids
        and s.get("recorded_at", "").startswith(datetime.utcnow().strftime("%Y-%m-%d"))
    ]
    unresolved_alerts = [
        a for a in DB["alerts"]
        if a.get("patient_id") in my_pt_ids and not a.get("resolved")
    ]
    avg_compliance = round(
        sum(s.get("compliance_pct", 0) for s in DB["sessions"] if s["patient_id"] in my_pt_ids)
        / max(len([s for s in DB["sessions"] if s["patient_id"] in my_pt_ids]), 1), 1
    )
    return {
        "total_patients": len(my_patients),
        "active_patients": active,
        "sessions_today": len(sessions_today),
        "unresolved_alerts": len(unresolved_alerts),
        "avg_compliance_pct": avg_compliance,
    }