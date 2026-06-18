"""
End-to-End Integration Tests

Complete workflow tests for the BIRD multi-agent system.
"""

import pytest
from datetime import datetime, timedelta
from app.agents.orchestrator_agent import orchestrate_query, ExecutionMode, OrchestratorAgent
from app.agents.vault_agent import VaultAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.debate_agent import DebateAgent
from app.agents.adaptive_planning_agent import AdaptivePlanningAgent
from app.agents.rar_agent import RARAgent
from app.agents.forge_agent import ForgeAgent, AssetType, ContentTone
from app.agents.attack_agent import AttackAgent, CampaignTarget, ChannelType


class TestEndToEndWorkflows:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_intelligence_analysis_workflow(self):
        """Test complete intelligence analysis workflow."""
        # Step 1: Query orchestration
        query = "Analyze market trends and competitive landscape"
        
        result = await orchestrate_query(
            query=query,
            workspace_id="e2e-test-1"
        )
        
        assert result["query"] == query
        assert "findings" in result
        assert result["confidence"] > 0
        
        # Step 2: Reasoning about findings
        reasoning_agent = ReasoningAgent()
        
        reasoning_result = await reasoning_agent.reason_about_query(
            query=query,
            context={"findings": result["findings"]}
        )
        
        assert "conclusions" in reasoning_result
        assert len(reasoning_result["conclusions"]) > 0
        
        # Step 3: Debate conclusions
        debate_agent = DebateAgent()
        
        debate_result = await debate_agent.debate_conclusion(
            conclusion=reasoning_result["conclusions"][0],
            context={"reasoning": reasoning_result}
        )
        
        assert "final_consensus" in debate_result
        assert debate_result["final_consensus"] >= 0
    
    @pytest.mark.asyncio
    async def test_adaptive_planning_with_rar(self):
        """Test adaptive planning with RAR."""
        # Step 1: Create adaptive plan
        planning_agent = AdaptivePlanningAgent()
        
        plan = await planning_agent.create_plan(
            query="Comprehensive market analysis",
            workspace_id="e2e-test-2",
            agents_needed=["vault", "reasoning", "debate"],
            context={}
        )
        
        assert len(plan.tasks) == 3
        
        # Step 2: Execute plan
        execution_result = await planning_agent.execute_plan(plan)
        
        assert execution_result["status"] in ["completed", "adjusted"]
        
        # Step 3: Perform RAR on results
        rar_agent = RARAgent()
        
        rar_result = await rar_agent.reason_with_retrieval(
            query="Analyze the findings from adaptive planning",
            workspace_id="e2e-test-2",
            max_hops=2
        )
        
        assert len(rar_result["steps"]) > 0
        assert "final_conclusion" in rar_result
    
    @pytest.mark.asyncio
    async def test_forge_to_attack_campaign_workflow(self):
        """Test complete Forge to Attack campaign workflow."""
        # Step 1: Generate marketing assets with Forge
        forge_agent = ForgeAgent()
        
        social_asset = await forge_agent.generate_asset(
            asset_type=AssetType.SOCIAL_POST,
            context={"topic": "New AI product launch", "hashtags": ["#AI", "#innovation"]},
            tone=ContentTone.INSPIRATIONAL
        )
        
        email_asset = await forge_agent.generate_asset(
            asset_type=AssetType.EMAIL_CAMPAIGN,
            context={"subject": "Introducing Our Latest Innovation", "body": "We're excited to announce..."},
            tone=ContentTone.PROFESSIONAL
        )
        
        assert social_asset.quality_score > 0
        assert email_asset.quality_score > 0
        
        # Step 2: Generate campaign variations
        campaign_variations = await forge_agent.generate_campaign(
            campaign_name="AI Product Launch 2024",
            campaign_type="social",
            context={"topic": "AI product", "headline": "Revolutionary AI Solution"},
            num_variations=3
        )
        
        assert len(campaign_variations["variations"]) == 3
        
        # Step 3: Deploy campaign with Attack
        attack_agent = AttackAgent()
        
        target = CampaignTarget(
            id="target-tech-enthusiasts",
            name="Tech Enthusiasts",
            description="People interested in AI and technology",
            size=100000,
            interests=["AI", "technology", "innovation"]
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await attack_agent.create_campaign(
            name="AI Product Launch Campaign",
            description="Multi-channel campaign for AI product",
            assets=[
                {"id": social_asset.id, "content": social_asset.content},
                {"id": email_asset.id, "content": email_asset.content}
            ],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA, ChannelType.EMAIL],
            budget=10000,
            start_date=start_date,
            end_date=end_date
        )
        
        deployment_result = await attack_agent.deploy_campaign(campaign.id)
        
        assert deployment_result["status"] == "deployed"
        assert deployment_result["executions"] > 0
        
        # Step 4: Monitor campaign
        metrics = await attack_agent.monitor_campaign(campaign.id)
        
        assert "total_impressions" in metrics
        assert "ctr" in metrics
        assert "roi" in metrics
    
    @pytest.mark.asyncio
    async def test_vault_to_reasoning_to_forge_workflow(self):
        """Test Vault → Reasoning → Forge workflow."""
        # Step 1: Query vault for facts
        vault_agent = VaultAgent()
        
        vault_result = await vault_agent.search_vault(
            query="customer feedback on product features",
            workspace_id="e2e-test-3",
            max_hops=2
        )
        
        assert "findings" in vault_result
        
        # Step 2: Reason about vault findings
        reasoning_agent = ReasoningAgent()
        
        reasoning_result = await reasoning_agent.reason_about_query(
            query="What are the key customer insights?",
            context={"vault_findings": vault_result}
        )
        
        assert "conclusions" in reasoning_result
        
        # Step 3: Generate marketing content based on reasoning
        forge_agent = ForgeAgent()
        
        blog_asset = await forge_agent.generate_asset(
            asset_type=AssetType.BLOG_POST,
            context={
                "title": "Customer Insights: What We Learned",
                "topic": reasoning_result["conclusions"][0] if reasoning_result["conclusions"] else "Customer feedback"
            },
            tone=ContentTone.EDUCATIONAL
        )
        
        assert blog_asset.asset_type == AssetType.BLOG_POST
        assert len(blog_asset.content) > 0
    
    @pytest.mark.asyncio
    async def test_multi_agent_orchestration_with_all_agents(self):
        """Test orchestration involving all agent types."""
        # Create a complex query that requires multiple agents
        query = "Analyze market trends, debate strategy options, and generate marketing content"
        
        # Step 1: Orchestrate query
        result = await orchestrate_query(
            query=query,
            workspace_id="e2e-test-4"
        )
        
        assert result["total_agents"] > 0
        assert result["confidence"] > 0
        
        # Step 2: Perform adaptive planning
        planning_agent = AdaptivePlanningAgent()
        
        plan = await planning_agent.create_plan(
            query=query,
            workspace_id="e2e-test-4",
            agents_needed=["vault", "reasoning", "debate", "forge"],
            context=result
        )
        
        assert len(plan.tasks) == 4
        
        # Step 3: Execute plan
        execution = await planning_agent.execute_plan(plan)
        
        assert execution["status"] in ["completed", "adjusted"]
        assert execution["confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_replanning(self):
        """Test error recovery and replanning."""
        planning_agent = AdaptivePlanningAgent()
        
        # Create initial plan
        plan = await planning_agent.create_plan(
            query="Test query",
            workspace_id="e2e-test-5",
            agents_needed=["vault"],
            context={}
        )
        
        # Simulate failure and replan
        new_plan = await planning_agent.replan_on_failure(
            plan=plan,
            failed_task_id="task-0",
            context={}
        )
        
        assert new_plan is not None
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test performance benchmarks."""
        import time
        
        # Benchmark orchestration
        start = time.time()
        result = await orchestrate_query(
            query="Quick market analysis",
            workspace_id="e2e-benchmark-1"
        )
        orchestration_time = time.time() - start
        
        assert orchestration_time < 5.0  # Should complete in under 5 seconds
        
        # Benchmark planning
        planning_agent = AdaptivePlanningAgent()
        
        start = time.time()
        plan = await planning_agent.create_plan(
            query="Test",
            workspace_id="e2e-benchmark-2",
            agents_needed=["vault", "reasoning"],
            context={}
        )
        planning_time = time.time() - start
        
        assert planning_time < 1.0  # Should complete in under 1 second
        
        # Benchmark asset generation
        forge_agent = ForgeAgent()
        
        start = time.time()
        asset = await forge_agent.generate_asset(
            asset_type=AssetType.SOCIAL_POST,
            context={"topic": "Test"},
            tone=ContentTone.PROFESSIONAL
        )
        generation_time = time.time() - start
        
        assert generation_time < 1.0  # Should complete in under 1 second


class TestSystemResilience:
    """Test system resilience and error handling."""
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when agents fail."""
        orchestrator = OrchestratorAgent()
        
        # Orchestrate with multiple agents
        result = await orchestrator.orchestrate(
            query="Test query",
            workspace_id="resilience-test-1"
        )
        
        # Should still return results even if some agents fail
        assert "findings" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_safety(self):
        """Test safety of concurrent execution."""
        import asyncio
        
        # Create multiple concurrent queries
        queries = [
            "Query 1: Market analysis",
            "Query 2: Competitive landscape",
            "Query 3: Customer insights"
        ]
        
        # Execute concurrently
        results = await asyncio.gather(
            *[orchestrate_query(q, f"concurrent-{i}") for i, q in enumerate(queries)]
        )
        
        # All should complete successfully
        assert len(results) == 3
        assert all("findings" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test behavior under resource constraints."""
        # Test with large number of tasks
        planning_agent = AdaptivePlanningAgent()
        
        plan = await planning_agent.create_plan(
            query="Large scale analysis",
            workspace_id="resource-test-1",
            agents_needed=["vault", "reasoning", "debate", "forge"] * 5,  # 20 agents
            context={}
        )
        
        # Should handle large number of tasks
        assert len(plan.tasks) == 20
        
        # Execution should complete
        result = await planning_agent.execute_plan(plan)
        assert result["status"] in ["completed", "adjusted"]


class TestDataConsistency:
    """Test data consistency across agents."""
    
    @pytest.mark.asyncio
    async def test_vault_consistency(self):
        """Test vault data consistency."""
        vault_agent = VaultAgent()
        
        # Add facts
        fact1 = await vault_agent.add_fact(
            fact="Market size is growing",
            category="market",
            workspace_id="consistency-test-1"
        )
        
        # Retrieve fact
        retrieved = await vault_agent.search_vault(
            query="market size",
            workspace_id="consistency-test-1"
        )
        
        # Data should be consistent
        assert len(retrieved["findings"]) > 0
    
    @pytest.mark.asyncio
    async def test_campaign_data_integrity(self):
        """Test campaign data integrity."""
        attack_agent = AttackAgent()
        
        target = CampaignTarget(
            id="integrity-test-1",
            name="Test Target",
            description="Test",
            size=10000
        )
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        campaign = await attack_agent.create_campaign(
            name="Integrity Test Campaign",
            description="Test",
            assets=[],
            targets=[target],
            channels=[ChannelType.SOCIAL_MEDIA],
            budget=1000,
            start_date=start_date,
            end_date=end_date
        )
        
        # Retrieve campaign
        status = attack_agent.get_campaign_status(campaign.id)
        
        # Data should match
        assert status["name"] == campaign.name
        assert status["budget"] == campaign.budget
