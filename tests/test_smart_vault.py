"""
Tests for Smart Vault - ChromaDB, Deduplication, Conflict Detection, and LLM-based Multi-hop RAG.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.models import Base, VaultFact, MemoryQualityScore
from app.agents.vault_agent import VaultAgent, RetrievedFact
from app.services.llm_service import OllamaClient
from app.embeddings import ChromaDBManager

# SQLite test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_smart_vault.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


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
def mock_chroma_manager():
    manager = MagicMock(spec=ChromaDBManager)
    manager.get_or_create_collection = MagicMock(return_value=MagicMock())
    manager.add_documents = MagicMock(return_value=True)
    manager.query = MagicMock(return_value={"ids": [], "documents": [], "distances": []})
    return manager


@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=OllamaClient)
    client.is_healthy = AsyncMock(return_value=True)
    client.generate = AsyncMock(return_value={"response": "expanded search query"})
    return client


@pytest.mark.asyncio
async def test_add_fact_to_sqlite_and_chromadb(db_session, mock_chroma_manager):
    """Test that adding a fact stores it in SQLite and ChromaDB."""
    agent = VaultAgent(db_session=db_session)
    agent.chromadb_manager = mock_chroma_manager
    
    fact = await agent.add_fact(
        fact="User prefer cold brew coffee.",
        workspace_id="test-workspace-123",
        category="preferences",
        source="user_profile"
    )
    
    # Verify in SQLite
    db_fact = db_session.query(VaultFact).filter(VaultFact.id == fact.id).first()
    assert db_fact is not None
    assert db_fact.fact == "User prefer cold brew coffee."
    
    # Verify in ChromaDB mock
    mock_chroma_manager.add_documents.assert_called_once_with(
        documents=["User prefer cold brew coffee."],
        ids=[fact.id],
        embeddings=[db_fact.embedding],
        metadatas=[{
            "workspace_id": "test-workspace-123",
            "category": "preferences",
            "source": "user_profile",
            "source_url": ""
        }]
    )


@pytest.mark.asyncio
async def test_retrieve_facts_chromadb_success(db_session, mock_chroma_manager):
    """Test retrieve_facts queries ChromaDB successfully and formats results."""
    # First, save a mock fact to SQLite so retrieve_facts can fetch it by ID
    from app.models import User, Workspace
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-1", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.flush()
    
    fact_obj = VaultFact(
        id="fact-xyz",
        workspace_id="ws-1",
        fact="The server is located in Oregon.",
        embedding=[0.1] * 384
    )
    db_session.add(fact_obj)
    db_session.commit()
    
    mock_chroma_manager.query.return_value = {
        "ids": [["fact-xyz"]],
        "distances": [[0.1]]
    }
    
    agent = VaultAgent(db_session=db_session)
    agent.chromadb_manager = mock_chroma_manager
    
    retrieved = await agent.retrieve_facts(query="where is the server?", workspace_id="ws-1")
    assert len(retrieved) == 1
    assert retrieved[0].fact == "The server is located in Oregon."
    assert retrieved[0].confidence == 0.9  # 1.0 - distance (0.1) = 0.9
    assert retrieved[0].id == "fact-xyz"


@pytest.mark.asyncio
async def test_retrieve_facts_chromadb_fallback(db_session, mock_chroma_manager):
    """Test retrieve_facts falls back to database scan when ChromaDB has no results."""
    from app.models import User, Workspace
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-1", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.flush()
    
    fact_obj = VaultFact(
        id="fact-abc",
        workspace_id="ws-1",
        fact="The API key is secret.",
        embedding=[0.1] * 384
    )
    db_session.add(fact_obj)
    db_session.commit()
    
    # ChromaDB returns empty list
    mock_chroma_manager.query.return_value = {"ids": [[]]}
    
    agent = VaultAgent(db_session=db_session)
    agent.chromadb_manager = mock_chroma_manager
    
    retrieved = await agent.retrieve_facts(query="API key", workspace_id="ws-1", similarity_threshold=0.1)
    assert len(retrieved) == 1
    assert retrieved[0].fact == "The API key is secret."
    assert retrieved[0].id == "fact-abc"


@pytest.mark.asyncio
async def test_generate_next_query_llm(mock_llm_client):
    """Test that _generate_next_query queries OllamaClient if healthy."""
    agent = VaultAgent(llm_client=mock_llm_client)
    fact = RetrievedFact(
        fact="AWS is down in us-east-1",
        source="alert",
        confidence=0.9,
        recency_score=1.0,
        source_credibility=1.0,
        overall_quality=0.9,
        created_at=datetime.utcnow()
    )
    
    next_query = await agent._generate_next_query([fact], "AWS status")
    assert next_query == "expanded search query"
    mock_llm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_next_query_fallback(mock_llm_client):
    """Test that _generate_next_query falls back when LLM is offline/fails."""
    mock_llm_client.is_healthy = AsyncMock(return_value=False)
    agent = VaultAgent(llm_client=mock_llm_client)
    
    fact = RetrievedFact(
        fact="AWS is down in us-east-1",
        source="alert",
        confidence=0.9,
        recency_score=1.0,
        source_credibility=1.0,
        overall_quality=0.9,
        created_at=datetime.utcnow()
    )
    
    next_query = await agent._generate_next_query([fact], "AWS status")
    assert "AWS status AND AWS is down" in next_query
    mock_llm_client.generate.assert_not_called()


def test_detect_conflicts():
    """Test conflict detection identifies contradictions."""
    agent = VaultAgent()
    
    f1 = RetrievedFact(
        fact="Revenue grew by 20% in Q3.",
        source="report",
        confidence=0.9,
        recency_score=1.0,
        source_credibility=1.0,
        overall_quality=0.9,
        created_at=datetime.utcnow()
    )
    f2 = RetrievedFact(
        fact="Revenue fell by 5% in Q3.",
        source="report",
        confidence=0.95,
        recency_score=1.0,
        source_credibility=1.0,
        overall_quality=0.95,
        created_at=datetime.utcnow()
    )
    
    conflicts = agent.detect_conflicts([f1, f2])
    assert len(conflicts) == 1
    assert conflicts[0][0].fact == "Revenue grew by 20% in Q3."
    assert conflicts[0][1].fact == "Revenue fell by 5% in Q3."
    assert conflicts[0][2] > 0.5


@pytest.mark.asyncio
async def test_semantic_deduplication():
    """Test semantic deduplication keeps highest quality copy."""
    agent = VaultAgent()
    
    f1 = RetrievedFact(
        fact="The deployment was successful.",
        source="slack",
        confidence=0.8,
        recency_score=0.8,
        source_credibility=0.8,
        overall_quality=0.8,
        created_at=datetime.utcnow()
    )
    f2 = RetrievedFact(
        fact="The deployment was successful.",
        source="ci",
        confidence=0.95,
        recency_score=0.95,
        source_credibility=0.95,
        overall_quality=0.95,
        created_at=datetime.utcnow()
    )
    
    dedup = await agent.semantic_deduplication([f1, f2])
    assert len(dedup) == 1
    assert dedup[0].overall_quality == 0.95


@pytest.mark.asyncio
async def test_cleanup_low_quality_memory(db_session, mock_chroma_manager):
    """Test that cleanup_memory deletes facts below quality threshold from SQLite and ChromaDB."""
    # Setup owner and workspace
    from app.models import User, Workspace
    owner = User(id="default-owner-id", username="default-owner", email="o@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-1", owner_id="default-owner-id", name="Default")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.flush()
    
    # Fact 1: High quality
    f1 = VaultFact(id="f-high", workspace_id="ws-1", fact="High quality info")
    db_session.add(f1)
    db_session.flush()
    q1 = MemoryQualityScore(fact_id="f-high", overall_score=0.9)
    db_session.add(q1)
    
    # Fact 2: Low quality
    f2 = VaultFact(id="f-low", workspace_id="ws-1", fact="Low quality info")
    db_session.add(f2)
    db_session.flush()
    q2 = MemoryQualityScore(fact_id="f-low", overall_score=0.3)
    db_session.add(q2)
    
    db_session.commit()
    
    agent = VaultAgent(db_session=db_session)
    agent.chromadb_manager = mock_chroma_manager
    
    # Cleanup facts under 0.5 threshold
    await agent.cleanup_memory(workspace_id="ws-1")
    
    # Verify low-quality fact is deleted and high-quality fact remains
    high_db = db_session.query(VaultFact).filter(VaultFact.id == "f-high").first()
    low_db = db_session.query(VaultFact).filter(VaultFact.id == "f-low").first()
    assert high_db is not None
    assert low_db is None
    
    # Verify mock collection deletion call
    mock_chroma_manager.get_or_create_collection.return_value.delete.assert_called_once_with(ids=["f-low"])
