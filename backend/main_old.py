from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uvicorn
import os
import json
import random

from database import get_db, init_db
from models import (
    User, JobDescription, Candidate, Match, Interview, 
    Payment, Analytics, BiasAuditLog,
    UserRole, PaymentStatus, PaymentPlan
)
from auth import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, get_current_user
)

app = FastAPI(
    title="Talentis.ai API",
    description="AI-powered global hiring platform with JWT authentication",
    version="3.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")


# Pydantic models for API requests/responses
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # 'employer' or 'candidate'

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    company_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    skills: List[str] = Field(..., min_items=1)
    location: str
    salary_min: int = Field(..., ge=0)
    salary_max: int = Field(..., ge=0)
    language: str = Field(default="en")

class JobResponse(BaseModel):
    job_id: int
    title: str
    description: str
    skills_required: List[str]
    location: str
    salary_range: str
    language: str
    created_at: datetime

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    match_id: int
    candidate_id: int
    candidate_name: str
    score: int
    explanation_text: str
    bias_audit_json: Dict
    created_at: datetime

class InterviewStartRequest(BaseModel):
    match_id: int

class InterviewQuestion(BaseModel):
    question_id: int
    question_text: str
    category: str

class InterviewStartResponse(BaseModel):
    interview_id: int
    questions: List[InterviewQuestion]
    language: str

class InterviewSubmitRequest(BaseModel):
    match_id: int
    responses: Dict[str, str]

class InterviewSubmitResponse(BaseModel):
    interview_id: int
    scores: Dict[str, float]
    total_score: float
    retention_prediction: float
    bias_audit: Dict
    recommendation: str

class PaymentCreateOrderRequest(BaseModel):
    amount: int = Field(..., ge=100)

class PaymentCreateOrderResponse(BaseModel)
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class JobPostingCreate(BaseModel):
    title: str
    description: str
    skills: List[str]
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None

class JobPostingResponse(BaseModel):
    id: int
    employer_id: int
    title: str
    description: str
    skills: List[str]
    location: Optional[str]
    salary_range: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    resume_text: Optional[str] = None
    skills: List[str]
    location: Optional[str] = None
    language: Optional[List[str]] = None
    experience_years: Optional[int] = None

class CandidateResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    skills: List[str]
    location: Optional[str]
    experience_years: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    jd_id: int
    candidate_id: int
    match_score: float
    explanation: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to Talentis.ai API",
        "version": "2.0.0",
        "status": "active",
        "features": [
            "AI-Powered Matching",
            "Bias Audit Logging",
            "ROI Analytics",
            "Interview Management",
            "Payment Processing"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }


# User endpoints
@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user (in production, hash the password!)
    db_user = User(
        email=user.email,
        password_hash=f"hashed_{user.password}",  # TODO: Use proper password hashing
        role=UserRole(user.role)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


# Job posting endpoints
@app.post("/api/jobs", response_model=JobPostingResponse)
async def create_job(job: JobPostingCreate, employer_id: int, db: Session = Depends(get_db)):
    """Create a new job posting"""
    # Verify employer exists
    employer = db.query(User).filter(
        User.id == employer_id,
        User.role == UserRole.EMPLOYER
    ).first()
    
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    db_job = JobDescription(
        employer_id=employer_id,
        title=job.title,
        description=job.description,
        skills=job.skills,
        location=job.location,
        salary_range=job.salary_range,
        job_type=job.job_type,
        experience_required=job.experience_required
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job

@app.get("/api/jobs", response_model=List[JobPostingResponse])
async def get_jobs(
    skip: int = 0, 
    limit: int = 10, 
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all job postings with pagination"""
    query = db.query(JobDescription)
    
    if active_only:
        query = query.filter(JobDescription.is_active == True)
    
    jobs = query.order_by(JobDescription.created_at.desc()).offset(skip).limit(limit).all()
    return jobs

@app.get("/api/jobs/{job_id}", response_model=JobPostingResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


# Candidate endpoints
@app.post("/api/candidates", response_model=CandidateResponse)
async def create_candidate(
    candidate: CandidateCreate, 
    user_id: int,
    db: Session = Depends(get_db)
):
    """Register a new candidate"""
    # Verify user exists and is a candidate
    user = db.query(User).filter(
        User.id == user_id,
        User.role == UserRole.CANDIDATE
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found or not a candidate")
    
    # Check if candidate profile already exists
    existing = db.query(Candidate).filter(Candidate.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Candidate profile already exists")
    
    db_candidate = Candidate(
        user_id=user_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        resume_text=candidate.resume_text,
        skills=candidate.skills,
        location=candidate.location,
        language=candidate.language,
        experience_years=candidate.experience_years
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    return db_candidate

@app.get("/api/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate profile"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return candidate


# AI Matching endpoints
@app.post("/api/ai/match", response_model=List[MatchResponse])
async def create_matches(
    job_id: int,
    min_score: float = 70.0,
    max_results: int = 20,
    db: Session = Depends(get_db)
):
    """
    AI-powered matching between job and candidates
    TODO: Implement actual LangChain AI matching logic
    """
    # Verify job exists
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all candidates
    candidates = db.query(Candidate).all()
    
    matches = []
    for candidate in candidates[:max_results]:
        # Placeholder AI matching score (implement with LangChain)
        # TODO: Implement actual AI matching algorithm
        match_score = 85.5  # Placeholder
        
        # Check if match already exists
        existing_match = db.query(Match).filter(
            Match.jd_id == job_id,
            Match.candidate_id == candidate.id
        ).first()
        
        if not existing_match and match_score >= min_score:
            db_match = Match(
                jd_id=job_id,
                candidate_id=candidate.id,
                match_score=match_score,
                explanation=f"Strong match based on skills and experience",
                skills_match={"matched": job.skills[:2], "missing": [], "additional": []},
                ai_model_version="gpt-4-2024"
            )
            db.add(db_match)
            matches.append(db_match)
    
    if matches:
        db.commit()
        for match in matches:
            db.refresh(match)
    
    return matches

@app.get("/api/matches/job/{job_id}", response_model=List[MatchResponse])
async def get_job_matches(
    job_id: int,
    min_score: float = 0,
    db: Session = Depends(get_db)
):
    """Get all matches for a specific job"""
    matches = db.query(Match).filter(
        Match.jd_id == job_id,
        Match.match_score >= min_score
    ).order_by(Match.match_score.desc()).all()
    
    return matches


# Analytics endpoints
@app.get("/api/analytics/user/{user_id}")
async def get_user_analytics(user_id: int, db: Session = Depends(get_db)):
    """Get analytics for a specific user"""
    analytics = db.query(Analytics).filter(
        Analytics.user_id == user_id
    ).order_by(Analytics.created_at.desc()).first()
    
    if not analytics:
        return {"message": "No analytics data available"}
    
    return {
        "user_id": analytics.user_id,
        "metric_type": analytics.metric_type,
        "roi_metrics": analytics.roi_metrics_json,
        "retention_data": analytics.retention_data,
        "engagement_data": analytics.engagement_data,
        "period": {
            "start": analytics.period_start,
            "end": analytics.period_end
        }
    }


# Bias audit endpoints
@app.get("/api/bias-audit/flagged")
async def get_flagged_audits(db: Session = Depends(get_db)):
    """Get bias audit logs flagged for review"""
    audits = db.query(BiasAuditLog).filter(
        BiasAuditLog.flagged_for_review == True,
        BiasAuditLog.reviewed_at == None
    ).order_by(BiasAuditLog.created_at.desc()).limit(50).all()
    
    return {
        "count": len(audits),
        "audits": [
            {
                "id": audit.id,
                "action_type": audit.action_type,
                "entity_type": audit.entity_type,
                "fairness_score": audit.fairness_score,
                "created_at": audit.created_at
            }
            for audit in audits
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
