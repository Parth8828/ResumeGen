
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from pydantic import BaseModel
from app.services.email_service import email_service

# Mock DB for OTPs (In-memory for simplicity)
otp_store = {} 

class EmailRequest(BaseModel):
    email: str

class VerifyRequest(BaseModel):
    email: str
    otp: str

router = APIRouter()

@router.post("/email/send-otp")
async def send_otp(request: EmailRequest):
    otp = email_service.generate_otp()
    otp_store[request.email] = otp
    
    success = email_service.send_otp(request.email, otp)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
        
    return {"message": "OTP sent successfully"}

@router.post("/email/verify-otp")
async def verify_otp(request: Request, data: VerifyRequest):
    stored_otp = otp_store.get(data.email)
    
    if not stored_otp or stored_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Login Success - Create Session
    # Using UI Avatars for consistent profile images
    request.session["user"] = {
        "id": data.email,
        "name": data.email.split('@')[0].title(),
        "email": data.email,
        "picture": f"https://ui-avatars.com/api/?name={data.email}&background=2563eb&color=fff"
    }
    
    # Clear OTP
    del otp_store[data.email]
    
    return {"message": "Login successful"}

@router.get("/mock")
async def mock_login(request: Request):
    """
    Simulated Google Login.
    """
    request.session["user"] = {
        "id": "1",
        "name": "Parth (Demo)",
        "email": "parth@example.com",
        "picture": "https://ui-avatars.com/api/?name=Parth+Demo&background=2563eb&color=fff"
    }
    return RedirectResponse(url="/")

@router.get("/logout")
async def logout(request: Request):
    """
    Clears the session.
    """
    request.session.clear()
    return RedirectResponse(url="/login")
