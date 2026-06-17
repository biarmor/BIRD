#!/usr/bin/env python3
"""
Simple Database Initialization Script
Run this to create the database without complex imports
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("BIRD Database Initialization")
print("=" * 60)

try:
    print("\n1. Importing SQLAlchemy...")
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    print("   ✅ SQLAlchemy imported successfully")
    
    print("\n2. Importing Models...")
    from app.models import Base
    print("   ✅ Models imported successfully")
    
    print("\n3. Creating Database Engine...")
    DATABASE_URL = "sqlite:///./bird.db"
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    print("   ✅ Database engine created")
    
    print("\n4. Enabling SQLite Foreign Keys...")
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    print("   ✅ Foreign keys enabled")
    
    print("\n5. Creating All Tables...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ All tables created successfully")
    
    print("\n6. Verifying Database...")
    # Test connection
    with engine.connect() as conn:
        result = conn.execute("SELECT sqlite_version()")
        version = result.fetchone()[0]
        print(f"   ✅ Database verified (SQLite {version})")
    
    print("\n" + "=" * 60)
    print("✅ DATABASE INITIALIZED SUCCESSFULLY!")
    print("=" * 60)
    print("\nDatabase file: bird.db")
    print("\nNext steps:")
    print("1. Run tests: pytest tests/ -v")
    print("2. Start server: python3 -m uvicorn app.main:app --reload")
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check if SQLAlchemy is installed: pip list | grep sqlalchemy")
    print("2. Reinstall requirements: pip install -r requirements.txt")
    print("3. Check virtual environment: which python3")
    print("=" * 60 + "\n")
    sys.exit(1)
