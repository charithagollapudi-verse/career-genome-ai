from fastapi.testclient import TestClient
from app.agent_runtime_app import fastapi_app

client = TestClient(fastapi_app)

def test_analyze_skills_api_with_role():
    payload = {
        "user_skills": ["Python", "Docker"],
        "target_role": "Machine Learning Engineer"
    }
    response = client.post("/analyze-skills", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Machine Learning Engineer"
    assert "career_readiness" in data
    assert "domain_affinity" in data
    assert "skill_strength" in data
    assert "learning_velocity" in data
    assert "matched_skills" in data
    assert "missing_skills" in data

def test_analyze_skills_api_all_roles():
    payload = {
        "user_skills": ["Python", "Docker"]
    }
    response = client.post("/analyze-skills", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) >= 2
    for profile in data["profiles"]:
        assert "role" in profile
        assert "career_readiness" in profile

def test_analyze_skills_api_empty_skills():
    payload = {
        "user_skills": []
    }
    response = client.post("/analyze-skills", json=payload)
    assert response.status_code == 400
    assert "user_skills list cannot be empty" in response.json()["detail"]

def test_analyze_skills_api_invalid_role():
    payload = {
        "user_skills": ["Python"],
        "target_role": "Senior Wizard Architect"
    }
    response = client.post("/analyze-skills", json=payload)
    assert response.status_code == 400
    assert "is not a predefined profile" in response.json()["detail"]
