"""
AI-powered resume parser using OpenAI
Extracts skills, experience, education from resumes
"""

import json
import re
from typing import Dict, List
import os

def parse_resume_text(resume_text: str) -> Dict:
    """
    Parse resume text and extract structured information
    Uses pattern matching and AI-like extraction
    """
    
    result = {
        "skills": [],
        "experience_years": 0,
        "education": "",
        "certifications": [],
        "languages": [],
        "summary": ""
    }
    
    # Common technical skills to look for
    common_skills = [
        "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Rust",
        "React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask", "FastAPI",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "CI/CD",
        "Git", "Linux", "REST", "GraphQL", "Microservices", "Agile", "Scrum",
        "Machine Learning", "TensorFlow", "PyTorch", "Data Science", "AI",
        "HTML", "CSS", "TypeScript", "Swift", "Kotlin", "PHP", "Laravel"
    ]
    
    # Extract skills
    text_lower = resume_text.lower()
    for skill in common_skills:
        if skill.lower() in text_lower:
            result["skills"].append(skill)
    
    # Extract experience years
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience:\s*(\d+)\+?\s*years?',
        r'(\d+)\s*years?\s*in\s*(?:software|development|engineering)'
    ]
    
    max_years = 0
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            years = int(match) if isinstance(match, str) else int(match[0])
            max_years = max(max_years, years)
    
    result["experience_years"] = max_years
    
    # Extract education
    education_keywords = ["bachelor", "master", "phd", "b.tech", "m.tech", "mba", "computer science", "engineering"]
    lines = resume_text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in education_keywords):
            if len(line.strip()) > 10:  # Avoid short lines
                result["education"] = line.strip()
                break
    
    # Extract certifications
    cert_keywords = ["certified", "certification", "aws certified", "azure certified", "google certified"]
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in cert_keywords):
            result["certifications"].append(line.strip())
    
    # Extract languages
    language_keywords = ["english", "spanish", "french", "german", "chinese", "hindi", "japanese"]
    for keyword in language_keywords:
        if keyword in text_lower:
            result["languages"].append(keyword.capitalize())
    
    # Generate summary
    first_lines = [line.strip() for line in lines[:5] if len(line.strip()) > 20]
    if first_lines:
        result["summary"] = first_lines[0][:200]
    
    return result

def calculate_ats_score(candidate_skills: List[str], job_skills: List[str]) -> Dict:
    """
    Calculate ATS (Applicant Tracking System) score
    More sophisticated matching algorithm
    """
    
    if not job_skills:
        return {"score": 50, "matched_skills": [], "missing_skills": []}
    
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    job_skills_lower = [s.lower() for s in job_skills]
    
    # Find matched skills
    matched = []
    for job_skill in job_skills:
        for candidate_skill in candidate_skills:
            if job_skill.lower() == candidate_skill.lower() or \
               job_skill.lower() in candidate_skill.lower() or \
               candidate_skill.lower() in job_skill.lower():
                matched.append(job_skill)
                break
    
    # Find missing skills
    missing = [s for s in job_skills if s.lower() not in [m.lower() for m in matched]]
    
    # Calculate score
    base_score = (len(matched) / len(job_skills)) * 100 if job_skills else 0
    
    # Bonus for having extra relevant skills
    extra_skills = len([s for s in candidate_skills if s.lower() not in job_skills_lower])
    bonus = min(extra_skills * 2, 15)  # Max 15% bonus
    
    final_score = min(base_score + bonus, 100)
    
    return {
        "score": round(final_score, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra_skills
    }

def get_latest_simulation_score(db, job_id: int, candidate_id: int):
    """
    Get the latest simulation score for a candidate on a specific job
    
    Args:
        db: Database session
        job_id: ID of the job posting
        candidate_id: ID of the candidate
    
    Returns:
        float: Latest AI simulation score (0-100) or None if no completed simulations
    """
    from models import Simulation, SimulationAttempt

    # Find simulations for the job
    sims = db.query(Simulation).filter(Simulation.job_id == job_id).all()
    if not sims:
        return None

    sim_ids = [s.id for s in sims]

    attempt = (
        db.query(SimulationAttempt)
          .filter(
              SimulationAttempt.simulation_id.in_(sim_ids),
              SimulationAttempt.candidate_id == candidate_id,
              SimulationAttempt.ai_score.isnot(None)
          )
          .order_by(SimulationAttempt.created_at.desc())
          .first()
    )

    return attempt.ai_score if attempt else None


def generate_match_explanation(ats_result: Dict, experience_years: int, required_experience: int = 3) -> str:
    """
    Generate human-readable match explanation
    """
    score = ats_result["score"]
    matched = len(ats_result["matched_skills"])
    missing = len(ats_result["missing_skills"])
    
    if score >= 80:
        rating = "Excellent match"
    elif score >= 60:
        rating = "Good match"
    elif score >= 40:
        rating = "Fair match"
    else:
        rating = "Weak match"
    
    explanation = f"{rating} - {matched} of {matched + missing} required skills matched"
    
    if experience_years >= required_experience:
        explanation += f". {experience_years} years experience (meets requirement)."
    elif experience_years > 0:
        explanation += f". {experience_years} years experience (below {required_experience} years requirement)."
    
    if ats_result["matched_skills"]:
        top_skills = ats_result["matched_skills"][:3]
        explanation += f" Strong in: {', '.join(top_skills)}."
    
    return explanation
