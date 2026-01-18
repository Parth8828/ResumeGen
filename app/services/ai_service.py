

from google import genai
from google.genai import types
from app.core.config import get_settings

settings = get_settings()

from pydantic import BaseModel, Field
from typing import List, Optional
import json

# --- Structured Output Models ---
class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None

class SkillCategory(BaseModel):
    category: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)

class ProfileData(BaseModel):
    personal_info: Optional[PersonalInfo] = None
    summary: Optional[str] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: List[SkillCategory] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)

class ChatAndExtractResponse(BaseModel):
    message: str
    extracted_data: Optional[ProfileData] = None

class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model_name = settings.GEMINI_MODEL_NAME
            
            # Specialized Chat System Instruction
            self.chat_system_instruction = """
            You are an expert Resume Builder AI Assistant.
            Your goal is to guide the user specifically to build or improve their resume.
            
            Rules:
            1. If the user says "Hey" or "Hello", welcome them and ask if they want to start building a resume or need help with a specific section.
            2. Do NOT be a generic assistant. Always tie the conversation back to Resumes, Jobs, or Career Advice.
            3. Guide them step-by-step: Ask for Name, then Summary, then Experience, etc.
            4. Be professional, concise, and helpful.
            
            IMPORTANT:
             You must output a JSON object with two keys:
            - "message": Your conversational response to the user.
            - "extracted_data": Any profile information extracted from the user's message (or null if none).
            
            If the user provides ANY profile information (Name, Skills, Experience, Education, Projects), extract it structured into "extracted_data".
            If no new info, set "extracted_data" to null.
            """
        else:
            print("WARNING: GEMINI_API_KEY not found. AI features will not work.")
            self.client = None

    async def generate_chat_response(self, history: list, user_message: str, profile_context: dict = None) -> dict:
        """
        Generates a response from the LLM based on chat history and new user message.
        Returns a dict: {"message": str, "extracted_data": dict | None}
        """
        if not self.client:
            return {"message": "AI Service is not configured. Please check API Key.", "extracted_data": None}

        try:
            # Prepare instructions with context
            instructions = self.chat_system_instruction
            if profile_context:
                instructions += f"\n\nCURRENT KNOWN PROFILE DATA (Do not ask for these if present):\n{json.dumps(profile_context, indent=2)}"

            # Create a chat session
            chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                    response_mime_type="application/json",
                    response_schema=ChatAndExtractResponse
                ),
                history=history 
            )
            
            response = chat.send_message(user_message)
            
            # DEBUG PRINT
            print(f"RAW AI RESPONSE: {response.text}")

            try:
                # Parse JSON
                loaded_json = json.loads(response.text)
                return loaded_json
            except json.JSONDecodeError:
                # Fallback if model fails to output JSON (rare with schema enforcement)
                print(f"Failed to parse JSON response: {response.text}")
                return {"message": response.text, "extracted_data": None}
                
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {"message": f"Sorry, I encountered an error: {str(e)}", "extracted_data": None}

    async def generate_resume_content(self, user_data: dict) -> str:
        """
        Generates professional resume content.
        """
        if not self.client:
            return "AI Service is not configured."
        
        prompt = f"""
        You are an expert Resume Writer. 
        Based on the following user data, satisfy the requirements below.
        
        User Data: {user_data}
        
        Task: 
        1. Write a compelling professional summary (3-4 lines).
        2. Enhance the descriptions of their projects and work experience with action verbs and impact metrics.
        3. Suggest 5 key skills if they are missing.
        
        Return the response in valid JSON format with keys: 'summary', 'enhanced_experience', 'skills_suggestions'.
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating content: {str(e)}"

    async def score_resume(self, resume_text: str) -> str:
        """
        Scores a resume (0-100) and provides improvement feedback.
        """
        if not self.client:
            return "AI Service is not configured."
            
        prompt = f"""
        Act as a hiring manager. Review the following resume text and provide a score out of 100.
        
        Resume Text:
        {resume_text}
        
        Output valid JSON:
        {{
            "score": <number>,
            "strengths": [<list of strings>],
            "weaknesses": [<list of strings>],
            "improvements": [<list of actionable advice>]
        }}
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error scoring resume: {str(e)}"
    
    async def generate_content(self, prompt: str) -> str:
        """
        Generic content generation method for various use cases (e.g., cover letters).
        """
        if not self.client:
            return "AI Service is not configured."
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating content: {str(e)}"

# Singleton instance
ai_service = AIService()
