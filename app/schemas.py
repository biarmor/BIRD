"""
BIRD Backend Pydantic Schemas

Request and response models for API validation and documentation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)


class UserLoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Workspace Schemas
# ============================================================================

class WorkspaceCreateRequest(BaseModel):
    """Workspace creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    """Workspace update request."""
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Workspace response."""
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Intelligence Query Schemas
# ============================================================================

class QueryMode(str, Enum):
    """Query execution mode."""
    ORCHESTRATOR_WORKER = "orchestrator-worker"
    ADAPTIVE_PLANNING = "adaptive-planning"
    DEBATE = "debate"


class IntelligenceQueryRequest(BaseModel):
    """Intelligence query request."""
    query: str = Field(..., min_length=1)
    mode: QueryMode = QueryMode.ORCHESTRATOR_WORKER
    workspace_id: str


class IntelligenceQueryResponse(BaseModel):
    """Intelligence query response."""
    id: str
    workspace_id: str
    query: str
    mode: str
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    token_count: Optional[int]
    cost_estimate: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Reasoning Chain Schemas
# ============================================================================

class ReasoningChainResponse(BaseModel):
    """Reasoning chain response."""
    id: str
    query_id: str
    step_number: int
    agent_type: str
    reasoning_text: str
    evidence: Optional[Dict[str, Any]]
    confidence: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Vault Schemas
# ============================================================================

class VaultFactRequest(BaseModel):
    """Vault fact creation request."""
    fact: str = Field(..., min_length=1)
    source: Optional[str] = None
    source_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class VaultFactResponse(BaseModel):
    """Vault fact response."""
    id: str
    workspace_id: str
    fact: str
    source: Optional[str]
    source_url: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VaultSearchRequest(BaseModel):
    """Vault search request."""
    query: str = Field(..., min_length=1)
    workspace_id: str
    hops: int = Field(1, ge=1, le=5)
    sources: Optional[List[str]] = None


class VaultSearchResponse(BaseModel):
    """Vault search response."""
    facts: List[VaultFactResponse]
    reasoning_chain: Optional[List[str]]
    confidence: float


# ============================================================================
# Agent Execution Schemas
# ============================================================================

class AgentInvokeRequest(BaseModel):
    """Agent invocation request."""
    agent_type: str = Field(..., min_length=1)
    task: Dict[str, Any]
    workspace_id: str


class AgentExecutionResponse(BaseModel):
    """Agent execution response."""
    id: str
    query_id: Optional[str]
    agent_type: str
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    cost_tokens: Optional[int]
    latency_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Campaign Schemas
# ============================================================================

class CampaignCreateRequest(BaseModel):
    """Campaign creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    intelligence_source: Optional[str] = None
    deployment_plan: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    """Campaign response."""
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    status: str
    metrics: Optional[Dict[str, Any]]
    created_at: datetime
    deployed_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "Validation Error"
    details: List[Dict[str, Any]]
    status_code: int = 422
