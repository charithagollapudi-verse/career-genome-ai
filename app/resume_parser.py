import logging
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.config import config

logger = logging.getLogger(__name__)

class EducationItem(BaseModel):
    institution: str = Field(description="Name of the university, college, or school.")
    degree: str = Field(description="Degree, diploma, or certificate obtained.")
    field_of_study: str | None = Field(None, description="Major or field of study.")
    start_year: str | None = Field(None, description="Start year or start date.")
    end_year: str | None = Field(None, description="End year, graduation date, or 'Present'.")

class ExperienceItem(BaseModel):
    company: str = Field(description="Name of the company or organization.")
    title: str = Field(description="Job title or role.")
    description: str | None = Field(None, description="Summary of responsibilities and achievements.")
    start_date: str | None = Field(None, description="Start date (e.g. 'MM/YYYY' or 'Year').")
    end_date: str | None = Field(None, description="End date or 'Present'.")

class ProjectItem(BaseModel):
    name: str = Field(description="Name of the project.")
    description: str | None = Field(None, description="Description of what was built and technologies used.")

class ResumeData(BaseModel):
    skills: list[str] = Field(default_factory=list, description="List of technical and soft skills.")
    education: list[EducationItem] = Field(default_factory=list, description="Education history.")
    experience: list[ExperienceItem] = Field(default_factory=list, description="Work experience history.")
    certifications: list[str] = Field(default_factory=list, description="Certifications, licenses, or professional credentials.")
    projects: list[ProjectItem] = Field(default_factory=list, description="List of notable projects.")

def parse_resume_text(resume_text: str) -> ResumeData:
    """
    Initialises the GenAI Client and parses a raw resume text into structured ResumeData.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")
        
    client = genai.Client()
    prompt = f"""
    You are an expert resume parsing assistant.
    Analyze the following resume text and extract skills, education, experience, certifications, and projects.
    Ensure everything is mapped correctly to the output schema.
    
    Resume Text:
    {resume_text}
    """
    
    try:
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeData,
                temperature=0.1,
            )
        )
        return ResumeData.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini API for resume parsing: {e}")
        raise
