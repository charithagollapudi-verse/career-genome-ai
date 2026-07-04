import logging
from app.database import get_connection

logger = logging.getLogger(__name__)

def get_predefined_profiles() -> dict[str, list[str]]:
    """
    Fetches all distinct roles and their required skills from the job market trends table.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT role, skill FROM job_market_trends")
        rows = cursor.fetchall()
        
        profiles = {}
        for row in rows:
            role = row["role"]
            skill = row["skill"]
            if role not in profiles:
                profiles[role] = []
            if skill not in profiles[role]:
                profiles[role].append(skill)
        return profiles
    except Exception as e:
        logger.error(f"Error querying predefined profiles: {e}")
        return {}
    finally:
        conn.close()

def analyze_user_skills(user_skills: list[str], target_role: str = None) -> dict:
    """
    Analyzes user skills against predefined profiles and calculates metrics.
    """
    profiles = get_predefined_profiles()
    
    # Normalize user skills
    user_skills_set = {s.strip().lower() for s in user_skills if s.strip()}
    
    def calculate_role_metrics(role: str, profile_skills: list[str]) -> dict:
        profile_skills_set = {s.strip().lower() for s in profile_skills}
        matched_skills = [s for s in profile_skills if s.strip().lower() in user_skills_set]
        missing_skills = [s for s in profile_skills if s.strip().lower() not in user_skills_set]
        
        # 1. Career Readiness (%)
        readiness = (len(matched_skills) / len(profile_skills)) * 100 if profile_skills else 0.0
        
        # 2. Skill Strength (%)
        # We query the database to get the demand index of the skills for this role in the base year 2026.
        conn = get_connection()
        demand_map = {}
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT skill, demand_index FROM job_market_trends WHERE role = ? AND year = 2026",
                (role,)
            )
            rows = cursor.fetchall()
            demand_map = {row["skill"].lower(): row["demand_index"] for row in rows}
        except Exception as e:
            logger.error(f"Error getting demand index for role {role}: {e}")
        finally:
            conn.close()
            
        total_demand = sum(demand_map.get(s.lower(), 1.0) for s in profile_skills)
        matched_demand = sum(demand_map.get(s.lower(), 1.0) for s in matched_skills)
        skill_strength = (matched_demand / total_demand) * 100 if total_demand > 0 else 0.0
        
        # 3. Domain Affinity (%)
        domain_affinity = (len(matched_skills) / len(user_skills)) * 100 if user_skills else 0.0
        
        # 4. Learning Velocity (skills/year)
        # Scaled based on affinity and current readiness. Baseline is 1.5.
        affinity_ratio = len(matched_skills) / len(user_skills) if user_skills else 0.0
        readiness_ratio = len(matched_skills) / len(profile_skills) if profile_skills else 0.0
        learning_velocity = 1.5 * (1.0 + 0.5 * affinity_ratio + 0.5 * readiness_ratio)
        
        return {
            "role": role,
            "career_readiness": round(readiness, 2),
            "skill_strength": round(skill_strength, 2),
            "domain_affinity": round(domain_affinity, 2),
            "learning_velocity": round(learning_velocity, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }

    if target_role:
        if target_role not in profiles:
            raise ValueError(f"Target role '{target_role}' is not a predefined profile. Available profiles: {list(profiles.keys())}")
        return calculate_role_metrics(target_role, profiles[target_role])
    else:
        results = []
        for role, profile_skills in profiles.items():
            results.append(calculate_role_metrics(role, profile_skills))
        # Sort by career readiness descending
        results.sort(key=lambda x: x["career_readiness"], reverse=True)
        return {"profiles": results}
