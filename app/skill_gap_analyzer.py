import logging
from google import genai
from google.genai import types
from app.config import config
from app.agent import SkillGapOutput
from app.skill_intelligence import get_predefined_profiles

logger = logging.getLogger(__name__)

def analyze_skill_gap(user_skills: list[str], target_role: str) -> SkillGapOutput:
    """
    Compares user skills against target role required skills and generates a qualitative gap analysis.
    """
    if not target_role or not target_role.strip():
        raise ValueError("Target role cannot be empty.")
        
    profiles = get_predefined_profiles()
    if target_role not in profiles:
        raise ValueError(f"Target role '{target_role}' is not a predefined profile. Available profiles: {list(profiles.keys())}")
        
    profile_skills = profiles[target_role]
    user_skills_set = {s.strip().lower() for s in user_skills if s.strip()}
    
    matched_skills = [s for s in profile_skills if s.strip().lower() in user_skills_set]
    missing_skills = [s for s in profile_skills if s.strip().lower() not in user_skills_set]
    
    match_percentage = int((len(matched_skills) / len(profile_skills)) * 100) if profile_skills else 0
    
    # Use Gemini to generate a qualitative gap summary
    client = genai.Client()
    prompt = f"""
    You are an expert technical recruiter and talent advisor.
    Provide a concise, qualitative gap analysis summary comparing the user's matched skills against the missing skills required for the role of '{target_role}'.
    Explain the impact of the missing skills and what the user should focus on next.
    
    Target Role: {target_role}
    Required Profile Skills: {', '.join(profile_skills)}
    User Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
    User Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}
    Current Match Score: {match_percentage}%
    """
    
    try:
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        gap_summary = response.text.strip()
    except Exception as e:
        logger.error(f"Error generating gap summary using Gemini: {e}")
        gap_summary = f"Currently matching {len(matched_skills)} out of {len(profile_skills)} required skills. Missing: {', '.join(missing_skills)}."
        
    from app.ml_forecaster import simulate_career_trajectory
    from app.xai import explain_career_match
    
    try:
        traj = simulate_career_trajectory(user_skills, target_role)
        confidence = traj.get("confidence_score", 0.80)
    except Exception:
        confidence = 0.80

    explanation = explain_career_match(user_skills, target_role, {
        "match_percentage": match_percentage,
        "missing_skills": missing_skills
    })

    return SkillGapOutput(
        match_percentage=match_percentage,
        missing_skills=missing_skills,
        gap_summary=gap_summary,
        confidence_score=confidence,
        explanation=explanation
    )
