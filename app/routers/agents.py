"""
Agents Router - Multi-Agent System invocation endpoints
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.agents import (
    OrchestratorAgent,
    VaultAgent,
    ReasoningAgent,
    DebateAgent,
    RadarAgent,
    ForgeAgent,
    AttackAgent
)
from app.agents.orchestrator_agent import ExecutionMode

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Request Schemas
# ============================================================================

class OrchestrateRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)
    mode: Optional[ExecutionMode] = ExecutionMode.PARALLEL


class VaultAgentRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)
    hops: Optional[int] = Field(1, ge=1, le=5)


class ReasoningAgentRequest(BaseModel):
    query: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = {}


class DebateAgentRequest(BaseModel):
    conclusion: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = {}
    num_rounds: Optional[int] = Field(3, ge=1, le=10)


class RadarAgentRequest(BaseModel):
    query: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)


class ForgeAgentRequest(BaseModel):
    asset_type: str = Field("social_post", description="Type of asset to generate (e.g. social_post, email_campaign, ad_copy, video_script)")
    context: Dict[str, Any]
    tone: Optional[str] = "professional"


class AttackAgentRequest(BaseModel):
    campaign_id: str = Field(..., min_length=1)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/invoke", status_code=status.HTTP_200_OK)
async def invoke_orchestrator(
    request: OrchestrateRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Orchestrator to dynamically route and run the query across multiple agents.
    """
    try:
        orchestrator = OrchestratorAgent(db_session=db)
        result = await orchestrator.orchestrate(
            query=request.query,
            workspace_id=request.workspace_id,
            execution_mode=request.mode
        )
        return result
    except Exception as e:
        logger.error(f"Error in orchestrator invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failure: {str(e)}"
        )


@router.post("/vault", status_code=status.HTTP_200_OK)
async def invoke_vault(
    request: VaultAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Vault Agent to search and retrieve facts.
    """
    try:
        vault = VaultAgent(db_session=db)
        if request.hops and request.hops > 1:
            facts, chain = await vault.multi_hop_retrieval(
                initial_query=request.query,
                workspace_id=request.workspace_id,
                hops=request.hops
            )
        else:
            facts = await vault.retrieve_facts(
                query=request.query,
                workspace_id=request.workspace_id
            )
            chain = []
            
        confidence = sum(f.confidence for f in facts) / len(facts) if facts else 0.0
        return {
            "facts": [
                {
                    "id": getattr(f, "id", None) or "fact-xyz",
                    "workspace_id": getattr(f, "workspace_id", None) or request.workspace_id,
                    "fact": f.fact,
                    "category": getattr(f, "category", None) or "market_intel",
                    "source": getattr(f, "source", None) or "Unknown",
                    "source_url": getattr(f, "source_url", None),
                    "tags": getattr(f, "tags", []),
                    "created_at": f.created_at.isoformat() if getattr(f, "created_at", None) else datetime.utcnow().isoformat(),
                    "updated_at": getattr(f, "updated_at", None).isoformat() if getattr(f, "updated_at", None) else None
                }
                for f in facts
            ],
            "reasoning_chain": chain,
            "confidence": confidence
        }
    except Exception as e:
        logger.error(f"Error in vault agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reasoning", status_code=status.HTTP_200_OK)
async def invoke_reasoning(
    request: ReasoningAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Reasoning Agent for causal and deductive query analysis.
    """
    try:
        reasoning = ReasoningAgent(db_session=db)
        result = await reasoning.reason_about_query(
            query=request.query,
            context=request.context
        )
        if "conclusions" in result and "conclusion" not in result:
            conclusions = result["conclusions"]
            result["conclusion"] = conclusions[0] if conclusions else "No conclusion reached"
        return result
    except Exception as e:
        logger.error(f"Error in reasoning agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debate", status_code=status.HTTP_200_OK)
async def invoke_debate(
    request: DebateAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Debate Agent to validate a conclusion from multiple perspectives.
    """
    try:
        debate = DebateAgent(db_session=db)
        result = await debate.debate_conclusion(
            conclusion=request.conclusion,
            context=request.context,
            num_rounds=request.num_rounds
        )
        return result
    except Exception as e:
        logger.error(f"Error in debate agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/radar", status_code=status.HTTP_200_OK)
async def invoke_radar(
    request: RadarAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Radar Agent to fetch and ingest competitor/market intelligence.
    """
    try:
        radar = RadarAgent(db_session=db)
        intel = await radar.fetch_intel(
            query=request.query,
            workspace_id=request.workspace_id
        )
        ingested = await radar.ingest_intel(
            intel=intel,
            workspace_id=request.workspace_id
        )
        return {
            "fetched_intel": intel,
            "ingested_facts": ingested
        }
    except Exception as e:
        logger.error(f"Error in radar agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/forge", status_code=status.HTTP_200_OK)
async def invoke_forge(
    request: ForgeAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Forge Agent to generate marketing content/assets.
    """
    try:
        from app.agents.forge_agent import AssetType, ContentTone
        forge = ForgeAgent(db_session=db)
        
        try:
            asset_type_enum = AssetType(request.asset_type)
        except ValueError:
            asset_type_enum = AssetType.SOCIAL_POST
            
        try:
            tone_enum = ContentTone(request.tone)
        except ValueError:
            tone_enum = ContentTone.PROFESSIONAL
            
        result = await forge.generate_asset(
            asset_type=asset_type_enum,
            context=request.context,
            tone=tone_enum
        )
        return result
    except Exception as e:
        logger.error(f"Error in forge agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/attack", status_code=status.HTTP_200_OK)
async def invoke_attack(
    request: AttackAgentRequest,
    db: Session = Depends(get_db)
):
    """
    Invoke Attack Agent to deploy campaigns on marketing channels.
    """
    try:
        attack = AttackAgent(db_session=db)
        result = await attack.deploy_campaign(
            campaign_id=request.campaign_id
        )
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Campaign deployment failed")
            )
        return result
    except Exception as e:
        logger.error(f"Error in attack agent invocation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
