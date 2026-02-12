

from fastapi import APIRouter, Depends, Request
from app.services.job_service import job_service
from app.services.ai_service import ai_service
from app.schemas.schemas import JobSearchRequest
from app.db.database import get_db
from sqlalchemy.orm import Session
from typing import List, Dict

router = APIRouter()

@router.post("/search", response_model=List[Dict])
async def search_jobs(request: JobSearchRequest):
    """
    Searches for jobs using the configured Job Service (Arbeitnow + Remotive + Fallback).
    """
    return job_service.search_jobs(request.query, request.location)

@router.get("/ai-recommendations")
async def get_ai_recommendations(request: Request, db: Session = Depends(get_db)):
    """
    Get AI-powered job recommendations based on user profile.
    """
    from app.api.endpoints.profile import get_current_user_id
    from app.models.models import UserProfile, Experience, Skill
    
    try:
        # Get user profile
        user_id = get_current_user_id(request, db)
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        experiences = db.query(Experience).filter(Experience.user_id == user_id).all()
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        
        recommendations = []
        seen_titles = set()  # Track unique job titles to avoid duplicates
        
        # Search for jobs based on skills (diversify across skill categories)
        if skills:
            for skill in skills[:3]:  # Take first 3 skill categories for diversity
                skill_list = skill.skills if isinstance(skill.skills, list) else []
                if skill_list and len(skill_list) > 0:
                    # Search for real jobs using the first skill
                    search_query = skill_list[0]
                    jobs = job_service.search_jobs(search_query, "Remote")
                    
                    # Add only unique jobs (check title similarity)
                    added_from_category = 0
                    for job in jobs:
                        job_title = job.get("title", "").lower()
                        # Check if we haven't seen a very similar title
                        is_duplicate = any(
                            job_title in seen or seen in job_title 
                            for seen in seen_titles
                        )
                        
                        if not is_duplicate and added_from_category < 2:  # Max 2 per skill category
                            recommendations.append({
                                "role": job.get("title", ""),
                                "company": job.get("company", ""),
                                "location": job.get("location", "Remote"),
                                "description": job.get("description", "")[:150] + "..." if len(job.get("description", "")) > 150 else job.get("description", ""),
                                "url": job.get("url", ""),
                                "remote": job.get("remote", False),
                                "reason": f"Matches your {skill.category} expertise"
                            })
                            seen_titles.add(job_title)
                            added_from_category += 1
                        
                        if len(recommendations) >= 5:
                            break
                    
                    if len(recommendations) >= 5:
                        break
        
        # If we still need more recommendations, add from experience
        if experiences and len(recommendations) < 5:
            latest_exp = experiences[0]
            jobs = job_service.search_jobs(latest_exp.title, "Remote")
            
            for job in jobs:
                if len(recommendations) >= 5:
                    break
                    
                job_title = job.get("title", "").lower()
                is_duplicate = any(
                    job_title in seen or seen in job_title 
                    for seen in seen_titles
                )
                
                if not is_duplicate:
                    recommendations.append({
                        "role": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", "Remote"),
                        "description": job.get("description", "")[:150] + "..." if len(job.get("description", "")) > 150 else job.get("description", ""),
                        "url": job.get("url", ""),
                        "remote": job.get("remote", False),
                        "reason": f"Similar to your role as {latest_exp.title}"
                    })
                    seen_titles.add(job_title)
        
        return {"recommendations": recommendations[:5]}  # Limit to 5 recommendations
        
    except Exception as e:
        print(f"Error getting AI recommendations: {e}")
        import traceback
        traceback.print_exc()
        return {"recommendations": []}

@router.post("/save")
async def save_job(job_data: Dict, db: Session = Depends(get_db)):
    """
    Save a job for later viewing/application.
    """
    from app.models.models import SavedJob
    
    try:
        # For now, using hardcoded user_id (in production, get from session)
        user_id = 1
        
        # Check if job already saved
        existing = db.query(SavedJob).filter(
            SavedJob.user_id == user_id,
            SavedJob.url == job_data.get("url")
        ).first()
        
        if existing:
            return {"message": "Job already saved", "id": existing.id}
        
        # Create new saved job
        saved_job = SavedJob(
            user_id=user_id,
            title=job_data.get("title"),
            company=job_data.get("company"),
            location=job_data.get("location"),
            url=job_data.get("url"),
            remote=job_data.get("remote", False),
            description=job_data.get("description"),
            source=job_data.get("source", "unknown")
        )
        
        db.add(saved_job)
        db.commit()
        db.refresh(saved_job)
        
        return {"message": "Job saved successfully", "id": saved_job.id}
    except Exception as e:
        db.rollback()
        print(f"Error saving job: {e}")
        return {"error": str(e)}

@router.delete("/unsave/{job_id}")
async def unsave_job(job_id: int, db: Session = Depends(get_db)):
    """
    Remove a saved job.
    """
    from app.models.models import SavedJob
    
    try:
        user_id = 1  # Hardcoded for now
        
        saved_job = db.query(SavedJob).filter(
            SavedJob.id == job_id,
            SavedJob.user_id == user_id
        ).first()
        
        if not saved_job:
            return {"error": "Job not found"}
        
        db.delete(saved_job)
        db.commit()
        
        return {"message": "Job removed successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error removing job: {e}")
        return {"error": str(e)}

@router.get("/saved")
async def get_saved_jobs(db: Session = Depends(get_db)):
    """
    Get all saved jobs for the user.
    """
    from app.models.models import SavedJob
    
    try:
        user_id = 1  # Hardcoded for now
        
        saved_jobs = db.query(SavedJob).filter(
            SavedJob.user_id == user_id
        ).order_by(SavedJob.created_at.desc()).all()
        
        return [{
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "remote": job.remote,
            "description": job.description,
            "source": job.source,
            "status": job.status,
            "applied_date": job.applied_date.isoformat() if job.applied_date else None,
            "notes": job.notes,
            "created_at": job.created_at.isoformat()
        } for job in saved_jobs]
    except Exception as e:
        print(f"Error getting saved jobs: {e}")
        return []

@router.patch("/update-status/{job_id}")
async def update_job_status(job_id: int, status_data: Dict, db: Session = Depends(get_db)):
    """
    Update the application status of a saved job.
    """
    from app.models.models import SavedJob
    from datetime import datetime
    
    try:
        user_id = 1  # Hardcoded for now
        
        saved_job = db.query(SavedJob).filter(
            SavedJob.id == job_id,
            SavedJob.user_id == user_id
        ).first()
        
        if not saved_job:
            return {"error": "Job not found"}
        
        # Update status
        if "status" in status_data:
            saved_job.status = status_data["status"]
            if status_data["status"] == "applied" and not saved_job.applied_date:
                saved_job.applied_date = datetime.utcnow()
        
        if "notes" in status_data:
            saved_job.notes = status_data["notes"]
        
        db.commit()
        
        return {"message": "Job status updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error updating job status: {e}")
        return {"error": str(e)}

