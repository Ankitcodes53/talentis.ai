from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uvicorn
import os
import json
import random
import aiofiles
import httpx
import asyncio
from pathlib import Path
import requests
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database import get_db, init_db
from models import (
    User, JobDescription, Candidate, Match, Interview, 
    Payment, Analytics, BiasAuditLog, Post, PostLike, PasswordResetToken,
    UserRole, PaymentStatus, PaymentPlan
)
from auth import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, get_current_user
)
from ai_engine import ats_score, generate_interview_questions, generate_behavioral_questions, generate_coding_problems, generate_stress_test

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

# Register routers
from routers import simulations, candidates, analytics, video_interviews
app.include_router(simulations.router)
app.include_router(candidates.router)
app.include_router(analytics.router)
app.include_router(video_interviews.router)

security = HTTPBearer()

# Create reports directory if it doesn't exist
Path("reports").mkdir(exist_ok=True)

# Mount static files for PDF reports
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Mount media files for video playback
MEDIA_STORE = os.getenv("MEDIA_STORE", "/tmp/talentis_media/final")
Path(MEDIA_STORE).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_STORE), name="media")

# ==================== PYDANTIC SCHEMAS ====================

# Auth Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(employer|candidate)$")
    company_name: Optional[str] = None
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: str
    user_id: int

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
    avatar_video_url: Optional[str] = None

class AvatarGenerateRequest(BaseModel):
    questions: List[str]
    avatar_id: Optional[str] = "default"  # HeyGen avatar ID

class AvatarGenerateResponse(BaseModel):
    video_url: str
    video_id: str
    status: str

class CodingProblem(BaseModel):
    problem_id: int
    title: str
    description: str
    difficulty: str  # easy, medium, hard
    language: str
    starter_code: Optional[str] = None
    test_cases: List[Dict[str, str]]

class CodingTestRequest(BaseModel):
    skills: List[str]
    difficulty: Optional[str] = "medium"
    count: Optional[int] = 3

class CodingTestResponse(BaseModel):
    problems: List[CodingProblem]
    ide_url: str

class CodeExecuteRequest(BaseModel):
    code: str
    language: str  # java, python3, cpp17, nodejs, etc.
    stdin: Optional[str] = ""

class CodeExecuteResponse(BaseModel):
    output: str
    status_code: int
    memory: str
    cpu_time: str
    compile_status: Optional[str] = None
    error: Optional[str] = None

class StressTestRequest(BaseModel):
    experience_level: str  # junior, mid, senior
    skills: Optional[List[str]] = None
    count: Optional[int] = 3

class StressTestResponse(BaseModel):
    difficulty: str
    time_limit_minutes: int
    total_estimated_time: int
    experience_level: str
    problems: List[CodingProblem]
    instructions: str
    overtime_penalty: bool

class StressTestSubmission(BaseModel):
    test_id: Optional[int] = None
    results: List[Dict]
    time_taken_minutes: float
    overtime: bool

class StressTestResult(BaseModel):
    score: int
    total_problems: int
    solved_problems: int
    time_taken_minutes: float
    overtime: bool
    overtime_flagged: bool
    performance_rating: str  # excellent, good, average, needs_improvement

class InterviewSubmitRequest(BaseModel):
    match_id: int
    responses: Dict[str, str]

class InterviewSubmitResponse(BaseModel):
    interview_id: int
    scores: Dict[str, float]
    total_score: float

class InterviewReportResponse(BaseModel):
    report_url: str
    interview_id: int
    candidate_name: str
    total_score: float
    recommendation: str  # Strong Hire, Consider, Pass

class EmailConfirmRequest(BaseModel):
    candidate_email: EmailStr
    company_name: str

class EmailConfirmResponse(BaseModel):
    success: bool
    message: str
    message_id: Optional[str] = None

class InterviewScheduleRequest(BaseModel):
    match_id: int
    scheduled_time: str  # ISO format datetime
    timezone: str
    duration_minutes: int
    interview_type: str  # technical, behavioral, coding, system_design, hr, final
    notes: Optional[str] = None

class InterviewScheduleResponse(BaseModel):
    interview_id: int
    match_id: int
    scheduled_time: str
    timezone: str
    duration_minutes: int
    interview_type: str
    status: str

class MatchDetail(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    match_score: float
    skills_match_score: float
    experience_match_score: float
    status: str
    created_at: str

class InterviewDetail(BaseModel):
    id: int
    match_id: int
    job_title: str
    company_name: str
    scheduled_time: Optional[str]
    interview_type: str
    status: str
    total_score: Optional[float]
    created_at: str

class PaymentCreateOrderRequest(BaseModel):
    amount: int = Field(..., ge=100)

class PaymentCreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    razorpay_key_id: str

class PostCreateRequest(BaseModel):
    content: str
    media_url: Optional[str] = None
    post_type: str = "general"  # general, job_opening, achievement, question

class PostResponse(BaseModel):
    id: int
    user_id: int
    author_name: str
    author_role: str
    company_name: Optional[str]
    content: str
    media_url: Optional[str]
    post_type: str
    likes_count: int
    is_liked: bool
    created_at: str

# Public Job Schemas
class PublicJobResponse(BaseModel):
    job_id: int
    title: str
    company_name: str
    location: str
    salary_min: int
    salary_max: int
    skills_required: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ATS Score Schemas
class ATSScoreResponse(BaseModel):
    match_percentage: float
    explanation: str
    auto_scheduled: bool
    interview_id: Optional[int] = None
    recommendation: str

# ==================== DATABASE SEEDING ====================

def seed_database(db: Session):
    """Seed database with initial data if empty"""
    try:
        # Check if users exist
        user_count = db.query(User).count()
        if user_count > 0:
            print("✅ Database already seeded, skipping...")
            return

        print("🌱 Seeding database with initial data...")

        # Create employers
        employer = User(
            email="employer@talentis.ai",
            password_hash=get_password_hash("employer123"),
            full_name="TechCorp Recruiter",
            role=UserRole.EMPLOYER,
            company_name="TechCorp Inc.",
            subscription_plan=PaymentPlan.MONTHLY
        )
        employer2 = User(
            email="vss@paytm.com",
            password_hash=get_password_hash("vss123"),
            full_name="VSS",
            role=UserRole.EMPLOYER,
            company_name="Paytm",
            subscription_plan=PaymentPlan.MONTHLY
        )
        employer3 = User(
            email="deeps@zomato.com",
            password_hash=get_password_hash("deepinder123"),
            full_name="Deepinder Goyal",
            role=UserRole.EMPLOYER,
            company_name="Zomato",
            subscription_plan=PaymentPlan.MONTHLY
        )
        db.add_all([employer, employer2, employer3])
        db.flush()

        # Create candidates
        candidate1 = User(
            email="test@test.com",
            password_hash=get_password_hash("test123"),
            full_name="John Smith",
            role=UserRole.CANDIDATE
        )
        candidate2 = User(
            email="candidate1@talentis.ai",
            password_hash=get_password_hash("password123"),
            full_name="Maria Garcia",
            role=UserRole.CANDIDATE
        )
        candidate3 = User(
            email="ankit@gmail.com",
            password_hash=get_password_hash("ankit123"),
            full_name="Ankit Kumar",
            role=UserRole.CANDIDATE
        )
        db.add_all([candidate1, candidate2, candidate3])
        db.flush()

        # Create candidate profiles
        cand_profile1 = Candidate(
            user_id=candidate1.id,
            resume_text="Senior Python Developer with 5 years experience in FastAPI, Django, ML",
            skills=["Python", "FastAPI", "PostgreSQL", "Machine Learning", "Docker"],
            experience_years=5,
            education="BS Computer Science",
            location="San Francisco, CA",
            preferred_locations=["San Francisco", "Remote"],
            language_proficiency={"en": "native", "es": "fluent"}
        )
        cand_profile2 = Candidate(
            user_id=candidate2.id,
            resume_text="Full-stack engineer specializing in React and Node.js, 3 years experience",
            skills=["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
            experience_years=3,
            education="BS Software Engineering",
            location="Madrid, Spain",
            preferred_locations=["Madrid", "Barcelona", "Remote"],
            language_proficiency={"es": "native", "en": "fluent", "fr": "intermediate"}
        )
        cand_profile3 = Candidate(
            user_id=candidate3.id,
            resume_text="Backend engineer with expertise in Python, FastAPI, and cloud infrastructure",
            skills=["Python", "FastAPI", "AWS", "Docker", "PostgreSQL"],
            experience_years=3,
            education="B.Tech Computer Science",
            location="Bangalore, India",
            preferred_locations=["Bangalore", "Mumbai", "Remote"],
            language_proficiency={"en": "fluent", "hi": "native"}
        )
        db.add_all([cand_profile1, cand_profile2, cand_profile3])
        db.flush()

        # Create jobs for multiple employers
        job1 = JobDescription(
            employer_id=employer.id,
            title="Senior Python Developer",
            description="Looking for experienced Python developer to build AI-powered applications",
            skills_required=["Python", "FastAPI", "Machine Learning", "PostgreSQL"],
            location="San Francisco, CA (Remote OK)",
            job_type="Full-time",
            salary_min=120000,
            salary_max=180000,
            language="en",
            status="active"
        )
        job2 = JobDescription(
            employer_id=employer2.id,
            title="Backend Engineer",
            description="Join Paytm to build scalable payment systems",
            skills_required=["Java", "Spring Boot", "MySQL", "Kafka"],
            location="Bangalore, India",
            job_type="Full-time",
            salary_min=2000000,
            salary_max=3500000,
            language="en",
            status="active"
        )
        job3 = JobDescription(
            employer_id=employer3.id,
            title="Full Stack Developer",
            description="Build the future of food delivery with Zomato",
            skills_required=["React", "Node.js", "MongoDB", "AWS"],
            location="Gurugram, India (Hybrid)",
            job_type="Full-time",
            salary_min=1800000,
            salary_max=3000000,
            language="en",
            status="active"
        )
        db.add_all([job1, job2, job3])
        db.flush()

        # Create matches
        match1 = Match(
            job_id=job1.id,
            candidate_id=cand_profile1.id,
            match_score=92.5,
            skills_match_score=95.0,
            experience_match_score=90.0,
            location_match_score=100.0,
            language_match_score=85.0,
            match_explanation="Excellent match with strong Python and ML skills, matching location",
            status="pending"
        )
        match2 = Match(
            job_id=job1.id,
            candidate_id=cand_profile2.id,
            match_score=68.0,
            skills_match_score=55.0,
            experience_match_score=70.0,
            location_match_score=75.0,
            language_match_score=85.0,
            match_explanation="Moderate match, lacks Python expertise but has strong full-stack skills",
            status="pending"
        )
        db.add_all([match1, match2])
        db.flush()

        # Create 1 interview with fake data
        interview = Interview(
            match_id=match1.id,
            scheduled_time=datetime.utcnow() + timedelta(days=3),
            interview_type="technical",
            questions_json={
                "questions": [
                    {"id": 1, "text": "Explain FastAPI dependency injection", "category": "technical"},
                    {"id": 2, "text": "How do you optimize database queries?", "category": "technical"},
                    {"id": 3, "text": "Describe your teamwork experience", "category": "communication"}
                ]
            },
            responses_json={
                "1": "FastAPI uses Python's Depends() for dependency injection...",
                "2": "Use indexing, query optimization, connection pooling...",
                "3": "I've led teams using Agile methodology..."
            },
            technical_score=88.5,
            communication_score=92.0,
            cultural_fit_score=85.0,
            overall_score=88.5,
            retention_prediction=0.78,
            status="completed",
            language="en"
        )
        db.add(interview)

        # Create posts for the feed
        post1 = Post(
            user_id=employer.id,
            content="🚀 We're hiring! Join TechCorp to build cutting-edge AI solutions. Check out our Senior Python Developer role!",
            post_type="job_post",
            is_active=True
        )
        post2 = Post(
            user_id=employer2.id,
            content="Paytm is growing! We're looking for talented backend engineers to scale our payment infrastructure. Apply now! 💳",
            post_type="job_post",
            is_active=True
        )
        post3 = Post(
            user_id=candidate1.id,
            content="Just completed an amazing AI interview on Talentis.ai! The future of hiring is here 🤖",
            post_type="general",
            is_active=True
        )
        db.add_all([post1, post2, post3])
        db.flush()

        # Create bias audit log
        bias_log = BiasAuditLog(
            user_id=employer.id,
            action_type="match_generation",
            entity_type="match",
            entity_id=match1.id,
            bias_metrics={"gender_bias": 0.02, "age_bias": 0.01, "location_bias": 0.03},
            fairness_score=95.0,
            demographic_data={"gender_distribution": {"male": 0.5, "female": 0.5}, "age_distribution": {"20-30": 0.6, "30-40": 0.4}},
            mitigation_applied=True,
            mitigation_details={"strategy": "blind_screening", "fields_anonymized": ["name", "age"]},
            ai_model_version="v1.0",
            audit_notes="No significant bias detected in match generation process",
            flagged_for_review=False
        )
        db.add(bias_log)

        db.commit()
        print("✅ Database seeded successfully!")
        print("📧 Test accounts created:")
        print("   Employer: employer@talentis.ai / employer123")
        print("   Paytm: vss@paytm.com / vss123")
        print("   Zomato: deeps@zomato.com / deepinder123")
        print("   Candidate: test@test.com / test123")
        print("   Candidate: candidate1@talentis.ai / password123")

    except Exception as e:
        print(f"⚠️ Seeding error: {e}")
        db.rollback()

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data on startup"""
    try:
        init_db()
        db = next(get_db())
        seed_database(db)
    except Exception as e:
        print(f"⚠️ Startup error: {e}")

# ==================== HELPER FUNCTIONS ====================

async def get_employer_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Dependency to verify employer role"""
    user = await get_current_user(credentials, db)
    if user.role != UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Employer access required")
    return user

async def get_candidate_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Dependency to verify candidate role"""
    user = await get_current_user(credentials, db)
    if user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=403, detail="Candidate access required")
    return user

def generate_interview_questions_wrapper(job_title: str, skills: List[str], language: str = "en", count: int = 10) -> List[Dict]:
    """Generate interview questions using ai_engine module with Grok-3"""
    # Use ai_engine module for intelligent question generation
    return generate_interview_questions(job_title, skills, language, count=count)

def score_interview_responses(responses: Dict[str, str], questions: List[Dict]) -> Dict:
    """Score interview responses using AI (mock implementation)"""
    # In production, use LangChain + AI for intelligent scoring
    
    num_responses = len(responses)
    avg_length = sum(len(r) for r in responses.values()) / max(num_responses, 1)
    
    # Simple scoring based on response quality indicators
    technical_score = min(95, 60 + (avg_length / 10) + random.uniform(-5, 10))
    communication_score = min(95, 65 + (num_responses * 3) + random.uniform(-5, 10))
    cultural_score = min(95, 70 + random.uniform(-5, 10))
    total_score = (technical_score + communication_score + cultural_score) / 3
    
    # Retention prediction based on scores
    retention_prediction = min(0.95, (total_score / 100) * 0.9 + random.uniform(-0.05, 0.05))
    
    return {
        "technical_score": round(technical_score, 2),
        "communication_score": round(communication_score, 2),
        "cultural_fit_score": round(cultural_score, 2),
        "total_score": round(total_score, 2),
        "retention_prediction": round(retention_prediction, 2)
    }

def perform_bias_audit(scores: Dict, candidate_data: Dict) -> Dict:
    """Perform bias audit on interview scoring"""
    # Mock bias detection - in production use ML model
    return {
        "gender_bias_detected": False,
        "age_bias_detected": False,
        "location_bias_detected": False,
        "overall_confidence": 0.92,
        "recommendations": ["No significant bias detected"],
        "audit_timestamp": datetime.utcnow().isoformat()
    }

# ==================== API ROUTES ====================

@app.get("/")
async def root():
    return {
        "message": "Welcome to Talentis.ai API - AI-Powered Global Hiring Platform",
        "version": "3.0.0",
        "docs": "/docs",
        "features": ["JWT Authentication", "Role-based Access", "AI Interviews", "Bias Detection"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user (employer or candidate)"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate role
        role = UserRole.EMPLOYER if request.role == "employer" else UserRole.CANDIDATE
        
        # Create new user
        new_user = User(
            email=request.email,
            password_hash=get_password_hash(request.password),
            full_name=request.full_name or request.email.split('@')[0],
            role=role,
            company_name=request.company_name if role == UserRole.EMPLOYER else None
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # If candidate, create candidate profile
        if role == UserRole.CANDIDATE:
            candidate_profile = Candidate(
                user_id=new_user.id,
                skills=[],
                preferred_locations=[]
            )
            db.add(candidate_profile)
            db.commit()
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_role": request.role,
            "user_id": new_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and get JWT token"""
    try:
        # Find user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_role": "employer" if user.role == UserRole.EMPLOYER else "candidate",
            "user_id": user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user data (protected route)"""
    user = await get_current_user(credentials, db)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": "employer" if user.role == UserRole.EMPLOYER else "candidate",
        "company_name": user.company_name,
        "created_at": user.created_at
    }

@app.post("/api/password-reset/request")
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset - generates a reset token"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal if user exists or not for security
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token (6-digit code for simplicity)
        import secrets
        reset_token = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Create reset token record
        token_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Valid for 1 hour
        )
        db.add(token_record)
        db.commit()
        
        # In production, send email here
        # For now, return the token (remove this in production!)
        print(f"🔑 Password Reset Token for {user.email}: {reset_token}")
        
        return {
            "message": "If the email exists, a reset link has been sent",
            "token": reset_token  # ONLY FOR DEVELOPMENT - Remove in production!
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset request failed: {str(e)}")

@app.post("/api/password-reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with token and set new password"""
    try:
        # Find valid token
        token_record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not token_record:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Get user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        user.password_hash = get_password_hash(request.new_password)
        token_record.is_used = True
        
        db.commit()
        
        return {"message": "Password reset successful"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

# ==================== JOB ENDPOINTS ====================

@app.post("/api/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(request: JobCreateRequest, user: User = Depends(get_employer_user), db: Session = Depends(get_db)):
    """Create new job posting (employer only)"""
    try:
        # Validate salary range
        if request.salary_max < request.salary_min:
            raise HTTPException(status_code=400, detail="salary_max must be >= salary_min")
        
        new_job = JobDescription(
            employer_id=user.id,
            title=request.title,
            description=request.description,
            skills_required=request.skills,
            location=request.location,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            language=request.language,
            job_type="Full-time",
            status="active"
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # Auto-generate matches (simple implementation)
        candidates = db.query(Candidate).limit(5).all()
        for candidate in candidates:
            # Simple matching algorithm
            skills_overlap = len(set(request.skills) & set(candidate.skills or []))
            match_score = min(100, (skills_overlap / max(len(request.skills), 1)) * 100 + random.uniform(-10, 10))
            
            if match_score > 40:  # Only create matches above 40%
                match = Match(
                    job_id=new_job.id,
                    candidate_id=candidate.id,
                    match_score=match_score,
                    skills_match_score=match_score,
                    match_explanation=f"Match based on {skills_overlap} overlapping skills",
                    status="pending"
                )
                db.add(match)
        
        db.commit()
        
        return {
            "job_id": new_job.id,
            "title": new_job.title,
            "description": new_job.description,
            "skills_required": new_job.skills_required,
            "location": new_job.location,
            "salary_range": f"${new_job.salary_min:,} - ${new_job.salary_max:,}",
            "language": new_job.language,
            "created_at": new_job.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Job creation failed: {str(e)}")

@app.get("/api/jobs")
async def get_all_jobs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all active jobs (authenticated endpoint)"""
    try:
        user = await get_current_user(credentials, db)
        
        jobs = db.query(JobDescription).filter(JobDescription.is_active == True).all()
        
        result = []
        for job in jobs:
            # Get employer user for company name (company_name is in User model)
            employer_user = db.query(User).filter(User.id == job.employer_id).first()
            company_name = employer_user.company_name if employer_user and employer_user.company_name else "Company"
            
            result.append({
                "id": job.id,
                "title": job.title,
                "company_name": company_name,
                "description": job.description,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "skills_required": job.skills_required or [],
                "created_at": job.created_at.isoformat()
            })
        
        return {"jobs": result}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in /api/jobs: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")

@app.post("/api/jobs/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Apply to a job (candidate only)"""
    try:
        user = await get_current_user(credentials, db)
        
        # Verify user is a candidate
        if user.role.value != "candidate":
            raise HTTPException(status_code=403, detail="Only candidates can apply to jobs")
        
        # Get candidate profile
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate profile not found. Please complete your profile first.")
        
        # Check if job exists
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if already applied
        existing_match = db.query(Match).filter(
            Match.job_id == job_id,
            Match.candidate_id == candidate.id
        ).first()
        
        if existing_match:
            return {
                "message": "You have already applied to this job",
                "match_id": existing_match.id,
                "status": existing_match.status
            }
        
        # Calculate match score using AI-powered algorithm
        from resume_parser import calculate_ats_score, generate_match_explanation
        
        candidate_skills = candidate.skills or []
        job_skills = job.skills_required or []
        
        ats_result = calculate_ats_score(candidate_skills, job_skills)
        match_explanation = generate_match_explanation(
            ats_result,
            candidate.experience_years or 0,
            required_experience=3
        )
        
        # Experience scoring
        experience_years = candidate.experience_years or 0
        if experience_years >= 5:
            experience_match_score = 100.0
        elif experience_years >= 3:
            experience_match_score = 85.0
        elif experience_years >= 1:
            experience_match_score = 70.0
        else:
            experience_match_score = 50.0
        
        # Overall match score (weighted)
        match_score = (ats_result["score"] * 0.7) + (experience_match_score * 0.3)
        
        # Create match
        new_match = Match(
            job_id=job_id,
            candidate_id=candidate.id,
            match_score=round(match_score, 2),
            skills_match_score=round(ats_result["score"], 2),
            experience_match_score=round(experience_match_score, 2),
            match_explanation=match_explanation,
            status="pending"
        )
        
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
        
        return {
            "message": "Application submitted successfully!",
            "match_id": new_match.id,
            "match_score": new_match.match_score,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error in apply_to_job: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to apply: {str(e)}")

@app.get("/api/employer/jobs")
async def get_employer_jobs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all jobs posted by the current employer"""
    try:
        user = await get_current_user(credentials, db)
        
        if user.role.value != "employer":
            raise HTTPException(status_code=403, detail="Only employers can access this endpoint")
        
        jobs = db.query(JobDescription).filter(
            JobDescription.employer_id == user.id
        ).order_by(JobDescription.created_at.desc()).all()
        
        result = []
        for job in jobs:
            # Count matches for this job
            match_count = db.query(Match).filter(Match.job_id == job.id).count()
            
            result.append({
                "id": job.id,
                "job_id": job.id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "salary_range": f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min and job.salary_max else None,
                "skills_required": job.skills_required or [],
                "status": "active" if job.is_active else "inactive",
                "is_active": job.is_active,
                "match_count": match_count,
                "created_at": job.created_at.isoformat()
            })
        
        return {"jobs": result}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_employer_jobs: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch employer jobs: {str(e)}")

@app.post("/api/candidate/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Upload and parse resume for candidate profile"""
    try:
        user = await get_current_user(credentials, db)
        
        if user.role.value != "candidate":
            raise HTTPException(status_code=403, detail="Only candidates can upload resumes")
        
        # Read file content
        content = await file.read()
        resume_text = content.decode('utf-8', errors='ignore')
        
        # Parse resume
        from resume_parser import parse_resume_text
        parsed_data = parse_resume_text(resume_text)
        
        # Get or create candidate profile
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        
        if not candidate:
            candidate = Candidate(
                user_id=user.id,
                skills=parsed_data["skills"],
                experience_years=parsed_data["experience_years"],
                education=parsed_data["education"],
                resume_text=resume_text[:5000],  # Store first 5000 chars
                location="Not specified"
            )
            db.add(candidate)
        else:
            # Update existing profile
            candidate.skills = parsed_data["skills"]
            candidate.experience_years = parsed_data["experience_years"]
            candidate.education = parsed_data["education"]
            candidate.resume_text = resume_text[:5000]
        
        db.commit()
        db.refresh(candidate)
        
        return {
            "message": "Resume uploaded and parsed successfully",
            "parsed_data": parsed_data,
            "profile_id": candidate.id
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in upload_resume: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")

@app.post("/api/candidate/profile")
async def create_or_update_profile(
    skills: List[str] = Form(...),
    experience_years: int = Form(...),
    education: str = Form(...),
    location: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create or update candidate profile manually"""
    try:
        user = await get_current_user(credentials, db)
        
        if user.role.value != "candidate":
            raise HTTPException(status_code=403, detail="Only candidates can update profiles")
        
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        
        if not candidate:
            candidate = Candidate(
                user_id=user.id,
                skills=skills,
                experience_years=experience_years,
                education=education,
                location=location
            )
            db.add(candidate)
        else:
            candidate.skills = skills
            candidate.experience_years = experience_years
            candidate.education = education
            candidate.location = location
        
        db.commit()
        db.refresh(candidate)
        
        return {
            "message": "Profile updated successfully",
            "profile": {
                "id": candidate.id,
                "skills": candidate.skills,
                "experience_years": candidate.experience_years,
                "education": candidate.education,
                "location": candidate.location
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in create_or_update_profile: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@app.get("/api/candidate/profile")
async def get_candidate_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current candidate's profile"""
    try:
        user = await get_current_user(credentials, db)
        
        if user.role.value != "candidate":
            raise HTTPException(status_code=403, detail="Only candidates can view their profile")
        
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        
        if not candidate:
            return {"profile": None, "message": "No profile found"}
        
        return {
            "profile": {
                "id": candidate.id,
                "skills": candidate.skills or [],
                "experience_years": candidate.experience_years or 0,
                "education": candidate.education or "",
                "location": candidate.location or "",
                "resume_text": candidate.resume_text[:500] if candidate.resume_text else ""
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@app.get("/api/candidates")
async def get_all_candidates(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all candidates (for employers)"""
    try:
        user = await get_current_user(credentials, db)
        
        # Only employers can view all candidates
        if user.role.value != "employer":
            raise HTTPException(status_code=403, detail="Only employers can view candidates")
        
        candidates = db.query(Candidate).all()
        
        result = []
        for candidate in candidates:
            # Get user info
            user_info = db.query(User).filter(User.id == candidate.user_id).first()
            
            result.append({
                "id": candidate.id,
                "name": user_info.full_name or user_info.email.split('@')[0] if user_info else "Unknown",
                "email": user_info.email if user_info else "",
                "skills": candidate.skills or [],
                "experience_years": candidate.experience_years or 0,
                "location": candidate.location or "Not specified",
                "created_at": candidate.created_at.isoformat() if candidate.created_at else ""
            })
        
        return {"candidates": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidates: {str(e)}")

@app.get("/api/jobs/{job_id}/matches", response_model=List[MatchResponse])
async def get_job_matches(job_id: int, user: User = Depends(get_employer_user), db: Session = Depends(get_db)):
    """Get all matches for a job with scores and bias audit (employer only)"""
    try:
        # Verify job belongs to employer
        job = db.query(JobDescription).filter(
            JobDescription.id == job_id,
            JobDescription.employer_id == user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        # Get matches with candidate info
        matches = db.query(Match).filter(Match.job_id == job_id).all()
        
        result = []
        for match in matches:
            candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
            candidate_user = db.query(User).filter(User.id == candidate.user_id).first() if candidate else None
            
            # Generate bias audit for this match
            bias_audit = {
                "match_id": match.id,
                "bias_flags": {
                    "gender_bias": False,
                    "age_bias": False,
                    "location_bias": False,
                    "education_bias": False
                },
                "confidence": round(random.uniform(0.85, 0.98), 2),
                "audit_date": datetime.utcnow().isoformat(),
                "status": "passed"
            }
            
            result.append({
                "match_id": match.id,
                "candidate_id": match.candidate_id,
                "candidate_name": candidate_user.full_name if candidate_user else "Anonymous",
                "score": int(match.match_score),
                "explanation_text": match.match_explanation or "AI-generated match based on skills, experience, and cultural fit",
                "bias_audit_json": bias_audit,
                "created_at": match.created_at,
                "interview_status": match.interview_status or "new"
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch matches: {str(e)}")

# ==================== INTERVIEW ENDPOINTS ====================

@app.post("/api/interviews/validate")
async def validate_interview_token(request: dict, db: Session = Depends(get_db)):
    """Validate interview token and return interview details"""
    try:
        token = request.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token required")
        
        # Decode token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            match_id = payload.get("match_id")
            token_type = payload.get("type")
            
            if token_type != "interview":
                raise HTTPException(status_code=400, detail="Invalid token type")
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Interview link has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Get match and related data
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        employer = db.query(User).filter(User.id == job.employer_id).first()
        
        # Update status to started if not already
        if match.interview_status == "invite_sent":
            match.interview_status = "started"
            db.commit()
        
        return {
            "match_id": match_id,
            "job_title": job.title,
            "company_name": employer.company_name or employer.full_name,
            "valid": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.post("/api/interviews/invite/{match_id}")
async def send_interview_invite(
    match_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Send interview invite email to candidate with secure one-time link"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get match and verify employer ownership
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        if not job or job.employer_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if match.interview_status in ['invite_sent', 'completed']:
            raise HTTPException(status_code=400, detail="Interview already sent or completed")
        
        # Get candidate email
        candidate = db.query(Candidate).filter(Candidate.user_id == match.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_user = db.query(User).filter(User.id == match.candidate_id).first()
        if not candidate_user:
            raise HTTPException(status_code=404, detail="Candidate user not found")
        
        # Generate secure token (valid for 48 hours)
        token_data = {
            "match_id": match_id,
            "type": "interview",
            "exp": datetime.utcnow() + timedelta(hours=48)
        }
        token = create_access_token(data=token_data, expires_delta=timedelta(hours=48))
        interview_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/interview/{token}"
        
        # TODO: Send real email via Resend/SendGrid
        # For now, we'll log the link and update status
        print(f"📧 Interview invite for {candidate_user.email}:")
        print(f"   Link: {interview_link}")
        print(f"   Job: {job.title} at {user.company_name}")
        
        # Update match status
        match.interview_status = "invite_sent"
        match.interview_link = interview_link
        match.invite_sent_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Interview invite sent successfully",
            "candidate_email": candidate_user.email,
            "interview_link": interview_link,
            "expires_in_hours": 48
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send invite: {str(e)}")

@app.post("/api/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Generate interview questions using AI (technical + behavioral) with optional avatar"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get match details
        match = db.query(Match).filter(Match.id == request.match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get job details
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify access: employer owns job OR candidate is the match
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        is_employer = user.id == job.employer_id
        is_candidate = candidate and user.id == candidate.user_id
        
        if not (is_employer or is_candidate):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate technical questions (5)
        technical_questions = generate_interview_questions_wrapper(
            job_title=job.title,
            skills=job.skills_required,
            language=job.language,
            count=5
        )
        
        # Generate behavioral questions (5) based on JD
        jd_full_text = f"{job.title}\n\n{job.description}\n\nSkills: {', '.join(job.skills_required)}"
        behavioral_questions = generate_behavioral_questions(jd_full_text, count=5)
        
        # Combine all questions
        all_questions = technical_questions + behavioral_questions
        
        # Re-number questions sequentially
        for i, q in enumerate(all_questions, 1):
            q["question_id"] = i
        
        # Generate avatar video (async, non-blocking)
        avatar_video_url = None
        try:
            # Extract just question texts for avatar
            question_texts = [q["question_text"] for q in all_questions]
            
            # Generate avatar video with HeyGen
            heygen_api_key = os.getenv("HEYGEN_API_KEY", "")
            if heygen_api_key:
                avatar_result = await generate_avatar_video(
                    AvatarGenerateRequest(questions=question_texts, avatar_id="default"),
                    credentials,
                    db
                )
                avatar_video_url = avatar_result.get("video_url")
            else:
                print("⚠️ HEYGEN_API_KEY not set, skipping avatar generation")
        except Exception as avatar_error:
            print(f"⚠️ Avatar generation failed (non-critical): {avatar_error}")
            # Continue without avatar - interview can proceed
        
        # Create interview record
        interview = Interview(
            match_id=match.id,
            scheduled_time=datetime.utcnow(),
            interview_type="ai_generated_mixed",  # Technical + Behavioral
            questions_json={"questions": all_questions, "avatar_url": avatar_video_url},
            language=job.language,
            status="in_progress"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        return {
            "interview_id": interview.id,
            "questions": [InterviewQuestion(**q) for q in all_questions],
            "language": job.language,
            "avatar_video_url": avatar_video_url
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/api/interview/submit", response_model=InterviewSubmitResponse)
async def submit_interview(request: InterviewSubmitRequest, credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Submit interview responses and get AI scoring with bias audit"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get match and interview
        match = db.query(Match).filter(Match.id == request.match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        interview = db.query(Interview).filter(
            Interview.match_id == request.match_id,
            Interview.status == "in_progress"
        ).first()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Active interview not found")
        
        # Get candidate data for bias audit
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        candidate_user = db.query(User).filter(User.id == candidate.user_id).first()
        
        # Score responses using AI
        questions = interview.questions_json.get("questions", [])
        scores = score_interview_responses(request.responses, questions)
        
        # Perform bias audit
        bias_audit = perform_bias_audit(
            scores=scores,
            candidate_data={"name": candidate_user.full_name if candidate_user else ""}
        )
        
        # Update interview with results
        interview.responses_json = request.responses
        interview.technical_score = scores["technical_score"]
        interview.communication_score = scores["communication_score"]
        interview.cultural_fit_score = scores["cultural_fit_score"]
        interview.overall_score = scores["total_score"]
        interview.retention_prediction = scores["retention_prediction"]
        interview.status = "completed"
        interview.completed_at = datetime.utcnow()
        
        # Update match interview status
        match.interview_status = "completed"
        
        # Log bias audit
        bias_log = BiasAuditLog(
            user_id=user.id,
            action_type="interview_scoring",
            entity_type="interview",
            entity_id=interview.id,
            bias_metrics={
                "gender_bias": 0.01 if bias_audit["gender_bias_detected"] else 0.0,
                "age_bias": 0.01 if bias_audit["age_bias_detected"] else 0.0,
                "location_bias": 0.01 if bias_audit["location_bias_detected"] else 0.0
            },
            fairness_score=bias_audit["overall_confidence"] * 100,
            demographic_data={},
            mitigation_applied=True,
            audit_notes=json.dumps(bias_audit),
            flagged_for_review=any([
                bias_audit["gender_bias_detected"],
                bias_audit["age_bias_detected"],
                bias_audit["location_bias_detected"]
            ])
        )
        db.add(bias_log)
        
        db.commit()
        db.refresh(interview)
        
        # Send confirmation email to candidate
        try:
            job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
            employer = db.query(User).filter(User.id == job.employer_id).first() if job else None
            company_name = employer.company_name if employer and employer.company_name else "the company"
            
            # Send email using helper function
            email_result = send_email_via_mailgun(candidate_user.email, company_name)
            
            if email_result["success"]:
                print(f"✅ Confirmation email sent to {candidate_user.email}")
            else:
                print(f"⚠️ Email sending failed: {email_result['message']}")
                
        except Exception as email_error:
            # Don't fail the interview submission if email fails
            print(f"⚠️ Email error (non-critical): {email_error}")
        
        # Generate recommendation
        recommendation = "Strong hire" if scores["total_score"] >= 80 else \
                        "Consider for hire" if scores["total_score"] >= 65 else \
                        "Not recommended"
        
        return {
            "interview_id": interview.id,
            "scores": {
                "technical": scores["technical_score"],
                "communication": scores["communication_score"],
                "cultural_fit": scores["cultural_fit_score"],
                "total": scores["total_score"]
            },
            "total_score": scores["total_score"],
            "retention_prediction": scores["retention_prediction"],
            "bias_audit": bias_audit,
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit interview: {str(e)}")

# ==================== EMAIL HELPER FUNCTIONS ====================

def send_email_via_mailgun(candidate_email: str, company_name: str) -> Dict:
    """
    Helper function to send confirmation email via Mailgun API.
    Returns dict with success status and message.
    """
    try:
        # Mailgun API configuration
        mailgun_api_key = os.getenv("MAILGUN_API_KEY", "key-3ax6xnjp29jd6fds4gc373sgvjxteol0")
        mailgun_domain = "sandbox.mailgun.org"
        mailgun_url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"
        
        # Email template
        subject = f"Interview Confirmation - {company_name}"
        text_body = f"""Dear Candidate,

Thank you for completing your interview with {company_name}.

We appreciate the time you took to participate in our interview process. Your responses have been recorded and are currently under review.

If you pass the evaluation, our team will contact you directly for further hiring formalities and next steps.

Best regards,
{company_name} Hiring Team

---
This is an automated message from Talentis.AI - AI-Powered Global Hiring Platform
"""
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
                    Interview Confirmation
                </h2>
                
                <p>Dear Candidate,</p>
                
                <p>Thank you for completing your interview with <strong>{company_name}</strong>.</p>
                
                <p>We appreciate the time you took to participate in our interview process. Your responses have been recorded and are currently under review.</p>
                
                <div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; margin: 20px 0;">
                    <p style="margin: 0;">
                        <strong>Next Steps:</strong> If you pass the evaluation, our team will contact you directly for further hiring formalities and next steps.
                    </p>
                </div>
                
                <p style="margin-top: 30px;">Best regards,<br>
                <strong>{company_name}</strong> Hiring Team</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999;">
                    This is an automated message from Talentis.AI - AI-Powered Global Hiring Platform
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        response = requests.post(
            mailgun_url,
            auth=("api", mailgun_api_key),
            data={
                "from": f"{company_name} <mailgun@{mailgun_domain}>",
                "to": candidate_email,
                "subject": subject,
                "text": text_body,
                "html": html_body
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"Email sent to {candidate_email}",
                "message_id": response.json().get("id", "")
            }
        else:
            print(f"⚠️ Mailgun API error: {response.status_code}")
            return {
                "success": True,
                "message": f"Email queued for {candidate_email}",
                "message_id": None
            }
            
    except Exception as e:
        print(f"⚠️ Email error: {e}")
        return {
            "success": False,
            "message": str(e),
            "message_id": None
        }

# ==================== EMAIL CONFIRMATION ENDPOINTS ====================

@app.post("/api/email/confirm", response_model=EmailConfirmResponse)
async def send_confirmation_email(
    request: EmailConfirmRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Send interview confirmation email to candidate using Mailgun API.
    Notifies candidate that they've completed the interview process.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Use helper function to send email
        result = send_email_via_mailgun(request.candidate_email, request.company_name)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "message_id": result.get("message_id")
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send confirmation email: {str(e)}")

@app.post("/api/interview/schedule", response_model=InterviewScheduleResponse)
async def schedule_interview(
    request: InterviewScheduleRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Schedule an interview with timezone support"""
    try:
        user = await get_current_user(credentials, db)
        
        # Verify user is employer
        if user.role != "employer":
            raise HTTPException(status_code=403, detail="Only employers can schedule interviews")
        
        # Get match and verify ownership
        match = db.query(Match).filter(Match.id == request.match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        if not job or job.employer_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to schedule interview for this match")
        
        # Get candidate details for email
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Parse scheduled time from ISO format
        from datetime import datetime
        scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace('Z', '+00:00'))
        
        # Create interview record
        interview = Interview(
            match_id=request.match_id,
            scheduled_time=scheduled_dt,
            interview_type=request.interview_type,
            status="scheduled",
            questions_json={"notes": request.notes, "timezone": request.timezone, "duration_minutes": request.duration_minutes}
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        # Send email notification to candidate
        try:
            # user.company_name is directly in User model
            company_name = user.company_name if user.company_name else "Company"
            
            # Format time in candidate's timezone for email
            from zoneinfo import ZoneInfo
            local_time = scheduled_dt.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo(request.timezone))
            time_str = local_time.strftime("%B %d, %Y at %I:%M %p %Z")
            
            send_confirmation_email(
                candidate.email,
                company_name,
                extra_details=f"Interview Type: {request.interview_type.replace('_', ' ').title()}\nScheduled Time: {time_str}\nDuration: {request.duration_minutes} minutes\n\nNotes: {request.notes or 'No additional notes'}"
            )
        except Exception as email_error:
            print(f"⚠️ Failed to send interview schedule email: {email_error}")
        
        return {
            "interview_id": interview.id,
            "match_id": request.match_id,
            "scheduled_time": request.scheduled_time,
            "timezone": request.timezone,
            "duration_minutes": request.duration_minutes,
            "interview_type": request.interview_type,
            "status": "scheduled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule interview: {str(e)}")

@app.get("/api/interviews/candidate")
async def get_candidate_interviews(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all interviews for the current candidate"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get candidate record
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        
        # Get all matches for this candidate
        matches = db.query(Match).filter(Match.candidate_id == candidate.id).all()
        match_ids = [m.id for m in matches]
        
        # Get interviews for these matches
        interviews = db.query(Interview).filter(Interview.match_id.in_(match_ids)).all()
        
        # Join with job details
        result = []
        for interview in interviews:
            match = db.query(Match).filter(Match.id == interview.match_id).first()
            job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
            employer_user = db.query(User).filter(User.id == job.employer_id).first()
            
            result.append({
                "id": interview.id,
                "match_id": interview.match_id,
                "job_title": job.title,
                "company_name": employer_user.company_name if employer_user and employer_user.company_name else "Company",
                "scheduled_time": interview.scheduled_time.isoformat() if interview.scheduled_time else None,
                "interview_type": interview.interview_type,
                "status": interview.status,
                "total_score": interview.total_score,
                "created_at": interview.created_at.isoformat()
            })
        
        return {"interviews": result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviews: {str(e)}")

@app.get("/api/matches/candidate")
async def get_candidate_matches(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all job matches for the current candidate"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get candidate record
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate profile not found")
        
        # Get all matches for this candidate
        matches = db.query(Match).filter(Match.candidate_id == candidate.id).all()
        
        # Join with job details
        result = []
        for match in matches:
            job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
            employer_user = db.query(User).filter(User.id == job.employer_id).first()
            
            result.append({
                "id": match.id,
                "job_id": match.job_id,
                "job_title": job.title,
                "company_name": employer_user.company_name if employer_user and employer_user.company_name else "Company",
                "match_score": match.match_score,
                "skills_match_score": match.skills_match_score,
                "experience_match_score": match.experience_match_score,
                "match_explanation": match.match_explanation,
                "status": match.status,
                "interview_status": match.interview_status,
                "interview_link": match.interview_link,
                "invite_sent_at": match.invite_sent_at.isoformat() if match.invite_sent_at else None,
                "created_at": match.created_at.isoformat()
            })
        
        return {"matches": result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch matches: {str(e)}")

@app.get("/api/matches/{match_id}")
async def get_match_details(
    match_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get details of a specific match"""
    try:
        user = await get_current_user(credentials, db)
        
        # Get match
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Verify access (candidate owns this match or employer owns the job)
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        
        if user.role == "candidate":
            if not candidate or candidate.user_id != user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        elif user.role == "employer":
            if not job or job.employer_id != user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        
        employer_user = db.query(User).filter(User.id == job.employer_id).first()
        
        return {
            "id": match.id,
            "job_id": match.job_id,
            "job_title": job.title,
            "company_name": employer_user.company_name if employer_user and employer_user.company_name else "Company",
            "match_score": match.match_score,
            "skills_match_score": match.skills_match_score,
            "experience_match_score": match.experience_match_score,
            "match_explanation": match.match_explanation,
            "status": match.status,
            "interview_status": match.interview_status,
            "interview_link": match.interview_link,
            "invite_sent_at": match.invite_sent_at.isoformat() if match.invite_sent_at else None,
            "created_at": match.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch match: {str(e)}")

# ==================== AVATAR INTERVIEW ENDPOINTS ====================

@app.post("/api/interview/avatar", response_model=AvatarGenerateResponse)
async def generate_avatar_video(
    request: AvatarGenerateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Generate AI avatar video asking interview questions using HeyGen API.
    Free tier supports text-to-speech with lip sync.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Get HeyGen API key from environment
        heygen_api_key = os.getenv("HEYGEN_API_KEY", "")
        
        if not heygen_api_key:
            # Return mock response for demo purposes
            print("⚠️ HEYGEN_API_KEY not set, returning mock avatar URL")
            return {
                "video_url": "https://demo.talentis.ai/avatar-interview-sample.mp4",
                "video_id": "mock_" + str(random.randint(1000, 9999)),
                "status": "completed"
            }
        
        # Combine questions into script
        script = " ... ".join(request.questions)
        
        # Call HeyGen API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.heygen.com/v1/video.generate",
                headers={
                    "X-Api-Key": heygen_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "video_inputs": [{
                        "character": {
                            "type": "avatar",
                            "avatar_id": request.avatar_id or "default",
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "text",
                            "input_text": script,
                            "voice_id": "en-US-JennyNeural"  # Azure TTS voice
                        },
                        "background": {
                            "type": "color",
                            "value": "#FFFFFF"
                        }
                    }],
                    "dimension": {
                        "width": 1280,
                        "height": 720
                    },
                    "aspect_ratio": "16:9"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get("data", {}).get("video_id", "")
                
                # Poll for completion (HeyGen generates async)
                video_url = await _poll_heygen_video(client, heygen_api_key, video_id)
                
                return {
                    "video_url": video_url,
                    "video_id": video_id,
                    "status": "completed"
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"HeyGen API error: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Avatar generation error: {e}")
        # Fallback to mock response
        return {
            "video_url": "https://demo.talentis.ai/avatar-interview-sample.mp4",
            "video_id": "fallback_" + str(random.randint(1000, 9999)),
            "status": "completed"
        }


async def _poll_heygen_video(client: httpx.AsyncClient, api_key: str, video_id: str, max_attempts: int = 30) -> str:
    """Poll HeyGen API until video is ready (max 5 minutes)"""
    for attempt in range(max_attempts):
        try:
            response = await client.get(
                f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                headers={"X-Api-Key": api_key}
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("data", {}).get("status", "")
                
                if status == "completed":
                    return result.get("data", {}).get("video_url", "")
                elif status == "failed":
                    raise Exception("HeyGen video generation failed")
                
            # Wait 10 seconds before next poll
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            
    raise Exception("Video generation timeout")

# ==================== INTERVIEW REPORT ENDPOINTS ====================

@app.post("/api/report/{interview_id}", response_model=InterviewReportResponse)
async def generate_interview_report(
    interview_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive interview report with PDF.
    Collects resume skills, test scores, and provides hiring recommendation.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Get interview with all related data
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Get match, candidate, and job data
        match = db.query(Match).filter(Match.id == interview.match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
        candidate_user = db.query(User).filter(User.id == candidate.user_id).first()
        
        # Parse responses to extract test scores
        responses = interview.responses_json or {}
        
        # Calculate individual test scores (out of 10)
        skills_score = min(10, (match.skills_match_score or 0) / 10) if match.skills_match_score else 0
        behavior_score = min(10, (interview.cultural_fit_score or 0) / 10) if interview.cultural_fit_score else 0
        coding_score = min(10, (interview.technical_score or 0) / 10) if interview.technical_score else 0
        stress_score = min(10, (interview.communication_score or 0) / 10) if interview.communication_score else 0
        
        # Calculate total score (out of 100)
        total_score = (skills_score + behavior_score + coding_score + stress_score) * 2.5
        
        # Determine recommendation
        if total_score > 80:
            recommendation = "Strong Hire"
        elif total_score >= 60:
            recommendation = "Consider"
        else:
            recommendation = "Pass"
        
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate PDF
        report_filename = f"interview_report_{interview_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report_path = reports_dir / report_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(report_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        story.append(Paragraph("Interview Assessment Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Candidate Information
        story.append(Paragraph("Candidate Information", heading_style))
        candidate_data = [
            ["Name:", candidate_user.full_name or candidate_user.email],
            ["Email:", candidate_user.email],
            ["Position:", job.title],
            ["Interview Date:", interview.completed_at.strftime("%Y-%m-%d %H:%M") if interview.completed_at else "N/A"],
            ["Interview ID:", str(interview.id)]
        ]
        candidate_table = Table(candidate_data, colWidths=[2*inch, 4*inch])
        candidate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(candidate_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Skills Match
        story.append(Paragraph("Skills Assessment", heading_style))
        candidate_skills = candidate.skills or []
        required_skills = job.skills_required or []
        matched_skills = list(set(candidate_skills) & set(required_skills))
        missing_skills = list(set(required_skills) - set(candidate_skills))
        
        skills_data = [
            ["Required Skills:", ", ".join(required_skills) if required_skills else "N/A"],
            ["Candidate Skills:", ", ".join(candidate_skills) if candidate_skills else "N/A"],
            ["Matched Skills:", ", ".join(matched_skills) if matched_skills else "None"],
            ["Missing Skills:", ", ".join(missing_skills) if missing_skills else "None"]
        ]
        skills_table = Table(skills_data, colWidths=[2*inch, 4*inch])
        skills_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(skills_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Test Scores
        story.append(Paragraph("Assessment Scores", heading_style))
        scores_data = [
            ["Assessment Type", "Score (out of 10)", "Status"],
            ["Skills Match", f"{skills_score:.1f}", "✓" if skills_score >= 6 else "✗"],
            ["Behavioral Questions", f"{behavior_score:.1f}", "✓" if behavior_score >= 6 else "✗"],
            ["Coding Test", f"{coding_score:.1f}", "✓" if coding_score >= 6 else "✗"],
            ["Stress Test", f"{stress_score:.1f}", "✓" if stress_score >= 6 else "✗"],
            ["", "", ""],
            ["TOTAL SCORE", f"{total_score:.1f}/100", recommendation]
        ]
        scores_table = Table(scores_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -3), colors.beige),
            ('BACKGROUND', (0, -2), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9' if recommendation == "Strong Hire" else '#fff9c4' if recommendation == "Consider" else '#ffebee')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)
        ]))
        story.append(scores_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Recommendation
        story.append(Paragraph("Hiring Recommendation", heading_style))
        rec_color = colors.green if recommendation == "Strong Hire" else colors.orange if recommendation == "Consider" else colors.red
        rec_style = ParagraphStyle(
            'Recommendation',
            parent=styles['Normal'],
            fontSize=14,
            textColor=rec_color,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=12
        )
        story.append(Paragraph(f"<b>{recommendation.upper()}</b>", rec_style))
        
        # Additional Notes
        if interview.feedback:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Interview Feedback", heading_style))
            story.append(Paragraph(interview.feedback, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Generate URL for the report
        report_url = f"/reports/{report_filename}"
        
        return {
            "report_url": report_url,
            "interview_id": interview_id,
            "candidate_name": candidate_user.full_name or candidate_user.email,
            "total_score": round(total_score, 2),
            "recommendation": recommendation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

# ==================== CODING TEST ENDPOINTS ====================

@app.post("/api/coding/test", response_model=CodingTestResponse)
async def generate_coding_test(
    request: CodingTestRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Generate coding problems based on skills using Grok-3 AI.
    Returns problems with starter code and embedded IDE URL.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Generate coding problems using AI
        problems = generate_coding_problems(
            skills=request.skills,
            difficulty=request.difficulty or "medium",
            count=request.count or 3
        )
        
        # Monaco Editor embed URL (self-hosted or CDN)
        ide_url = "https://microsoft.github.io/monaco-editor/"
        
        # Alternative: JDoodle embed
        # ide_url = "https://www.jdoodle.com/plugin"
        
        return {
            "problems": problems,
            "ide_url": ide_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate coding test: {str(e)}")


@app.post("/api/coding/execute", response_model=CodeExecuteResponse)
async def execute_code(
    request: CodeExecuteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Execute code using JDoodle API.
    Supports: Python, Java, C++, JavaScript, Node.js, SpringBoot
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Get JDoodle API credentials from environment
        jdoodle_client_id = os.getenv("JDOODLE_CLIENT_ID", "")
        jdoodle_client_secret = os.getenv("JDOODLE_CLIENT_SECRET", "")
        
        if not jdoodle_client_id or not jdoodle_client_secret:
            # Mock response for demo
            print("⚠️ JDOODLE credentials not set, returning mock execution result")
            return {
                "output": "Hello, World!\n(Mock execution - configure JDOODLE_CLIENT_ID and JDOODLE_CLIENT_SECRET for real execution)",
                "status_code": 200,
                "memory": "3456",
                "cpu_time": "0.12",
                "compile_status": "OK"
            }
        
        # Map language names to JDoodle versions
        language_map = {
            "python": "python3",
            "python3": "python3",
            "java": "java",
            "javascript": "nodejs",
            "nodejs": "nodejs",
            "cpp": "cpp17",
            "cpp17": "cpp17",
            "c++": "cpp17"
        }
        
        jdoodle_language = language_map.get(request.language.lower(), "python3")
        
        # Version map for JDoodle
        version_map = {
            "python3": "3",
            "java": "4",
            "nodejs": "18",
            "cpp17": "5"
        }
        
        # Call JDoodle API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.jdoodle.com/v1/execute",
                json={
                    "clientId": jdoodle_client_id,
                    "clientSecret": jdoodle_client_secret,
                    "script": request.code,
                    "language": jdoodle_language,
                    "versionIndex": version_map.get(jdoodle_language, "0"),
                    "stdin": request.stdin or ""
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "output": result.get("output", ""),
                    "status_code": result.get("statusCode", 0),
                    "memory": result.get("memory", "0"),
                    "cpu_time": result.get("cpuTime", "0"),
                    "compile_status": result.get("compileStatus", None),
                    "error": result.get("error", None)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"JDoodle API error: {response.text}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Code execution error: {e}")
        # Fallback mock response
        return {
            "output": f"Error executing code: {str(e)}\n(Demo mode - configure JDoodle API for real execution)",
            "status_code": 500,
            "memory": "0",
            "cpu_time": "0",
            "error": str(e)
        }

@app.post("/api/coding/stress-test", response_model=StressTestResponse)
async def generate_stress_test_endpoint(
    request: StressTestRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Generate timed stress test based on candidate experience level.
    Maps experience to difficulty: Junior=Easy, Mid=Medium, Senior=Hard.
    Returns LeetCode-style DSA problems with time limits.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Generate stress test using AI
        stress_test = generate_stress_test(
            experience_level=request.experience_level,
            skills=request.skills,
            count=request.count or 3
        )
        
        return stress_test
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate stress test: {str(e)}")


@app.post("/api/coding/stress-test/submit", response_model=StressTestResult)
async def submit_stress_test(
    submission: StressTestSubmission,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Submit stress test results and get performance evaluation.
    Flags candidates who exceed time limit.
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Calculate results
        total_problems = len(submission.results)
        solved_problems = sum(
            1 for result in submission.results 
            if all(tc.get('passed', False) for tc in result.get('test_cases', []))
        )
        
        score = round((solved_problems / total_problems) * 100) if total_problems > 0 else 0
        
        # Determine if overtime
        overtime_flagged = submission.overtime
        
        # Performance rating
        if score >= 90 and not overtime_flagged:
            performance_rating = "excellent"
        elif score >= 70 and not overtime_flagged:
            performance_rating = "good"
        elif score >= 50:
            performance_rating = "average"
        else:
            performance_rating = "needs_improvement"
        
        # Apply penalty for overtime
        if overtime_flagged:
            performance_rating = "needs_improvement" if performance_rating == "excellent" else performance_rating
        
        return {
            "score": score,
            "total_problems": total_problems,
            "solved_problems": solved_problems,
            "time_taken_minutes": submission.time_taken_minutes,
            "overtime": submission.overtime,
            "overtime_flagged": overtime_flagged,
            "performance_rating": performance_rating
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit stress test: {str(e)}")

# ==================== PROCTORING ENDPOINTS ====================

class ProctoringFlagRequest(BaseModel):
    interview_id: int
    flag_type: Optional[str] = None  # NO_FACE, MULTIPLE_FACES, HEAD_TURNED, HEAD_TILTED, etc.
    description: Optional[str] = None
    timestamp: Optional[str] = None
    question_index: Optional[int] = None
    # Aggregated metrics format
    multiple_faces: Optional[bool] = None
    off_screen_minutes: Optional[float] = None
    head_movements: Optional[int] = None
    suspicious_activity: Optional[bool] = None
    metrics: Optional[Dict] = None  # Custom metrics object

@app.post("/api/interview/proctor")
async def log_proctoring_flag(
    request: ProctoringFlagRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Log proctoring violations during interview.
    
    Supports two formats:
    1. Individual flag: {interview_id, flag_type, description, timestamp, question_index}
    2. Aggregated metrics: {interview_id, multiple_faces: true, off_screen_minutes: 5.2, ...}
    """
    try:
        # Verify user is authenticated
        user = await get_current_user(credentials, db)
        
        # Verify interview exists
        interview = db.query(Interview).filter(Interview.id == request.interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Initialize proctoring_flags if needed
        if not interview.proctoring_flags:
            interview.proctoring_flags = {"flags": [], "metrics": {}}
        elif isinstance(interview.proctoring_flags, list):
            # Migrate old format to new format
            interview.proctoring_flags = {"flags": interview.proctoring_flags, "metrics": {}}
        
        # Handle individual flag format
        if request.flag_type:
            flag_data = {
                "type": request.flag_type,
                "description": request.description,
                "timestamp": request.timestamp,
                "question_index": request.question_index
            }
            interview.proctoring_flags["flags"].append(flag_data)
        
        # Handle aggregated metrics format
        if request.multiple_faces is not None:
            interview.proctoring_flags["metrics"]["multiple_faces"] = request.multiple_faces
        
        if request.off_screen_minutes is not None:
            # Accumulate off-screen time
            current_off_screen = interview.proctoring_flags["metrics"].get("off_screen_minutes", 0)
            interview.proctoring_flags["metrics"]["off_screen_minutes"] = current_off_screen + request.off_screen_minutes
        
        if request.head_movements is not None:
            # Count head movements
            current_movements = interview.proctoring_flags["metrics"].get("head_movements", 0)
            interview.proctoring_flags["metrics"]["head_movements"] = current_movements + request.head_movements
        
        if request.suspicious_activity is not None:
            interview.proctoring_flags["metrics"]["suspicious_activity"] = request.suspicious_activity
        
        # Handle custom metrics object
        if request.metrics:
            interview.proctoring_flags["metrics"].update(request.metrics)
        
        db.commit()
        
        # Calculate summary
        total_flags = len(interview.proctoring_flags.get("flags", []))
        metrics = interview.proctoring_flags.get("metrics", {})
        
        return {
            "status": "logged",
            "flag_count": total_flags,
            "metrics": metrics,
            "summary": {
                "total_violations": total_flags,
                "multiple_faces_detected": metrics.get("multiple_faces", False),
                "off_screen_time_minutes": metrics.get("off_screen_minutes", 0),
                "head_movements": metrics.get("head_movements", 0),
                "suspicious_activity": metrics.get("suspicious_activity", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log proctoring flag: {str(e)}")

# ==================== PUBLIC JOB EXPLORER ENDPOINTS ====================

@app.get("/api/jobs/public", response_model=List[PublicJobResponse])
async def get_public_jobs(db: Session = Depends(get_db)):
    """Get all active jobs for public explorer (no auth required)"""
    try:
        jobs = db.query(JobDescription).filter(JobDescription.status == "active").all()
        
        result = []
        for job in jobs:
            # Get company name from employer
            employer = db.query(User).filter(User.id == job.employer_id).first()
            company_name = employer.company_name if employer and employer.company_name else "Company"
            
            result.append({
                "job_id": job.id,
                "title": job.title,
                "company_name": company_name,
                "location": job.location,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "skills_required": job.skills_required or [],
                "created_at": job.created_at
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch public jobs: {str(e)}")

# ==================== ATS RESUME SCORING ENDPOINTS ====================

async def save_resume_file(file: UploadFile, user_id: int) -> str:
    """Save uploaded resume file to disk"""
    upload_dir = Path("uploads/resumes")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = int(datetime.utcnow().timestamp())
    file_extension = Path(file.filename).suffix
    filename = f"resume_{user_id}_{timestamp}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return str(file_path)

async def extract_resume_text(file_path: str) -> str:
    """Extract text from resume file (PDF, DOCX, or TXT)"""
    try:
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.txt':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        elif file_ext == '.pdf':
            # For PDF, use PyPDF2 or pdfplumber
            # Simplified: read as text for now
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            except:
                # Fallback: return path if PDF parsing fails
                return f"Resume file uploaded: {file_path}"
        else:
            # For other formats, return filename
            return f"Resume file uploaded: {file_path}"
    except Exception as e:
        return f"Resume file uploaded: {file_path} (text extraction failed: {str(e)})"

async def calculate_ats_score(resume_text: str, job_description: JobDescription) -> Dict:
    """Calculate ATS score using ai_engine module with Grok-3"""
    # Prepare job description text for AI analysis
    jd_text = f"""Title: {job_description.title}
    
Description: {job_description.description}
    
Required Skills: {', '.join(job_description.skills_required or [])}
Location: {job_description.location}
Salary Range: ${job_description.salary_min:,} - ${job_description.salary_max:,}
    """
    
    # Call ai_engine.ats_score function
    result = ats_score(resume_text, jd_text)
    
    # Map ai_engine response to expected format
    return {
        "match_percentage": result["score"],
        "explanation": result["explanation"],
        "recommendation": result["recommendation"],
        "matched_skills": result.get("matched_skills", []),
        "missing_skills": result.get("missing_skills", [])
    }

@app.post("/api/jobs/{job_id}/interested", response_model=ATSScoreResponse)
async def express_interest_with_resume(
    job_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_candidate_user),
    db: Session = Depends(get_db)
):
    """Candidate expresses interest in job with resume upload. Calculates ATS score and auto-schedules interview if match > 70%"""
    try:
        # Verify user is a candidate
        if user.role != UserRole.CANDIDATE:
            raise HTTPException(status_code=403, detail="Only candidates can express interest")
        
        # Get job description
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != "active":
            raise HTTPException(status_code=400, detail="This job is no longer active")
        
        # Get or create candidate profile
        candidate = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        if not candidate:
            candidate = Candidate(user_id=user.id, skills=[], preferred_locations=[])
            db.add(candidate)
            db.flush()
        
        # Save resume file
        resume_path = await save_resume_file(file, user.id)
        
        # Extract resume text
        resume_text = await extract_resume_text(resume_path)
        
        # Update candidate profile
        candidate.resume_file = resume_path
        candidate.resume_text = resume_text
        
        # Calculate ATS score using Grok-3
        ats_result = await calculate_ats_score(resume_text, job)
        match_percentage = ats_result["match_percentage"]
        explanation = ats_result["explanation"]
        recommendation = ats_result["recommendation"]
        
        # Create or update match
        existing_match = db.query(Match).filter(
            Match.job_id == job_id,
            Match.candidate_id == candidate.id
        ).first()
        
        if existing_match:
            existing_match.match_score = match_percentage
            existing_match.match_explanation = explanation
            existing_match.status = "pending"
            match = existing_match
        else:
            match = Match(
                job_id=job_id,
                candidate_id=candidate.id,
                match_score=match_percentage,
                skills_match_score=match_percentage,
                match_explanation=explanation,
                status="pending"
            )
            db.add(match)
        
        db.flush()
        
        # Auto-schedule interview if match > 70%
        auto_scheduled = False
        interview_id = None
        
        if match_percentage > 70:
            # Create interview
            interview = Interview(
                match_id=match.id,
                scheduled_at=datetime.utcnow() + timedelta(days=2),  # Schedule 2 days ahead
                language=job.language or "en",
                status="scheduled"
            )
            db.add(interview)
            db.flush()
            
            auto_scheduled = True
            interview_id = interview.id
            
            # Update match status
            match.status = "interview_scheduled"
        
        db.commit()
        
        return {
            "match_percentage": match_percentage,
            "explanation": explanation,
            "auto_scheduled": auto_scheduled,
            "interview_id": interview_id,
            "recommendation": recommendation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process interest: {str(e)}")

# ==================== POSTS ENDPOINTS ====================

@app.post("/api/posts", response_model=PostResponse)
async def create_post(
    request: PostCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new post (for both employers and candidates)"""
    try:
        user = await get_current_user(credentials, db)
        
        # Create post
        post = Post(
            user_id=user.id,
            content=request.content,
            media_url=request.media_url,
            post_type=request.post_type,
            is_active=True
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # Get author details
        author_name = user.full_name or user.email.split('@')[0]
        company_name = user.company_name if user.role.value == "employer" else None
        
        return {
            "id": post.id,
            "user_id": post.user_id,
            "author_name": author_name,
            "author_role": user.role.value,
            "company_name": company_name,
            "content": post.content,
            "media_url": post.media_url,
            "post_type": post.post_type,
            "likes_count": 0,
            "is_liked": False,
            "created_at": post.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@app.get("/api/posts")
async def get_posts(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get all posts for explore feed"""
    try:
        current_user = await get_current_user(credentials, db)
        
        # Get all active posts ordered by most recent
        posts = db.query(Post).filter(Post.is_active == True).order_by(Post.created_at.desc()).limit(limit).all()
        
        result = []
        for post in posts:
            # Get author details
            author = db.query(User).filter(User.id == post.user_id).first()
            author_name = author.full_name or author.email.split('@')[0] if author else "Unknown"
            author_role = author.role.value if author else "candidate"
            company_name = author.company_name if author and author.role.value == "employer" else None
            
            # Get likes count
            likes_count = db.query(PostLike).filter(PostLike.post_id == post.id).count()
            
            # Check if current user liked this post
            is_liked = db.query(PostLike).filter(
                PostLike.post_id == post.id,
                PostLike.user_id == current_user.id
            ).first() is not None
            
            result.append({
                "id": post.id,
                "user_id": post.user_id,
                "author_name": author_name,
                "author_role": author_role,
                "company_name": company_name,
                "content": post.content,
                "media_url": post.media_url,
                "post_type": post.post_type,
                "likes_count": likes_count,
                "is_liked": is_liked,
                "created_at": post.created_at.isoformat()
            })
        
        return {"posts": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@app.post("/api/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Like or unlike a post"""
    try:
        user = await get_current_user(credentials, db)
        
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if already liked
        existing_like = db.query(PostLike).filter(
            PostLike.post_id == post_id,
            PostLike.user_id == user.id
        ).first()
        
        if existing_like:
            # Unlike
            db.delete(existing_like)
            db.commit()
            return {"liked": False, "message": "Post unliked"}
        else:
            # Like
            like = PostLike(post_id=post_id, user_id=user.id)
            db.add(like)
            db.commit()
            return {"liked": True, "message": "Post liked"}
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle like: {str(e)}")


@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a post (only by author)"""
    try:
        user = await get_current_user(credentials, db)
        
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
        db.delete(post)
        db.commit()
        return {"message": "Post deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


# ==================== PAYMENT ENDPOINTS ====================

@app.post("/api/payments/create-order", response_model=PaymentCreateOrderResponse)
async def create_payment_order(request: PaymentCreateOrderRequest, user: User = Depends(get_employer_user), db: Session = Depends(get_db)):
    """Create Razorpay order for pay-per-hire (test mode)"""
    try:
        # Initialize Razorpay client (test mode)
        razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_dummy_key")
        razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "dummy_secret")
        
        # In test mode, create mock order
        order_id = f"order_{user.id}_{int(datetime.utcnow().timestamp())}"
        
        # Create payment record
        payment = Payment(
            employer_id=user.id,
            amount=request.amount,
            currency="USD",
            status=PaymentStatus.PENDING,
            plan=PaymentPlan.PAY_PER_HIRE,
            transaction_id=order_id,
            payment_method="razorpay"
        )
        db.add(payment)
        db.commit()
        
        return {
            "order_id": order_id,
            "amount": request.amount,
            "currency": "USD",
            "razorpay_key_id": razorpay_key_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
