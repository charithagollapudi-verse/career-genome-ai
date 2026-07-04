# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
from typing import Any

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp

from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()

# Fallback Google Cloud Project for local development and testing to prevent credential errors
if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = "dummy-project"



class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Runtime application."""
        return self


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.skill_intelligence import analyze_user_skills

gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_runtime = AgentEngineApp(
    app=adk_app,
    artifact_service_builder=lambda: (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
)

fastapi_app = FastAPI(title="Career Genome AI - Skill Intelligence Engine")

class AnalyzeSkillsRequest(BaseModel):
    user_skills: list[str]
    target_role: str | None = None

@fastapi_app.post("/analyze-skills")
def analyze_skills(request: AnalyzeSkillsRequest):
    if not request.user_skills:
        raise HTTPException(status_code=400, detail="user_skills list cannot be empty")
    try:
        return analyze_user_skills(request.user_skills, request.target_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.resume_parser import parse_resume_text, ResumeData

class ParseResumeRequest(BaseModel):
    resume_text: str

@fastapi_app.post("/parse-resume", response_model=ResumeData)
def parse_resume(request: ParseResumeRequest):
    if not request.resume_text or not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="resume_text cannot be empty")
    try:
        return parse_resume_text(request.resume_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.career_dna import generate_career_dna, CareerDNAOutput
from app.skill_gap_analyzer import analyze_skill_gap, SkillGapOutput
from app.recommendation_engine import generate_recommendations, RecommendationOutput

class AnalyzeDnaRequest(BaseModel):
    profile_text: str

class AnalyzeGapRequest(BaseModel):
    user_skills: list[str]
    target_role: str

class GenerateRecommendationsRequest(BaseModel):
    missing_skills: list[str]
    target_role: str

@fastapi_app.post("/analyze-dna", response_model=CareerDNAOutput)
def analyze_dna(request: AnalyzeDnaRequest):
    if not request.profile_text or not request.profile_text.strip():
        raise HTTPException(status_code=400, detail="profile_text cannot be empty")
    try:
        return generate_career_dna(request.profile_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/analyze-gap", response_model=SkillGapOutput)
def analyze_gap(request: AnalyzeGapRequest):
    try:
        return analyze_skill_gap(request.user_skills, request.target_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/generate-recommendations", response_model=RecommendationOutput)
def get_recommendations(request: GenerateRecommendationsRequest):
    try:
        return generate_recommendations(request.missing_skills, request.target_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
