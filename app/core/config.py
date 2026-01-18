
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Generator Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # GEMINI AI
    GEMINI_API_KEY: str = "" # Defaults to empty, should be set in env or .env file
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash" # Default model
    
    # Database
    DATABASE_URL: str = "sqlite:///./resume_gen.db"

    # EMAIL / SMTP
    SMTP_SERVER: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@resumegen.com"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
