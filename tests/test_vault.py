"""
Vault Tests

Unit and integration tests for Vault agent and endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, VaultFact, MemoryQualityScore
from datetime import datetime, timedelta

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_vault.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


class TestVaultAgent:
    """Test Vault agent functionality."""
    
    @pytest.mark.asyncio
    async def test_vault_query_single_hop(self):
        """Test single-hop vault query."""
        from app.agents.vault_agent import VaultAgent
        
        db = TestingSessionLocal()
        agent = VaultAgent(db_session=db)
        
        result = await agent.query_vault(
            query="test query",
            workspace_id="test-workspace",
            mode="single-hop"
        )
        
        assert result["query"] == "test query"
        assert result["mode"] == "single-hop"
        assert "thoughts" in result
        assert len(result["thoughts"]) > 0
        
        db.close()
    
    @pytest.mark.asyncio
    async def test_multi_hop_retrieval(self):
        """Test multi-hop retrieval."""
        from app.agents.vault_agent import VaultAgent
        
        db = TestingSessionLocal()
        agent = VaultAgent(db_session=db)
        
        facts, reasoning_chain = await agent.multi_hop_retrieval(
            initial_query="test query",
            workspace_id="test-workspace",
            hops=2
        )
        
        assert isinstance(facts, list)
        assert isinstance(reasoning_chain, list)
        assert len(reasoning_chain) >= 2  # At least 2 hops
        
        db.close()
    
    def test_memory_quality_score(self):
        """Test memory quality score calculation."""
        from app.agents.vault_agent import VaultAgent
        
        agent = VaultAgent()
        
        # Test with all high scores
        score = agent.calculate_memory_quality_score(
            source_credibility=1.0,
            recency_score=1.0,
            conflict_score=0.0,
            retrieval_count=10
        )
        
        assert score > 0.8
        
        # Test with low scores
        score = agent.calculate_memory_quality_score(
            source_credibility=0.3,
            recency_score=0.3,
            conflict_score=0.8,
            retrieval_count=0
        )
        
        assert score < 0.5
    
    def test_recency_score(self):
        """Test recency score calculation."""
        from app.agents.vault_agent import VaultAgent
        
        agent = VaultAgent()
        
        # New fact
        now = datetime.utcnow()
        score = agent.calculate_recency_score(now)
        assert score > 0.9
        
        # Old fact (30 days)
        old = now - timedelta(days=30)
        score = agent.calculate_recency_score(old)
        assert 0.4 < score < 0.6
        
        # Very old fact (90 days)
        very_old = now - timedelta(days=90)
        score = agent.calculate_recency_score(very_old)
        assert score < 0.2


class TestVaultEndpoints:
    """Test Vault API endpoints."""
    
    def test_add_fact(self):
        """Test adding a fact to vault."""
        response = client.post(
            "/api/v2/vault/facts?workspace_id=test-workspace",
            json={
                "fact": "Test fact about competitor",
                "source": "TechCrunch",
                "source_url": "https://techcrunch.com/article",
                "category": "competitor-news",
                "tags": ["competitor", "news"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["fact"] == "Test fact about competitor"
        assert data["source"] == "TechCrunch"
        assert data["category"] == "competitor-news"
    
    def test_get_fact(self):
        """Test retrieving a fact from vault."""
        # Add a fact first
        add_response = client.post(
            "/api/v2/vault/facts?workspace_id=test-workspace",
            json={
                "fact": "Test fact",
                "source": "Source",
                "category": "test"
            }
        )
        
        fact_id = add_response.json()["id"]
        
        # Get the fact
        get_response = client.get(f"/api/v2/vault/facts/{fact_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == fact_id
        assert data["fact"] == "Test fact"
    
    def test_get_nonexistent_fact(self):
        """Test retrieving a nonexistent fact."""
        response = client.get("/api/v2/vault/facts/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_fact(self):
        """Test updating a fact in vault."""
        # Add a fact first
        add_response = client.post(
            "/api/v2/vault/facts?workspace_id=test-workspace",
            json={
                "fact": "Original fact",
                "source": "Original Source"
            }
        )
        
        fact_id = add_response.json()["id"]
        
        # Update the fact
        update_response = client.put(
            f"/api/v2/vault/facts/{fact_id}",
            json={
                "fact": "Updated fact",
                "source": "Updated Source",
                "category": "updated"
            }
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["fact"] == "Updated fact"
        assert data["source"] == "Updated Source"
    
    def test_delete_fact(self):
        """Test deleting a fact from vault."""
        # Add a fact first
        add_response = client.post(
            "/api/v2/vault/facts?workspace_id=test-workspace",
            json={
                "fact": "Fact to delete",
                "source": "Source"
            }
        )
        
        fact_id = add_response.json()["id"]
        
        # Delete the fact
        delete_response = client.delete(f"/api/v2/vault/facts/{fact_id}")
        
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/v2/vault/facts/{fact_id}")
        assert get_response.status_code == 404
    
    def test_vault_stats(self):
        """Test getting vault statistics."""
        workspace_id = "test-workspace"
        
        # Add some facts
        for i in range(3):
            client.post(
                f"/api/v2/vault/facts?workspace_id={workspace_id}",
                json={
                    "fact": f"Test fact {i}",
                    "source": "Source"
                }
            )
        
        # Get stats
        response = client.get(f"/api/v2/vault/stats?workspace_id={workspace_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == workspace_id
        assert data["total_facts"] == 3
        assert "average_quality" in data


class TestEmbeddingManager:
    """Test embedding functionality."""
    
    def test_embed_text(self):
        """Test embedding a single text."""
        from app.embeddings import get_embedding_manager
        
        manager = get_embedding_manager()
        embedding = manager.embed_text("Test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    def test_embed_texts(self):
        """Test embedding multiple texts."""
        from app.embeddings import get_embedding_manager
        
        manager = get_embedding_manager()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = manager.embed_texts(texts)
        
        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        from app.embeddings import get_embedding_manager
        
        manager = get_embedding_manager()
        
        # Same text should have high similarity
        embedding1 = manager.embed_text("Test text")
        embedding2 = manager.embed_text("Test text")
        
        similarity = manager.cosine_similarity(embedding1, embedding2)
        assert similarity > 0.9
        
        # Different texts should have lower similarity
        embedding3 = manager.embed_text("Completely different text")
        similarity = manager.cosine_similarity(embedding1, embedding3)
        assert similarity < 0.9
