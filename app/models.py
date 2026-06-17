"""
BIRD Backend Database Models

SQLAlchemy ORM models for users, sessions, authentication, and intelligence data.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Float, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
    )


class Session(Base):
    """Session model for secure session management."""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_token", "token"),
        Index("idx_session_expires_at", "expires_at"),
    )


class Workspace(Base):
    """Workspace model for organizing intelligence projects."""
    
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="workspaces")
    intelligence_queries = relationship("IntelligenceQuery", back_populates="workspace", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_workspace_owner_id", "owner_id"),
        Index("idx_workspace_is_active", "is_active"),
    )


class IntelligenceQuery(Base):
    """Intelligence query model for tracking analysis requests."""
    
    __tablename__ = "intelligence_queries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    mode = Column(String(50), nullable=False, default="orchestrator-worker")  # orchestrator-worker, adaptive-planning, debate
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, executing, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="intelligence_queries")
    reasoning_chains = relationship("ReasoningChain", back_populates="query", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_query_workspace_id", "workspace_id"),
        Index("idx_query_status", "status"),
        Index("idx_query_created_at", "created_at"),
    )


class ReasoningChain(Base):
    """Reasoning chain model for explainability and transparency."""
    
    __tablename__ = "reasoning_chains"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("intelligence_queries.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    agent_type = Column(String(50), nullable=False)  # orchestrator, radar, vault, reasoning, debate, forge, attack
    reasoning_text = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    query = relationship("IntelligenceQuery", back_populates="reasoning_chains")
    
    __table_args__ = (
        Index("idx_reasoning_query_id", "query_id"),
        Index("idx_reasoning_step", "step_number"),
        Index("idx_reasoning_agent_type", "agent_type"),
    )


class VaultFact(Base):
    """Vault fact model for intelligent memory storage."""
    
    __tablename__ = "vault_facts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    fact = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    source_url = Column(String(512), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # Vector embedding for semantic search
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quality_score = relationship("MemoryQualityScore", back_populates="fact", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_fact_workspace_id", "workspace_id"),
        Index("idx_fact_category", "category"),
        Index("idx_fact_created_at", "created_at"),
    )


class MemoryQualityScore(Base):
    """Memory quality score model for vault optimization."""
    
    __tablename__ = "memory_quality_scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fact_id = Column(String(36), ForeignKey("vault_facts.id"), nullable=False, unique=True, index=True)
    source_credibility = Column(Float, nullable=False, default=0.5)  # 0-1
    recency_score = Column(Float, nullable=False, default=0.5)  # 0-1, time-decay
    conflict_score = Column(Float, nullable=False, default=0.0)  # 0-1, 0 = no conflicts
    overall_score = Column(Float, nullable=False, default=0.5)  # 0-1, weighted average
    retrieval_count = Column(Integer, default=0)
    last_retrieved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fact = relationship("VaultFact", back_populates="quality_score")
    
    __table_args__ = (
        Index("idx_quality_fact_id", "fact_id"),
        Index("idx_quality_overall_score", "overall_score"),
    )


class AgentExecution(Base):
    """Agent execution model for monitoring and logging."""
    
    __tablename__ = "agent_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("intelligence_queries.id"), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False, index=True)  # orchestrator, radar, vault, reasoning, debate, forge, attack
    task = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, executing, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    cost_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_execution_query_id", "query_id"),
        Index("idx_execution_agent_type", "agent_type"),
        Index("idx_execution_status", "status"),
    )


class Campaign(Base):
    """Campaign model for tracking deployed intelligence-driven campaigns."""
    
    __tablename__ = "campaigns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    intelligence_source = Column(String(36), ForeignKey("intelligence_queries.id"), nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, scheduled, executing, completed, failed
    deployment_plan = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deployed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_campaign_workspace_id", "workspace_id"),
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_created_at", "created_at"),
    )
