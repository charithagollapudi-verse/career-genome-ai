# ruff: noqa
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

import os
import json
import logging
from typing import Any
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.workflow import Workflow, START, node
from google.adk.events.event import Event
from google.adk.agents.context import Context
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

from app.config import config

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# 1. State and Output Schemas
# -------------------------------------------------------------

class ResumeAnalysisOutput(BaseModel):
    skills: list[str] = Field(default_factory=list, description="Extracted skills from the resume.")
    experience_level: str = Field("", description="Determined experience level (e.g., Junior, Mid, Senior).")
    industries: list[str] = Field(default_factory=list, description="Matched industry domains.")

class CareerDNAOutput(BaseModel):
    archetype: str = Field("", description="Calculated career personality archetype.")
    values: list[str] = Field(default_factory=list, description="Core professional value drivers.")
    interests: list[str] = Field(default_factory=list, description="User's primary career interests.")

class MarketIntelligenceOutput(BaseModel):
    role: str = Field("", description="Target role analyzed.")
    skills_demand: list[dict[str, Any]] = Field(default_factory=list, description="List of skills and their demand metrics.")

class SkillGapOutput(BaseModel):
    match_percentage: int = Field(0, description="Match score out of 100.")
    missing_skills: list[str] = Field(default_factory=list, description="Required skills missing from user profile.")
    gap_summary: str = Field("", description="Qualitative summary of the skill gaps.")

class ForecastOutput(BaseModel):
    role: str = Field("", description="Target role analyzed.")
    trajectory: list[dict[str, Any]] = Field(default_factory=list, description="Year-over-year match probability projections.")

class RecommendationOutput(BaseModel):
    courses: list[str] = Field(default_factory=list, description="Recommended learning paths or courses.")
    projects: list[str] = Field(default_factory=list, description="Suggested practical projects to build missing skills.")
    next_roles: list[str] = Field(default_factory=list, description="Suggested next logical career roles.")

class WorkflowState(BaseModel):
    user_query: str = ""
    resume_text: str = ""
    target_role: str = ""
    resume_analysis: ResumeAnalysisOutput | None = None
    career_dna: CareerDNAOutput | None = None
    market_intelligence: MarketIntelligenceOutput | None = None
    skill_gap: SkillGapOutput | None = None
    forecast: ForecastOutput | None = None
    recommendations: RecommendationOutput | None = None
    audit_log: list[str] = Field(default_factory=list)


# -------------------------------------------------------------
# 2. MCP Toolset Setup
# -------------------------------------------------------------

mcp_connection = StdioConnectionParams(
    server_params=StdioServerParameters(
        command="python",
        args=["app/mcp_server.py"],
    )
)
mcp_tools = McpToolset(connection_params=mcp_connection)


# -------------------------------------------------------------
# 3. Sub-Agent Declarations (Architecture Interfaces)
# -------------------------------------------------------------

resume_agent = LlmAgent(
    name="resume_intelligence_agent",
    model=config.model,
    instruction=(
        "You are the Resume Intelligence Agent. "
        "Your task is to analyze the user's resume text and extract their skills, experience level, and industries. "
        "Do not implement detailed business logic yet. Output a mock analysis adhering to the schema."
    ),
    output_schema=ResumeAnalysisOutput,
    output_key="resume_analysis"
)

dna_agent = LlmAgent(
    name="career_dna_agent",
    model=config.model,
    instruction=(
        "You are the Career DNA Agent. "
        "Your task is to analyze the user's query and profile to determine their career archetype, values, and interests. "
        "Do not implement detailed business logic yet. Output a mock Career DNA adhering to the schema."
    ),
    output_schema=CareerDNAOutput,
    output_key="career_dna"
)

market_agent = LlmAgent(
    name="market_intelligence_agent",
    model=config.model,
    instruction=(
        "You are the Market Intelligence Agent. "
        "Your task is to query job market trends for the target role using the query_job_market_data tool. "
        "Do not implement detailed business logic yet."
    ),
    tools=[mcp_tools],
    output_key="market_intelligence"
)

gap_agent = LlmAgent(
    name="skill_gap_agent",
    model=config.model,
    instruction=(
        "You are the Skill Gap Agent. "
        "Your task is to compare user skills with target role requirements using the calculate_skill_gap tool. "
        "Do not implement detailed business logic yet."
    ),
    tools=[mcp_tools],
    output_key="skill_gap"
)

forecast_agent = LlmAgent(
    name="forecast_agent",
    model=config.model,
    instruction=(
        "You are the Forecast Agent. "
        "Your task is to project future demand for target skills using the get_skill_forecast and simulate_career_path tools. "
        "Do not implement detailed business logic yet."
    ),
    tools=[mcp_tools],
    output_key="forecast"
)

recommendation_agent = LlmAgent(
    name="recommendation_agent",
    model=config.model,
    instruction=(
        "You are the Recommendation Agent. "
        "Your task is to generate actionable recommendations for courses, projects, and next roles. "
        "Do not implement detailed business logic yet. Output mock recommendations adhering to the schema."
    ),
    output_schema=RecommendationOutput,
    output_key="recommendations"
)

mentor_agent = LlmAgent(
    name="career_mentor_agent",
    model=config.model,
    instruction=(
        "You are the Career Mentor Agent. "
        "Your task is to serve as the friendly, guidance-oriented orchestrator. "
        "Synthesize all available insights from the sub-agents (Resume, DNA, Market, Gap, Forecast, Recommendations) "
        "into a cohesive, mentor-like conversation response. "
        "Do not implement detailed business logic yet."
    )
)


# -------------------------------------------------------------
# 4. Workflow Function Nodes
# -------------------------------------------------------------

@node
def security_checkpoint(ctx: Context, node_input: types.Content) -> Event:
    """
    Performs basic input safety checking, PII scrubbing, and logs the request.
    """
    audit_entry = f"[{ctx.run_id}] Request safety verification started."
    
    user_text = ""
    if node_input and node_input.parts:
        user_text = "".join([part.text for part in node_input.parts if part.text])
    
    is_breach = False
    lower_text = user_text.lower()
    
    if "ignore previous instructions" in lower_text or "system prompt" in lower_text:
        is_breach = True
        audit_entry += " Alert: Potential prompt injection detected!"
        
    state_delta = {
        "user_query": user_text,
        "audit_log": ctx.state.get("audit_log", []) + [audit_entry]
    }
    
    if is_breach:
        return Event(output="Security breach detected.", route="security_breach", state=state_delta)
    
    return Event(output=user_text, route="secure", state=state_delta)


@node
def security_event(ctx: Context, node_input: str) -> Event:
    """
    Handles security breach actions by returning a clean rejection message.
    """
    audit_entry = f"[{ctx.run_id}] Security breach action triggered. Rejection output generated."
    state_delta = {"audit_log": ctx.state.get("audit_log", []) + [audit_entry]}
    
    violation_content = types.Content(
        role="model",
        parts=[types.Part.from_text(text="I cannot fulfill this request as it violates security policies.")]
    )
    return Event(content=violation_content, output="Security rejection executed.", state=state_delta)


@node
def intent_router(ctx: Context, node_input: str) -> Event:
    """
    Determines user intent from the query and routes to the appropriate specialized sub-agent.
    """
    lower_query = node_input.lower()
    
    route = "mentor"
    if "resume" in lower_query or "cv" in lower_query:
        route = "resume"
    elif "dna" in lower_query or "personality" in lower_query or "archetype" in lower_query:
        route = "dna"
    elif "market" in lower_query or "trend" in lower_query:
        route = "market"
    elif "gap" in lower_query or "missing" in lower_query:
        route = "gap"
    elif "forecast" in lower_query or "predict" in lower_query or "future" in lower_query:
        route = "forecast"
    elif "recommendation" in lower_query or "course" in lower_query or "project" in lower_query:
        route = "recommendation"
        
    audit_entry = f"[{ctx.run_id}] Intent router selected target route: {route}."
    state_delta = {"audit_log": ctx.state.get("audit_log", []) + [audit_entry]}
    
    return Event(output=node_input, route=route, state=state_delta)


@node
def final_output(ctx: Context, node_input: Any) -> Event:
    """
    Ensures final content is mapped properly to the user-facing output schema.
    """
    if isinstance(node_input, types.Content):
        return Event(content=node_input, output=node_input)
    
    text = str(node_input)
    content_event = types.Content(
        role="model",
        parts=[types.Part.from_text(text=text)]
    )
    return Event(content=content_event, output=text)


# -------------------------------------------------------------
# 5. Workflow Graph Definition
# -------------------------------------------------------------

workflow_agent = Workflow(
    name="career_genome_workflow",
    state_schema=WorkflowState,
    edges=[
        (START, security_checkpoint),
        
        # Security routing using dictionary mapping
        (security_checkpoint, {
            "security_breach": security_event,
            "secure": intent_router
        }),
        
        # Intent-based spoke routing using dictionary mapping
        (intent_router, {
            "resume": resume_agent,
            "dna": dna_agent,
            "market": market_agent,
            "gap": gap_agent,
            "forecast": forecast_agent,
            "recommendation": recommendation_agent,
            "mentor": mentor_agent
        }),
        
        # Spokes converge back to career mentor
        ((resume_agent, dna_agent, market_agent, gap_agent, forecast_agent, recommendation_agent), mentor_agent),
        
        # Final terminal routing
        ((mentor_agent, security_event), final_output)
    ]
)

app = App(
    root_agent=workflow_agent,
    name="app",
)

# Alias for backward compatibility with integration tests
root_agent = workflow_agent

