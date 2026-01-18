
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Chat Schemas ---
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    timestamp: datetime
    class Config:
        from_attributes = True

class ChatSessionBase(BaseModel):
    title: str

class ChatSessionCreate(ChatSessionBase):
    user_id: int

class ChatSession(ChatSessionBase):
    id: int
    created_at: datetime
    messages: List[Message] = []
    class Config:
        from_attributes = True

# --- Resume Schemas ---
class ResumeData(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    summary: Optional[str] = None
    education: List[dict] = []
    experience: List[dict] = []
    skills: List[str] = []
    projects: List[dict] = []

class ResumeCreate(BaseModel):
    title: str
    user_id: int
    data: ResumeData

class ResumeResponse(BaseModel):
    id: int
    title: str
    score: float
    created_at: datetime
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    class Config:
        from_attributes = True

# --- API Request/Response ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    user_id: int # Simulating auth for now

class ScoreRequest(BaseModel):
    resume_text: str

class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = ""
