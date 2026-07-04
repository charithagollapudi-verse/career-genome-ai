from unittest.mock import patch
from fastapi.testclient import TestClient
from app.agent_runtime_app import fastapi_app
from app.agent import CareerDNAOutput, SkillGapOutput, RecommendationOutput

client = TestClient(fastapi_app)

@patch("app.agent_runtime_app.generate_career_dna")
def test_analyze_dna_endpoint_success(mock_generate):
    mock_dna = CareerDNAOutput(
        archetype="Technologist",
        values=["Innovation"],
        interests=["Data Science"]
    )
    mock_generate.return_value = mock_dna
    
    response = client.post("/analyze-dna", json={"profile_text": "Sample details"})
    assert response.status_code == 200
    data = response.json()
    assert data["archetype"] == "Technologist"
    assert "Innovation" in data["values"]
    mock_generate.assert_called_once_with("Sample details")

def test_analyze_dna_endpoint_empty_input():
    response = client.post("/analyze-dna", json={"profile_text": "   "})
    assert response.status_code == 400
    assert "profile_text cannot be empty" in response.json()["detail"]

@patch("app.agent_runtime_app.analyze_skill_gap")
def test_analyze_gap_endpoint_success(mock_analyze):
    mock_gap = SkillGapOutput(
        match_percentage=60,
        missing_skills=["Kubernetes", "DevOps"],
        gap_summary="Missing standard operations skills."
    )
    mock_analyze.return_value = mock_gap
    
    payload = {
        "user_skills": ["Python", "Docker"],
        "target_role": "Cloud Engineer"
    }
    response = client.post("/analyze-gap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["match_percentage"] == 60
    assert "Kubernetes" in data["missing_skills"]
    assert data["gap_summary"] == "Missing standard operations skills."
    mock_analyze.assert_called_once_with(["Python", "Docker"], "Cloud Engineer")

@patch("app.agent_runtime_app.generate_recommendations")
def test_generate_recommendations_endpoint_success(mock_recommend):
    mock_recs = RecommendationOutput(
        courses=["DevOps Tutorial"],
        projects=["Build AWS infrastructure"],
        next_roles=["Junior DevOps Engineer"]
    )
    mock_recommend.return_value = mock_recs
    
    payload = {
        "missing_skills": ["Kubernetes", "DevOps"],
        "target_role": "Cloud Engineer"
    }
    response = client.post("/generate-recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "DevOps Tutorial" in data["courses"]
    assert "Build AWS infrastructure" in data["projects"]
    assert "Junior DevOps Engineer" in data["next_roles"]
    mock_recommend.assert_called_once_with(["Kubernetes", "DevOps"], "Cloud Engineer")
