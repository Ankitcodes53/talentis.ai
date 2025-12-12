# routers/candidates.py
"""
Candidate profile and resume upload routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
import aiofiles
import os
import uuid

from database import get_db
from models import CandidateProfile, User
from auth import get_current_user
from services.resume_parser_service import parse_resume_and_extract_fields

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/resumes")


def generate_profile_embedding_background(profile_id: int):
    """Background task to generate embedding for profile"""
    from database import SessionLocal
    from services.ai_client import generate_profile_embedding
    
    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(
            CandidateProfile.id == profile_id
        ).first()
        if profile:
            generate_profile_embedding(db, profile)
    except Exception as e:
        print(f"Error generating profile embedding: {e}")
    finally:
        db.close()


@router.post("/upload-resume")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Upload resume and extract structured data using AI
    
    - Parses resume with OpenAI
    - Creates/updates candidate profile
    - Generates semantic embedding in background
    """
    if user.role.value != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can upload resumes")
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    fname = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, fname)
    
    # Save file
    try:
        async with aiofiles.open(path, "wb") as out:
            content = await file.read()
            await out.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Extract structured data from resume
    extracted = await parse_resume_and_extract_fields(path)
    
    # Get or create candidate profile
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user.id
    ).first()
    
    if not profile:
        profile = CandidateProfile(user_id=user.id, resume_path=path)
    else:
        profile.resume_path = path
    
    # Update profile with extracted data
    profile.headline = extracted.get("headline")
    profile.location = extracted.get("location")
    profile.education = extracted.get("education") or []
    profile.experience = extracted.get("experience") or []
    profile.skills = extracted.get("skills") or []
    profile.certifications = extracted.get("certifications") or []
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Generate embedding in background
    background_tasks.add_task(generate_profile_embedding_background, profile.id)
    
    return {
        "message": "Resume uploaded and processed successfully",
        "profile_id": profile.id,
        "extracted": {
            "headline": profile.headline,
            "location": profile.location,
            "skills": profile.skills,
            "education_count": len(profile.education) if profile.education else 0,
            "experience_count": len(profile.experience) if profile.experience else 0
        }
    }


@router.get("/profile")
async def get_my_profile(
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get current candidate's profile"""
    if user.role.value != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can view this")
    
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user.id
    ).first()
    
    if not profile:
        return {"message": "No profile found", "profile": None}
    
    return {
        "profile": {
            "id": profile.id,
            "headline": profile.headline,
            "location": profile.location,
            "phone": profile.phone,
            "education": profile.education,
            "experience": profile.experience,
            "skills": profile.skills,
            "certifications": profile.certifications,
            "consent_profile_share": profile.consent_profile_share,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
    }


@router.put("/profile/consent")
async def update_consent(
    consent: bool,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Update profile sharing consent"""
    if user.role.value != "candidate":
        raise HTTPException(status_code=403, detail="Only candidates can update this")
    
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile.consent_profile_share = consent
    db.commit()
    
    return {"message": "Consent updated", "consent_profile_share": consent}
