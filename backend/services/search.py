# services/search.py
"""
Similarity search and matching service
"""
import json
from sqlalchemy.orm import Session
from models import Embedding
from services.ai_client import cosine_similarity


def find_similar_candidates_for_job(db: Session, job_id: int, top_k: int = 50):
    """
    Find candidates with highest semantic similarity to a job
    Returns list of dicts with candidate_profile_id and similarity score
    """
    # Get job embedding
    job_emb = db.query(Embedding).filter(
        Embedding.entity_type == "job",
        Embedding.entity_id == job_id
    ).order_by(Embedding.created_at.desc()).first()
    
    if not job_emb:
        return []
    
    job_vec = json.loads(job_emb.vector)
    
    # Get all candidate profile embeddings
    cands = db.query(Embedding).filter(
        Embedding.entity_type == "candidate_profile"
    ).all()
    
    scored = []
    for c in cands:
        try:
            cvec = json.loads(c.vector)
            sim = cosine_similarity(job_vec, cvec)
            scored.append({
                "candidate_profile_id": c.entity_id,
                "similarity": sim,
                "user_id": c.meta_data.get("user_id") if c.meta_data else None
            })
        except Exception as e:
            print(f"Error computing similarity for candidate {c.entity_id}: {e}")
            continue
    
    # Sort by similarity descending
    scored_sorted = sorted(scored, key=lambda x: x["similarity"], reverse=True)[:top_k]
    return scored_sorted


def find_similar_jobs_for_candidate(db: Session, candidate_profile_id: int, top_k: int = 50):
    """
    Find jobs with highest semantic similarity to a candidate
    Returns list of dicts with job_id and similarity score
    """
    # Get candidate profile embedding
    cand_emb = db.query(Embedding).filter(
        Embedding.entity_type == "candidate_profile",
        Embedding.entity_id == candidate_profile_id
    ).order_by(Embedding.created_at.desc()).first()
    
    if not cand_emb:
        return []
    
    cand_vec = json.loads(cand_emb.vector)
    
    # Get all job embeddings
    jobs = db.query(Embedding).filter(
        Embedding.entity_type == "job"
    ).all()
    
    scored = []
    for j in jobs:
        try:
            jvec = json.loads(j.vector)
            sim = cosine_similarity(cand_vec, jvec)
            scored.append({
                "job_id": j.entity_id,
                "similarity": sim
            })
        except Exception as e:
            print(f"Error computing similarity for job {j.entity_id}: {e}")
            continue
    
    # Sort by similarity descending
    scored_sorted = sorted(scored, key=lambda x: x["similarity"], reverse=True)[:top_k]
    return scored_sorted
