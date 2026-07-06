import logging
from app.database import get_connection
from app.skill_intelligence import get_predefined_profiles

logger = logging.getLogger(__name__)

def explain_skill_forecast(role: str, skill: str, forecast_result: dict) -> dict:
    """
    Generates a natural language and structured feature-level explanation for a skill demand forecast.
    """
    predicted_growth = forecast_result.get("predicted_growth", 0.0)
    predicted_demand = forecast_result.get("predicted_demand_index", 0.0)
    confidence = forecast_result.get("confidence_score", 0.0)
    
    # Analyze trend direction
    if predicted_growth > 15.0:
        trend = "rapidly growing"
    elif predicted_growth > 5.0:
        trend = "growing"
    elif predicted_growth < -5.0:
        trend = "declining"
    else:
        trend = "stable"
        
    text_explanation = (
        f"The demand for '{skill}' in the '{role}' role is predicted to be {trend} "
        f"with a projected growth rate of {predicted_growth}% and a projected demand index "
        f"of {predicted_demand} by the year {forecast_result.get('year', 2028)}."
    )
    if confidence < 0.5:
        text_explanation += " Note: This forecast is based on fallback estimation due to sparse historical records."
        
    return {
        "trend_direction": trend,
        "average_annual_growth": predicted_growth,
        "text_explanation": text_explanation,
        "confidence_score": confidence
    }

def explain_career_match(user_skills: list[str], target_role: str, gap_result: dict) -> dict:
    """
    Generates feature contributions (importance weights) for matched skills and a natural language explanation.
    """
    match_pct = gap_result.get("match_percentage", 0)
    missing_skills = gap_result.get("missing_skills", [])
    
    # Query database to get demand index of required skills to determine contribution weights
    conn = get_connection()
    demand_map = {}
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT skill, demand_index FROM job_market_trends WHERE role = ? AND year = 2026",
            (target_role,)
        )
        rows = cursor.fetchall()
        demand_map = {row["skill"].lower(): row["demand_index"] for row in rows}
    except Exception as e:
        logger.error(f"Error querying market trends for XAI: {e}")
    finally:
        conn.close()
        
    user_skills_set = {s.strip().lower() for s in user_skills if s.strip()}
    profiles = get_predefined_profiles()
    profile_skills = profiles.get(target_role, [])
    
    feature_contributions = []
    total_importance = sum(demand_map.get(s.lower(), 1.0) for s in profile_skills)
    
    for skill in profile_skills:
        weight = demand_map.get(skill.lower(), 1.0)
        norm_weight = round(weight / total_importance, 2) if total_importance > 0 else 0.0
        status = "matched" if skill.lower() in user_skills_set else "missing"
        
        feature_contributions.append({
            "skill": skill,
            "importance_weight": norm_weight,
            "status": status,
            "impact_direction": "positive" if status == "matched" else "negative"
        })
        
    matched_skills = [f["skill"] for f in feature_contributions if f["status"] == "matched"]
    
    text_explanation = (
        f"Your career readiness score for '{target_role}' is {match_pct}%. "
        f"This is driven positively by matched skills ({', '.join(matched_skills) if matched_skills else 'none'}) "
        f"which align with key market requirements. "
    )
    if missing_skills:
        text_explanation += f"To improve your readiness, focusing on {', '.join(missing_skills)} will yield the highest impact."
    else:
        text_explanation += "You possess all required core skills for this profile."
        
    return {
        "match_percentage": match_pct,
        "feature_contributions": feature_contributions,
        "text_explanation": text_explanation
    }
