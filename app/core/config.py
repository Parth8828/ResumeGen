
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Generator Chatbot"
    API_V1_STR: str = "/api/v1"
    
    # GEMINI AI
    GEMINI_API_KEYS: str = "" # Comma-separated list
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash" 
    
    @property
    def api_keys(self) -> list[str]:
        if self.GEMINI_API_KEYS:
            return [k.strip() for k in self.GEMINI_API_KEYS.split(',') if k.strip()]
        return []

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
