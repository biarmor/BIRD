from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.orchestrator import Orchestrator
from app.api.v1.auth import get_current_user
from app.db.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/intelligence", tags=["intelligence"])
orchestrator = Orchestrator()

class IntelligenceQuery(BaseModel):
    query: str
    workspace_id: int

@router.post("/analyze")
async def run_intelligence_analysis(
    request: IntelligenceQuery,
    current_user: User = Depends(get_current_user)
):
    """Run full intelligence analysis"""
    try:
        result = orchestrator.execute_intelligence_cycle(
            query=request.query,
            workspace_id=request.workspace_id,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        logger.error(f"Intelligence API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
