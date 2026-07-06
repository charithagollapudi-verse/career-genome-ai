import pytest
from app.ml_forecaster import forecast_skill_demand, simulate_career_trajectory
from app.xai import explain_skill_forecast, explain_career_match

def test_explain_skill_forecast():
    forecast_result = {
        "role": "Machine Learning Engineer",
        "skill": "MLOps",
        "year": 2028,
        "predicted_demand_index": 0.92,
        "predicted_growth": 32.0,
        "confidence_score": 0.95
    }
    
    explanation = explain_skill_forecast("Machine Learning Engineer", "MLOps", forecast_result)
    assert explanation["trend_direction"] == "rapidly growing"
    assert explanation["average_annual_growth"] == 32.0
    assert explanation["confidence_score"] == 0.95
    assert "rapidly growing" in explanation["text_explanation"]
    assert "MLOps" in explanation["text_explanation"]

def test_explain_career_match():
    gap_result = {
        "match_percentage": 40,
        "missing_skills": ["Deep Learning", "MLOps", "Model Deployment"]
    }
    
    explanation = explain_career_match(["Python", "Docker"], "Machine Learning Engineer", gap_result)
    assert explanation["match_percentage"] == 40
    assert len(explanation["feature_contributions"]) == 5 # Python, Deep Learning, MLOps, Docker, Model Deployment
    
    # Check that Python and Docker are status="matched"
    matched_skills = [f["skill"] for f in explanation["feature_contributions"] if f["status"] == "matched"]
    assert "Python" in matched_skills
    assert "Docker" in matched_skills
    assert "Deep Learning" not in matched_skills
    
    assert "readiness score" in explanation["text_explanation"]

def test_ml_forecaster_confidence_scores():
    # Test confidence score on demand forecast
    fc = forecast_skill_demand("Machine Learning Engineer", "Python", 2028)
    assert "confidence_score" in fc
    assert fc["confidence_score"] in [0.40, 0.70, 0.95]
    
    # Test confidence score on career trajectory simulation
    traj = simulate_career_trajectory(["Python", "Docker"], "Machine Learning Engineer")
    assert "confidence_score" in traj
    assert 0.0 <= traj["confidence_score"] <= 1.0
