"""
SQLAlchemy models for Talentis.ai
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, JSON, 
    ForeignKey, Enum, Boolean, Index, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User role enumeration"""
    EMPLOYER = "employer"
    CANDIDATE = "candidate"
    ADMIN = "admin"


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentPlan(str, enum.Enum):
    """Payment plan enumeration"""
    FREEMIUM = "freemium"
    PAY_PER_HIRE = "pay-per-hire"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class User(Base):
    """User table - for both employers and candidates"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)  # For employers
    subscription_plan = Column(Enum(PaymentPlan), nullable=True)  # For employers
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    job_descriptions = relationship("JobDescription", back_populates="employer", cascade="all, delete-orphan")
    candidate_profile = relationship("Candidate", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="employer", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    bias_audit_logs = relationship("BiasAuditLog", back_populates="user", cascade="all, delete-orphan")
    simulation_attempts = relationship("SimulationAttempt", back_populates="candidate", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_email_role', 'email', 'role'),
        Index('idx_user_active_role', 'is_active', 'role'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class JobDescription(Base):
    """Job descriptions posted by employers"""
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    skills_required = Column(JSON, nullable=False)  # Array of required skills
    location = Column(String(255), nullable=True, index=True)
    salary_range = Column(String(100), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    experience_required = Column(String(50), nullable=True)  # e.g., "3-5 years"
    language = Column(String(10), default="en", nullable=False)
    status = Column(String(20), default="active", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    employer = relationship("User", back_populates="job_descriptions")
    matches = relationship("Match", back_populates="job_description", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_jd_employer_active', 'employer_id', 'is_active'),
        Index('idx_jd_location_active', 'location', 'is_active'),
        Index('idx_jd_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, title='{self.title}')>"


class Candidate(Base):
    """Candidate profiles with resume and skills"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    resume_text = Column(Text, nullable=True)  # Extracted resume text
    resume_url = Column(String(500), nullable=True)  # URL to stored resume
    resume_file = Column(String(500), nullable=True)  # Path to uploaded resume file
    skills = Column(JSON, nullable=True, default=list)  # Array of skills
    location = Column(String(255), nullable=True, index=True)
    preferred_locations = Column(JSON, nullable=True, default=list)  # Array of preferred locations
    language_proficiency = Column(JSON, nullable=True, default=dict)  # Language skills
    experience_years = Column(Integer, nullable=True)
    education = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    availability = Column(String(50), nullable=True)  # immediate, 2-weeks, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="candidate_profile")
    matches = relationship("Match", back_populates="candidate", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_candidate_location', 'location'),
        Index('idx_candidate_experience', 'experience_years'),
    )
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, user_id={self.user_id})>"


class CandidateProfile(Base):
    """Enhanced candidate profile with structured data for AI matching"""
    __tablename__ = "candidate_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    headline = Column(String(255), nullable=True)
    location = Column(String(128), nullable=True)
    phone = Column(String(64), nullable=True)
    education = Column(JSON, nullable=True)  # list of education records
    experience = Column(JSON, nullable=True)  # list of job records
    skills = Column(JSON, nullable=True)  # list of {name, level}
    certifications = Column(JSON, nullable=True)
    portfolio = Column(JSON, nullable=True)
    resume_path = Column(String(512), nullable=True)
    consent_profile_share = Column(Boolean, default=True)  # privacy flag
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user_profile = relationship("User", backref="enhanced_profile", uselist=False)
    
    __table_args__ = (
        Index('idx_candidate_profile_user', 'user_id'),
        Index('idx_candidate_profile_consent', 'consent_profile_share'),
    )
    
    def __repr__(self):
        return f"<CandidateProfile(id={self.id}, user_id={self.user_id}, headline='{self.headline}')>"


class Embedding(Base):
    """Vector embeddings for semantic search"""
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(64), nullable=False, index=True)  # "candidate_profile", "job", "simulation_response"
    entity_id = Column(Integer, nullable=False, index=True)
    model = Column(String(64), nullable=False)
    vector = Column(Text, nullable=False)  # JSON-serialized list[float] for SQLite
    meta_data = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_embedding_entity', 'entity_type', 'entity_id'),
        Index('idx_embedding_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id})>"


class Match(Base):
    """AI-powered matches between job descriptions and candidates"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False, index=True)  # 0-100 score
    skills_match_score = Column(Float, nullable=True)
    experience_match_score = Column(Float, nullable=True)
    location_match_score = Column(Float, nullable=True)
    language_match_score = Column(Float, nullable=True)
    match_explanation = Column(Text, nullable=True)  # AI-generated explanation
    skills_match = Column(JSON, nullable=True)  # Detailed skills matching
    location_match = Column(Boolean, default=False)
    salary_match = Column(Boolean, default=False)
    ai_model_version = Column(String(50), nullable=True)  # Track AI model used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    employer_viewed = Column(Boolean, default=False, index=True)
    candidate_viewed = Column(Boolean, default=False)
    status = Column(String(50), default="pending", index=True)  # pending, accepted, rejected, interviewing
    interview_status = Column(String(50), default="new", index=True)  # new, invite_sent, started, in_progress, completed, reviewed
    interview_link = Column(String(500), nullable=True)  # Secure one-time link
    invite_sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    job_description = relationship("JobDescription", back_populates="matches")
    candidate = relationship("Candidate", back_populates="matches")
    interviews = relationship("Interview", back_populates="match", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_match_job_score', 'job_id', 'match_score'),
        Index('idx_match_candidate_score', 'candidate_id', 'match_score'),
        Index('idx_match_status', 'status'),
        Index('idx_match_created', 'created_at'),
        CheckConstraint('match_score >= 0 AND match_score <= 100', name='check_match_score_range'),
    )
    
    def __repr__(self):
        return f"<Match(id={self.id}, score={self.match_score})>"


class Interview(Base):
    """Interview sessions with AI-generated questions and video recordings"""
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=True, index=True)
    interview_type = Column(String(50), nullable=True)
    questions_json = Column(JSON, nullable=True)  # AI-generated interview questions
    responses_json = Column(JSON, nullable=True)  # Candidate responses
    proctoring_flags = Column(JSON, nullable=True, default=list)  # Proctoring violations log
    technical_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    cultural_fit_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)  # Overall interview score
    retention_prediction = Column(Float, nullable=True)  # 0-1 probability
    video_url = Column(String(500), nullable=True)  # URL to video recording
    feedback = Column(Text, nullable=True)  # AI-generated feedback
    language = Column(String(10), default="en", nullable=False)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="scheduled", index=True)  # scheduled, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    match = relationship("Match", back_populates="interviews")
    
    __table_args__ = (
        Index('idx_interview_match_status', 'match_id', 'status'),
        Index('idx_interview_scheduled', 'scheduled_at'),
        CheckConstraint('overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)', name='check_interview_score_range'),
    )
    
    def __repr__(self):
        return f"<Interview(id={self.id}, status='{self.status}')>"


class Payment(Base):
    """Payment transactions and subscription management"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    plan = Column(Enum(PaymentPlan), nullable=False, index=True)
    transaction_id = Column(String(255), unique=True, nullable=True, index=True)  # External payment gateway ID
    payment_method = Column(String(50), nullable=True)  # credit_card, paypal, etc.
    billing_period_start = Column(DateTime, nullable=True)
    billing_period_end = Column(DateTime, nullable=True)
    invoice_url = Column(String(500), nullable=True)
    payment_metadata = Column(JSON, nullable=True)  # Additional payment metadata (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employer = relationship("User", back_populates="payments")
    
    __table_args__ = (
        Index('idx_payment_employer_status', 'employer_id', 'status'),
        Index('idx_payment_plan_status', 'plan', 'status'),
        Index('idx_payment_created', 'created_at'),
        CheckConstraint('amount >= 0', name='check_payment_amount_positive'),
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status='{self.status}')>"


class Analytics(Base):
    """Analytics and metrics for users (ROI tracking, retention, etc.)"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)  # roi, retention, engagement, etc.
    roi_metrics_json = Column(JSON, nullable=True)  # ROI calculations and metrics
    retention_data = Column(JSON, nullable=True)  # User retention statistics
    engagement_data = Column(JSON, nullable=True)  # User engagement metrics
    conversion_data = Column(JSON, nullable=True)  # Conversion funnel data
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analytics")
    
    __table_args__ = (
        Index('idx_analytics_user_type', 'user_id', 'metric_type'),
        Index('idx_analytics_period', 'period_start', 'period_end'),
        Index('idx_analytics_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, user_id={self.user_id}, type='{self.metric_type}')>"


class BiasAuditLog(Base):
    """Bias audit logs for transparency and fairness tracking"""
    __tablename__ = "bias_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type = Column(String(100), nullable=False, index=True)  # match_generation, interview_scoring, etc.
    entity_type = Column(String(50), nullable=False)  # job, candidate, match, interview
    entity_id = Column(Integer, nullable=True, index=True)
    bias_metrics = Column(JSON, nullable=True)  # Detected bias metrics
    fairness_score = Column(Float, nullable=True)  # 0-100 fairness score
    demographic_data = Column(JSON, nullable=True)  # Anonymous demographic distribution
    mitigation_applied = Column(Boolean, default=False)  # Whether bias mitigation was applied
    mitigation_details = Column(JSON, nullable=True)  # Details of mitigation strategies
    ai_model_version = Column(String(50), nullable=True)
    audit_notes = Column(Text, nullable=True)
    flagged_for_review = Column(Boolean, default=False, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="bias_audit_logs")
    
    __table_args__ = (
        Index('idx_bias_action_entity', 'action_type', 'entity_type'),
        Index('idx_bias_flagged', 'flagged_for_review', 'created_at'),
        Index('idx_bias_user_created', 'user_id', 'created_at'),
        Index('idx_bias_fairness', 'fairness_score'),
    )
    
    def __repr__(self):
        return f"<BiasAuditLog(id={self.id}, action='{self.action_type}')>"


# Additional utility table for system configuration
class SystemConfig(Base):
    """System-wide configuration settings"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"


class Post(Base):
    """Social posts by employers and candidates"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)  # Optional image/video URL
    post_type = Column(String(50), default="general", nullable=False)  # general, job_opening, achievement, question
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", backref="posts")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_post_user_active', 'user_id', 'is_active'),
        Index('idx_post_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Post(id={self.id}, user_id={self.user_id}, type='{self.post_type}')>"


class PostLike(Base):
    """Likes on posts"""
    __tablename__ = "post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    
    # Relationships
    post = relationship("Post", back_populates="likes")
    user = relationship("User", backref="post_likes")
    
    __table_args__ = (
        Index('idx_postlike_post_user', 'post_id', 'user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<PostLike(post_id={self.post_id}, user_id={self.user_id})>"


class PasswordResetToken(Base):
    """Password reset tokens for user authentication"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", backref="reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, is_used={self.is_used})>"


class Simulation(Base):
    """Scenario-based simulations for candidate assessment"""
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default="general")  # "technical", "support", "pm", "sales"
    prompt = Column(Text, nullable=False)  # scenario shown to candidate
    rubric = Column(JSON, nullable=False)  # criteria the AI uses to score
    created_by_ai = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("JobDescription", back_populates="simulations")
    attempts = relationship("SimulationAttempt", back_populates="simulation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Simulation(id={self.id}, title='{self.title}', type='{self.type}')>"


class SimulationAttempt(Base):
    """Candidate attempts at simulations with AI scoring"""
    __tablename__ = "simulation_attempts"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Store full response; if multi-step UI, keep structure
    responses = Column(JSON, nullable=True)  # Nullable until submission

    # AI evaluation
    ai_score = Column(Float, nullable=True)          # 0–100
    ai_subscores = Column(JSON, nullable=True)       # e.g. {"communication": 0.8, "reasoning": 0.7}
    ai_feedback = Column(Text, nullable=True)        # explanation for recruiter/candidate
    
    status = Column(String(20), default="in_progress", nullable=False)  # "in_progress", "completed"
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    simulation = relationship("Simulation", back_populates="attempts")
    candidate = relationship("User", back_populates="simulation_attempts")
    
    __table_args__ = (
        Index('idx_simulation_candidate', 'simulation_id', 'candidate_id'),
    )

    def __repr__(self):
        return f"<SimulationAttempt(id={self.id}, candidate_id={self.candidate_id}, score={self.ai_score})>"



