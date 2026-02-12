

from xhtml2pdf import pisa
from fastapi.templating import Jinja2Templates
from app.schemas.schemas import ResumeData
import os

templates = Jinja2Templates(directory="app/templates")

class ResumeGeneratorService:
    def __init__(self):
        pass
        
    def generate_pdf(self, data: ResumeData, template_name: str = "professional") -> str:
        """
        Generates a PDF resume from data and returns the file path.
        """
        # 1. Render HTML
        # Map template_name to filename
        # Ensure secure path
        safe_name = os.path.basename(template_name) 
        template_path = f"resume_templates/{safe_name}.html"
        
        try:
            template = templates.get_template(template_path)
        except:
            # Fallback
            print(f"Template {template_name} not found, defaulting...")
            template = templates.get_template("resume_templates/professional.html")
            
        # Prepare Context for Jinja (Adapter)
        context = data.dict()
        
        # 1. Map full_name -> name
        context['name'] = context.get('full_name', '')
        
        # 2. Skills - keep as list (template expects list, not dict)
        raw_skills = context.get('skills', [])
        if isinstance(raw_skills, list):
            context['skills'] = raw_skills
        else:
            # If it's already a dict or other format, try to extract values
            context['skills'] = list(raw_skills.values()) if isinstance(raw_skills, dict) else []
        
        # 3. Languages - parse from JSON string if needed
        import json
        raw_languages = context.get('languages', [])
        if isinstance(raw_languages, str):
            try:
                context['languages'] = json.loads(raw_languages)
            except:
                context['languages'] = []
        elif isinstance(raw_languages, list):
            context['languages'] = raw_languages
        else:
            context['languages'] = []
        
        # 4. Hobbies - parse from JSON string if needed
        raw_hobbies = context.get('hobbies', [])
        if isinstance(raw_hobbies, str):
            try:
                context['hobbies'] = json.loads(raw_hobbies)
            except:
                context['hobbies'] = []
        elif isinstance(raw_hobbies, list):
            context['hobbies'] = raw_hobbies
        else:
            context['hobbies'] = []
             
        # Render with unpacked context
        html_content = template.render(**context)
        
        # 2. Output Path
        output_dir = "app/static/generated_resumes"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"resume_{data.full_name.replace(' ', '_')}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        # 3. Convert to PDF using xhtml2pdf
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,                # the HTML to convert
                dest=pdf_file                # file handle to recieve result
            )

        if pisa_status.err:
            raise Exception(f"PDF generation failed: {pisa_status.err}")
            
        return output_path

resume_generator = ResumeGeneratorService()
