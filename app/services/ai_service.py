import json
from typing import Dict, Any

class AgenticAIService:
    """
    Dummy AI service for now. Replace with real LLM/model integration.
    """
    
    @staticmethod
    async def analyze_form(patient_id: int, exercise_name: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze form data and return AI feedback.
        """
        # Placeholder logic
        feedback = {
            "patient_id": patient_id,
            "exercise": exercise_name,
            "status": "good",
            "message": f"Form looks good for {exercise_name}. Keep up the consistency.",
            "suggestions": [],
            "alert": None
        }
        
        # Example: if deviation > 15, flag it
        if form_data.get("deviation", 0) > 15:
            feedback["status"] = "warning"
            feedback["message"] = f"Detected form deviation during {exercise_name}."
            feedback["suggestions"] = ["Adjust ankle position", "Keep knee straight"]
            feedback["alert"] = "Form correction needed"
        
        return feedback
    
    @staticmethod
    async def generate_coaching_message(patient_id: int, context: str) -> str:
        """
        Generate personalized coaching message based on context.
        """
        messages = {
            "start_session": "Great! Let's begin your session. Remember to focus on form over speed.",
            "mid_session": "You're doing great! Keep the momentum going.",
            "form_alert": "I noticed some form issues. Let's correct that.",
            "compliance": "You've been consistent! Your progress is impressive.",
            "rest": "Time for a rest day. Recovery is important.",
        }
        return messages.get(context, "Keep up the great work!")
    
    @staticmethod
    async def get_alert_interject(patient_id: int) -> Dict[str, Any]:
        """
        Agentic AI interject (pops up during exercise).
        """
        return {
            "type": "form_alert",
            "message": "I noticed unusual ankle rotation during your last rep. Would you like me to show a correction guide?",
            "actions": ["Show Fix", "Dismiss"]
        }