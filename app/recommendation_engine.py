import logging
from google import genai
from google.genai import types
from app.config import config
from app.agent import RecommendationOutput

logger = logging.getLogger(__name__)

def generate_recommendations(missing_skills: list[str], target_role: str) -> RecommendationOutput:
    """
    Generates structured course, project, and career step suggestions based on missing skills and a target role,
    integrated with ML-based demand forecasts.
    """
    if not target_role or not target_role.strip():
        raise ValueError("Target role cannot be empty.")
        
    if not missing_skills:
        return RecommendationOutput(
            courses=["No missing skills found. Keep refining your advanced knowledge!"],
            projects=["You already have all the core skills. Build a custom project showcasing integration."],
            next_roles=[target_role]
        )
        
    # Integrate predictions: Forecast demand for each missing skill to prioritize them
    from app.ml_forecaster import forecast_skill_demand
    
    forecasts = []
    for skill in missing_skills:
        try:
            fc = forecast_skill_demand(target_role, skill, target_year=2028)
            forecasts.append((skill, fc))
        except Exception:
            forecasts.append((skill, {"predicted_demand_index": 0.5, "predicted_growth": 0.0}))
            
    # Sort by projected demand index descending
    forecasts.sort(key=lambda x: x[1].get("predicted_demand_index", 0.0), reverse=True)
    
    forecast_context_lines = []
    for skill, fc in forecasts:
        forecast_context_lines.append(
            f"- {skill}: Projected 2028 Demand Index is {fc.get('predicted_demand_index')}, "
            f"Projected Growth is {fc.get('predicted_growth')}% per year."
        )
    forecast_context = "\n".join(forecast_context_lines)
        
    client = genai.Client()
    prompt = f"""
    You are an expert career growth and learning path architect.
    We have run machine learning forecasting models on the job market trends for the role '{target_role}'.
    Here are the missing skills along with their projected growth metrics:
    {forecast_context}
    
    Please generate a structured Recommendation Output prioritizing the highest demand/growth skills first.
    For each course or project recommended, explain briefly why it is prioritized using the forecasting growth metrics provided above (e.g. 'Recommended due to high projected demand of 0.92').
    
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
