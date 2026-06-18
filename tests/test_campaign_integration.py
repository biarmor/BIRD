"""
Integration tests for Phase 4: Campaign Generation, Deployment, and Campaigns Router.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.database import get_db
from app.models import Base, User, Workspace, Campaign
from app.agents.attack_agent import ChannelType

# SQLite test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_campaign_integration.db"
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


def test_campaign_lifecycle_endpoints(test_client, db_session):
    """Test full E2E lifecycle of a campaign via API routes."""
    # 1. Create a mock user and workspace
    owner = User(id="user-123", username="campaign-owner", email="c@x.com", hashed_password="pw")
    workspace = Workspace(id="ws-campaigns", owner_id="user-123", name="Marketing ws")
    db_session.add(owner)
    db_session.add(workspace)
    db_session.commit()

    # 2. Create campaign
    create_response = test_client.post(
        "/api/v2/campaigns/",
        params={"workspace_id": "ws-campaigns"},
        json={
            "name": "Summer Launch",
            "description": "Marketing campaign for new local LLM integration",
            "deployment_plan": {
                "budget": 2500.0,
                "channels": [ChannelType.SOCIAL_MEDIA.value, ChannelType.EMAIL.value],
                "targets": [
                    {"id": "t-devs", "name": "Developers", "description": "Software devs", "size": 8000},
                    {"id": "t-managers", "name": "Product Managers", "description": "PMs", "size": 3000}
                ],
                "assets": [
                    {"type": "social_post", "content": "Check out our new local LLM support!"}
                ]
            }
        }
    )
    
    assert create_response.status_code == 201
    campaign_data = create_response.json()
    campaign_id = campaign_data["id"]
    assert campaign_data["name"] == "Summer Launch"
    assert campaign_data["status"] == "draft"

    # 3. Get Campaign detail
    get_response = test_client.get(f"/api/v2/campaigns/{campaign_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Summer Launch"

    # 4. List Campaigns
    list_response = test_client.get("/api/v2/campaigns/", params={"workspace_id": "ws-campaigns"})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == campaign_id

    # 5. Deploy campaign
    deploy_response = test_client.post(f"/api/v2/campaigns/{campaign_id}/deploy")
    assert deploy_response.status_code == 200
    deploy_data = deploy_response.json()
    assert deploy_data["campaign_id"] == campaign_id
    assert deploy_data["status"] == "deployed"
    # 2 channels * 2 targets = 4 executions
    assert deploy_data["executions"] == 4
    # (8000 + 3000) * 2 channels = 22000 total reach
    assert deploy_data["total_reach"] == 22000

    # 6. Verify database updates (status completed, metrics computed)
    db_campaign = db_session.query(Campaign).filter(Campaign.id == campaign_id).first()
    assert db_campaign.status == "completed"
    assert db_campaign.deployed_at is not None
    assert db_campaign.metrics is not None
    assert db_campaign.metrics["total_impressions"] == 22000

    # 7. Get Metrics via monitoring endpoint
    metrics_response = test_client.get(f"/api/v2/campaigns/{campaign_id}/metrics")
    assert metrics_response.status_code == 200
    metrics_data = metrics_response.json()
    assert metrics_data["campaign_id"] == campaign_id
    assert metrics_data["status"] == "completed"
    assert metrics_data["total_impressions"] == 22000
    assert metrics_data["total_clicks"] > 0
    assert metrics_data["total_conversions"] > 0
