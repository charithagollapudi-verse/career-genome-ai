import pytest
from unittest.mock import MagicMock, patch

# Mock google.auth.default, google.cloud.logging, and project_id lookup before importing agent_runtime_app
import google.auth
import google.cloud.logging
from google.cloud.aiplatform.utils import resource_manager_utils

# Bypasses live Google Resource Manager gRPC API lookup
resource_manager_utils.get_project_id = lambda project: "dummy-project"

class DummyCredentials:
    def __init__(self):
        self.quota_project_id = "dummy-project"
        self.token = "dummy-token"
        self.valid = True
        self.expired = False
    def before_request(self, request, method, url, headers):
        headers["Authorization"] = "Bearer dummy-token"
    def refresh(self, request):
        pass

import vertexai
vertexai.init = MagicMock()

import google.genai
original_init = google.genai.Client.__init__
def patched_init(self, *args, **kwargs):
    if kwargs.get("vertexai") is not True:
        kwargs["vertexai"] = False
    original_init(self, *args, **kwargs)
google.genai.Client.__init__ = patched_init

google.auth.default = MagicMock(return_value=(DummyCredentials(), "dummy-project"))
google.cloud.logging.Client = MagicMock()

from fastapi.testclient import TestClient
from app.agent_runtime_app import fastapi_app
from app.agent import RecommendationOutput

client = TestClient(fastapi_app)

def test_analyze_gap_endpoint_with_xai():
    payload = {
        "user_skills": ["Python", "Docker"],
        "target_role": "Machine Learning Engineer"
    }
    response = client.post("/analyze-gap", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "confidence_score" in data
    assert "explanation" in data
    assert data["explanation"]["match_percentage"] == data["match_percentage"]
    assert len(data["explanation"]["feature_contributions"]) > 0

def test_forecast_demand_endpoint():
    payload = {
        "role": "Machine Learning Engineer",
        "skill": "MLOps",
        "target_year": 2028
    }
    response = client.post("/forecast-demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "Machine Learning Engineer"
    assert data["skill"] == "MLOps"
    assert "confidence_score" in data
    assert "explanation" in data
    assert "trend_direction" in data["explanation"]
    assert "text_explanation" in data["explanation"]

@patch("app.agent_runtime_app.generate_recommendations")
def test_generate_recommendations_with_prediction_integration(mock_recommend):
    mock_recs = RecommendationOutput(
        courses=["Advanced ML Course"],
        projects=["Build standard deployment pipeline"],
        next_roles=["Junior ML Engineer"]
    )
    mock_recommend.return_value = mock_recs

    payload = {
        "missing_skills": ["MLOps", "Deep Learning"],
        "target_role": "Machine Learning Engineer"
    }
    response = client.post("/generate-recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Advanced ML Course" in data["courses"]
    assert "Build standard deployment pipeline" in data["projects"]
    assert "Junior ML Engineer" in data["next_roles"]
    mock_recommend.assert_called_once_with(["MLOps", "Deep Learning"], "Machine Learning Engineer")
