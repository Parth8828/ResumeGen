

from google import genai
from google.genai import types
from app.core.config import get_settings

settings = get_settings()

from pydantic import BaseModel, Field
from typing import List, Optional
import json
import random

# --- Structured Output Models ---
class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
# ... (Leaving models alone, targeting __init__)

# I need to target the class AIService definition.
# Let's skip to line 63-91 in original file.
# Since I can't use "..." in replacement content for lines I want to keep unless I include them.
# I will just replacing the Imports separately or merged.
# Let's replace the top imports first.


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
        self.api_keys = settings.api_keys
        self.model_name = settings.GEMINI_MODEL_NAME
        
        if not self.api_keys:
            print("WARNING: GEMINI_API_KEYs not found. AI features will not work.")
            self.client = None # Legacy support
        else:
            # Initialize with first key
            self.client = genai.Client(api_key=self.api_keys[0])

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

    async def _execute_with_retry(self, operation_coroutine_func):
        """
        Executes a function with automatic API key rotation and retries.
        """
        if not self.api_keys:
            return {"error": "No API Keys configured"}

        # Shuffle keys (copy to avoid side effects)
        keys = list(self.api_keys)
        random.shuffle(keys)

        last_error = None
        
        for key in keys:
            try:
                # Create ephemeral client for this attempt
                client = genai.Client(api_key=key)
                return await operation_coroutine_func(client)
            except Exception as e:
                # Catch 429 (Resource Exhausted) or 503 (Overloaded)
                print(f"Key {key[:5]}... failed with error: {e}. Rotating...")
                last_error = e
                continue
        
        # If all failed
        print("All API keys failed.")
        raise last_error


    async def generate_chat_response(self, history: list, user_message: str, profile_context: dict = None) -> dict:
        """
        Generates a response from the LLM based on chat history and new user message.
        Returns a dict: {"message": str, "extracted_data": dict | None}
        """
        
        async def _attempt_chat(client):
            # Prepare instructions with context
            instructions = self.chat_system_instruction
            if profile_context:
                instructions += f"\n\nCURRENT KNOWN PROFILE DATA (Do not ask for these if present):\n{json.dumps(profile_context, indent=2)}"

            # Create a chat session using Async client
            chat = client.aio.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                    response_mime_type="application/json",
                    response_schema=ChatAndExtractResponse
                ),
                history=history 
            )
            
            response = await chat.send_message(user_message)
            
            # DEBUG PRINT
            print(f"RAW AI RESPONSE ({client._api_key[:5]}...): {response.text}") # Verify rotation

            try:
                # Parse JSON
                loaded_json = json.loads(response.text)
                return loaded_json
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response: {response.text}")
                return {"message": response.text, "extracted_data": None}

        try:
            return await self._execute_with_retry(_attempt_chat)
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {"message": f"Sorry, I encountered an error: {str(e)}", "extracted_data": None}


    async def generate_resume_content(self, user_data: dict) -> str:
        """
        Generates professional resume content.
        """
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
        
        async def _attempt_gen(client):
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text

        try:
            return await self._execute_with_retry(_attempt_gen)
        except Exception as e:
            return f"Error generating content: {str(e)}"


    async def analyze_and_enhance(self, profile_data: dict) -> dict:
        """
        Analyzes the resume data, provides a score (0-100), and generates an enhanced version.
        Returns JSON with score, analysis, and enhanced_profile.
        """
        prompt = f"""
        Act as an expert Resume Writer and Hiring Manager.
        Analyze the following candidate profile data.

        Task 1: Score & Analyze
        - Assign a "Score" (0-100) based on impact, clarity, and completeness.
        - List 3 key "Strengths".
        - List 3 key "Weaknesses" or areas for improvement.

        Task 2: Enhance Content
        - Rewrite the 'summary' to be more professional and impactful.
        - Rewrite 'experience' and 'projects' descriptions:
            - Use strong action verbs (e.g., "Spearheaded", "Optimized", "Developed").
            - Fix grammar and flow.
            - Do NOT invent new facts. Polish existing info.
        
        Input Data:
        {json.dumps(profile_data, indent=2)}

        Output a Valid JSON Object with this EXACT structure:
        {{
            "score": <int 0-100>,
            "strengths": ["string", "string"],
            "weaknesses": ["string", "string"],
            "suggestions": ["string", "string"],
            "enhanced_profile": <The COMPLETE profile_data object but with polished/rewritten text fields>
        }}
        """

        async def _attempt_analyze(client):
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)

        try:
            return await self._execute_with_retry(_attempt_analyze)
        except Exception as e:
            print(f"Error analyzing resume: {e}")
            return {"error": str(e)}


    async def extract_profile_from_text(self, text: str) -> dict:
        """
        Extracts structured profile data (JSON) from raw resume text using the LLM.
        """
        prompt = f"""
        Act as a Resume Parser. Extract structured data from the following Resume Text.
        
        Resume Text:
        {text}
        
        Output valid JSON exactly matching this schema:
        {{
            "personal_info": {{
                "full_name": "string", "email": "string", "phone": "string",
                "location": "string", "linkedin": "string", "github": "string", "portfolio": "string"
            }},
            "summary": "string",
            "experience": [
                {{ "title": "string", "company": "string", "start_date": "string", "end_date": "string", "description": "string", "achievements": ["string"] }}
            ],
            "education": [
                {{ "degree": "string", "institution": "string", "graduation_date": "string", "gpa": "string" }}
            ],
            "skills": [
                {{ "category": "string", "skills": ["string"] }}
            ],
            "projects": [
                {{ "name": "string", "description": "string", "date": "string", "technologies": ["string"] }}
            ]
        }}
        If a field is missing, omit it or use empty strings/lists.
        """

        async def _attempt_extract(client):
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)

        try:
            return await self._execute_with_retry(_attempt_extract)
        except Exception as e:
            print(f"Error extracting profile: {e}")
            return {}


    async def score_resume(self, resume_text: str) -> str:
        """
        Scores a resume (0-100) and provides improvement feedback.
        Return: JSON string.
        """
        prompt = f"""
        Act as a strict Resume Scorer. Analyze the following resume text.
        
        Resume Text:
        {resume_text}
        
        Output a valid JSON object with:
        - "score": (0-100 integer)
        - "strengths": [list of strings]
        - "weaknesses": [list of strings]
        - "improvements": [list of actionable advice strings]
        """
        
        async def _attempt_score(client):
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return response.text

        try:
            return await self._execute_with_retry(_attempt_score)
        except Exception as e:
            print(f"Scoring error: {e}")
            return '{"score": 0, "strengths": [], "weaknesses": ["Error analyzing resume"], "improvements": []}'


    async def generate_content(self, prompt: str) -> str:
        """
        Generic content generation method for various use cases (e.g., cover letters).
        """
        async def _attempt_gen_generic(client):
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text

        try:
            return await self._execute_with_retry(_attempt_gen_generic)
        except Exception as e:
            return f"Error generating content: {str(e)}"


# Singleton instance
ai_service = AIService()
