"""
Tests for Phase 2: Multi-Agent Orchestration, Radar Agent, and Agents Router.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Base, VaultFact, User, Workspace
from app.agents.radar_agent import RadarAgent
from app.agents.orchestrator_agent import OrchestratorAgent, ExecutionMode, AgentType, AgentTask, AgentExecutionResult

# SQLite test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_orchestration.db"
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
    agent = MagicMock()
    # Mock add_fact returning a dummy VaultFact model
    fact_mock = VaultFact(
        id="fact-1",
        workspace_id="ws-123",
        fact="[Test Info] Test snippet (Source: test.com)",
        category="market_intel"
    )
    agent.add_fact = AsyncMock(return_value=fact_mock)
    agent.retrieve_facts = AsyncMock(return_value=([], [], 0.5))
    return agent


# ============================================================================
# 1. Radar Agent Tests
# ============================================================================

@pytest.mark.asyncio
async def test_radar_agent_fetch_pricing():
    """Test RadarAgent fetching pricing intelligence."""
    radar = RadarAgent()
    intel = await radar.fetch_intel("pricing info of competitor x", "ws-123")
    assert len(intel) > 0
    assert any("pricing" in item["category"] for item in intel)
    assert any("Starter at $29/mo" in item["snippet"] for item in intel)


@pytest.mark.asyncio
async def test_radar_agent_fetch_roadmap():
    """Test RadarAgent fetching roadmap and feature intelligence."""
    radar = RadarAgent()
    intel = await radar.fetch_intel("new features and roadmap updates", "ws-123")
    assert len(intel) > 0
    assert any("product" in item["category"] for item in intel)
    assert any("Competitor Y" in item["snippet"] for item in intel)


@pytest.mark.asyncio
async def test_radar_agent_ingestion(db_session, mock_vault_agent):
    """Test RadarAgent ingesting fetched intelligence into the Vault."""
    radar = RadarAgent(db_session=db_session, vault_agent=mock_vault_agent)
    intel = [
        {
            "title": "Pricing Change",
            "snippet": "Premium subscription at $49/mo.",
            "source": "https://test.com",
            "category": "pricing"
        }
    ]
    ingested = await radar.ingest_intel(intel, "ws-123")
    assert len(ingested) == 1
    assert ingested[0]["fact_id"] == "fact-1"
    mock_vault_agent.add_fact.assert_called_once()


# ============================================================================
# 2. Orchestrator Parallel Execution Tests
# ============================================================================

def test_orchestrator_query_analysis():
    """Test OrchestratorAgent routes queries correctly to agents."""
    orchestrator = OrchestratorAgent()
    agents, mode = orchestrator.analyze_query("show me pricing news and competitor roadmap")
    assert AgentType.RADAR in agents
    assert AgentType.VAULT in agents
    assert mode == ExecutionMode.PARALLEL


@pytest.mark.asyncio
async def test_orchestrator_parallel_execution_exception(db_session):
    """Test that exceptions during parallel task execution do not drop tasks but mark them as failed."""
    orchestrator = OrchestratorAgent(db_session=db_session)
    
    # Intentionally corrupt _execute_task to raise an exception for a specific task
    async def flawed_execute_task(task):
        if task.agent_type == AgentType.DEBATE:
            raise RuntimeError("Debate agent crashed")
        # Return success for other tasks
        return AgentExecutionResult(
            task_id=task.id,
            agent_type=task.agent_type,
            status="success",
            result={"findings": "vault ok"}
        )
    
    orchestrator._execute_task = flawed_execute_task
    
    tasks = [
        AgentTask(id="t1", agent_type=AgentType.VAULT, query="test", parameters={}),
        AgentTask(id="t2", agent_type=AgentType.DEBATE, query="test", parameters={})
    ]
    
    results = await orchestrator.execute_parallel(tasks)
    assert len(results) == 2
    
    success_task = next(r for r in results if r.agent_type == AgentType.VAULT)
    assert success_task.status == "success"
    
    failed_task = next(r for r in results if r.agent_type == AgentType.DEBATE)
    assert failed_task.status == "failed"
    assert "Debate agent crashed" in failed_task.error_message


# ============================================================================
# 3. Agents Router (FastAPI Endpoint) Tests
# ============================================================================

def test_endpoint_invoke_orchestrator(test_client):
    """Test POST /api/v2/agents/invoke endpoint."""
    response = test_client.post(
        "/api/v2/agents/invoke",
        json={
            "query": "pricing news and competitor feature updates",
            "workspace_id": "ws-test",
            "mode": "parallel"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "findings" in data
    assert data["successful_agents"] > 0


def test_endpoint_invoke_vault_agent(test_client, db_session):
    """Test POST /api/v2/agents/vault endpoint."""
    # Add a mock owner and workspace to the test database
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-test", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.flush()
    
    # Save a mock fact
    fact_obj = VaultFact(
        id="fact-xyz",
        workspace_id="ws-test",
        fact="The server is located in Oregon.",
        embedding=[0.1] * 384
    )
    db_session.add(fact_obj)
    db_session.commit()
    
    response = test_client.post(
        "/api/v2/agents/vault",
        json={
            "query": "Oregon",
            "workspace_id": "ws-test",
            "hops": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "facts" in data
    assert "confidence" in data
    assert len(data["facts"]) == 1
    assert data["facts"][0]["id"] == "fact-xyz"


def test_endpoint_invoke_reasoning_agent(test_client):
    """Test POST /api/v2/agents/reasoning endpoint."""
    response = test_client.post(
        "/api/v2/agents/reasoning",
        json={
            "query": "Why did competitor X lower prices?",
            "context": {"competitor": "X"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "conclusion" in data


def test_endpoint_invoke_debate_agent(test_client):
    """Test POST /api/v2/agents/debate endpoint."""
    response = test_client.post(
        "/api/v2/agents/debate",
        json={
            "conclusion": "Lowering prices increases total subscription revenue.",
            "context": {},
            "num_rounds": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "debate_rounds" in data
    assert "final_consensus" in data


def test_endpoint_invoke_radar_agent(test_client, db_session):
    """Test POST /api/v2/agents/radar endpoint."""
    # Add a mock owner and workspace to the test database
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-test", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.commit()
    
    response = test_client.post(
        "/api/v2/agents/radar",
        json={
            "query": "pricing",
            "workspace_id": "ws-test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "fetched_intel" in data
    assert "ingested_facts" in data
    assert len(data["fetched_intel"]) > 0
    assert len(data["ingested_facts"]) > 0


def test_endpoint_invoke_forge_agent(test_client):
    """Test POST /api/v2/agents/forge endpoint."""
    response = test_client.post(
        "/api/v2/agents/forge",
        json={
            "asset_type": "social_post",
            "context": {"topic": "Local LLM growth"},
            "tone": "creative"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "metadata" in data


def test_endpoint_invoke_attack_agent(test_client):
    """Test POST /api/v2/agents/attack endpoint."""
    response = test_client.post(
        "/api/v2/agents/attack",
        json={
            "campaign_id": "campaign-123"
        }
    )
    # Since campaign-123 doesn't exist in the database, expect a 500 error from internal DB logic
    assert response.status_code == 500
