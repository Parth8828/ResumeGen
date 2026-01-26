from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.ai_service import AIService
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
import io
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, UserProfile, Experience, Skill, Project, Education
from fastapi import Request
import json

router = APIRouter()

# Dependency (Copied for stability, should be shared)
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.email == user_data["email"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    tone: str = "professional"
    resume_context: str | None = None

class CoverLetterDownloadRequest(BaseModel):
    cover_letter: str
    job_title: str
    company_name: str

@router.post("/generate")
async def generate_cover_letter(
    request: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a personalized cover letter using AI and User Profile"""
    try:
        candidate_info = ""

        if request.resume_context and request.resume_context.strip():
             # User provided/edited context
             candidate_info = request.resume_context
        else:
            # Fallback to fetching User Profile Data from DB
            profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
            experiences = db.query(Experience).filter(Experience.user_id == current_user.id).all()
            skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
            projects = db.query(Project).filter(Project.user_id == current_user.id).all()
            education = db.query(Education).filter(Education.user_id == current_user.id).all()

            # format data for prompt
            candidate_data = {
                "name": profile.full_name if profile else "Candidate",
                "summary": profile.summary if profile else "",
                "experience": [{
                    "title": e.title, "company": e.company, 
                    "description": e.description, "achievements": e.achievements
                } for e in experiences],
                "skills": [{
                    "category": s.category, "skills": s.skills
                } for s in skills],
                "projects": [{
                    "name": p.name, "description": p.description, "technologies": p.technologies
                } for p in projects],
                 "education": [{
                    "degree": edu.degree, "institution": edu.institution
                } for edu in education]
            }
            candidate_info = json.dumps(candidate_data, indent=2)

        # Define tone-specific instructions
        tone_instructions = {
            "professional": "Use formal, corporate language. Be respectful and professional throughout.",
            "enthusiastic": "Use energetic, passionate language. Show genuine excitement about the opportunity.",
            "creative": "Use unique, personality-driven language. Be memorable and showcase creativity."
        }
        
        tone_instruction = tone_instructions.get(request.tone, tone_instructions["professional"])
        
        # Create AI prompt
        prompt = f"""Generate a highly personalized professional cover letter.

        CANDIDATE PROFILE CONTEXT:
        {candidate_info}

        JOB APPLICATION DETAILS:
        Job Title: {request.job_title}
        Company: {request.company_name}
        Tone: {request.tone.capitalize()}
        
        Job Description:
        {request.job_description}
        
        Instructions:
        - Write the letter AS the candidate defined above.
        - MATCH the candidate's specific skills/experiences to the Job Description requirements.
        - {tone_instruction}
        - Keep it concise (3-4 paragraphs).
        - Start with "Dear Hiring Manager,"
        - End with "Sincerely," followed by the candidate's name (found in profile context).
        - If the candidate data is empty, write a generic template but use brackets for placeholders.

        Generate ONLY the cover letter text, no additional commentary."""

        # Call Gemini API
        ai_service = AIService()
        cover_letter = await ai_service.generate_content(prompt)
        
        return {"cover_letter": cover_letter}
        
    except Exception as e:
        print(f"Cover letter error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

@router.post("/download")
async def download_cover_letter(request: CoverLetterDownloadRequest):
    """Generate PDF of cover letter"""
    try:
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom style for cover letter
        cover_letter_style = ParagraphStyle(
            'CoverLetter',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        
        # Add date
        date_text = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(date_text, cover_letter_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Split cover letter into paragraphs
        paragraphs = request.cover_letter.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Clean up the text
                para = para.strip()
                elements.append(Paragraph(para, cover_letter_style))
                elements.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        buffer.seek(0)
        
        # Sanitize filename
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', request.company_name)
        if not safe_name:
            safe_name = "Cover_Letter"
            
        print(f"PDF Generated. Size: {len(buffer.getvalue())} bytes. Filename: {safe_name}.pdf")

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Cover_Letter_{safe_name}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@router.post("/suggestions")
async def suggest_roles_and_companies(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suggest job roles and companies based on profile"""
    try:
        # Get resume_context from body manual check or just fetch from DB
        body = await request.json()
        resume_context = body.get("resume_context", "")

        candidate_info = ""
        if resume_context and resume_context.strip():
             candidate_info = resume_context
        else:
            # Fallback to DB
            profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
            experiences = db.query(Experience).filter(Experience.user_id == current_user.id).all()
            skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
            
            candidate_data = {
                "name": profile.full_name if profile else "Candidate",
                "summary": profile.summary if profile else "",
                "experience": [e.title for e in experiences],
                "skills": [s.category + ": " + ", ".join(s.skills) for s in skills]
            }
            candidate_info = json.dumps(candidate_data, indent=2)

        ai_service = AIService()
        suggestions = await ai_service.suggest_jobs(candidate_info)
        return suggestions

    except Exception as e:
        print(f"Suggestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

