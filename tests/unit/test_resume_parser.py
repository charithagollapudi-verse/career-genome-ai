import pytest
from unittest.mock import MagicMock, patch
from app.resume_parser import parse_resume_text, ResumeData

def test_parse_resume_text_empty_input():
    with pytest.raises(ValueError) as excinfo:
        parse_resume_text("  ")
    assert "cannot be empty" in str(excinfo.value)

@patch("app.resume_parser.genai.Client")
def test_parse_resume_text_successful(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    # Mock return JSON string from Gemini that matches ResumeData schema
    mock_response.text = """
    {
        "skills": ["Python", "Docker", "Machine Learning"],
        "education": [
            {
                "institution": "Stanford University",
                "degree": "Master of Science",
                "field_of_study": "Computer Science",
                "start_year": "2022",
                "end_year": "2024"
            }
        ],
        "experience": [
            {
                "company": "OpenAI",
                "title": "Research Engineer",
                "description": "Built scaling infrastructure.",
                "start_date": "2024-06",
                "end_date": "Present"
            }
        ],
        "certifications": ["AWS Certified Solutions Architect"],
        "projects": [
            {
                "name": "LocalGPT",
                "description": "Private document search."
            }
        ]
    }
    """
    mock_client.models.generate_content.return_value = mock_response
    
    result = parse_resume_text("John Doe Stanford OpenAI LocalGPT AWS")
    
    assert isinstance(result, ResumeData)
    assert "Python" in result.skills
    assert len(result.education) == 1
    assert result.education[0].institution == "Stanford University"
    assert result.experience[0].company == "OpenAI"
    assert result.certifications == ["AWS Certified Solutions Architect"]
    assert result.projects[0].name == "LocalGPT"
    
    # Assert generate_content was called
    mock_client.models.generate_content.assert_called_once()
