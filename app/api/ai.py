from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..services.ai_service import AgenticAIService

router = APIRouter(prefix="/api/ai", tags=["ai"])

class FormAnalysisRequest(BaseModel):
    patient_id: int
    exercise_name: str
    deviation: float = 0
    form_quality: str = "good"

class CoachingRequest(BaseModel):
    patient_id: int
    context: str  # e.g., "start_session", "form_alert"

@router.post("/analyze-form")
async def analyze_form(request: FormAnalysisRequest):
    """
    Agentic AI analyzes exercise form and returns feedback.
    """
    feedback = await AgenticAIService.analyze_form(
        request.patient_id,
        request.exercise_name,
        request.dict()
    )
    return feedback

@router.post("/coaching-message")
async def get_coaching_message(request: CoachingRequest):
    """
    Get AI-generated coaching message.
    """
    message = await AgenticAIService.generate_coaching_message(
        request.patient_id,
        request.context
    )
    return {"message": message}

@router.get("/interject/{patient_id}")
async def get_ai_interject(patient_id: int):
    """
    Get agentic AI popup message during exercise.
    """
    interject = await AgenticAIService.get_alert_interject(patient_id)
    return interject