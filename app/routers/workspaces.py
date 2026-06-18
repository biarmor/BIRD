"""
Workspaces Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Workspace, User
from app.schemas import WorkspaceCreateRequest, WorkspaceResponse
import uuid
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(db: Session = Depends(get_db)):
    """List all active workspaces."""
    return db.query(Workspace).filter(Workspace.is_active == True).all()

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(request: WorkspaceCreateRequest, owner_id: str = None, db: Session = Depends(get_db)):
    """Create a new workspace."""
    # Find a valid user to act as owner
    if not owner_id:
        user = db.query(User).first()
        if not user:
            # Create a placeholder user to satisfy constraints if database is clean
            from app.security import hash_password
            user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@bird.local",
                hashed_password=hash_password("adminpassword123"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        owner_id = user.id
    else:
        user = db.query(User).filter(User.id == owner_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Owner user not found."
            )

    workspace = Workspace(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=request.name,
        description=request.description or "",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace
