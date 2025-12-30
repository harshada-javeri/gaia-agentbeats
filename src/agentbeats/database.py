"""Database models and configuration for leaderboard and submission tracking."""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    JSON,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./agentbeats_leaderboard.db"
)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # For SQLite, use StaticPool to support concurrent access
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # For PostgreSQL and other databases
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Submission(Base):
    """Stores benchmark submission records."""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Submission metadata
    submission_id = Column(String(255), unique=True, index=True, nullable=False)
    agent_name = Column(String(255), index=True, nullable=False)
    agent_version = Column(String(50), nullable=False)
    team_name = Column(String(255), nullable=True, index=True)
    
    # GAIA benchmark configuration
    level = Column(Integer, nullable=False)  # 1, 2, or 3
    split = Column(String(50), nullable=False)  # validation or test
    
    # Results
    total_tasks = Column(Integer, nullable=False)
    correct_tasks = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)  # 0-100
    errors = Column(Integer, default=0)
    
    # Performance metrics
    total_time_seconds = Column(Float, nullable=False)
    average_time_per_task = Column(Float, nullable=False)
    
    # Detailed results
    task_results = Column(JSON, nullable=True)  # Detailed per-task results
    
    # GitHub integration
    github_repo = Column(String(255), nullable=True, index=True)
    github_commit_hash = Column(String(40), nullable=True)
    github_pr_number = Column(Integer, nullable=True)
    github_branch = Column(String(255), nullable=True)
    
    # Submission context
    environment = Column(String(100), nullable=True)  # docker, local, etc
    model_used = Column(String(255), nullable=True)  # e.g., gpt-4o
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Status tracking
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_team_level_split", "team_name", "level", "split"),
        Index("idx_agent_timestamp", "agent_name", "timestamp"),
        Index("idx_github_repo", "github_repo"),
    )


class LeaderboardEntry(Base):
    """Materialized view for leaderboard rankings."""

    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ranking info
    rank = Column(Integer, nullable=False, index=True)
    level = Column(Integer, nullable=False, index=True)
    split = Column(String(50), nullable=False, index=True)
    
    # Agent info
    agent_name = Column(String(255), nullable=False, index=True)
    team_name = Column(String(255), nullable=True, index=True)
    agent_version = Column(String(50), nullable=False)
    
    # Score
    accuracy = Column(Float, nullable=False, index=True)
    correct_tasks = Column(Integer, nullable=False)
    total_tasks = Column(Integer, nullable=False)
    
    # Performance
    average_time_per_task = Column(Float, nullable=False)
    
    # Reference
    best_submission_id = Column(String(255), nullable=False, index=True)
    submission_timestamp = Column(DateTime, nullable=False, index=True)
    
    # GitHub info
    github_repo = Column(String(255), nullable=True)
    github_commit_hash = Column(String(40), nullable=True)
    
    # Update timestamp for tracking when leaderboard was refreshed
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_leaderboard_level_rank", "level", "rank"),
        Index("idx_leaderboard_team", "level", "team_name"),
    )


class WebhookEvent(Base):
    """Stores GitHub webhook events for audit and retry logic."""

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    
    event_type = Column(String(50), nullable=False)  # push, pull_request, etc
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Webhook payload
    payload = Column(JSON, nullable=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    repository = Column(String(255), nullable=False, index=True)
    branch = Column(String(255), nullable=True)
    commit_hash = Column(String(40), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_webhook_repo_event", "repository", "event_type"),
        Index("idx_webhook_unprocessed", "is_processed", "timestamp"),
    )


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized")


def get_db():
    """Dependency for getting DB session in FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
