
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.ai_service import ai_service
from app.services.profile_extractor import ProfileExtractor
from app.schemas.schemas import ChatRequest, Message
from app.models.models import ChatSession, ChatMessage, User, UserProfile, Experience, Education, Skill, Project

router = APIRouter()
profile_extractor = ProfileExtractor()

@router.post("/message")
async def chat_message(request_obj: Request, chat_req: ChatRequest, db: Session = Depends(get_db)):
    # Get user from session
    user_data = request_obj.session.get("user")
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_email = user_data.get("email")
    
    # 1. Get or Create User (by email, not ID)
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        # Create new user with auto-incrementing ID
        user = User(
            username=user_data.get("name", user_email.split('@')[0]),
            email=user_email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    user_id = user.id

    # 2. Get or Create Session
    if chat_req.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == chat_req.session_id).first()
        if not session:
             raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=user.id)
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # 3. Store User Message
    user_msg = ChatMessage(session_id=session.id, role="user", content=chat_req.message)
    db.add(user_msg)
    
    # 4. Get AI Response
    # Fetch history for context
    history_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.timestamp).all()
    
    # Convert to proper GenAI format - use Content objects
    from google.genai import types
    history = []
    for m in history_msgs:
        history.append(
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part(text=m.content)]
            )
        )
    
    
    # NEW: Fetch Current Profile for Context
    profile_context = {}
    curr_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if curr_profile:
        profile_context = {
            "personal_info": {
                "name": curr_profile.full_name,
                "email": curr_profile.email,
                "phone": curr_profile.phone,
                "location": curr_profile.location,
                "linkedin": curr_profile.linkedin,
                "github": curr_profile.github,
            },
            "summary": curr_profile.summary
        }
        # Add quick summary of lists
        exps = db.query(Experience).filter(Experience.user_id == user_id).all()
        if exps:
            profile_context["experience"] = [{"title": e.title, "company": e.company, "years": f"{e.start_date}-{e.end_date}"} for e in exps]
        
        edus = db.query(Education).filter(Education.user_id == user_id).all()
        if edus:
            profile_context["education"] = [{"degree": e.degree, "school": e.institution} for e in edus]
            
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        if skills:
            # Flatten skills for context
            all_skills = []
            for s in skills:
                if s.skills:
                    all_skills.extend(s.skills)
            profile_context["skills"] = all_skills

    ai_response_data = await ai_service.generate_chat_response(history, chat_req.message, profile_context=profile_context)
    print(f"DEBUG: ai_response_data keys: {ai_response_data.keys()}")
    ai_response_text = ai_response_data.get("message", "Sorry, I encountered an error.")
    extracted = ai_response_data.get("extracted_data")
    
    # 5. Store AI Message
    ai_msg = ChatMessage(session_id=session.id, role="model", content=ai_response_text)
    db.add(ai_msg)
    db.commit()
    
    # 6. PROCESS EXTRACTED PROFILE DATA (from the same API hit)
    try:
        if extracted:
            print(f"✓ AI extracted profile data: {list(extracted.keys())}")
            
            # Get or create profile
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.add(profile)
            
            # Update personal info (ONLY IF EMPTY)
            if 'personal_info' in extracted and extracted['personal_info']:
                for key, value in extracted['personal_info'].items():
                    # Only update if value exists AND current field is empty/None
                    if value and not getattr(profile, key):
                        setattr(profile, key, value)
            
            # Update summary (ONLY IF EMPTY)
            if 'summary' in extracted and extracted['summary']:
                if not profile.summary:
                    profile.summary = extracted['summary']
                
            # Add experiences (Dedup check)
            if 'experience' in extracted and extracted['experience']:
                for exp_data in extracted['experience']:
                    # Check for duplicate (Title + Company)
                    exists = db.query(Experience).filter(
                        Experience.user_id == user_id,
                        Experience.title == exp_data.get('title'),
                        Experience.company == exp_data.get('company')
                    ).first()
                    if not exists:
                        exp = Experience(user_id=user_id, **exp_data)
                        db.add(exp)
            
            # Add education (Dedup check)
            if 'education' in extracted:
                for edu_data in extracted['education']:
                    exists = db.query(Education).filter(
                        Education.user_id == user_id,
                        Education.degree == edu_data.get('degree'),
                        Education.institution == edu_data.get('institution')
                    ).first()
                    if not exists:
                        edu = Education(user_id=user_id, **edu_data)
                        db.add(edu)
            
            # Add skills (Dedup by Category)
            if 'skills' in extracted:
                for skill_data in extracted['skills']:
                     # Check if category exists
                    existing_cat = db.query(Skill).filter(
                        Skill.user_id == user_id,
                        Skill.category == skill_data.get('category')
                    ).first()
                    
                    if existing_cat:
                        # Append new skills to existing category
                        new_skills = skill_data.get('skills', [])
                        current_skills = existing_cat.skills or []
                        # Merge and uniq
                        updated_skills = list(set(current_skills + new_skills))
                        existing_cat.skills = updated_skills
                    else:
                        skill = Skill(user_id=user_id, **skill_data)
                        db.add(skill)
            
            # Add projects (Dedup by Name)
            if 'projects' in extracted:
                for proj_data in extracted['projects']:
                    exists = db.query(Project).filter(
                        Project.user_id == user_id,
                        Project.name == proj_data.get('name')
                    ).first()
                    if not exists:
                        proj = Project(user_id=user_id, **proj_data)
                        db.add(proj)
            
            db.commit()
            print(f"✓ Auto-extracted and saved profile data: {list(extracted.keys())}")
    
    except Exception as e:
        print(f"Profile extraction error (non-fatal): {e}")
        # Don't fail the chat if extraction fails
    
    # 7. Fetch latest profile data for UI update
    current_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    # Get related data
    experiences = db.query(Experience).filter(Experience.user_id == user_id).all()
    education = db.query(Education).filter(Education.user_id == user_id).all()
    skills = db.query(Skill).filter(Skill.user_id == user_id).all()
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    
    profile_data = {
        "full_name": current_profile.full_name if current_profile else "",
        "email": current_profile.email if current_profile else "",
        "phone": current_profile.phone if current_profile else "",
        "location": current_profile.location if current_profile else "",
        "linkedin": current_profile.linkedin if current_profile else "",
        "github": current_profile.github if current_profile else "",
        "portfolio": current_profile.portfolio if current_profile else "",
        "summary": current_profile.summary if current_profile else "",
        "experience": [{"title": e.title, "company": e.company, "start_date": e.start_date, "end_date": e.end_date, "description": e.description} for e in experiences],
        "education": [{"degree": e.degree, "institution": e.institution, "graduation_date": e.graduation_date} for e in education],
        "skills": [s.category for s in skills] if skills else [], # Simplified for now, or elaborate
        "projects": [{"name": p.name, "description": p.description} for p in projects]
    }

    return {
        "session_id": session.id,
        "message": ai_response_text,
        "profile_data": profile_data, # Return updated profile
        "history": [{"role": m.role, "content": m.content} for m in history_msgs] + 
                   [{"role": "user", "content": chat_req.message}, {"role": "model", "content": ai_response_text}]
    }
