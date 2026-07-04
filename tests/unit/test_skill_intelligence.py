import pytest
from app.skill_intelligence import get_predefined_profiles, analyze_user_skills

def test_get_predefined_profiles():
    profiles = get_predefined_profiles()
    assert isinstance(profiles, dict)
    assert "Machine Learning Engineer" in profiles
    assert "Cloud Engineer" in profiles
    assert "Python" in profiles["Machine Learning Engineer"]
    assert "Kubernetes" in profiles["Cloud Engineer"]

def test_analyze_user_skills_with_valid_role():
    # User has some skills for Machine Learning Engineer
    user_skills = ["Python", "Docker", "UnrelatedSkill"]
    
    result = analyze_user_skills(user_skills, "Machine Learning Engineer")
    
    assert result["role"] == "Machine Learning Engineer"
    # Machine Learning Engineer profile has 5 skills: Python, Deep Learning, MLOps, Docker, Model Deployment
    # Matched (2): Python, Docker. Missing (3): Deep Learning, MLOps, Model Deployment.
    assert "Python" in result["matched_skills"]
    assert "Docker" in result["matched_skills"]
    assert "Deep Learning" in result["missing_skills"]
    
    assert result["career_readiness"] == 40.0 # 2/5 * 100
    assert result["domain_affinity"] == 66.67 # 2/3 * 100
    assert result["skill_strength"] > 0.0
    assert result["learning_velocity"] > 1.5

def test_analyze_user_skills_all_matched():
    user_skills = ["Python", "Deep Learning", "MLOps", "Docker", "Model Deployment"]
    result = analyze_user_skills(user_skills, "Machine Learning Engineer")
    assert result["career_readiness"] == 100.0
    assert result["domain_affinity"] == 100.0
    assert result["skill_strength"] == 100.0
    assert len(result["missing_skills"]) == 0

def test_analyze_user_skills_no_matched():
    user_skills = ["UnrelatedSkill"]
    result = analyze_user_skills(user_skills, "Machine Learning Engineer")
    assert result["career_readiness"] == 0.0
    assert result["domain_affinity"] == 0.0
    assert result["skill_strength"] == 0.0
    assert len(result["matched_skills"]) == 0

def test_analyze_user_skills_invalid_role():
    with pytest.raises(ValueError) as excinfo:
        analyze_user_skills(["Python"], "Senior Principal Software Wizard")
    assert "Wizard" in str(excinfo.value)

def test_analyze_user_skills_all_roles():
    user_skills = ["Python", "Docker"]
    result = analyze_user_skills(user_skills)
    assert "profiles" in result
    assert len(result["profiles"]) >= 2
    # Verify profiles are sorted by career readiness descending
    readiness_scores = [r["career_readiness"] for r in result["profiles"]]
    assert readiness_scores == sorted(readiness_scores, reverse=True)
