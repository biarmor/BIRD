"""
Adaptive Planning Tests

Unit and integration tests for adaptive planning and RAR agents.
"""

import pytest
import asyncio
from app.agents.adaptive_planning_agent import (
    AdaptivePlanningAgent, ExecutionPlan, PlanTask, PlanStatus, TaskPriority,
    create_and_execute_plan
)
from app.agents.rar_agent import RARAgent, reason_with_retrieval


class TestAdaptivePlanningAgent:
    """Test Adaptive Planning Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_plan_creation(self):
        """Test plan creation."""
        agent = AdaptivePlanningAgent()
        
        plan = await agent.create_plan(
            query="Analyze market trends",
            workspace_id="test-workspace",
            agents_needed=["vault", "reasoning", "debate"],
            context={}
        )
        
        assert plan.query == "Analyze market trends"
        assert len(plan.tasks) == 3
        assert plan.status == PlanStatus.CREATED
        assert plan.total_estimated_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test task creation."""
        agent = AdaptivePlanningAgent()
        
        tasks = await agent._create_tasks(
            query="Test query",
            agents_needed=["vault", "reasoning"],
            context={}
        )
        
        assert len(tasks) == 2
        assert all(isinstance(t, PlanTask) for t in tasks)
        assert all(t.status == "pending" for t in tasks)
    
    @pytest.mark.asyncio
    async def test_priority_calculation(self):
        """Test priority calculation."""
        agent = AdaptivePlanningAgent()
        
        tasks = await agent._create_tasks(
            query="Test query",
            agents_needed=["vault", "reasoning", "debate"],
            context={}
        )
        
        tasks = await agent._calculate_priorities(tasks, {})
        
        assert tasks[0].priority == TaskPriority.CRITICAL
        assert tasks[1].priority == TaskPriority.HIGH
        assert tasks[2].priority == TaskPriority.LOW
    
    @pytest.mark.asyncio
    async def test_plan_execution(self):
        """Test plan execution."""
        agent = AdaptivePlanningAgent()
        
        plan = await agent.create_plan(
            query="Test query",
            workspace_id="test-workspace",
            agents_needed=["vault", "reasoning"],
            context={}
        )
        
        result = await agent.execute_plan(plan)
        
        assert result["status"] in ["completed", "adjusted"]
        assert "results" in result
        assert "confidence" in result
        assert result["total_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_plan_adjustment(self):
        """Test plan adjustment."""
        agent = AdaptivePlanningAgent()
        
        plan = await agent.create_plan(
            query="Test query",
            workspace_id="test-workspace",
            agents_needed=["vault"],
            context={}
        )
        
        # Create evaluation that requires adjustment
        evaluation = {
            "time_variance": 0.5,
            "success_rate": 0.7,
            "needs_adjustment": True,
            "reason": "Significant time variance"
        }
        
        await agent._adjust_plan(plan, evaluation)
        
        assert plan.adjustments_made == 1
    
    @pytest.mark.asyncio
    async def test_execution_evaluation(self):
        """Test execution evaluation."""
        agent = AdaptivePlanningAgent()
        
        plan = await agent.create_plan(
            query="Test query",
            workspace_id="test-workspace",
            agents_needed=["vault"],
            context={}
        )
        
        # Execute tasks
        results = await agent._execute_tasks(plan)
        
        # Evaluate
        evaluation = await agent._evaluate_execution(plan, results)
        
        assert "success_rate" in evaluation
        assert "time_variance" in evaluation
        assert "confidence" in evaluation
    
    def test_plan_status(self):
        """Test getting plan status."""
        agent = AdaptivePlanningAgent()
        
        # No plans yet
        status = agent.get_plan_status("non-existent")
        assert status is None
    
    def test_plan_history(self):
        """Test getting plan history."""
        agent = AdaptivePlanningAgent()
        
        history = agent.get_plan_history()
        
        assert isinstance(history, list)
        assert len(history) == 0  # No plans yet
    
    @pytest.mark.asyncio
    async def test_replan_on_failure(self):
        """Test replanning on failure."""
        agent = AdaptivePlanningAgent()
        
        plan = await agent.create_plan(
            query="Test query",
            workspace_id="test-workspace",
            agents_needed=["vault"],
            context={}
        )
        
        # Simulate failure
        new_plan = await agent.replan_on_failure(
            plan=plan,
            failed_task_id="task-0",
            context={}
        )
        
        assert new_plan is not None


class TestRARAgent:
    """Test Retrieval-Augmented Reasoning Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_rar_reasoning(self):
        """Test RAR reasoning."""
        agent = RARAgent()
        
        result = await agent.reason_with_retrieval(
            query="Why did market share decline?",
            workspace_id="test-workspace",
            max_hops=2
        )
        
        assert "steps" in result
        assert "final_conclusion" in result
        assert "confidence" in result
        assert len(result["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_retrieval_context(self):
        """Test retrieval context creation."""
        agent = RARAgent()
        
        context = await agent._retrieve_facts(
            query="Test query",
            workspace_id="test-workspace",
            hop_number=1
        )
        
        assert context.query == "Test query"
        assert len(context.retrieved_facts) > 0
        assert len(context.relevance_scores) == len(context.retrieved_facts)
        assert context.hop_number == 1
    
    @pytest.mark.asyncio
    async def test_reasoning_with_context(self):
        """Test reasoning with retrieved context."""
        agent = RARAgent()
        
        context = await agent._retrieve_facts(
            query="Test query",
            workspace_id="test-workspace",
            hop_number=1
        )
        
        step = await agent._reason_with_context(
            query="Test query",
            retrieval_context=context,
            step_number=1
        )
        
        assert step.step_number == 1
        assert step.query == "Test query"
        assert step.confidence > 0
        assert len(step.evidence_used) > 0
    
    @pytest.mark.asyncio
    async def test_next_query_generation(self):
        """Test next query generation."""
        agent = RARAgent()
        
        context = await agent._retrieve_facts(
            query="Test query",
            workspace_id="test-workspace",
            hop_number=1
        )
        
        step = await agent._reason_with_context(
            query="Test query",
            retrieval_context=context,
            step_number=1
        )
        
        next_query = await agent._generate_next_query(
            current_query="Test query",
            retrieval_context=context,
            reasoning_step=step
        )
        
        assert isinstance(next_query, str)
        assert len(next_query) > 0
    
    @pytest.mark.asyncio
    async def test_reasoning_verification(self):
        """Test reasoning verification."""
        agent = RARAgent()
        
        result = await agent.verify_reasoning(
            conclusion="Market share declined due to competition",
            evidence=["Evidence 1", "Evidence 2", "Evidence 3"]
        )
        
        assert "conclusion" in result
        assert "evidence_count" in result
        assert "verification_confidence" in result
        assert "verified" in result
    
    @pytest.mark.asyncio
    async def test_reasoning_explanation(self):
        """Test reasoning explanation."""
        agent = RARAgent()
        
        # Perform reasoning first
        await agent.reason_with_retrieval(
            query="Test query",
            workspace_id="test-workspace",
            max_hops=2
        )
        
        # Get explanation
        explanation = await agent.explain_reasoning()
        
        assert "total_steps" in explanation
        assert "total_retrieved_facts" in explanation
        assert "average_confidence" in explanation
        assert "reasoning_chain" in explanation


class TestIntegrationPhase3:
    """Integration tests for Phase 3."""
    
    @pytest.mark.asyncio
    async def test_full_adaptive_planning_flow(self):
        """Test full adaptive planning flow."""
        result = await create_and_execute_plan(
            query="Analyze market trends",
            workspace_id="test-workspace",
            agents_needed=["vault", "reasoning"],
            context={}
        )
        
        assert "plan_id" in result
        assert "status" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_rar_flow(self):
        """Test RAR flow."""
        result = await reason_with_retrieval(
            query="Why did market share decline?",
            workspace_id="test-workspace",
            max_hops=3
        )
        
        assert "steps" in result
        assert "final_conclusion" in result
        assert len(result["steps"]) > 0
