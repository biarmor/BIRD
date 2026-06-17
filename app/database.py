"""
BIRD Backend Database Module

Handles database connection, session management, and initialization.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
import os

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bird.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"


class DatabaseManager:
    """Database connection and session management."""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize(cls):
        """Initialize database connection and create tables."""
        if cls._engine is not None:
            return
        
        try:
            # Create engine
            if DATABASE_URL.startswith("sqlite"):
                # SQLite-specific configuration
                cls._engine = create_engine(
                    DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=DATABASE_ECHO
                )
                
                # Enable foreign keys for SQLite
                @event.listens_for(cls._engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            else:
                # PostgreSQL or other databases
                cls._engine = create_engine(
                    DATABASE_URL,
                    echo=DATABASE_ECHO,
                    pool_pre_ping=True
                )
            
            # Create session factory
            cls._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine
            )
            
            # Import models here to avoid circular imports
            from app.models import Base
            
            # Create all tables
            Base.metadata.create_all(bind=cls._engine)
            logger.info("✅ Database initialized successfully")
            print("✅ Database initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            print(f"❌ Database initialization failed: {e}")
            raise
    
    @classmethod
    def get_session(cls) -> Session:
        """Get a database session."""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()
    
    @classmethod
    def close(cls):
        """Close database connection."""
        if cls._engine is not None:
            cls._engine.dispose()
            logger.info("Database connection closed")


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = DatabaseManager.get_session()
    try:
        yield db
    finally:
        db.close()
