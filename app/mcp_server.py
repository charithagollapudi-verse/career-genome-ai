import json
import sys
from mcp.server.fastmcp import FastMCP

# Add parent directory to sys.path so we can import from app
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_connection
from app.ml_forecaster import forecast_skill_demand, simulate_career_trajectory

# Create the MCP server
mcp = FastMCP("career-genome-server")

@mcp.tool()
def calculate_skill_gap(user_skills: str, target_role: str) -> str:
    """
    Compares user skills with real-world target role requirements.
    
    Args:
        user_skills: Comma-separated list of skills currently possessed (e.g. 'Python, SQL')
        target_role: Target role to check (e.g. 'Machine Learning Engineer', 'Cloud Engineer')
    """
    skills_list = [s.strip() for s in user_skills.split(",") if s.strip()]
    result = simulate_career_trajectory(skills_list, target_role)
    
    match_percentage = int(result["current_match_probability"] * 100)
    
    output = {
        "target_role": target_role,
        "match_percentage": match_percentage,
        "missing_skills": result["missing_skills"],
        "recommended_priority": [
            {"skill": skill, "priority": "High" if idx < 2 else "Medium"}
            for idx, skill in enumerate(result["missing_skills"])
        ]
    }
    return json.dumps(output, indent=2)

@mcp.tool()
def get_skill_forecast(role: str, skill: str, target_year: int = 2028) -> str:
    """
    Predicts future demand index and growth rates of a skill for a given role.
    
    Args:
        role: Target role (e.g. 'Machine Learning Engineer')
        skill: Target skill to forecast (e.g. 'MLOps', 'Python')
        target_year: Future year to forecast (e.g. 2028, 2029)
    """
    result = forecast_skill_demand(role, skill, target_year)
    return json.dumps(result, indent=2)

@mcp.tool()
def simulate_career_path(user_skills: str, target_role: str) -> str:
    """
    Simulates a year-over-year trajectory of skill matching for a target role.
    
    Args:
        user_skills: Comma-separated list of current skills.
        target_role: Target role to simulate.
    """
    skills_list = [s.strip() for s in user_skills.split(",") if s.strip()]
    result = simulate_career_trajectory(skills_list, target_role)
    return json.dumps(result, indent=2)

@mcp.tool()
def query_job_market_data(role: str) -> str:
    """
    Queries current database market trend indices for all skills associated with a role.
    
    Args:
        role: Target role (e.g. 'Cloud Engineer')
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT skill, demand_index, projected_growth 
        FROM job_market_trends 
        WHERE role = ? AND year = 2026
    """, (role,))
    rows = cursor.fetchall()
    conn.close()
    
    market_data = [
        {
            "skill": r["skill"],
            "demand_index": r["demand_index"],
            "projected_growth": r["projected_growth"]
        } for r in rows
    ]
    
    return json.dumps({"role": role, "market_trends_2026": market_data}, indent=2)

if __name__ == "__main__":
    mcp.run("stdio")
