# routers/analytics.py
"""
Analytics and reporting endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, func

from database import get_db
from models import Match, Simulation, SimulationAttempt, JobDescription, User
from auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/job-funnel/{job_id}")
async def job_funnel(
    job_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get recruitment funnel metrics for a specific job
    
    Returns:
        - total_matches: Total candidates matched
        - simulations_completed: Candidates who completed simulations
        - invites_sent: Interview invitations sent
        - interviews_completed: Interviews completed
        - hired: Candidates hired
    """
    # Verify job ownership (employers only)
    if user.role.value == "employer":
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job or job.employer_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this job")
    
    # Get funnel metrics
    total_matches = db.query(func.count(Match.id)).filter(Match.job_id == job_id).scalar() or 0
    
    # Simulations completed
    sim = db.query(Simulation).filter(Simulation.job_id == job_id).first()
    sims_completed = 0
    if sim:
        sims_completed = db.query(func.count(SimulationAttempt.id)).filter(
            SimulationAttempt.simulation_id == sim.id,
            SimulationAttempt.status == "completed"
        ).scalar() or 0
    
    # Invites sent
    invites_sent = db.query(func.count(Match.id)).filter(
        Match.job_id == job_id,
        Match.interview_status == "invite_sent"
    ).scalar() or 0
    
    # Interviews completed
    interviews_completed = db.query(func.count(Match.id)).filter(
        Match.job_id == job_id,
        Match.interview_status == "completed"
    ).scalar() or 0
    
    # Hired (if you have a status field for this)
    hired = db.query(func.count(Match.id)).filter(
        Match.job_id == job_id,
        Match.status == "hired"
    ).scalar() or 0
    
    return {
        "job_id": job_id,
        "funnel": {
            "total_matches": total_matches,
            "simulations_completed": sims_completed,
            "invites_sent": invites_sent,
            "interviews_completed": interviews_completed,
            "hired": hired
        },
        "conversion_rates": {
            "simulation_completion": round((sims_completed / total_matches * 100) if total_matches > 0 else 0, 2),
            "invite_rate": round((invites_sent / total_matches * 100) if total_matches > 0 else 0, 2),
            "hire_rate": round((hired / total_matches * 100) if total_matches > 0 else 0, 2)
        }
    }


@router.get("/embedding-coverage")
async def embedding_coverage(
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Get statistics on embedding coverage
    Shows how many entities have embeddings generated
    """
    from models import Embedding, CandidateProfile
    
    # Count entities by type
    candidate_profiles = db.query(func.count(CandidateProfile.id)).scalar() or 0
    candidate_embeddings = db.query(func.count(Embedding.id)).filter(
        Embedding.entity_type == "candidate_profile"
    ).scalar() or 0
    
    jobs = db.query(func.count(JobDescription.id)).scalar() or 0
    job_embeddings = db.query(func.count(Embedding.id)).filter(
        Embedding.entity_type == "job"
    ).scalar() or 0
    
    simulation_responses = db.query(func.count(SimulationAttempt.id)).filter(
        SimulationAttempt.status == "completed"
    ).scalar() or 0
    simulation_embeddings = db.query(func.count(Embedding.id)).filter(
        Embedding.entity_type == "simulation_response"
    ).scalar() or 0
    
    return {
        "coverage": {
            "candidates": {
                "total": candidate_profiles,
                "with_embeddings": candidate_embeddings,
                "coverage_percent": round((candidate_embeddings / candidate_profiles * 100) if candidate_profiles > 0 else 0, 2)
            },
            "jobs": {
                "total": jobs,
                "with_embeddings": job_embeddings,
                "coverage_percent": round((job_embeddings / jobs * 100) if jobs > 0 else 0, 2)
            },
            "simulations": {
                "total": simulation_responses,
                "with_embeddings": simulation_embeddings,
                "coverage_percent": round((simulation_embeddings / simulation_responses * 100) if simulation_responses > 0 else 0, 2)
            }
        }
    }
