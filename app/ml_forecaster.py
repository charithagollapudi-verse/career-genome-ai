import numpy as np
from sklearn.linear_model import LinearRegression
from app.database import get_connection

def forecast_skill_demand(role: str, skill: str, target_year: int) -> dict:
    """
    Fits a LinearRegression model to project the demand index of a skill up to target_year.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, demand_index, projected_growth 
        FROM job_market_trends 
        WHERE role = ? AND skill = ?
        ORDER BY year ASC
    """, (role, skill))
    
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) < 2:
        # Fallback linear growth
        return {
            "role": role,
            "skill": skill,
            "year": target_year,
            "predicted_demand_index": 0.85,
            "predicted_growth": 10.0,
            "confidence_score": 0.40,
            "note": "Fallback projection due to insufficient historical data"
        }
        
    X = np.array([[r["year"]] for r in rows])
    y_demand = np.array([r["demand_index"] for r in rows])
    y_growth = np.array([r["projected_growth"] for r in rows])
    
    # Train Linear Regression models
    reg_demand = LinearRegression().fit(X, y_demand)
    reg_growth = LinearRegression().fit(X, y_growth)
    
    pred_demand = reg_demand.predict(np.array([[target_year]]))[0]
    pred_growth = reg_growth.predict(np.array([[target_year]]))[0]
    
    # Clip demand index between 0.0 and 1.0
    pred_demand = float(np.clip(pred_demand, 0.0, 1.0))
    pred_growth = float(pred_growth)
    
    confidence = 0.70
    if len(rows) >= 3:
        confidence = 0.95

    return {
        "role": role,
        "skill": skill,
        "year": target_year,
        "predicted_demand_index": round(pred_demand, 3),
        "predicted_growth": round(pred_growth, 2),
        "confidence_score": confidence,
        "note": "Successfully projected using Linear Regression model"
    }

def simulate_career_trajectory(user_skills: list, target_role: str) -> dict:
    """
    Simulates path trajectory match probability based on overlapping skills and growth.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT skill 
        FROM job_market_trends 
        WHERE role = ?
    """, (target_role,))
    
    required_skills = [row["skill"] for row in cursor.fetchall()]
    conn.close()
    
    if not required_skills:
        return {
            "target_role": target_role,
            "current_match_probability": 0.0,
            "missing_skills": [],
            "trajectory": [],
            "confidence_score": 0.00
        }
        
    user_skills_set = set([s.strip().lower() for s in user_skills])
    required_skills_set = set([s.strip().lower() for s in required_skills])
    
    overlap = user_skills_set.intersection(required_skills_set)
    missing = list(required_skills_set - user_skills_set)
    
    # Simple match score
    match_prob = len(overlap) / len(required_skills_set)
    
    # Simulate year-over-year progress assuming learning velocity
    trajectory = []
    current_prob = match_prob
    for i in range(1, 4):
        # Assume user learns 1.5 skills per year
        learned_count = min(len(missing), int(i * 1.5))
        simulated_prob = (len(overlap) + learned_count) / len(required_skills_set)
        simulated_prob = min(simulated_prob, 1.0)
        trajectory.append({
            "year": 2026 + i,
            "projected_match_probability": round(simulated_prob, 2)
        })
        
    # Map back original skill names for missing
    missing_original = [s for s in required_skills if s.lower() in missing]
    
    conf = 0.80
    if user_skills:
        match_ratio = len(overlap) / max(1, len(user_skills))
        conf = round(0.70 + 0.25 * match_ratio, 2)
    conf = min(conf, 1.0)
    
    return {
        "target_role": target_role,
        "current_match_probability": round(match_prob, 2),
        "missing_skills": missing_original,
        "trajectory": trajectory,
        "confidence_score": conf
    }
