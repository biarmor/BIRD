"""
Forge Agent - Asset and Content Generation

Generates marketing assets, content, and creative materials based on intelligence insights.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """Types of assets that can be generated."""
    SOCIAL_POST = "social_post"
    EMAIL_CAMPAIGN = "email_campaign"
    BLOG_POST = "blog_post"
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"
    INFOGRAPHIC = "infographic"
    VIDEO_SCRIPT = "video_script"
    PRESENTATION = "presentation"


class ContentTone(str, Enum):
    """Tone of generated content."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    URGENT = "urgent"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"


@dataclass
class GeneratedAsset:
    """Generated asset."""
    id: str
    asset_type: AssetType
    title: str
    content: str
    metadata: Dict[str, Any]
    tone: ContentTone
    quality_score: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ForgeAgent:
    """
    Forge Agent - Asset and Content Generation
    
    Capabilities:
    - Marketing asset generation
    - Content creation
    - Copy writing
    - Multi-format output
    - Quality scoring
    - Version management
    """
    
    def __init__(self, db_session=None):
        """
        Initialize Forge Agent.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.generated_assets = []
        self.asset_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load asset templates."""
        return {
            AssetType.SOCIAL_POST: "Social Post Template: {content}",
            AssetType.EMAIL_CAMPAIGN: "Email Subject: {subject}\n\nBody: {content}",
            AssetType.BLOG_POST: "# {title}\n\n{content}",
            AssetType.AD_COPY: "Headline: {headline}\n\nBody: {content}\n\nCTA: {cta}",
            AssetType.VIDEO_SCRIPT: "[SCENE] {scene}\n[VOICEOVER] {content}",
        }
    
    async def generate_asset(
        self,
        asset_type: AssetType,
        context: Dict[str, Any],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        workspace_id: str = ""
    ) -> GeneratedAsset:
        """
        Generate a marketing asset.
        
        Args:
            asset_type: Type of asset to generate
            context: Context information for generation
            tone: Tone of the content
            workspace_id: Workspace ID
            
        Returns:
            Generated asset
        """
        logger.info(f"Generating {asset_type.value} asset with {tone.value} tone")
        
        # Generate content based on type
        if asset_type == AssetType.SOCIAL_POST:
            content = await self._generate_social_post(context, tone)
        elif asset_type == AssetType.EMAIL_CAMPAIGN:
            content = await self._generate_email_campaign(context, tone)
        elif asset_type == AssetType.BLOG_POST:
            content = await self._generate_blog_post(context, tone)
        elif asset_type == AssetType.AD_COPY:
            content = await self._generate_ad_copy(context, tone)
        elif asset_type == AssetType.VIDEO_SCRIPT:
            content = await self._generate_video_script(context, tone)
        else:
            content = await self._generate_generic_content(context, tone)
        
        # Calculate quality score
        quality_score = await self._calculate_quality_score(content, asset_type)
        
        # Create asset
        asset = GeneratedAsset(
            id=f"asset-{workspace_id}-{datetime.utcnow().timestamp()}",
            asset_type=asset_type,
            title=context.get("title", f"Generated {asset_type.value}"),
            content=content,
            metadata=context,
            tone=tone,
            quality_score=quality_score
        )
        
        self.generated_assets.append(asset)
        
        logger.info(f"Asset generated: {asset.id}, quality={quality_score:.2f}")
        
        return asset
    
    async def _generate_social_post(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate social media post."""
        # Placeholder: In production, use LLM
        topic = context.get("topic", "General update")
        hashtags = context.get("hashtags", ["#update"])
        
        post = f"Check out this: {topic}\n\n"
        post += " ".join(hashtags)
        
        return post
    
    async def _generate_email_campaign(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate email campaign."""
        # Placeholder: In production, use LLM
        subject = context.get("subject", "Important Update")
        body = context.get("body", "We have exciting news to share with you.")
        
        email = f"Subject: {subject}\n\n{body}"
        
        return email
    
    async def _generate_blog_post(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate blog post."""
        # Placeholder: In production, use LLM
        title = context.get("title", "Untitled")
        topic = context.get("topic", "General topic")
        
        post = f"# {title}\n\n"
        post += f"## Introduction\n{topic}\n\n"
        post += f"## Main Content\nDetailed content about {topic}\n\n"
        post += "## Conclusion\nSummary and call to action"
        
        return post
    
    async def _generate_ad_copy(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate advertising copy."""
        # Placeholder: In production, use LLM
        headline = context.get("headline", "Amazing Offer")
        body = context.get("body", "Limited time offer")
        cta = context.get("cta", "Learn More")
        
        copy = f"Headline: {headline}\n\nBody: {body}\n\nCTA: {cta}"
        
        return copy
    
    async def _generate_video_script(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate video script."""
        # Placeholder: In production, use LLM
        scene = context.get("scene", "Office setting")
        voiceover = context.get("voiceover", "Welcome to our video")
        
        script = f"[SCENE] {scene}\n[VOICEOVER] {voiceover}"
        
        return script
    
    async def _generate_generic_content(
        self,
        context: Dict[str, Any],
        tone: ContentTone
    ) -> str:
        """Generate generic content."""
        topic = context.get("topic", "General content")
        return f"Content about {topic} in {tone.value} tone"
    
    async def _calculate_quality_score(
        self,
        content: str,
        asset_type: AssetType
    ) -> float:
        """
        Calculate quality score for generated content.
        
        Args:
            content: Generated content
            asset_type: Type of asset
            
        Returns:
            Quality score (0-1)
        """
        score = 0.0
        
        # Check content length
        if len(content) > 50:
            score += 0.3
        
        # Check for variety
        words = content.split()
        unique_words = len(set(words))
        if unique_words > 20:
            score += 0.3
        
        # Check for structure
        if "\n" in content:
            score += 0.2
        
        # Check for completeness
        if len(content) > 100:
            score += 0.2
        
        return min(score, 1.0)
    
    async def generate_campaign(
        self,
        campaign_name: str,
        campaign_type: str,
        context: Dict[str, Any],
        num_variations: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a complete marketing campaign with variations.
        
        Args:
            campaign_name: Name of campaign
            campaign_type: Type of campaign
            context: Campaign context
            num_variations: Number of variations to generate
            
        Returns:
            Campaign with variations
        """
        logger.info(f"Generating campaign: {campaign_name}")
        
        campaign = {
            "name": campaign_name,
            "type": campaign_type,
            "created_at": datetime.utcnow().isoformat(),
            "variations": []
        }
        
        # Generate variations
        tones = [ContentTone.PROFESSIONAL, ContentTone.CASUAL, ContentTone.INSPIRATIONAL]
        
        for idx in range(min(num_variations, len(tones))):
            tone = tones[idx]
            
            # Determine asset type based on campaign type
            if campaign_type == "social":
                asset_type = AssetType.SOCIAL_POST
            elif campaign_type == "email":
                asset_type = AssetType.EMAIL_CAMPAIGN
            elif campaign_type == "blog":
                asset_type = AssetType.BLOG_POST
            elif campaign_type == "ads":
                asset_type = AssetType.AD_COPY
            else:
                asset_type = AssetType.SOCIAL_POST
            
            # Generate asset
            asset = await self.generate_asset(
                asset_type=asset_type,
                context=context,
                tone=tone,
                workspace_id=campaign_name
            )
            
            campaign["variations"].append({
                "id": asset.id,
                "tone": tone.value,
                "content": asset.content,
                "quality_score": asset.quality_score
            })
        
        logger.info(f"Campaign generated: {len(campaign['variations'])} variations")
        
        return campaign
    
    async def optimize_content(
        self,
        content: str,
        asset_type: AssetType,
        optimization_goal: str = "engagement"
    ) -> str:
        """
        Optimize existing content.
        
        Args:
            content: Content to optimize
            asset_type: Type of asset
            optimization_goal: Goal for optimization
            
        Returns:
            Optimized content
        """
        logger.info(f"Optimizing content for {optimization_goal}")
        
        # Placeholder: In production, use LLM for optimization
        optimized = content
        
        if optimization_goal == "engagement":
            optimized = content + "\n\nCall to action: Engage with us!"
        elif optimization_goal == "conversion":
            optimized = content + "\n\nLimited time offer - Act now!"
        elif optimization_goal == "clarity":
            optimized = content + "\n\nLearn more about this topic."
        
        return optimized
    
    def get_generated_assets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of generated assets."""
        assets = []
        
        for asset in self.generated_assets[-limit:]:
            assets.append({
                "id": asset.id,
                "type": asset.asset_type.value,
                "title": asset.title,
                "tone": asset.tone.value,
                "quality_score": asset.quality_score,
                "created_at": asset.created_at.isoformat()
            })
        
        return assets


# Convenience function
async def generate_marketing_asset(
    asset_type: AssetType,
    context: Dict[str, Any],
    tone: ContentTone = ContentTone.PROFESSIONAL,
    db_session=None
) -> GeneratedAsset:
    """
    Generate a marketing asset.
    
    Args:
        asset_type: Type of asset
        context: Context information
        tone: Tone of content
        db_session: Database session
        
    Returns:
        Generated asset
    """
    agent = ForgeAgent(db_session)
    return await agent.generate_asset(asset_type, context, tone)
