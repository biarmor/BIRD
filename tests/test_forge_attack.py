"""
Forge and Attack Agent Tests

Unit and integration tests for asset generation and campaign deployment.
"""

import pytest
from datetime import datetime, timedelta
from app.agents.forge_agent import (
    ForgeAgent, AssetType, ContentTone, GeneratedAsset, generate_marketing_asset
)
from app.agents.attack_agent import (
    AttackAgent, CampaignStatus, ChannelType, CampaignTarget, Campaign,
    deploy_marketing_campaign
)


class TestForgeAgent:
    """Test Forge Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_social_post_generation(self):
        """Test social media post generation."""
        agent = ForgeAgent()
        
        context = {
            "topic": "New product launch",
            "hashtags": ["#launch", "#product"]
        }
        
        asset = await agent.generate_asset(
            asset_type=AssetType.SOCIAL_POST,
            context=context,
            tone=ContentTone.PROFESSIONAL
        )
        
        assert asset.asset_type == AssetType.SOCIAL_POST
        assert asset.tone == ContentTone.PROFESSIONAL
        assert len(asset.content) > 0
        assert asset.quality_score > 0
    
    @pytest.mark.asyncio
    async def test_email_campaign_generation(self):
        """Test email campaign generation."""
        agent = ForgeAgent()
        
        context = {
            "subject": "Exclusive Offer",
            "body": "Limited time offer for our valued customers"
        }
        
        asset = await agent.generate_asset(
            asset_type=AssetType.EMAIL_CAMPAIGN,
            context=context,
            tone=ContentTone.URGENT
        )
        
        assert asset.asset_type == AssetType.EMAIL_CAMPAIGN
        assert asset.tone == ContentTone.URGENT
        assert "Subject:" in asset.content
    
    @pytest.mark.asyncio
    async def test_blog_post_generation(self):
        """Test blog post generation."""
        agent = ForgeAgent()
        
        context = {
            "title": "10 Tips for Success",
            "topic": "Business growth strategies"
        }
        
        asset = await agent.generate_asset(
            asset_type=AssetType.BLOG_POST,
            context=context,
            tone=ContentTone.EDUCATIONAL
        )
        
        assert asset.asset_type == AssetType.BLOG_POST
        assert "#" in asset.content  # Markdown headers
    
    @pytest.mark.asyncio
    async def test_ad_copy_generation(self):
        """Test advertising copy generation."""
        agent = ForgeAgent()
        
        context = {
            "headline": "Transform Your Business",
            "body": "Our solution helps you achieve your goals",
            "cta": "Start Free Trial"
        }
        
        asset = await agent.generate_asset(
            asset_type=AssetType.AD_COPY,
            context=context,
            tone=ContentTone.INSPIRATIONAL
        )
        
        assert asset.asset_type == AssetType.AD_COPY
        assert "Headline:" in asset.content
        assert "CTA:" in asset.content
    
    @pytest.mark.asyncio
    async def test_video_script_generation(self):
        """Test video script generation."""
        agent = ForgeAgent()
        
        context = {
            "scene": "Modern office with team",
            "voiceover": "Welcome to our company"
        }
        
        asset = await agent.generate_asset(
            asset_type=AssetType.VIDEO_SCRIPT,
            context=context,
            tone=ContentTone.PROFESSIONAL
        )
        
        assert asset.asset_type == AssetType.VIDEO_SCRIPT
        assert "[SCENE]" in asset.content
        assert "[VOICEOVER]" in asset.content
    
    @pytest.mark.asyncio
    async def test_quality_scoring(self):
        """Test quality scoring."""
        agent = ForgeAgent()
        
        # Short content
        score1 = await agent._calculate_quality_score("Short", AssetType.SOCIAL_POST)
        
        # Long, detailed content
        long_content = " ".join(["word"] * 100)
        score2 = await agent._calculate_quality_score(long_content, AssetType.BLOG_POST)
        
        assert score2 > score1
    
    @pytest.mark.asyncio
    async def test_campaign_generation(self):
        """Test campaign generation with variations."""
        agent = ForgeAgent()
        
        context = {
            "topic": "New product launch",
            "headline": "Revolutionary Product"
        }
        
        campaign = await agent.generate_campaign(
            campaign_name="Product Launch 2024",
            campaign_type="social",
            context=context,
            num_variations=3
        )
        
        assert campaign["name"] == "Product Launch 2024"
        assert len(campaign["variations"]) == 3
        assert all("tone" in v for v in campaign["variations"])
    
    @pytest.mark.asyncio
    async def test_content_optimization(self):
        """Test content optimization."""
        agent = ForgeAgent()
        
        original = "Check out our new product"
        
        optimized_engagement = await agent.optimize_content(
            content=original,
            asset_type=AssetType.SOCIAL_POST,
            optimization_goal="engagement"
        )
        
        assert len(optimized_engagement) > len(original)
        assert "engagement" in optimized_engagement.lower() or "action" in optimized_engagement.lower()
    
    def test_asset_tracking(self):
        """Test asset tracking."""
        agent = ForgeAgent()
        
        assets = agent.get_generated_assets()
        
        assert isinstance(assets, list)
        assert len(assets) == 0  # No assets yet


class TestAttackAgent:
    """Test Attack Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_campaign_creation(self):
        """Test campaign creation."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000,
            interests=["tech", "innovation"]
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Tech Product Launch",
            description="Launch campaign for new tech product",
            assets=[{"type": "social_post", "content": "Check out our new product"}],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        assert campaign.name == "Tech Product Launch"
        assert campaign.status == CampaignStatus.DRAFT
        assert len(campaign.targets) == 1
        assert campaign.budget == 5000
    
    @pytest.mark.asyncio
    async def test_campaign_scheduling(self):
        """Test campaign scheduling."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Test Campaign",
            description="Test",
            assets=[],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        scheduled = await agent.schedule_campaign(
            campaign_id=campaign.id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert scheduled.status == CampaignStatus.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_campaign_deployment(self):
        """Test campaign deployment."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Test Campaign",
            description="Test",
            assets=[{"type": "social_post"}],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA, ChannelType.EMAIL],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        result = await agent.deploy_campaign(campaign.id)
        
        assert result["status"] == "deployed"
        assert result["executions"] > 0
    
    @pytest.mark.asyncio
    async def test_campaign_monitoring(self):
        """Test campaign monitoring."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Test Campaign",
            description="Test",
            assets=[],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        await agent.deploy_campaign(campaign.id)
        
        metrics = await agent.monitor_campaign(campaign.id)
        
        assert metrics["campaign_id"] == campaign.id
        assert "total_impressions" in metrics
        assert "ctr" in metrics
        assert "roi" in metrics
    
    @pytest.mark.asyncio
    async def test_campaign_pause_resume(self):
        """Test campaign pause and resume."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Test Campaign",
            description="Test",
            assets=[],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        await agent.deploy_campaign(campaign.id)
        
        # Pause
        paused = await agent.pause_campaign(campaign.id)
        assert paused.status == CampaignStatus.PAUSED
        
        # Resume
        resumed = await agent.resume_campaign(campaign.id)
        assert resumed.status == CampaignStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_campaign_stop(self):
        """Test campaign stop."""
        agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await agent.create_campaign(
            name="Test Campaign",
            description="Test",
            assets=[],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        await agent.deploy_campaign(campaign.id)
        
        stopped = await agent.stop_campaign(campaign.id)
        assert stopped.status == CampaignStatus.COMPLETED
    
    def test_campaign_status(self):
        """Test getting campaign status."""
        agent = AttackAgent()
        
        status = agent.get_campaign_status("non-existent")
        assert status is None
    
    def test_campaigns_list(self):
        """Test getting campaigns list."""
        agent = AttackAgent()
        
        campaigns = agent.get_campaigns()
        
        assert isinstance(campaigns, list)
        assert len(campaigns) == 0  # No campaigns yet


class TestIntegrationPhase4:
    """Integration tests for Phase 4."""
    
    @pytest.mark.asyncio
    async def test_forge_to_attack_flow(self):
        """Test flow from Forge to Attack."""
        # Generate asset with Forge
        forge_agent = ForgeAgent()
        
        asset = await forge_agent.generate_asset(
            asset_type=AssetType.SOCIAL_POST,
            context={"topic": "New product"},
            tone=ContentTone.PROFESSIONAL
        )
        
        # Deploy with Attack
        attack_agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-1",
            name="Tech Enthusiasts",
            description="People interested in technology",
            size=50000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await attack_agent.create_campaign(
            name="Generated Asset Campaign",
            description="Campaign using generated asset",
            assets=[{"id": asset.id, "content": asset.content}],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=5000,
            start_date=start_date,
            end_date=end_date
        )
        
        result = await attack_agent.deploy_campaign(campaign.id)
        
        assert result["status"] == "deployed"
