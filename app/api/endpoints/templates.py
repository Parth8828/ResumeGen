from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Sample resume data for previews
SAMPLE_DATA = {
    "name": "John Doe",
    "title": "Senior Software Engineer",
    "email": "john.doe@email.com",
    "phone": "(555) 123-4567",
    "location": "San Francisco, CA",
    "linkedin": "linkedin.com/in/johndoe",
    "summary": "Experienced software engineer with 5+ years of expertise in full-stack development, specializing in Python, JavaScript, and cloud technologies. Proven track record of delivering scalable solutions and leading cross-functional teams.",
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "start_date": "Jan 2020",
            "end_date": "Present",
            "description": "Lead development of microservices architecture and cloud infrastructure.",
            "achievements": [
                "Improved system performance by 40% through optimization",
                "Led team of 5 developers on critical projects",
                "Implemented CI/CD pipeline reducing deployment time by 60%"
            ]
        },
        {
            "title": "Software Engineer",
            "company": "StartupXYZ",
            "start_date": "Jun 2018",
            "end_date": "Dec 2019",
            "description": "Developed full-stack web applications using React and Node.js.",
            "achievements": [
                "Built customer-facing dashboard serving 10,000+ users",
                "Reduced API response time by 50%"
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University of California",
            "graduation_date": "2018",
            "gpa": "3.8/4.0"
        }
    ],
    "skills": {
        "Programming Languages": ["Python", "JavaScript", "TypeScript", "Java"],
        "Frameworks": ["React", "Node.js", "FastAPI", "Django"],
        "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "CI/CD"],
        "Databases": ["PostgreSQL", "MongoDB", "Redis"]
    },
    "projects": [
        {
            "name": "E-Commerce Platform",
            "date": "2021",
            "description": "Built a scalable e-commerce platform handling 1M+ transactions monthly.",
            "technologies": ["React", "Node.js", "PostgreSQL", "AWS"]
        },
        {
            "name": "Real-Time Analytics Dashboard",
            "date": "2020",
            "description": "Developed real-time analytics dashboard with WebSocket integration.",
            "technologies": ["Python", "FastAPI", "Redis", "Chart.js"]
        }
    ]
}

TEMPLATE_NAMES = {
    "professional": "Professional"
}

@router.get("/list")
async def list_templates():
    """List all available templates"""
    return {
        "templates": [
            {
                "id": template_id,
                "name": name,
                "description": f"{name} resume template"
            }
            for template_id, name in TEMPLATE_NAMES.items()
        ]
    }

@router.get("/preview/{template_name}", response_class=HTMLResponse)
async def preview_template(request: Request, template_name: str):
    """Preview a template with sample data"""
    if template_name not in TEMPLATE_NAMES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        # Render the template with sample data
        # All templates now use the same data format
        template_path = f"resume_templates/{template_name}.html"
        return templates.TemplateResponse(
            template_path,
            {"request": request, **SAMPLE_DATA}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering template: {str(e)}")

class TemplateSelectionRequest(BaseModel):
    template_name: str

from app.db.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.models import User, UserProfile

@router.post("/select")
async def select_template(
    request: Request, 
    selection: TemplateSelectionRequest,
    db: Session = Depends(get_db)
):
    """Save user's template selection"""
    if selection.template_name not in TEMPLATE_NAMES:
        raise HTTPException(status_code=400, detail="Invalid template name")
    
    # Get user from session
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Save to Session (legacy support)
    request.session["selected_template"] = selection.template_name
    
    # SAVE TO DB
    email = user_data.get("email")
    user = db.query(User).filter(User.email == email).first()
    if user:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        
        profile.selected_template = selection.template_name
        db.commit()
    
    return {
        "success": True,
        "message": f"Template switched to {TEMPLATE_NAMES[selection.template_name]}",
        "template_name": selection.template_name
    }

@router.get("/current")
async def get_current_template(request: Request):
    """Get user's current template selection"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get template from session, default to professional
    current_template = request.session.get("selected_template", "professional")
    
    return {
        "template_name": current_template,
        "template_display_name": TEMPLATE_NAMES.get(current_template, "Modern Clean")
    }
