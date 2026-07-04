import logging
from google import genai
from google.genai import types
from app.config import config
from app.agent import CareerDNAOutput

logger = logging.getLogger(__name__)

def generate_career_dna(profile_text: str) -> CareerDNAOutput:
    """
    Generates a Career DNA Profile based on user profile text, background, or interests.
    """
    if not profile_text or not profile_text.strip():
        raise ValueError("Profile text cannot be empty.")
        
    client = genai.Client()
    prompt = f"""
    You are an expert career counsellor and profile analyst.
    Analyze the following user profile text, professional background, or statement of interests,
    and generate a Career DNA Profile including:
    1. Career personality archetype (e.g. 'Technologist', 'Architect', 'Strategist', 'Innovator', 'Educator').
    2. Core professional value drivers (e.g. 'Autonomy', 'Innovation', 'Impact', 'Growth', 'Collaboration').
    3. Primary career interests.
    
    User Profile Details:
    {profile_text}
    """
    
    try:
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CareerDNAOutput,
                temperature=0.2,
            )
        )
        return CareerDNAOutput.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini API for career DNA generation: {e}")
        raise
