from app.database import SessionLocal, engine
from app.models import Base, User, PatientProfile, Exercise, ExerciseSession
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed database with initial data"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("✓ Database already seeded")
            return
        
        print("🌱 Seeding database...")
        
        # 1. Create Doctor
        doctor = User(
            name="Dr. Ramesh Iyer",
            email="ramesh.iyer@apollohospitals.com",
            phone="+91-9876543210",
            role="doctor",
            qr_token="DOC001"
        )
        db.add(doctor)
        db.flush()
        
        # 2. Seed Exercises
        exercises_data = [
            {
                "name": "Knee Flexion",
                "icon": "🦵",
                "body_part": "Knee",
                "description": "Bending and straightening of the knee joint",
                "ml_model": "knee_flex_v2",
                "default_sets": 3,
                "default_reps": 10
            },
            {
                "name": "Shoulder Roll",
                "icon": "💪",
                "body_part": "Shoulder",
                "description": "Circular movement of the shoulder joint",
                "ml_model": "shoulder_v1",
                "default_sets": 3,
                "default_reps": 15
            },
            {
                "name": "Hip Abduction",
                "icon": "🏃",
                "body_part": "Hip",
                "description": "Moving leg away from body midline",
                "ml_model": "hip_abd_v3",
                "default_sets": 3,
                "default_reps": 12
            },
            {
                "name": "Wrist Curl",
                "icon": "🤲",
                "body_part": "Wrist",
                "description": "Curling motion of the wrist",
                "ml_model": "wrist_v1",
                "default_sets": 3,
                "default_reps": 15
            },
            {
                "name": "Calf Raise",
                "icon": "🦶",
                "body_part": "Ankle",
                "description": "Raising body weight on toes",
                "ml_model": "calf_v2",
                "default_sets": 4,
                "default_reps": 15
            },
            {
                "name": "Wall Squat",
                "icon": "🧱",
                "body_part": "Knee/Hip",
                "description": "Squat position against wall",
                "ml_model": "squat_v3",
                "default_sets": 3,
                "default_reps": 1,
                "default_hold_seconds": 30
            },
            {
                "name": "Back Extension",
                "icon": "🧘",
                "body_part": "Back",
                "description": "Extension of the back muscles",
                "ml_model": "back_ext_v1",
                "default_sets": 3,
                "default_reps": 10
            },
            {
                "name": "Straight Leg Raise",
                "icon": "🦵",
                "body_part": "Knee",
                "description": "Raising straight leg without bending",
                "ml_model": "slr_v2",
                "default_sets": 3,
                "default_reps": 10
            },
            {
                "name": "Shoulder Abduction",
                "icon": "💪",
                "body_part": "Shoulder",
                "description": "Moving arm away from body",
                "ml_model": "sh_abd_v2",
                "default_sets": 3,
                "default_reps": 12
            },
            {
                "name": "Bridge Exercise",
                "icon": "🌉",
                "body_part": "Hip/Back",
                "description": "Lifting hips off ground",
                "ml_model": "bridge_v2",
                "default_sets": 3,
                "default_reps": 10
            },
            {
                "name": "Ankle Circles",
                "icon": "🦶",
                "body_part": "Ankle",
                "description": "Circular motion of ankle joint",
                "ml_model": "ankle_circ_v1",
                "default_sets": 2,
                "default_reps": 20
            },
            {
                "name": "Neck Side Bend",
                "icon": "🧑",
                "body_part": "Neck",
                "description": "Bending neck to sides",
                "ml_model": "neck_v1",
                "default_sets": 3,
                "default_reps": 10
            },
            {
                "name": "Hip Flexion",
                "icon": "🏃",
                "body_part": "Hip",
                "description": "Raising leg towards chest",
                "ml_model": "hip_flex_v2",
                "default_sets": 3,
                "default_reps": 12
            },
            {
                "name": "Elbow Flexion",
                "icon": "💪",
                "body_part": "Elbow",
                "description": "Bending of elbow joint",
                "ml_model": "elbow_v1",
                "default_sets": 3,
                "default_reps": 15
            },
        ]
        
        exercises = []
        for ex_data in exercises_data:
            ex = Exercise(**ex_data)
            db.add(ex)
            exercises.append(ex)
        db.flush()
        
        # 3. Create Sample Patients
        patients_data = [
            {
                "name": "Suresh Anand",
                "phone": "+91-9876543211",
                "email": "suresh.anand@email.com",
                "diagnosis": "ACL Tear — Post-op Rehab",
                "compliance": 82
            },
            {
                "name": "Priya Mehta",
                "phone": "+91-9876543212",
                "email": "priya.mehta@email.com",
                "diagnosis": "Frozen Shoulder",
                "compliance": 91
            },
            {
                "name": "Rajesh Kumar",
                "phone": "+91-9876543213",
                "email": "rajesh.kumar@email.com",
                "diagnosis": "Hip Replacement Rehab",
                "compliance": 67
            },
            {
                "name": "Anita Nair",
                "phone": "+91-9876543214",
                "email": "anita.nair@email.com",
                "diagnosis": "Lumbar Disc Herniation L4-L5",
                "compliance": 34
            },
            {
                "name": "Deepak Verma",
                "phone": "+91-9876543215",
                "email": "deepak.verma@email.com",
                "diagnosis": "Wrist Fracture Recovery",
                "compliance": 78
            },
            {
                "name": "Kavya Srinivas",
                "phone": "+91-9876543216",
                "email": "kavya.srinivas@email.com",
                "diagnosis": "Knee Osteoarthritis",
                "compliance": 55
            },
            {
                "name": "Vikram Singh",
                "phone": "+91-9876543217",
                "email": "vikram.singh@email.com",
                "diagnosis": "Rotator Cuff Injury",
                "compliance": 88
            },
            {
                "name": "Meera Patel",
                "phone": "+91-9876543218",
                "email": "meera.patel@email.com",
                "diagnosis": "Post-Stroke Rehabilitation",
                "compliance": 72
            },
            {
                "name": "Arjun Desai",
                "phone": "+91-9876543219",
                "email": "arjun.desai@email.com",
                "diagnosis": "Ankle Sprain Recovery",
                "compliance": 85
            },
            {
                "name": "Pooja Sharma",
                "phone": "+91-9876543220",
                "email": "pooja.sharma@email.com",
                "diagnosis": "Back Strain Management",
                "compliance": 60
            },
        ]
        
        patients = []
        status_map = {82: "active", 91: "active", 67: "alert", 34: "alert", 78: "active", 55: "pending", 88: "active", 72: "active", 85: "active", 60: "active"}
        
        for idx, patient_data in enumerate(patients_data):
            user = User(
                name=patient_data["name"],
                phone=patient_data["phone"],
                email=patient_data["email"],
                role="patient"
            )
            db.add(user)
            db.flush()
            
            profile = PatientProfile(
                user_id=user.id,
                diagnosis=patient_data["diagnosis"],
                assigned_doctor_id=doctor.id,
                sessions_per_week=3,
                rehab_duration_weeks=6
            )
            db.add(profile)
            patients.append((profile, patient_data["compliance"], status_map[patient_data["compliance"]]))
        db.flush()
        
        # 4. Create Exercise Sessions (Timeline Data)
        now = datetime.utcnow()
        session_data = [
            (0, 0, "prescribed", 92, "Minor inward collapse in rep 7-9"),
            (1, 1, "self", 100, ""),
            (2, 2, "prescribed", 75, "Secondary phone used as sensor"),
            (0, 7, "prescribed", 100, ""),
            (3, 3, "self", 60, "Wrist not in neutral position"),
            (4, 4, "prescribed", 88, ""),
            (5, 9, "self", 70, "Slight pain during movement"),
            (6, 0, "prescribed", 95, "Excellent form"),
            (1, 8, "prescribed", 82, "Minor deviation"),
            (7, 5, "self", 80, "Good compliance"),
        ]
        
        for patient_idx, exercise_idx, session_type, compliance, notes in session_data:
            session = ExerciseSession(
                patient_id=patients[patient_idx][0].id,
                exercise_id=exercises[exercise_idx].id,
                type=session_type,
                sets=exercises[exercise_idx].default_sets,
                reps=exercises[exercise_idx].default_reps,
                form_score=random.randint(60, 100),
                compliance_score=compliance,
                notes=notes,
                created_at=now - timedelta(hours=random.randint(0, 48))
            )
            db.add(session)
        # 5. Create Sample Schedules
        from .models import ExerciseSchedule

        sample_schedules = [
            {
                "patient_id": 1,  # Suresh Anand
                "schedule": {
                    "Mon": [
                        {"id": 1, "name": "Knee Flexion", "sets": 3, "reps": 10, "hold_seconds": 0},
                        {"id": 7, "name": "Straight Leg Raise", "sets": 3, "reps": 10, "hold_seconds": 0}
                    ],
                    "Tue": [
                        {"id": 2, "name": "Shoulder Roll", "sets": 3, "reps": 15, "hold_seconds": 0}
                    ],
                    "Wed": [
                        {"id": 3, "name": "Hip Abduction", "sets": 3, "reps": 12, "hold_seconds": 0},
                        {"id": 4, "name": "Calf Raise", "sets": 4, "reps": 15, "hold_seconds": 0}
                    ],
                    "Thu": [],
                    "Fri": [
                        {"id": 1, "name": "Knee Flexion", "sets": 3, "reps": 10, "hold_seconds": 0},
                        {"id": 7, "name": "Straight Leg Raise", "sets": 3, "reps": 10, "hold_seconds": 0}
                    ],
                    "Sat": [],
                    "Sun": []
                }
            },
            {
                "patient_id": 2,  # Priya Mehta
                "schedule": {
                    "Mon": [
                        {"id": 2, "name": "Shoulder Roll", "sets": 3, "reps": 15, "hold_seconds": 0},
                        {"id": 9, "name": "Shoulder Abduction", "sets": 3, "reps": 12, "hold_seconds": 0}
                    ],
                    "Tue": [],
                    "Wed": [
                        {"id": 2, "name": "Shoulder Roll", "sets": 3, "reps": 15, "hold_seconds": 0}
                    ],
                    "Thu": [
                        {"id": 9, "name": "Shoulder Abduction", "sets": 3, "reps": 12, "hold_seconds": 0}
                    ],
                    "Fri": [
                        {"id": 2, "name": "Shoulder Roll", "sets": 3, "reps": 15, "hold_seconds": 0},
                        {"id": 9, "name": "Shoulder Abduction", "sets": 3, "reps": 12, "hold_seconds": 0}
                    ],
                    "Sat": [],
                    "Sun": []
                }
            }
        ]

        for sched in sample_schedules:
            schedule = ExerciseSchedule(
                patient_id=sched["patient_id"],
                doctor_id=doctor.id,
                schedule_data=sched["schedule"],
                is_daily_template="false",
                is_active="true"
            )
            db.add(schedule)

        print(f"  - {len(sample_schedules)} Exercise Schedules")
        db.commit()
        print("✓ Database seeded successfully!")
        print(f"  - 1 Doctor: Dr. Ramesh Iyer")
        print(f"  - {len(exercises)} Exercises")
        print(f"  - {len(patients)} Patients")
        print(f"  - {len(session_data)} Session Logs")
        
    except Exception as e:
        print(f"✗ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()