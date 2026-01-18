
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.services.ai_service import ai_service
from app.services.resume_generator import resume_generator
from app.schemas.schemas import ScoreRequest, ResumeCreate, ResumeData
from fastapi.responses import FileResponse
import json
import os

router = APIRouter()

from fastapi import Request
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.models.models import UserProfile, User

@router.post("/generate/pdf")
async def generate_resume_pdf(
    data: ResumeData, 
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Determine template
        template_name = "modern_clean" # Default
        
        user_data = request.session.get("user")
        if user_data:
            email = user_data.get("email")
            # Resolve user
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Get profile
                profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
                if profile and profile.selected_template:
                    template_name = profile.selected_template
        
        file_path = resume_generator.generate_pdf(data, template_name=template_name)
        return FileResponse(file_path, media_type='application/pdf', filename=os.path.basename(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score")
async def score_resume(request: ScoreRequest):
    """
    Scores the provided resume text using Gemini AI.
    """
    result = await ai_service.score_resume(request.resume_text)
    try:
        # Try to parse JSON from AI response if it's a string
        json_result = json.loads(result.replace('```json', '').replace('```', ''))
        return json_result
    except:
        # Return raw text if strict JSON parsing fails
        return {"raw_analysis": result}

@router.post("/enhancements")
async def get_enhancements(resume_data: dict):
    """
    Generates enhanced content (summary, skills) for a resume.
    """
    result = await ai_service.generate_resume_content(resume_data)
    try:
        json_result = json.loads(result.replace('```json', '').replace('```', ''))
        return json_result
    except:
         return {"raw_enhancements": result}
