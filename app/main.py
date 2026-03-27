from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from .database import engine
from .models import Base
from .api import exercises, users, patients, ai

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PhysioAI Backend",
    description="Medical rehabilitation platform API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# Include API routers
app.include_router(exercises.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(ai.router)

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
def doctor_dashboard():
    """Serve doctor portal"""
    try:
        with open("app/static/dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Doctor Portal HTML not found</h1>"

@app.get("/mobile", response_class=HTMLResponse)
def patient_dashboard():
    """Serve patient mobile dashboard"""
    try:
        with open("app/static/phone.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Patient Dashboard HTML not found</h1>"

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "PhysioAI Backend"}

# Seed exercises on startup
@app.on_event("startup")
def seed_data():
    from .database import SessionLocal
    from .models import Exercise
    
    db = SessionLocal()
    try:
        if db.query(Exercise).count() == 0:
            exercises_data = [
                {"name": "Knee Flexion", "icon": "🦵", "body_part": "Knee", "ml_model": "knee_flex_v2", "default_sets": 3, "default_reps": 10},
                {"name": "Shoulder Roll", "icon": "💪", "body_part": "Shoulder", "ml_model": "shoulder_v1", "default_sets": 3, "default_reps": 15},
                {"name": "Hip Abduction", "icon": "🏃", "body_part": "Hip", "ml_model": "hip_abd_v3", "default_sets": 3, "default_reps": 12},
                {"name": "Wrist Curl", "icon": "🤲", "body_part": "Wrist", "ml_model": "wrist_v1", "default_sets": 3, "default_reps": 15},
                {"name": "Calf Raise", "icon": "🦶", "body_part": "Ankle", "ml_model": "calf_v2", "default_sets": 4, "default_reps": 15},
                {"name": "Wall Squat", "icon": "🧱", "body_part": "Knee/Hip", "ml_model": "squat_v3", "default_sets": 3, "default_reps": 1, "default_hold_seconds": 30},
                {"name": "Back Extension", "icon": "🧘", "body_part": "Back", "ml_model": "back_ext_v1", "default_sets": 3, "default_reps": 10},
                {"name": "Straight Leg Raise", "icon": "🦵", "body_part": "Knee", "ml_model": "slr_v2", "default_sets": 3, "default_reps": 10},
                {"name": "Shoulder Abduction", "icon": "💪", "body_part": "Shoulder", "ml_model": "sh_abd_v2", "default_sets": 3, "default_reps": 12},
                {"name": "Bridge Exercise", "icon": "🌉", "body_part": "Hip/Back", "ml_model": "bridge_v2", "default_sets": 3, "default_reps": 10},
                {"name": "Ankle Circles", "icon": "🦶", "body_part": "Ankle", "ml_model": "ankle_circ_v1", "default_sets": 2, "default_reps": 20},
                {"name": "Neck Side Bend", "icon": "🧑", "body_part": "Neck", "ml_model": "neck_v1", "default_sets": 3, "default_reps": 10},
            ]
            
            for ex_data in exercises_data:
                ex = Exercise(**ex_data)
                db.add(ex)
            
            db.commit()
            print("✓ Exercises seeded successfully")
    except Exception as e:
        print(f"Error seeding exercises: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)