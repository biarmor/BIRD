"""
Authentication Tests

Unit and integration tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, User
from app.security import hash_password

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


client = TestClient(app)


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
    """Clear database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_success(self):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "securepassword123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "hashed_password" not in data
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "securepassword123"
            }
        )
        
        # Try to create user with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )
        
        # Try to create user with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_invalid_email(self):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 422
    
    def test_register_short_password(self):
        """Test registration with short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint."""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user."""
        db = TestingSessionLocal()
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("securepassword123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        yield user
        db.close()
    
    def test_login_success(self, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    def test_login_invalid_username(self, test_user):
        """Test login with invalid username."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        db = TestingSessionLocal()
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password=hash_password("securepassword123"),
            is_active=False
        )
        db.add(user)
        db.commit()
        db.close()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "inactiveuser",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"]


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data
