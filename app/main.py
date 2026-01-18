from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from starlette.middleware.sessions import SessionMiddleware
from app.api.endpoints import chat, resume, jobs, auth, cover_letter, templates, profile
from app.api import views
import os

app = FastAPI(title="Resume Generator Chatbot")

# Session Middleware (Required for Auth)
# SECRET_KEY should be in .env but using random for mock is fine
app.add_middleware(SessionMiddleware, secret_key="mock-secret-key-resume-gen")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init Database
@app.on_event("startup")
def on_startup():
    init_db()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates_jinja = Jinja2Templates(directory="app/templates")

# Routers (API)
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(cover_letter.router, prefix="/api/cover-letter", tags=["Cover Letter"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])

# Routers (Frontend - Views)
app.include_router(views.router, tags=["Frontend"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Resume Generator Chatbot API"}
