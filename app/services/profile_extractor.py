from typing import Dict, Any, Optional
import json
from google import genai
from google.genai import types
from app.core.config import get_settings

settings = get_settings()

import random

class ProfileExtractor:
    """Service to extract structured profile data from chat conversations"""
    
    def __init__(self):
        self.model_id = 'gemini-2.0-flash-exp' # or settings.GEMINI_MODEL_NAME
        self.api_keys = settings.api_keys
        if self.api_keys:
             # Pick random key for now, or just first one
             self.client = genai.Client(api_key=random.choice(self.api_keys))
        else:
             print("WARNING: No API Keys found for ProfileExtractor")
             self.client = None
    
    def extract_from_message(self, message: str, existing_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract profile information from a chat message.
        Returns only the NEW information found, not the entire profile.
        """
        
        prompt = f"""You are a profile data extraction assistant. Analyze the following user message and extract ANY profile-related information.

IMPORTANT RULES:
1. Extract ONLY information that is explicitly stated in the message
2. Return ONLY the NEW information found, not existing data
3. Use proper formatting (e.g., "Jan 2020" for dates, not "January 2020")
4. For skills, categorize them appropriately
5. If no profile information is found, return an empty object {{}}

USER MESSAGE:
"{message}"

EXISTING PROFILE DATA (for context, DO NOT repeat this):
{json.dumps(existing_profile, indent=2)}

Extract and return a JSON object with ANY of these fields that are mentioned:
{{
  "personal_info": {{
    "full_name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string",
    "github": "string",
    "portfolio": "string"
  }},
  "summary": "string - professional summary if mentioned",
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "location": "string (optional)",
      "start_date": "string (e.g., 'Jan 2020')",
      "end_date": "string (e.g., 'Present' or 'Dec 2022')",
      "is_current": boolean,
      "description": "string (optional)",
      "achievements": ["string", "string"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "location": "string (optional)",
      "graduation_date": "string (e.g., '2020' or 'May 2020')",
      "gpa": "string (optional)"
    }}
  ],
  "skills": [
    {{
      "category": "string (e.g., 'Programming Languages', 'Frameworks')",
      "skills": ["string", "string"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "description": "string",
      "date": "string (optional)",
      "url": "string (optional)",
      "technologies": ["string", "string"]
    }}
  ],
  "languages": ["string", "string"],
  "hobbies": ["string", "string"]
}}

EXAMPLES:
User: "My name is John Doe"
Response: {{"personal_info": {{"full_name": "John Doe"}}}}

User: "I worked at Google as a Software Engineer for 2 years from 2020 to 2022"
Response: {{"experience": [{{"title": "Software Engineer", "company": "Google", "start_date": "Jan 2020", "end_date": "Dec 2022", "is_current": false}}]}}

User: "I know Python, JavaScript, and React"
Response: {{"skills": [{{"category": "Programming Languages", "skills": ["Python", "JavaScript"]}}, {{"category": "Frameworks", "skills": ["React"]}}]}}

User: "I graduated from MIT in 2020 with a degree in Computer Science"
Response: {{"education": [{{"degree": "Bachelor of Science in Computer Science", "institution": "MIT", "graduation_date": "2020"}}]}}

Return ONLY valid JSON, no explanations."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            extracted_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if extracted_text.startswith('```'):
                extracted_text = extracted_text.split('```')[1]
                if extracted_text.startswith('json'):
                    extracted_text = extracted_text[4:]
                extracted_text = extracted_text.strip()
            
            # Parse JSON
            extracted_data = json.loads(extracted_text)
            
            # Return None if empty
            if not extracted_data or extracted_data == {}:
                return None
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {extracted_text}")
            return None
        except Exception as e:
            print(f"Extraction error: {e}")
            return None
    
    def merge_profile_data(self, existing: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently merge new extracted data with existing profile.
        Rules:
        - Personal info: Update if new value provided
        - Summary: Update if new value provided
        - Lists (experience, education, skills, projects): Append new items
        """
        merged = existing.copy()
        
        # Merge personal info
        if 'personal_info' in new_data:
            if 'personal_info' not in merged:
                merged['personal_info'] = {}
            for key, value in new_data['personal_info'].items():
                if value:  # Only update if value is not empty
                    merged['personal_info'][key] = value
        
        # Merge summary
        if 'summary' in new_data and new_data['summary']:
            merged['summary'] = new_data['summary']
        
        # Merge lists - append new items
        for list_field in ['experience', 'education', 'skills', 'projects', 'languages', 'hobbies']:
            if list_field in new_data and new_data[list_field]:
                if list_field not in merged:
                    merged[list_field] = []
                merged[list_field].extend(new_data[list_field])
        
        return merged
