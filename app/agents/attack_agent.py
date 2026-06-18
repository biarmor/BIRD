"""
Attack Agent - Campaign Deployment and Execution

Manages campaign deployment, scheduling, and monitoring.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class CampaignStatus(str, Enum):
    """Campaign execution status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ChannelType(str, Enum):
    """Distribution channels."""
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    WEB = "web"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    DIRECT_MAIL = "direct_mail"


@dataclass
class CampaignTarget:
    """Target audience for campaign."""
    id: str
    name: str
    description: str
    size: int  # Estimated audience size
    demographics: Dict[str, Any] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class CampaignExecution:
    """Campaign execution record."""
    id: str
    campaign_id: str
    channel: ChannelType
    target: CampaignTarget
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    cost: float = 0.0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Campaign:
    """Marketing campaign."""
    id: str
    name: str
    description: str
    assets: List[Dict[str, Any]]
    targets: List[CampaignTarget]
    channels: List[ChannelType]
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: datetime = None
    end_date: datetime = None
    budget: float = 0.0
    executions: List[CampaignExecution] = field(default_factory=list)
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class AttackAgent:
    """
    Attack Agent - Campaign Deployment and Execution
    
    Capabilities:
    - Campaign creation and management
    - Multi-channel deployment
    - Scheduling and timing
    - Performance monitoring
    - Budget management
    - Audience targeting
    """
    
    def __init__(self, db_session=None):
        """
        Initialize Attack Agent.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.campaigns = {}
        self.executions = []
    
    async def create_campaign(
        self,
        name: str,
        description: str,
        assets: List[Dict[str, Any]],
        targets: List[CampaignTarget],
        channels: List[ChannelType],
        budget: float,
        start_date: datetime,
        end_date: datetime
    ) -> Campaign:
        """
        Create a marketing campaign.
        
        Args:
            name: Campaign name
            description: Campaign description
            assets: Marketing assets to use
            targets: Target audiences
            channels: Distribution channels
            budget: Campaign budget
            start_date: Campaign start date
            end_date: Campaign end date
            
        Returns:
            Created campaign
        """
        logger.info(f"Creating campaign: {name}")
        
        campaign_id = f"campaign-{datetime.utcnow().timestamp()}"
        
        campaign = Campaign(
            id=campaign_id,
            name=name,
            description=description,
            assets=assets,
            targets=targets,
            channels=channels,
            budget=budget,
            start_date=start_date,
            end_date=end_date,
            status=CampaignStatus.DRAFT
        )
        
        self.campaigns[campaign_id] = campaign
        
        logger.info(f"Campaign created: {campaign_id}")
        logger.info(f"Targets: {len(targets)}, Channels: {len(channels)}, Budget: ${budget}")
        
        return campaign
    
    async def schedule_campaign(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Campaign:
        """
        Schedule a campaign for execution.
        
        Args:
            campaign_id: Campaign ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Updated campaign
        """
        logger.info(f"Scheduling campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None
        
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.status = CampaignStatus.SCHEDULED
        
        logger.info(f"Campaign scheduled: {start_date} to {end_date}")
        
        return campaign
    
    async def deploy_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Deploy a campaign across channels.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Deployment result
        """
        logger.info(f"Deploying campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        db_campaign = None
        
        if not campaign and self.db_session:
            from app.models import Campaign as DbCampaign
            db_campaign = self.db_session.query(DbCampaign).filter(DbCampaign.id == campaign_id).first()
            if db_campaign:
                plan = db_campaign.deployment_plan or {}
                channels = [ChannelType(c) for c in plan.get("channels", [ChannelType.SOCIAL_MEDIA.value])]
                targets = [
                    CampaignTarget(
                        id=t.get("id", "t-default"),
                        name=t.get("name", "Target"),
                        description=t.get("description", ""),
                        size=t.get("size", 1000)
                    )
                    for t in plan.get("targets", [{"id": "t-default", "name": "Default Target", "description": "", "size": 1000}])
                ]
                campaign = Campaign(
                    id=db_campaign.id,
                    name=db_campaign.name,
                    description=db_campaign.description or "",
                    assets=plan.get("assets", []),
                    targets=targets,
                    channels=channels,
                    budget=plan.get("budget", 0.0),
                    status=CampaignStatus.DRAFT
                )
                self.campaigns[campaign_id] = campaign
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return {"status": "failed", "error": "Campaign not found"}
        
        campaign.status = CampaignStatus.RUNNING
        if db_campaign:
            db_campaign.status = "executing"
            self.db_session.flush()
        
        # Deploy to each channel
        deployment_results = []
        
        channels = campaign.channels or [ChannelType.SOCIAL_MEDIA]
        targets = campaign.targets or [CampaignTarget("t-default", "Default Target", "All customers", 1000)]
        
        for channel in channels:
            for target in targets:
                execution = await self._deploy_to_channel(
                    campaign=campaign,
                    channel=channel,
                    target=target
                )
                deployment_results.append(execution)
                campaign.executions.append(execution)
        
        campaign.status = CampaignStatus.COMPLETED
        
        total_impressions = sum(e.impressions for e in campaign.executions)
        total_clicks = sum(e.clicks for e in campaign.executions)
        total_conversions = sum(e.conversions for e in campaign.executions)
        total_cost = sum(e.cost for e in campaign.executions)
        
        if db_campaign:
            db_campaign.status = "completed"
            db_campaign.deployed_at = datetime.utcnow()
            db_campaign.completed_at = datetime.utcnow()
            db_campaign.metrics = {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "total_cost": total_cost,
                "ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
                "conversion_rate": total_conversions / total_clicks if total_clicks > 0 else 0,
                "roi": (total_conversions * 100 - total_cost) / total_cost if total_cost > 0 else 0
            }
            self.db_session.commit()
            
        logger.info(f"Campaign deployed: {len(deployment_results)} executions")
        
        return {
            "campaign_id": campaign_id,
            "status": "deployed",
            "executions": len(deployment_results),
            "total_reach": sum(e.target.size for e in campaign.executions)
        }
    
    async def _deploy_to_channel(
        self,
        campaign: Campaign,
        channel: ChannelType,
        target: CampaignTarget
    ) -> CampaignExecution:
        """Deploy campaign to a specific channel and target."""
        logger.info(f"Deploying to {channel.value} for target {target.name}")
        
        execution = CampaignExecution(
            id=f"exec-{campaign.id}-{channel.value}-{target.id}",
            campaign_id=campaign.id,
            channel=channel,
            target=target,
            scheduled_at=campaign.start_date or datetime.utcnow(),
            status=CampaignStatus.RUNNING
        )
        
        # Simulate deployment
        await asyncio.sleep(0.1)
        
        # Simulate performance metrics
        execution.impressions = target.size
        execution.clicks = int(target.size * 0.05)  # 5% CTR
        execution.conversions = int(execution.clicks * 0.1)  # 10% conversion
        execution.cost = (execution.impressions / 1000) * 5  # $5 CPM
        
        execution.started_at = datetime.utcnow()
        execution.completed_at = datetime.utcnow()
        execution.status = CampaignStatus.COMPLETED
        
        self.executions.append(execution)
        
        logger.info(f"Execution complete: {execution.impressions} impressions, {execution.conversions} conversions")
        
        return execution
    
    async def monitor_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Monitor campaign performance.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Performance metrics
        """
        logger.info(f"Monitoring campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        db_campaign = None
        
        if not campaign and self.db_session:
            from app.models import Campaign as DbCampaign
            db_campaign = self.db_session.query(DbCampaign).filter(DbCampaign.id == campaign_id).first()
            if db_campaign:
                metrics = db_campaign.metrics or {}
                return {
                    "campaign_id": campaign_id,
                    "campaign_name": db_campaign.name,
                    "status": db_campaign.status,
                    "total_impressions": metrics.get("total_impressions", 0),
                    "total_clicks": metrics.get("total_clicks", 0),
                    "total_conversions": metrics.get("total_conversions", 0),
                    "total_cost": metrics.get("total_cost", 0),
                    "ctr": metrics.get("ctr", 0.0),
                    "conversion_rate": metrics.get("conversion_rate", 0.0),
                    "roi": metrics.get("roi", 0.0),
                    "executions": metrics.get("executions", 0),
                    "channels": plan.get("channels", []) if (plan := db_campaign.deployment_plan) else []
                }
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None
        
        # Aggregate metrics
        total_impressions = sum(e.impressions for e in campaign.executions)
        total_clicks = sum(e.clicks for e in campaign.executions)
        total_conversions = sum(e.conversions for e in campaign.executions)
        total_cost = sum(e.cost for e in campaign.executions)
        
        # Calculate metrics
        ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        conversion_rate = total_conversions / total_clicks if total_clicks > 0 else 0
        cpc = total_cost / total_clicks if total_clicks > 0 else 0
        roi = (total_conversions * 100 - total_cost) / total_cost if total_cost > 0 else 0
        
        metrics = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_cost": total_cost,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
            "cpc": cpc,
            "roi": roi,
            "executions": len(campaign.executions),
            "channels": [c.value for c in campaign.channels]
        }
        
        logger.info(f"Campaign metrics: CTR={ctr:.2%}, Conversions={total_conversions}, ROI={roi:.2%}")
        
        return metrics
    
    async def pause_campaign(self, campaign_id: str) -> Campaign:
        """
        Pause a running campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Updated campaign
        """
        logger.info(f"Pausing campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None
        
        campaign.status = CampaignStatus.PAUSED
        
        # Pause all executions
        for execution in campaign.executions:
            if execution.status == CampaignStatus.RUNNING:
                execution.status = CampaignStatus.PAUSED
        
        logger.info(f"Campaign paused")
        
        return campaign
    
    async def resume_campaign(self, campaign_id: str) -> Campaign:
        """
        Resume a paused campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Updated campaign
        """
        logger.info(f"Resuming campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None
        
        campaign.status = CampaignStatus.RUNNING
        
        # Resume all executions
        for execution in campaign.executions:
            if execution.status == CampaignStatus.PAUSED:
                execution.status = CampaignStatus.RUNNING
        
        logger.info(f"Campaign resumed")
        
        return campaign
    
    async def stop_campaign(self, campaign_id: str) -> Campaign:
        """
        Stop a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Updated campaign
        """
        logger.info(f"Stopping campaign: {campaign_id}")
        
        campaign = self.campaigns.get(campaign_id)
        
        if not campaign:
            logger.error(f"Campaign not found: {campaign_id}")
            return None
        
        campaign.status = CampaignStatus.COMPLETED
        
        # Complete all executions
        for execution in campaign.executions:
            if execution.status in [CampaignStatus.RUNNING, CampaignStatus.PAUSED]:
                execution.status = CampaignStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
        
        logger.info(f"Campaign stopped")
        
        return campaign
    
    def get_campaign_status(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign status."""
        campaign = self.campaigns.get(campaign_id)
        
        if not campaign:
            return None
        
        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status.value,
            "channels": [c.value for c in campaign.channels],
            "targets": len(campaign.targets),
            "executions": len(campaign.executions),
            "budget": campaign.budget,
            "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None
        }
    
    def get_campaigns(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of campaigns."""
        campaigns = []
        
        for campaign in list(self.campaigns.values())[-limit:]:
            campaigns.append({
                "id": campaign.id,
                "name": campaign.name,
                "status": campaign.status.value,
                "channels": len(campaign.channels),
                "targets": len(campaign.targets),
                "budget": campaign.budget,
                "created_at": campaign.created_at.isoformat()
            })
        
        return campaigns


# Convenience function
async def deploy_marketing_campaign(
    name: str,
    assets: List[Dict[str, Any]],
    targets: List[CampaignTarget],
    channels: List[ChannelType],
    budget: float,
    db_session=None
) -> Dict[str, Any]:
    """
    Deploy a marketing campaign.
    
    Args:
        name: Campaign name
        assets: Marketing assets
        targets: Target audiences
        channels: Distribution channels
        budget: Campaign budget
        db_session: Database session
        
    Returns:
        Deployment result
    """
    agent = AttackAgent(db_session)
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30)
    
    campaign = await agent.create_campaign(
        name=name,
        description=f"Campaign: {name}",
        assets=assets,
        targets=targets,
        channels=channels,
        budget=budget,
        start_date=start_date,
        end_date=end_date
    )
    
    return await agent.deploy_campaign(campaign.id)
