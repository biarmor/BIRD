"""
Orchestration Tests

Unit and integration tests for multi-agent orchestration.
"""

import pytest
import asyncio
from app.agents.orchestrator_agent import (
    OrchestratorAgent, AgentType, ExecutionMode, AgentTask, orchestrate_query
)
from app.agents.reasoning_agent import ReasoningAgent, reason_about_query
from app.agents.debate_agent import DebateAgent, debate_conclusion
from datetime import datetime


class TestOrchestratorAgent:
    """Test Orchestrator Agent functionality."""
    
    def test_agent_registration(self):
        """Test agent registration."""
        orchestrator = OrchestratorAgent()
        
        assert len(orchestrator.agent_registry) == 6
        assert AgentType.VAULT in orchestrator.agent_registry
        assert AgentType.RADAR in orchestrator.agent_registry
        assert AgentType.REASONING in orchestrator.agent_registry
        assert AgentType.DEBATE in orchestrator.agent_registry
    
    def test_query_analysis_web_search(self):
        """Test query analysis for web search."""
        orchestrator = OrchestratorAgent()
        
        agents, mode = orchestrator.analyze_query("Find competitor news on the market")
        
        assert AgentType.RADAR in agents
        assert AgentType.VAULT in agents
    
    def test_query_analysis_reasoning(self):
        """Test query analysis for reasoning."""
        orchestrator = OrchestratorAgent()
        
        agents, mode = orchestrator.analyze_query("Why did our market share decline?")
        
        assert AgentType.REASONING in agents
    
    def test_query_analysis_debate(self):
        """Test query analysis for debate."""
        orchestrator = OrchestratorAgent()
        
        agents, mode = orchestrator.analyze_query("Debate the pros and cons of this strategy")
        
        assert AgentType.DEBATE in agents
    
    def test_execution_mode_selection(self):
        """Test execution mode selection."""
        orchestrator = OrchestratorAgent()
        
        # Single agent should be sequential
        agents, mode = orchestrator.analyze_query("Search vault for facts")
        assert mode == ExecutionMode.SEQUENTIAL
        
        # Multiple agents should be parallel
        agents, mode = orchestrator.analyze_query("Search web, reason about findings, and debate conclusions")
        assert mode == ExecutionMode.PARALLEL
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test task creation."""
        orchestrator = OrchestratorAgent()
        
        tasks = await orchestrator.create_tasks(
            query="Test query",
            workspace_id="test-workspace",
            agents=[AgentType.VAULT, AgentType.REASONING]
        )
        
        assert len(tasks) == 2
        assert tasks[0].agent_type == AgentType.VAULT
        assert tasks[1].agent_type == AgentType.REASONING
        assert tasks[0].priority > tasks[1].priority
    
    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test sequential task execution."""
        orchestrator = OrchestratorAgent()
        
        tasks = await orchestrator.create_tasks(
            query="Test query",
            workspace_id="test-workspace",
            agents=[AgentType.VAULT, AgentType.REASONING]
        )
        
        results = await orchestrator.execute_sequential(tasks)
        
        assert len(results) == 2
        assert all(r.status == "success" for r in results)
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel task execution."""
        orchestrator = OrchestratorAgent()
        
        tasks = await orchestrator.create_tasks(
            query="Test query",
            workspace_id="test-workspace",
            agents=[AgentType.VAULT, AgentType.REASONING, AgentType.DEBATE]
        )
        
        results = await orchestrator.execute_parallel(tasks)
        
        assert len(results) == 3
        assert all(r.status == "success" for r in results)
    
    @pytest.mark.asyncio
    async def test_orchestration(self):
        """Test full orchestration."""
        orchestrator = OrchestratorAgent()
        
        result = await orchestrator.orchestrate(
            query="Analyze market trends",
            workspace_id="test-workspace"
        )
        
        assert "query" in result
        assert "findings" in result
        assert "confidence" in result
        assert result["total_agents"] > 0
    
    def test_execution_history(self):
        """Test execution history tracking."""
        orchestrator = OrchestratorAgent()
        
        history = orchestrator.get_execution_history()
        
        assert isinstance(history, list)
        assert len(history) == 0  # No executions yet
    
    def test_agent_stats(self):
        """Test agent statistics."""
        orchestrator = OrchestratorAgent()
        
        stats = orchestrator.get_agent_stats()
        
        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 0
        assert stats["success_rate"] == 0.0


class TestReasoningAgent:
    """Test Reasoning Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_causality_analysis(self):
        """Test causality analysis."""
        agent = ReasoningAgent()
        
        result = await agent.analyze_causality(
            effect="Market share declined",
            context={"industry": "tech", "recent_events": ["competitor launch"]}
        )
        
        assert result["effect"] == "Market share declined"
        assert "potential_causes" in result
        assert "causal_chain" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_hypothesis_generation(self):
        """Test hypothesis generation."""
        agent = ReasoningAgent()
        
        observations = ["Observation 1", "Observation 2", "Observation 3"]
        
        hypotheses = await agent.generate_hypotheses(
            observations=observations,
            context={}
        )
        
        assert len(hypotheses) == 3
        assert all("hypothesis" in h for h in hypotheses)
    
    @pytest.mark.asyncio
    async def test_evidence_evaluation(self):
        """Test evidence evaluation."""
        agent = ReasoningAgent()
        
        result = await agent.evaluate_evidence(
            hypothesis="Market share decline is due to competition",
            evidence_items=["support evidence", "contradicting evidence", "neutral evidence"]
        )
        
        assert result["total_evidence"] == 3
        assert "support_score" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_reasoning_about_query(self):
        """Test reasoning about a query."""
        agent = ReasoningAgent()
        
        result = await agent.reason_about_query(
            query="Why did our revenue decline?",
            context={}
        )
        
        assert result["query"] == "Why did our revenue decline?"
        assert "concepts" in result
        assert "relationships" in result
        assert "conclusions" in result


class TestDebateAgent:
    """Test Debate Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_debate_conclusion(self):
        """Test debate on a conclusion."""
        agent = DebateAgent()
        
        result = await agent.debate_conclusion(
            conclusion="We should expand to new markets",
            context={},
            num_rounds=2
        )
        
        assert result["conclusion"] == "We should expand to new markets"
        assert "debate_rounds" in result
        assert len(result["debate_rounds"]) == 2
        assert "final_consensus" in result
    
    @pytest.mark.asyncio
    async def test_perspective_generation(self):
        """Test perspective generation."""
        agent = DebateAgent()
        
        perspectives = await agent._generate_perspectives(
            conclusion="Test conclusion",
            context={}
        )
        
        assert len(perspectives) == 4  # Optimistic, Pessimistic, Neutral, Skeptical
        assert all(p.confidence > 0 for p in perspectives)
    
    @pytest.mark.asyncio
    async def test_claim_validation(self):
        """Test claim validation."""
        agent = DebateAgent()
        
        result = await agent.validate_claim(
            claim="Our product is the best in market",
            evidence=["Evidence 1", "Evidence 2"],
            context={}
        )
        
        assert result["claim"] == "Our product is the best in market"
        assert "validity_score" in result
        assert "recommendation" in result
    
    @pytest.mark.asyncio
    async def test_conflict_resolution(self):
        """Test conflict resolution."""
        agent = DebateAgent()
        
        result = await agent.resolve_conflict(
            position1="We should focus on cost reduction",
            position2="We should invest in innovation",
            context={}
        )
        
        assert "position1" in result
        assert "position2" in result
        assert "synthesis" in result
        assert "resolution_confidence" in result


class TestIntegration:
    """Integration tests for multi-agent system."""
    
    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self):
        """Test full orchestration flow."""
        result = await orchestrate_query(
            query="Analyze market trends and debate strategy",
            workspace_id="test-workspace"
        )
        
        assert "query" in result
        assert "findings" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_reasoning_flow(self):
        """Test reasoning flow."""
        result = await reason_about_query(
            query="Why did our market share decline?",
            context={"industry": "tech"}
        )
        
        assert "query" in result
        assert "conclusions" in result
    
    @pytest.mark.asyncio
    async def test_debate_flow(self):
        """Test debate flow."""
        result = await debate_conclusion(
            conclusion="We should expand to new markets",
            context={},
            num_rounds=2
        )
        
        assert "conclusion" in result
        assert "final_consensus" in result
