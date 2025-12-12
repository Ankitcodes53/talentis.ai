"""
Simulation & Scenario-based Assessment Routes
Handles AI-powered scenario simulations for candidate evaluation
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import json

from database import get_db
from models import (
    Simulation, SimulationAttempt, JobDescription, 
    User, UserRole, Candidate
)
from main import get_current_user

router = APIRouter(prefix="/api/simulations", tags=["simulations"])
security = HTTPBearer()


# ==================== PYDANTIC SCHEMAS ====================

class CreateSimulationRequest(BaseModel):
    job_id: int
    title: str
    simulation_type: str
    prompt: str
    rubric: dict

class SubmitResponsesRequest(BaseModel):
    responses: dict

class UpdateSimulationRequest(BaseModel):
    title: Optional[str] = None
    prompt: Optional[str] = None
    rubric: Optional[dict] = None
    is_active: Optional[bool] = None


# ==================== EMPLOYER ENDPOINTS ====================

@router.post("/create")
async def create_simulation(
    request: CreateSimulationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """
    Create a new simulation/scenario for a job posting
    
    Args:
        job_id: ID of the job this simulation is for
        title: Short title (e.g., "Customer Conflict Resolution")
        simulation_type: Type of simulation (roleplay, case_study, technical_challenge)
        prompt: The scenario prompt/description for the candidate
        rubric: JSON rubric for AI evaluation (scoring criteria)
    """
    user = await get_current_user(credentials, db)
    
    if user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can create simulations")
    
    # Verify job ownership
    job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
    if not job or job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this job")
    
    # Create simulation
    simulation = Simulation(
        job_id=request.job_id,
        title=request.title,
        type=request.simulation_type,
        prompt=request.prompt,
        rubric=request.rubric,
        created_by_ai=False,
        is_active=True
    )
    
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    
    return {
        "message": "Simulation created successfully",
        "simulation_id": simulation.id,
        "title": simulation.title,
        "type": simulation.type
    }


@router.get("/job/{job_id}")
async def get_job_simulations(
    job_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get all simulations for a specific job"""
    user = await get_current_user(credentials, db)
    
    # Verify access - employer must own job, candidate can view if they have a match
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if user.role == UserRole.EMPLOYER and job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    simulations = db.query(Simulation).filter(
        Simulation.job_id == job_id,
        Simulation.is_active == True
    ).all()
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "simulations": [
            {
                "id": sim.id,
                "title": sim.title,
                "type": sim.type,
                "prompt": sim.prompt,
                "created_at": sim.created_at.isoformat() if sim.created_at else None
            }
            for sim in simulations
        ]
    }


@router.get("/{simulation_id}/attempts")
async def get_simulation_attempts(
    simulation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get all attempts for a simulation (employer only)"""
    user = await get_current_user(credentials, db)
    
    if user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can view attempts")
    
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    job = db.query(JobDescription).filter(JobDescription.id == simulation.job_id).first()
    if job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    attempts = db.query(SimulationAttempt, User).join(
        User, SimulationAttempt.candidate_id == User.id
    ).filter(
        SimulationAttempt.simulation_id == simulation_id
    ).all()
    
    return {
        "simulation_id": simulation_id,
        "title": simulation.title,
        "attempts": [
            {
                "id": attempt.id,
                "candidate_email": candidate.email,
                "candidate_name": candidate.full_name,
                "status": attempt.status,
                "ai_score": attempt.ai_score,
                "ai_subscores": attempt.ai_subscores,
                "ai_feedback": attempt.ai_feedback,
                "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
                "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
            }
            for attempt, candidate in attempts
        ]
    }


# ==================== CANDIDATE ENDPOINTS ====================

@router.post("/{simulation_id}/start")
async def start_simulation_attempt(
    simulation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """
    Start a new simulation attempt for a candidate
    Returns the simulation prompt and creates an attempt record
    """
    user = await get_current_user(credentials, db)
    
    if user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can attempt simulations")
    
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation or not simulation.is_active:
        raise HTTPException(status_code=404, detail="Simulation not found or inactive")
    
    # Check if candidate already has a completed attempt
    existing_attempt = db.query(SimulationAttempt).filter(
        SimulationAttempt.simulation_id == simulation_id,
        SimulationAttempt.candidate_id == user.id,
        SimulationAttempt.status == "completed"
    ).first()
    
    if existing_attempt:
        raise HTTPException(status_code=400, detail="You have already completed this simulation")
    
    # Check for in-progress attempt
    in_progress = db.query(SimulationAttempt).filter(
        SimulationAttempt.simulation_id == simulation_id,
        SimulationAttempt.candidate_id == user.id,
        SimulationAttempt.status == "in_progress"
    ).first()
    
    if in_progress:
        # Return existing attempt
        return {
            "attempt_id": in_progress.id,
            "simulation_title": simulation.title,
            "simulation_type": simulation.type,
            "prompt": simulation.prompt,
            "started_at": in_progress.started_at.isoformat(),
            "status": "resumed"
        }
    
    # Create new attempt
    attempt = SimulationAttempt(
        simulation_id=simulation_id,
        candidate_id=user.id,
        status="in_progress",
        started_at=datetime.utcnow()
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return {
        "attempt_id": attempt.id,
        "simulation_title": simulation.title,
        "simulation_type": simulation.type,
        "prompt": simulation.prompt,
        "started_at": attempt.started_at.isoformat(),
        "status": "started"
    }


@router.post("/attempts/{attempt_id}/submit")
async def submit_simulation_responses(
    attempt_id: int,
    request: SubmitResponsesRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """
    Submit responses for a simulation attempt
    AI will evaluate based on the rubric and provide scoring
    
    Args:
        attempt_id: ID of the simulation attempt
        responses: JSON object with candidate's responses
    """
    user = await get_current_user(credentials, db)
    
    attempt = db.query(SimulationAttempt).filter(SimulationAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if attempt.status == "completed":
        raise HTTPException(status_code=400, detail="Attempt already completed")
    
    # Get simulation rubric for AI evaluation
    simulation = db.query(Simulation).filter(Simulation.id == attempt.simulation_id).first()
    
    # TODO: Integrate with OpenAI/Claude for actual AI evaluation
    # For now, generate mock scores
    ai_score = 75.0  # Mock score
    ai_subscores = {
        "problem_solving": 80,
        "communication": 70,
        "technical_accuracy": 75,
        "creativity": 72
    }
    ai_feedback = """
    Strong analytical approach to the problem. Communication was clear and structured.
    Consider providing more specific examples in future responses.
    Overall performance demonstrates competence in the required areas.
    """
    
    # Update attempt
    attempt.responses = request.responses
    attempt.ai_score = ai_score
    attempt.ai_subscores = ai_subscores
    attempt.ai_feedback = ai_feedback
    attempt.status = "completed"
    attempt.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(attempt)
    
    # Generate embedding for simulation response
    try:
        import json
        from services.ai_client import text_to_embedding
        from models import Embedding
        
        # Extract text from responses
        text = request.responses.get("response_text") if isinstance(request.responses, dict) else str(request.responses)
        if not text:
            text = json.dumps(request.responses)
        
        vec = text_to_embedding(text)
        emb = Embedding(
            entity_type="simulation_response",
            entity_id=attempt.id,
            model="text-embedding-3-small",
            vector=json.dumps(vec),
            meta_data={
                "candidate_id": attempt.candidate_id,
                "job_id": simulation.job_id,
                "score": ai_score
            }
        )
        db.add(emb)
        db.commit()
    except Exception as e:
        print(f"Error generating simulation embedding: {e}")
    
    # Recompute match with new simulation score
    try:
        from services.matching import recompute_match_for_candidate_job
        recompute_match_for_candidate_job(db, attempt.candidate_id, simulation.job_id)
    except Exception as e:
        print(f"Error recomputing match: {e}")
    
    return {
        "message": "Simulation completed successfully",
        "attempt_id": attempt.id,
        "ai_score": ai_score,
        "ai_subscores": ai_subscores,
        "ai_feedback": ai_feedback,
        "completed_at": attempt.completed_at.isoformat()
    }


@router.get("/my-attempts")
async def get_candidate_attempts(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get all simulation attempts for the current candidate"""
    user = await get_current_user(credentials, db)
    
    if user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Only candidates can view their attempts")
    
    attempts = db.query(SimulationAttempt, Simulation, JobDescription).join(
        Simulation, SimulationAttempt.simulation_id == Simulation.id
    ).join(
        JobDescription, Simulation.job_id == JobDescription.id
    ).filter(
        SimulationAttempt.candidate_id == user.id
    ).all()
    
    return {
        "attempts": [
            {
                "id": attempt.id,
                "simulation_title": simulation.title,
                "simulation_type": simulation.type,
                "job_title": job.title,
                "status": attempt.status,
                "ai_score": attempt.ai_score,
                "ai_subscores": attempt.ai_subscores,
                "ai_feedback": attempt.ai_feedback if attempt.status == "completed" else None,
                "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
                "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None
            }
            for attempt, simulation, job in attempts
        ]
    }


@router.get("/attempts/{attempt_id}")
async def get_attempt_details(
    attempt_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get detailed results for a specific attempt"""
    user = await get_current_user(credentials, db)
    
    attempt = db.query(SimulationAttempt, Simulation).join(
        Simulation, SimulationAttempt.simulation_id == Simulation.id
    ).filter(SimulationAttempt.id == attempt_id).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    attempt_obj, simulation = attempt
    
    # Verify authorization
    if user.role == UserRole.CANDIDATE and attempt_obj.candidate_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if user.role == UserRole.EMPLOYER:
        job = db.query(JobDescription).filter(JobDescription.id == simulation.job_id).first()
        if job.employer_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "id": attempt_obj.id,
        "simulation_title": simulation.title,
        "simulation_type": simulation.type,
        "prompt": simulation.prompt,
        "responses": attempt_obj.responses,
        "status": attempt_obj.status,
        "ai_score": attempt_obj.ai_score,
        "ai_subscores": attempt_obj.ai_subscores,
        "ai_feedback": attempt_obj.ai_feedback,
        "started_at": attempt_obj.started_at.isoformat() if attempt_obj.started_at else None,
        "completed_at": attempt_obj.completed_at.isoformat() if attempt_obj.completed_at else None
    }


# ==================== ADMIN ENDPOINTS ====================

@router.delete("/{simulation_id}")
async def delete_simulation(
    simulation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Delete/deactivate a simulation (soft delete)"""
    user = await get_current_user(credentials, db)
    
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    job = db.query(JobDescription).filter(JobDescription.id == simulation.job_id).first()
    if user.role == UserRole.EMPLOYER and job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    simulation.is_active = False
    db.commit()
    
    return {"message": "Simulation deactivated successfully"}


@router.put("/{simulation_id}")
async def update_simulation(
    simulation_id: int,
    request: UpdateSimulationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Update simulation details"""
    user = await get_current_user(credentials, db)
    
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    job = db.query(JobDescription).filter(JobDescription.id == simulation.job_id).first()
    if user.role == UserRole.EMPLOYER and job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if request.title:
        simulation.title = request.title
    if request.prompt:
        simulation.prompt = request.prompt
    if request.rubric:
        simulation.rubric = request.rubric
    if request.is_active is not None:
        simulation.is_active = request.is_active
    
    simulation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(simulation)
    
    return {
        "message": "Simulation updated successfully",
        "simulation": {
            "id": simulation.id,
            "title": simulation.title,
            "type": simulation.type,
            "is_active": simulation.is_active
        }
    }
