import logging
from google import genai
from google.genai import types
from app.config import config
from app.agent import RecommendationOutput

logger = logging.getLogger(__name__)

def generate_recommendations(missing_skills: list[str], target_role: str) -> RecommendationOutput:
    """
    Generates structured course, project, and career step suggestions based on missing skills and a target role.
    """
    if not target_role or not target_role.strip():
        raise ValueError("Target role cannot be empty.")
        
    if not missing_skills:
        return RecommendationOutput(
            courses=["No missing skills found. Keep refining your advanced knowledge!"],
            projects=["You already have all the core skills. Build a custom project showcasing integration."],
            next_roles=[target_role]
        )
        
    client = genai.Client()
    prompt = f"""
    You are an expert career growth and learning path architect.
    Generate a structured Recommendation Output for a professional aiming to transition to the role of '{target_role}',
    but currently missing these skills: {', '.join(missing_skills)}.
    
    Provide:
    1. A list of specific online courses, books, or training programs to learn these missing skills.
    2. Concrete, hands-on, practical projects they can build to demonstrate competence in these skills.
    3. Immediate stepping-stone roles or positions on the path to becoming a '{target_role}'.
    """
    
    try:
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationOutput,
                temperature=0.4,
            )
        )
        return RecommendationOutput.model_validate_json(response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini API for recommendations: {e}")
        raise
