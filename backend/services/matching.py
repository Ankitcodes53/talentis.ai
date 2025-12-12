# services/matching.py
"""
Enhanced matching service with embeddings and simulation scores
"""
from sqlalchemy.orm import Session
from models import Match, Simulation, SimulationAttempt, CandidateProfile
from services.search import find_similar_candidates_for_job


def compute_match_score(
    skills_score: float,
    experience_score: float,
    embedding_similarity: float = None,
    simulation_score: float = None
) -> float:
    """
    Compute overall match score from multiple components
    
    Args:
        skills_score: 0-100 score from skill matching
        experience_score: 0-100 score from experience matching
        embedding_similarity: 0-1 semantic similarity from embeddings
        simulation_score: 0-100 score from simulation attempt
    
    Returns:
        float: Overall match score 0-100
    """
    # Convert embedding similarity to 0-100 scale
    emb_score = (embedding_similarity * 100) if embedding_similarity is not None else None
    
    # Weight breakdown:
    # - Skills: 50%
    # - Experience: 20%
    # - Embedding: 20% (if available)
    # - Simulation: 10% (if available)
    
    if emb_score is None and simulation_score is None:
        # Fallback: only skills and experience
        score = 0.7 * skills_score + 0.3 * experience_score
    elif emb_score is None:
        # No embedding but have simulation
        score = 0.5 * skills_score + 0.25 * experience_score + 0.25 * simulation_score
    elif simulation_score is None:
        # No simulation but have embedding
        score = 0.5 * skills_score + 0.2 * experience_score + 0.3 * emb_score
    else:
        # All components available
        score = 0.5 * skills_score + 0.2 * experience_score + 0.2 * emb_score + 0.1 * simulation_score
    
    return round(score, 2)


def recompute_match_for_candidate_job(db: Session, candidate_id: int, job_id: int) -> Match:
    """
    Recompute or create match score for a candidate-job pair
    
    Args:
        db: Database session
        candidate_id: User ID of candidate
        job_id: Job description ID
    
    Returns:
        Match: Updated or new match object
    """
    # Get existing candidate profile data for skill/experience scores
    # For prototype, using placeholder scores - adapt to your schema
    from models import Candidate
    
    candidate = db.query(Candidate).filter(Candidate.user_id == candidate_id).first()
    
    # Placeholder skill/experience scores (you should compute these from actual data)
    skills_score = 70.0
    experience_score = 30.0
    
    # Find embedding similarity
    emb_sim = None
    sims = find_similar_candidates_for_job(db, job_id, top_k=500)
    
    # Find candidate profile id
    cand_profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == candidate_id
    ).first()
    
    if cand_profile:
        for s in sims:
            if s["candidate_profile_id"] == cand_profile.id:
                emb_sim = s["similarity"]
                break
    
    # Get latest simulation score
    simulation_score = None
    sim = db.query(Simulation).filter(Simulation.job_id == job_id).first()
    if sim:
        attempt = db.query(SimulationAttempt).filter(
            SimulationAttempt.simulation_id == sim.id,
            SimulationAttempt.candidate_id == candidate_id,
            SimulationAttempt.ai_score.isnot(None)
        ).order_by(SimulationAttempt.created_at.desc()).first()
        
        if attempt:
            simulation_score = attempt.ai_score
    
    # Compute overall score
    score = compute_match_score(skills_score, experience_score, emb_sim, simulation_score)
    
    # Create or update match record
    match = db.query(Match).filter(
        Match.candidate_id == candidate_id,
        Match.job_id == job_id
    ).first()
    
    if not match:
        match = Match(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=score,
            match_explanation=f"Skills: {skills_score}%, Experience: {experience_score}%, Semantic: {int(emb_sim*100) if emb_sim else 'N/A'}%, Simulation: {simulation_score if simulation_score else 'N/A'}%"
        )
        # Set simulation_score if Match model has this field
        if hasattr(match, 'simulation_score'):
            match.simulation_score = simulation_score
    else:
        match.match_score = score
        match.match_explanation = f"Skills: {skills_score}%, Experience: {experience_score}%, Semantic: {int(emb_sim*100) if emb_sim else 'N/A'}%, Simulation: {simulation_score if simulation_score else 'N/A'}%"
        if hasattr(match, 'simulation_score'):
            match.simulation_score = simulation_score
    
    db.add(match)
    db.commit()
    db.refresh(match)
    return match
