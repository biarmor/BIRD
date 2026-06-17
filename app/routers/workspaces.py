"""Workspaces Router - Phase 0 Placeholder"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_workspaces():
    return {"message": "Workspaces endpoint - Phase 1"}
