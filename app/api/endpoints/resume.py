
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
from app.models.models import UserProfile, User, Experience, Education, Skill, Project

# Link User Dependency
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = user_data.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create user if missing logic (auto-provisioning for demo)
        user = User(
            username=user_data.get("name", email.split('@')[0]),
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/generate/pdf")
async def generate_resume_pdf(
    data: ResumeData, 
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Determine template
        template_name = "professional" # Default
        
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

        return {"raw_analysis": result}

@router.post("/score_pdf")
async def score_resume_pdf(file: UploadFile = File(...)):
    """
    Extracts text from PDF and scores it.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        from pypdf import PdfReader
        from io import BytesIO

        content = await file.read()
        pdf = PdfReader(BytesIO(content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        
        # Reuse existing scoring logic
        result = await ai_service.score_resume(text)
        try:
             json_result = json.loads(result.replace('```json', '').replace('```', ''))
             return json_result
        except:
             return {"raw_analysis": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

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
@router.post("/analyze")
async def analyze_resume(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes the user's profile and returns a score + enhanced version.
    """
    # 1. Fetch full profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    experiences = db.query(Experience).filter(Experience.user_id == current_user.id).all()
    education = db.query(Education).filter(Education.user_id == current_user.id).all()
    skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()

    # 2. Construct dict
    profile_data = {
        "personal_info": {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin": profile.linkedin,
            "github": profile.github,
            "portfolio": profile.portfolio
        },
        "summary": profile.summary,
        "experience": [{"id": e.id, "title": e.title, "company": e.company, "start_date": e.start_date, "end_date": e.end_date, "description": e.description, "achievements": e.achievements or []} for e in experiences],
        "education": [{"id": e.id, "degree": e.degree, "institution": e.institution, "graduation_date": e.graduation_date, "gpa": e.gpa} for e in education],
        "skills": [{"id": s.id, "category": s.category, "skills": s.skills or []} for s in skills],
        "projects": [{"id": p.id, "name": p.name, "description": p.description, "date": p.date, "technologies": p.technologies or []} for p in projects]
    }

    # 3. Call AI
    result = await ai_service.analyze_and_enhance(profile_data)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@router.post("/apply_enhancements")
async def apply_enhancements(
    enhanced_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Overwrites the user's profile with the enhanced data.
    """
    if "enhanced_profile" not in enhanced_data:
        raise HTTPException(status_code=400, detail="Invalid data format")

    new_profile = enhanced_data["enhanced_profile"]
    
    # Update Summary
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if "summary" in new_profile and new_profile["summary"]:
        profile.summary = new_profile["summary"]

    # Update Experience Descriptions
    db_exps = db.query(Experience).filter(Experience.user_id == current_user.id).all()
    new_exps = new_profile.get("experience", [])
    
    # Match by index (Assuming AI preserves order)
    for i, db_exp in enumerate(db_exps):
        if i < len(new_exps):
            db_exp.description = new_exps[i].get("description", db_exp.description)
            # Optional: Update achievements if returned
            
    # Update Project Descriptions
    db_projs = db.query(Project).filter(Project.user_id == current_user.id).all()
    new_projs = new_profile.get("projects", [])
    
    for i, db_proj in enumerate(db_projs):
        if i < len(new_projs):
            db_proj.description = new_projs[i].get("description", db_proj.description)

    db.commit()
    return {"status": "success", "message": "Enhancements applied successfully"}

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parses a PDF resume, extracts structured data using AI, and updates the user profile.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # 1. Read PDF content
        from pypdf import PdfReader
        from io import BytesIO

        content = await file.read()
        pdf = PdfReader(BytesIO(content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        
        # 2. Extract structured data using AI
        extracted_data = await ai_service.extract_profile_from_text(text)
        
        if not extracted_data:
             raise HTTPException(status_code=500, detail="Failed to extract data from resume")

        # 3. Update Profile Data
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
        
        # Helper to update if empty or overwrite? 
        # Strategy: Overwrite fields if they are present in extraction
        
        p_info = extracted_data.get("personal_info", {})
        if p_info.get("full_name"): profile.full_name = p_info["full_name"]
        if p_info.get("email"): profile.email = p_info["email"]
        if p_info.get("phone"): profile.phone = p_info["phone"]
        if p_info.get("location"): profile.location = p_info["location"]
        if p_info.get("linkedin"): profile.linkedin = p_info["linkedin"]
        if p_info.get("github"): profile.github = p_info["github"]
        if p_info.get("portfolio"): profile.portfolio = p_info["portfolio"]
        
        if extracted_data.get("summary"):
            profile.summary = extracted_data["summary"]

        # Clear existing lists to avoid duplicates on re-upload
        # Or should we append? Upload usually implies "Import this resume", so getting a fresh state is safer.
        db.query(Experience).filter(Experience.user_id == current_user.id).delete()
        db.query(Education).filter(Education.user_id == current_user.id).delete()
        db.query(Skill).filter(Skill.user_id == current_user.id).delete()
        db.query(Project).filter(Project.user_id == current_user.id).delete()
        
        # Add Experience
        for exp in extracted_data.get("experience", []):
            db_exp = Experience(
                user_id=current_user.id,
                title=exp.get("title"),
                company=exp.get("company"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                description=exp.get("description"),
                achievements=json.dumps(exp.get("achievements", []))
            )
            db.add(db_exp)
            
        # Add Education
        for edu in extracted_data.get("education", []):
            db_edu = Education(
                user_id=current_user.id,
                degree=edu.get("degree"),
                institution=edu.get("institution"),
                graduation_date=edu.get("graduation_date"),
                gpa=edu.get("gpa")
            )
            db.add(db_edu)
            
        # Add Skills
        for skill_cat in extracted_data.get("skills", []):
            db_skill = Skill(
                user_id=current_user.id,
                category=skill_cat.get("category"),
                skills=json.dumps(skill_cat.get("skills", []))
            )
            db.add(db_skill)
            
        # Add Projects
        for proj in extracted_data.get("projects", []):
            db_proj = Project(
                user_id=current_user.id,
                name=proj.get("name"),
                description=proj.get("description"),
                date=proj.get("date"),
                technologies=json.dumps(proj.get("technologies", []))
            )
            db.add(db_proj)

        db.commit()
        return {"status": "success", "message": "Resume uploaded and parsed successfully"}

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
