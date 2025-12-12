# services/ai_client.py
"""
AI client for embeddings and scoring support
"""
import os
import json
import math
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Try to use OpenAI if key present (kept optional)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Local embedding fallback
try:
    from services.local_embeddings import text_to_embedding as local_text_to_embedding
except Exception as e:
    logger.warning(f"Local embeddings not available: {e}")
    local_text_to_embedding = None


def text_to_embedding(text: str, model: str = "text-embedding-3-small"):
    """
    Convert text to embedding vector
    Returns list[float]
    
    Priority:
      1) OpenAI embeddings if OPENAI_API_KEY set and call succeeds
      2) local sentence-transformers fallback
    """
    # Attempt OpenAI if configured
    if OPENAI_KEY:
        try:
            # Import lazily to avoid hard requirement at import time
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            response = client.embeddings.create(
                model=model,
                input=text[:8000]  # Limit input length
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, falling back to local: {e}")
    
    # Local fallback
    if local_text_to_embedding:
        return local_text_to_embedding(text)
    
    # Last resort: return zero vector
    logger.error("No embedding provider available")
    return [0.0] * 384  # Local model dimension


def generate_profile_embedding(db: Session, profile):
    """
    Generate and store embedding for candidate profile
    Returns Embedding object
    """
    from models import Embedding
    
    # Build canonical text for profile
    parts = []
    if profile.headline:
        parts.append(profile.headline)
    if profile.skills:
        if isinstance(profile.skills, list):
            skill_names = []
            for s in profile.skills:
                if isinstance(s, str):
                    skill_names.append(s)
                elif isinstance(s, dict):
                    skill_names.append(s.get("name", ""))
            parts.append("Skills: " + ", ".join(skill_names))
    if profile.experience:
        if isinstance(profile.experience, list):
            ex = profile.experience[-3:]  # Last 3 roles
            role_strs = []
            for e in ex:
                if isinstance(e, dict):
                    title = e.get('title', '')
                    company = e.get('company', '')
                    role_strs.append(f"{title} at {company}")
            if role_strs:
                parts.append("Recent roles: " + "; ".join(role_strs))
    
    text = "\n".join(parts)[:3000]
    
    if not text:
        text = "No profile data available"
    
    vector = text_to_embedding(text)
    
    # Store embedding in DB
    emb = Embedding(
        entity_type="candidate_profile",
        entity_id=profile.id,
        model="text-embedding-3-small",
        vector=json.dumps(vector),
        meta_data={"user_id": profile.user_id}
    )
    db.add(emb)
    db.commit()
    db.refresh(emb)
    return emb


def generate_job_embedding(db: Session, job):
    """
    Generate and store embedding for job posting
    Returns Embedding object
    """
    from models import Embedding
    
    parts = [
        job.title or "",
        job.description or ""
    ]
    text = "\n".join(parts)[:3000]
    
    if not text:
        text = "No job data available"
    
    vector = text_to_embedding(text)
    
    # Store embedding in DB
    emb = Embedding(
        entity_type="job",
        entity_id=job.id,
        model="text-embedding-3-small",
        vector=json.dumps(vector),
        meta_data={"job_title": job.title}
    )
    db.add(emb)
    db.commit()
    db.refresh(emb)
    return emb


def cosine_similarity(a, b):
    """
    Calculate cosine similarity between two vectors
    a, b are lists of floats
    Returns float between -1 and 1
    """
    if len(a) != len(b):
        return 0.0
    
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    
    if na == 0 or nb == 0:
        return 0.0
    
    return dot / (na * nb)
