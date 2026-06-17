"""
BIRD Backend Database Module

Handles database connection, session management, and initialization.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config.settings import get_settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    """Database connection and session management."""
    
    _engine = None
    _SessionLocal = None
    
    @classmethod
    def initialize(cls):
        """Initialize database connection and create tables."""
        if cls._engine is not None:
            return
        
        # Create engine
        if settings.database_url.startswith("sqlite"):
            # SQLite-specific configuration
            cls._engine = create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.database_echo
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
                settings.database_url,
                echo=settings.database_echo,
                pool_pre_ping=True
            )
        
        # Create session factory
        cls._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls._engine
        )
        
        # Create all tables
        Base.metadata.create_all(bind=cls._engine)
        logger.info("Database initialized successfully")
    
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


# Initialize database on module import
DatabaseManager.initialize()
