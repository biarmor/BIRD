"""
Tests for Phase 3: Adaptive Planning & Reasoning, RAR Agent, and Explainability.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.database import get_db
from app.models import Base, VaultFact, User, Workspace, ReasoningChain, IntelligenceQuery
from app.agents.rar_agent import RARAgent
from app.agents.vault_agent import VaultAgent, RetrievedFact
from app.agents.orchestrator_agent import OrchestratorAgent, ExecutionMode, AgentType
from app.services.llm_service import OllamaClient

# SQLite test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_adaptive_reasoning.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True, scope="module")
def setup_dependency_overrides():
    """Set database dependency override for this test module."""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture(autouse=True)
def clear_db():
    """Clear SQLite database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_vault_agent():
    agent = MagicMock(spec=VaultAgent)
    retrieved = [
        RetrievedFact(
            fact="Vault fact: Competitor pricing starts at $49/mo.",
            source="pricing_page",
            confidence=0.9,
            recency_score=1.0,
            source_credibility=1.0,
            overall_quality=0.9,
            created_at=datetime.utcnow()
        )
    ]
    agent.retrieve_facts = AsyncMock(return_value=retrieved)
    return agent


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=OllamaClient)
    client.is_healthy = AsyncMock(return_value=True)
    client.generate = AsyncMock(return_value={
        "response": "Reasoning: Analyzing competitor prices.\nConclusion: Competitor is more expensive."
    })
    return client


# ============================================================================
# 1. RAR Agent Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rar_agent_with_vault_and_llm(db_session, mock_vault_agent, mock_llm_client):
    """Test RARAgent queries VaultAgent and leverages LLM when active."""
    rar = RARAgent(db_session=db_session, vault_agent=mock_vault_agent, llm_client=mock_llm_client)
    
    result = await rar.reason_with_retrieval(
        query="what is competitor pricing?",
        workspace_id="ws-123",
        max_hops=2,
        confidence_threshold=0.9
    )
    
    assert result["confidence"] > 0.0
    assert result["total_hops"] > 0
    assert result["final_conclusion"] == "Competitor is more expensive."
    assert any("Vault fact: Competitor pricing starts at $49/mo." in f for f in result["unique_evidence"])
    
    mock_vault_agent.retrieve_facts.assert_called()
    mock_llm_client.generate.assert_called()


@pytest.mark.asyncio
async def test_rar_agent_offline_fallback(db_session, mock_vault_agent, mock_llm_client):
    """Test RARAgent falls back gracefully when LLM is offline."""
    mock_llm_client.is_healthy = AsyncMock(return_value=False)
    rar = RARAgent(db_session=db_session, vault_agent=mock_vault_agent, llm_client=mock_llm_client)
    
    result = await rar.reason_with_retrieval(
        query="what is competitor pricing?",
        workspace_id="ws-123",
        max_hops=2,
        confidence_threshold=0.9
    )
    
    assert result["confidence"] > 0.0
    assert "Conclusion based on retrieved facts" in result["final_conclusion"]
    mock_llm_client.generate.assert_not_called()


# ============================================================================
# 2. Adaptive Orchestration Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_orchestrator_adaptive_mode(db_session):
    """Test Orchestrator routing to AdaptivePlanningAgent in ADAPTIVE mode."""
    orchestrator = OrchestratorAgent(db_session=db_session)
    
    result = await orchestrator.orchestrate(
        query="analyze pricing news",
        workspace_id="ws-123",
        execution_mode=ExecutionMode.ADAPTIVE
    )
    
    assert result["query"] == "analyze pricing news"
    assert result["total_agents"] > 0
    assert len(result["findings"]) > 0
    assert any("Result from" in str(f) for f in result["findings"])


# ============================================================================
# 3. Explainability / Reasoning Chain Endpoint Tests
# ============================================================================

def test_analyze_persists_reasoning_steps(test_client, db_session):
    """Test that POST /analyze persists reasoning steps to the database."""
    # Add workspace & user to avoid foreign key failures or validate correctly
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-test", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.commit()
    
    response = test_client.post(
        "/api/v2/intelligence/analyze",
        json={
            "query": "pricing updates and roadmap changes",
            "workspace_id": "ws-test",
            "mode": "orchestrator-worker"
        }
    )
    
    assert response.status_code == 201
    query_id = response.json()["id"]
    
    # Verify in DB that reasoning chain steps exist
    steps = db_session.query(ReasoningChain).filter(ReasoningChain.query_id == query_id).all()
    assert len(steps) > 0
    assert steps[0].step_number == 1
    
    # Verify GET /{query_id}/reasoning returns steps successfully
    get_response = test_client.get(f"/api/v2/intelligence/{query_id}/reasoning")
    assert get_response.status_code == 200
    chain_data = get_response.json()
    assert chain_data["query_id"] == query_id
    assert len(chain_data["steps"]) == len(steps)
    assert "reasoning_text" in chain_data["steps"][0]
