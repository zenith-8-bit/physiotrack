from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os

from .database import engine
from .models import Base
from .api import exercises, users, patients, ai, timeline, schedules, dashboard
from .seed import seed_database

# Create all tables
Base.metadata.create_all(bind=engine)

# Seed database on startup
seed_database()

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

# Include API routers - ORDER MATTERS
app.include_router(exercises.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(schedules.router)  # ADD THIS LINE
app.include_router(ai.router)
app.include_router(timeline.router)
app.include_router(dashboard.router)
@app.get("/", response_class=HTMLResponse)
def doctor_dashboard():
    """Serve doctor portal"""
    try:
        with open("app/static/physiotrack_doctor_portal.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Doctor Portal HTML not found</h1>"

@app.get("/mobile", response_class=HTMLResponse)
def patient_dashboard():
    """Serve patient mobile dashboard"""
    try:
        with open("app/static/physioai_dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Patient Dashboard HTML not found</h1>"

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "PhysioAI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)