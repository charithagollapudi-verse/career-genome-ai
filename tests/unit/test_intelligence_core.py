import pytest
from unittest.mock import MagicMock, patch
from app.career_dna import generate_career_dna
from app.skill_gap_analyzer import analyze_skill_gap
from app.recommendation_engine import generate_recommendations
from app.agent import CareerDNAOutput, SkillGapOutput, RecommendationOutput

# -------------------------------------------------------------
# 1. Career DNA Tests
# -------------------------------------------------------------

def test_generate_career_dna_empty_input():
    with pytest.raises(ValueError) as excinfo:
        generate_career_dna(" ")
    assert "cannot be empty" in str(excinfo.value)

@patch("app.career_dna.genai.Client")
def test_generate_career_dna_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = '{"archetype": "Technologist", "values": ["Innovation", "Impact"], "interests": ["AI", "Cloud"]}'
    mock_client.models.generate_content.return_value = mock_response
    
    result = generate_career_dna("Professional background in software engineering and cloud.")
    assert isinstance(result, CareerDNAOutput)
    assert result.archetype == "Technologist"
    assert "Innovation" in result.values
    assert "AI" in result.interests
    mock_client.models.generate_content.assert_called_once()

# -------------------------------------------------------------
# 2. Skill Gap Tests
# -------------------------------------------------------------

def test_analyze_skill_gap_empty_role():
    with pytest.raises(ValueError) as excinfo:
        analyze_skill_gap(["Python"], "")
    assert "cannot be empty" in str(excinfo.value)

def test_analyze_skill_gap_invalid_role():
    with pytest.raises(ValueError) as excinfo:
        analyze_skill_gap(["Python"], "Quantum AI Space Wizard")
    assert "is not a predefined profile" in str(excinfo.value)

@patch("app.skill_gap_analyzer.genai.Client")
def test_analyze_skill_gap_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = "Mocked qualitative summary of skills gap."
    mock_client.models.generate_content.return_value = mock_response
    
    # Predefined 'Machine Learning Engineer' has Python, Deep Learning, MLOps, Docker, Model Deployment
    user_skills = ["Python", "Docker"]
    result = analyze_skill_gap(user_skills, "Machine Learning Engineer")
    
    assert isinstance(result, SkillGapOutput)
    assert result.match_percentage == 40  # 2 matched / 5 total * 100
    assert "Deep Learning" in result.missing_skills
    assert "MLOps" in result.missing_skills
    assert result.gap_summary == "Mocked qualitative summary of skills gap."
    mock_client.models.generate_content.assert_called_once()

# -------------------------------------------------------------
# 3. Recommendation Engine Tests
# -------------------------------------------------------------

def test_generate_recommendations_empty_role():
    with pytest.raises(ValueError) as excinfo:
        generate_recommendations(["Deep Learning"], "")
    assert "cannot be empty" in str(excinfo.value)

def test_generate_recommendations_no_missing():
    # If no missing skills
    result = generate_recommendations([], "Machine Learning Engineer")
    assert isinstance(result, RecommendationOutput)
    assert len(result.courses) > 0
    assert len(result.projects) > 0
    assert "Machine Learning Engineer" in result.next_roles

@patch("app.recommendation_engine.genai.Client")
def test_generate_recommendations_success(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = '{"courses": ["Advanced ML Course"], "projects": ["Build standard deployment pipeline"], "next_roles": ["Junior ML Engineer"]}'
    mock_client.models.generate_content.return_value = mock_response
    
    result = generate_recommendations(["Model Deployment", "MLOps"], "Machine Learning Engineer")
    assert isinstance(result, RecommendationOutput)
    assert "Advanced ML Course" in result.courses
    assert "Build standard deployment pipeline" in result.projects
    assert "Junior ML Engineer" in result.next_roles
    mock_client.models.generate_content.assert_called_once()
