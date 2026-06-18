"""
Campaigns Router - Campaign operations (create, deploy, list, retrieve, metrics)
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas import CampaignCreateRequest, CampaignResponse
from app.models import Campaign
from app.agents.attack_agent import AttackAgent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreateRequest,
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new intelligence-driven campaign.
    """
    try:
        campaign = Campaign(
            workspace_id=workspace_id,
            name=request.name,
            description=request.description,
            intelligence_source=request.intelligence_source,
            status="draft",
            deployment_plan=request.deployment_plan
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        logger.info(f"Created campaign in database: {campaign.id}")
        return campaign
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating campaign: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{campaign_id}/deploy", status_code=status.HTTP_200_OK)
async def deploy_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Deploy an existing campaign across configured channels.
    """
    # Find campaign first
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    try:
        agent = AttackAgent(db_session=db)
        res = await agent.deploy_campaign(campaign_id)
        if res.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("error", "Deployment failed")
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying campaign: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[CampaignResponse], status_code=status.HTTP_200_OK)
async def list_campaigns(
    workspace_id: str,
    limit: Optional[int] = 100,
    db: Session = Depends(get_db)
):
    """
    List campaigns in a workspace.
    """
    try:
        campaigns = db.query(Campaign).filter(
            Campaign.workspace_id == workspace_id
        ).order_by(Campaign.created_at.desc()).limit(limit).all()
        return campaigns
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{campaign_id}", response_model=CampaignResponse, status_code=status.HTTP_200_OK)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve campaign details by ID.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    return campaign


@router.get("/{campaign_id}/metrics", status_code=status.HTTP_200_OK)
async def get_campaign_metrics(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Monitor and retrieve campaign performance metrics.
    """
    # Verify campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    try:
        agent = AttackAgent(db_session=db)
        metrics = await agent.monitor_campaign(campaign_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metrics not available"
            )
        return metrics
    except Exception as e:
        logger.error(f"Error fetching campaign metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
