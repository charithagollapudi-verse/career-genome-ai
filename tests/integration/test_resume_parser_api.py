from unittest.mock import patch
from fastapi.testclient import TestClient
from app.agent_runtime_app import fastapi_app
from app.resume_parser import ResumeData

client = TestClient(fastapi_app)

@patch("app.agent_runtime_app.parse_resume_text")
def test_parse_resume_endpoint_success(mock_parse):
    mock_data = ResumeData(
        skills=["Go", "Kubernetes"],
        education=[
            {
                "institution": "Stanford University",
                "degree": "MS",
                "field_of_study": "CS",
                "start_year": "2020",
                "end_year": "2022"
            }
        ],
        experience=[
            {
                "company": "Google",
                "title": "Staff Engineer",
                "description": "Led team.",
                "start_date": "2022",
                "end_date": "Present"
            }
        ],
        certifications=["CKA"],
        projects=[
            {
                "name": "Kubebuilder",
                "description": "Operator SDK tool."
            }
        ]
    )
    mock_parse.return_value = mock_data
    
    payload = {"resume_text": "Staff Engineer Google CKA Stanford"}
    response = client.post("/parse-resume", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "Go" in data["skills"]
    assert data["education"][0]["institution"] == "Stanford University"
    assert data["experience"][0]["company"] == "Google"
    assert "CKA" in data["certifications"]
    assert data["projects"][0]["name"] == "Kubebuilder"
    
    mock_parse.assert_called_once_with("Staff Engineer Google CKA Stanford")

def test_parse_resume_endpoint_empty_text():
    response = client.post("/parse-resume", json={"resume_text": ""})
    assert response.status_code == 400
    assert "resume_text cannot be empty" in response.json()["detail"]

def test_parse_resume_endpoint_whitespace_text():
    response = client.post("/parse-resume", json={"resume_text": "   "})
    assert response.status_code == 400
    assert "resume_text cannot be empty" in response.json()["detail"]
