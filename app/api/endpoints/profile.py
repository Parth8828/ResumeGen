from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db.database import get_db
from app.models.models import UserProfile, Experience, Education, Skill, Project, ResumeHistory
from datetime import datetime

router = APIRouter()

# Pydantic Models for Request/Response

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None

class ExperienceCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: str
    end_date: str
    is_current: bool = False
    description: Optional[str] = None
    achievements: List[str] = []

class EducationCreate(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = None
    graduation_date: str
    gpa: Optional[str] = None

class SkillCreate(BaseModel):
    category: str
    skills: List[str]

class ProjectCreate(BaseModel):
    name: str
    description: str
    date: Optional[str] = None
    url: Optional[str] = None
    technologies: List[str] = []

# Helper function to get user ID from session
# Helper function to get user ID from session/DB
def get_current_user_id(request: Request, db: Session) -> int:
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Robust lookup by email
    email = user_data.get("email")
    from app.models.models import User
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create user if missing
        user = User(
            username=user_data.get("name", email.split('@')[0]),
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user.id

# Profile Endpoints

@router.get("/")
async def get_profile(request: Request, db: Session = Depends(get_db)):
    """Get user's complete profile"""
    user_id = get_current_user_id(request, db)
    
    # Get or create profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        # Create empty profile
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Get all related data
    experiences = db.query(Experience).filter(Experience.user_id == user_id).order_by(Experience.order).all()
    education = db.query(Education).filter(Education.user_id == user_id).order_by(Education.order).all()
    skills = db.query(Skill).filter(Skill.user_id == user_id).order_by(Skill.order).all()
    projects = db.query(Project).filter(Project.user_id == user_id).order_by(Project.order).all()
    
    return {
        "profile": {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.location,
            "linkedin": profile.linkedin,
            "github": profile.github,
            "portfolio": profile.portfolio,
            "summary": profile.summary,
            "selected_template": profile.selected_template
        },
        "experiences": [
            {
                "id": exp.id,
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "is_current": exp.is_current,
                "description": exp.description,
                "achievements": exp.achievements or []
            }
            for exp in experiences
        ],
        "education": [
            {
                "id": edu.id,
                "degree": edu.degree,
                "institution": edu.institution,
                "location": edu.location,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa
            }
            for edu in education
        ],
        "skills": [
            {
                "id": skill.id,
                "category": skill.category,
                "skills": skill.skills or []
            }
            for skill in skills
        ],
        "projects": [
            {
                "id": proj.id,
                "name": proj.name,
                "description": proj.description,
                "date": proj.date,
                "url": proj.url,
                "technologies": proj.technologies or []
            }
            for proj in projects
        ]
    }

@router.put("/")
async def update_profile(
    request: Request,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user's profile information"""
    user_id = get_current_user_id(request, db)
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    # Update fields
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return {"success": True, "message": "Profile updated successfully"}

# Experience Endpoints

@router.post("/experience")
async def add_experience(
    request: Request,
    exp_data: ExperienceCreate,
    db: Session = Depends(get_db)
):
    """Add new experience"""
    user_id = get_current_user_id(request, db)
    
    # Get max order
    max_order = db.query(Experience).filter(Experience.user_id == user_id).count()
    
    experience = Experience(
        user_id=user_id,
        order=max_order,
        **exp_data.dict()
    )
    db.add(experience)
    db.commit()
    db.refresh(experience)
    
    return {"success": True, "id": experience.id, "message": "Experience added"}

@router.put("/experience/{exp_id}")
async def update_experience(
    request: Request,
    exp_id: int,
    exp_data: ExperienceCreate,
    db: Session = Depends(get_db)
):
    """Update experience"""
    user_id = get_current_user_id(request, db)
    
    experience = db.query(Experience).filter(
        Experience.id == exp_id,
        Experience.user_id == user_id
    ).first()
    
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    
    for field, value in exp_data.dict().items():
        setattr(experience, field, value)
    
    db.commit()
    return {"success": True, "message": "Experience updated"}

@router.delete("/experience/{exp_id}")
async def delete_experience(
    request: Request,
    exp_id: int,
    db: Session = Depends(get_db)
):
    """Delete experience"""
    user_id = get_current_user_id(request, db)
    
    experience = db.query(Experience).filter(
        Experience.id == exp_id,
        Experience.user_id == user_id
    ).first()
    
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    
    db.delete(experience)
    db.commit()
    return {"success": True, "message": "Experience deleted"}

# Education Endpoints

@router.post("/education")
async def add_education(
    request: Request,
    edu_data: EducationCreate,
    db: Session = Depends(get_db)
):
    """Add new education"""
    user_id = get_current_user_id(request, db)
    
    max_order = db.query(Education).filter(Education.user_id == user_id).count()
    
    education = Education(
        user_id=user_id,
        order=max_order,
        **edu_data.dict()
    )
    db.add(education)
    db.commit()
    db.refresh(education)
    
    return {"success": True, "id": education.id, "message": "Education added"}

@router.put("/education/{edu_id}")
async def update_education(
    request: Request,
    edu_id: int,
    edu_data: EducationCreate,
    db: Session = Depends(get_db)
):
    """Update education"""
    user_id = get_current_user_id(request, db)
    
    education = db.query(Education).filter(
        Education.id == edu_id,
        Education.user_id == user_id
    ).first()
    
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    
    for field, value in edu_data.dict().items():
        setattr(education, field, value)
    
    db.commit()
    return {"success": True, "message": "Education updated"}

@router.delete("/education/{edu_id}")
async def delete_education(
    request: Request,
    edu_id: int,
    db: Session = Depends(get_db)
):
    """Delete education"""
    user_id = get_current_user_id(request, db)
    
    education = db.query(Education).filter(
        Education.id == edu_id,
        Education.user_id == user_id
    ).first()
    
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    
    db.delete(education)
    db.commit()
    return {"success": True, "message": "Education deleted"}

# Skills Endpoints

@router.post("/skills")
async def add_skill_category(
    request: Request,
    skill_data: SkillCreate,
    db: Session = Depends(get_db)
):
    """Add new skill category"""
    user_id = get_current_user_id(request, db)
    
    max_order = db.query(Skill).filter(Skill.user_id == user_id).count()
    
    skill = Skill(
        user_id=user_id,
        order=max_order,
        **skill_data.dict()
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return {"success": True, "id": skill.id, "message": "Skill category added"}

@router.put("/skills/{skill_id}")
async def update_skill_category(
    request: Request,
    skill_id: int,
    skill_data: SkillCreate,
    db: Session = Depends(get_db)
):
    """Update skill category"""
    user_id = get_current_user_id(request, db)
    
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == user_id
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill category not found")
    
    for field, value in skill_data.dict().items():
        setattr(skill, field, value)
    
    db.commit()
    return {"success": True, "message": "Skill category updated"}

@router.delete("/skills/{skill_id}")
async def delete_skill_category(
    request: Request,
    skill_id: int,
    db: Session = Depends(get_db)
):
    """Delete skill category"""
    user_id = get_current_user_id(request, db)
    
    skill = db.query(Skill).filter(
        Skill.id == skill_id,
        Skill.user_id == user_id
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill category not found")
    
    db.delete(skill)
    db.commit()
    return {"success": True, "message": "Skill category deleted"}

# Projects Endpoints

@router.post("/projects")
async def add_project(
    request: Request,
    proj_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Add new project"""
    user_id = get_current_user_id(request, db)
    
    max_order = db.query(Project).filter(Project.user_id == user_id).count()
    
    project = Project(
        user_id=user_id,
        order=max_order,
        **proj_data.dict()
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {"success": True, "id": project.id, "message": "Project added"}

@router.put("/projects/{proj_id}")
async def update_project(
    request: Request,
    proj_id: int,
    proj_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Update project"""
    user_id = get_current_user_id(request, db)
    
    project = db.query(Project).filter(
        Project.id == proj_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in proj_data.dict().items():
        setattr(project, field, value)
    
    db.commit()
    return {"success": True, "message": "Project updated"}

@router.delete("/projects/{proj_id}")
async def delete_project(
    request: Request,
    proj_id: int,
    db: Session = Depends(get_db)
):
    """Delete project"""
    user_id = get_current_user_id(request, db)
    
    project = db.query(Project).filter(
        Project.id == proj_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"success": True, "message": "Project deleted"}

# Resume History Endpoints

@router.get("/resume-history")
async def get_resume_history(request: Request, db: Session = Depends(get_db)):
    """Get all user's resume history"""
    user_id = get_current_user_id(request, db)
    
    resumes = db.query(ResumeHistory).filter(
        ResumeHistory.user_id == user_id
    ).order_by(ResumeHistory.created_at.desc()).all()
    
    return {
        "resumes": [
            {
                "id": resume.id,
                "title": resume.title,
                "template_used": resume.template_used,
                "file_path": resume.file_path,
                "is_favorite": resume.is_favorite,
                "notes": resume.notes,
                "created_at": resume.created_at.isoformat()
            }
            for resume in resumes
        ]
    }

@router.delete("/resume-history/{resume_id}")
async def delete_resume(
    request: Request,
    resume_id: int,
    db: Session = Depends(get_db)
):
    """Delete resume from history"""
    user_id = get_current_user_id(request, db)
    
    resume = db.query(ResumeHistory).filter(
        ResumeHistory.id == resume_id,
        ResumeHistory.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    db.delete(resume)
    db.commit()
    return {"success": True, "message": "Resume deleted"}

@router.put("/resume-history/{resume_id}/favorite")
async def toggle_favorite(
    request: Request,
    resume_id: int,
    db: Session = Depends(get_db)
):
    """Toggle resume favorite status"""
    user_id = get_current_user_id(request, db)
    
    resume = db.query(ResumeHistory).filter(
        ResumeHistory.id == resume_id,
        ResumeHistory.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume.is_favorite = not resume.is_favorite
    db.commit()
    
    return {"success": True, "is_favorite": resume.is_favorite}

class NotesUpdate(BaseModel):
    notes: str

@router.put("/resume-history/{resume_id}/notes")
async def update_notes(
    request: Request,
    resume_id: int,
    notes_data: NotesUpdate,
    db: Session = Depends(get_db)
):
    """Update resume notes"""
    user_id = get_current_user_id(request, db)
    
    resume = db.query(ResumeHistory).filter(
        ResumeHistory.id == resume_id,
        ResumeHistory.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume.notes = notes_data.notes
    db.commit()
    
    return {"success": True, "message": "Notes updated"}
