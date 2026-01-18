from fastapi import APIRouter, HTTPException
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

router = APIRouter()

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    tone: str = "professional"

class CoverLetterDownloadRequest(BaseModel):
    cover_letter: str
    job_title: str
    company_name: str

@router.post("/generate")
async def generate_cover_letter(request: CoverLetterRequest):
    """Generate a personalized cover letter using AI"""
    try:
        # Define tone-specific instructions
        tone_instructions = {
            "professional": "Use formal, corporate language. Be respectful and professional throughout.",
            "enthusiastic": "Use energetic, passionate language. Show genuine excitement about the opportunity.",
            "creative": "Use unique, personality-driven language. Be memorable and showcase creativity."
        }
        
        tone_instruction = tone_instructions.get(request.tone, tone_instructions["professional"])
        
        # Create AI prompt
        prompt = f"""Generate a professional cover letter for the following job application:

Job Title: {request.job_title}
Company: {request.company_name}
Tone: {request.tone.capitalize()}

Job Description:
{request.job_description}

Instructions:
- {tone_instruction}
- Make it compelling and specific to the role
- Highlight relevant skills and experience that match the job description
- Keep it concise (3-4 paragraphs)
- Include a strong opening and closing
- Use proper business letter format
- Do NOT include placeholder text like [Your Name] or [Date] - leave those sections blank or use generic text
- Start with "Dear Hiring Manager,"
- End with "Sincerely," followed by a blank line

Generate ONLY the cover letter text, no additional commentary."""

        # Call Gemini API
        ai_service = AIService()
        cover_letter = await ai_service.generate_content(prompt)
        
        return {"cover_letter": cover_letter}
        
    except Exception as e:
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
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Cover_Letter_{request.company_name.replace(' ', '_')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
