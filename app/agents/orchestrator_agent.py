"""
Orchestrator Agent - Multi-Agent Coordination

Coordinates multiple specialized agents, routes tasks, manages execution flow.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Agent execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class AgentType(str, Enum):
    """Available agent types."""
    ORCHESTRATOR = "orchestrator"
    RADAR = "radar"
    VAULT = "vault"
    REASONING = "reasoning"
    DEBATE = "debate"
    FORGE = "forge"
    ATTACK = "attack"


@dataclass
class AgentTask:
    """Task for agent execution."""
    id: str
    agent_type: AgentType
    query: str
    parameters: Dict[str, Any]
    priority: int = 5  # 1-10, higher is more important
    timeout_seconds: int = 300
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AgentExecutionResult:
    """Result from agent execution."""
    task_id: str
    agent_type: AgentType
    status: str  # success, failed, timeout
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    executed_at: datetime = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.utcnow()


class OrchestratorAgent:
    """
    Orchestrator Agent - Multi-Agent Coordination
    
    Responsibilities:
    - Task routing to appropriate agents
    - Execution scheduling (sequential, parallel, adaptive)
    - Result aggregation and synthesis
    - Error handling and recovery
    - Performance monitoring
    """
    
    def __init__(self, db_session=None):
        """
        Initialize Orchestrator Agent.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.execution_history = []
        self.active_tasks = {}
        self.agent_registry = {}
        self._register_agents()
    
    def _register_agents(self):
        """Register available agents."""
        self.agent_registry = {
            AgentType.VAULT: "VaultAgent",
            AgentType.RADAR: "RadarAgent",
            AgentType.REASONING: "ReasoningAgent",
            AgentType.DEBATE: "DebateAgent",
            AgentType.FORGE: "ForgeAgent",
            AgentType.ATTACK: "AttackAgent"
        }
        logger.info(f"Registered {len(self.agent_registry)} agents")
    
    def analyze_query(self, query: str) -> Tuple[List[AgentType], ExecutionMode]:
        """
        Analyze query to determine required agents and execution mode.
        
        Args:
            query: Intelligence query
            
        Returns:
            Tuple of (agent_types, execution_mode)
        """
        logger.info(f"Analyzing query: {query}")
        
        # Simple heuristic-based routing
        # In production, this would use ML-based classification
        
        agents_needed = []
        execution_mode = ExecutionMode.SEQUENTIAL
        
        query_lower = query.lower()
        
        # Determine agents
        if any(word in query_lower for word in ["web", "search", "news", "competitor", "market"]):
            agents_needed.append(AgentType.RADAR)
        
        if any(word in query_lower for word in ["memory", "history", "fact", "knowledge", "vault"]):
            agents_needed.append(AgentType.VAULT)
        
        if any(word in query_lower for word in ["why", "reason", "cause", "analysis", "explain"]):
            agents_needed.append(AgentType.REASONING)
        
        if any(word in query_lower for word in ["debate", "pros", "cons", "perspective", "validate"]):
            agents_needed.append(AgentType.DEBATE)
        
        if any(word in query_lower for word in ["create", "generate", "asset", "content", "forge"]):
            agents_needed.append(AgentType.FORGE)
        
        if any(word in query_lower for word in ["deploy", "campaign", "launch", "attack", "execute"]):
            agents_needed.append(AgentType.ATTACK)
        
        # Default to vault if no specific agents identified
        if not agents_needed:
            agents_needed = [AgentType.VAULT]
        
        # Determine execution mode
        if len(agents_needed) > 1:
            # Multiple agents can run in parallel
            execution_mode = ExecutionMode.PARALLEL
        
        logger.info(f"Query analysis: {len(agents_needed)} agents, mode: {execution_mode}")
        
        return agents_needed, execution_mode
    
    async def create_tasks(
        self,
        query: str,
        workspace_id: str,
        agents: List[AgentType]
    ) -> List[AgentTask]:
        """
        Create tasks for agents.
        
        Args:
            query: Intelligence query
            workspace_id: Workspace ID
            agents: List of agent types
            
        Returns:
            List of created tasks
        """
        tasks = []
        
        for idx, agent_type in enumerate(agents):
            task = AgentTask(
                id=f"task-{workspace_id}-{agent_type}-{idx}",
                agent_type=agent_type,
                query=query,
                parameters={
                    "workspace_id": workspace_id,
                    "query": query,
                    "agent_index": idx
                },
                priority=10 - idx  # First agents have higher priority
            )
            tasks.append(task)
            logger.info(f"Created task: {task.id}")
        
        return tasks
    
    async def execute_sequential(
        self,
        tasks: List[AgentTask]
    ) -> List[AgentExecutionResult]:
        """
        Execute tasks sequentially.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List of execution results
        """
        logger.info(f"Starting sequential execution of {len(tasks)} tasks")
        
        results = []
        
        for task in tasks:
            logger.info(f"Executing task: {task.id}")
            
            # Execute task (placeholder)
            result = await self._execute_task(task)
            results.append(result)
            
            # Store in history
            self.execution_history.append(result)
        
        logger.info(f"Sequential execution complete: {len(results)} results")
        return results
    
    async def execute_parallel(
        self,
        tasks: List[AgentTask]
    ) -> List[AgentExecutionResult]:
        """
        Execute tasks in parallel.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            List of execution results
        """
        logger.info(f"Starting parallel execution of {len(tasks)} tasks")
        
        # Create coroutines for all tasks
        coroutines = [self._execute_task(task) for task in tasks]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, AgentExecutionResult)]
        
        # Store in history
        for result in valid_results:
            self.execution_history.append(result)
        
        logger.info(f"Parallel execution complete: {len(valid_results)} results")
        return valid_results
    
    async def _execute_task(self, task: AgentTask) -> AgentExecutionResult:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Placeholder: In production, this would invoke the actual agent
            logger.info(f"Executing {task.agent_type} agent for query: {task.query}")
            
            # Simulate execution delay
            await asyncio.sleep(0.1)
            
            # Create result
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = AgentExecutionResult(
                task_id=task.id,
                agent_type=task.agent_type,
                status="success",
                result={
                    "agent": task.agent_type.value,
                    "query": task.query,
                    "findings": f"Findings from {task.agent_type.value} agent"
                },
                execution_time_ms=execution_time_ms,
                tokens_used=100,
                cost_estimate=0.01
            )
            
            logger.info(f"Task {task.id} completed in {execution_time_ms}ms")
            return result
        
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            
            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return AgentExecutionResult(
                task_id=task.id,
                agent_type=task.agent_type,
                status="failed",
                error_message=str(e),
                execution_time_ms=execution_time_ms
            )
    
    async def synthesize_results(
        self,
        results: List[AgentExecutionResult],
        query: str
    ) -> Dict[str, Any]:
        """
        Synthesize results from multiple agents.
        
        Args:
            results: List of execution results
            query: Original query
            
        Returns:
            Synthesized result
        """
        logger.info(f"Synthesizing {len(results)} results")
        
        successful_results = [r for r in results if r.status == "success"]
        failed_results = [r for r in results if r.status == "failed"]
        
        # Aggregate findings
        findings = []
        total_tokens = 0
        total_cost = 0.0
        total_time_ms = 0
        
        for result in successful_results:
            if result.result:
                findings.append(result.result)
            total_tokens += result.tokens_used
            total_cost += result.cost_estimate
            total_time_ms += result.execution_time_ms
        
        # Calculate confidence
        confidence = len(successful_results) / len(results) if results else 0.0
        
        synthesized = {
            "query": query,
            "findings": findings,
            "total_agents": len(results),
            "successful_agents": len(successful_results),
            "failed_agents": len(failed_results),
            "confidence": confidence,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_execution_time_ms": total_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Synthesis complete: confidence={confidence:.2f}, cost=${total_cost:.4f}")
        
        return synthesized
    
    async def orchestrate(
        self,
        query: str,
        workspace_id: str,
        execution_mode: Optional[ExecutionMode] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-agent execution.
        
        Args:
            query: Intelligence query
            workspace_id: Workspace ID
            execution_mode: Execution mode (auto-detect if None)
            
        Returns:
            Orchestration result
        """
        logger.info(f"Starting orchestration for query: {query}")
        
        # Analyze query
        agents_needed, auto_mode = self.analyze_query(query)
        
        if execution_mode is None:
            execution_mode = auto_mode
        
        # Create tasks
        tasks = await self.create_tasks(query, workspace_id, agents_needed)
        
        # Execute tasks
        if execution_mode == ExecutionMode.PARALLEL:
            results = await self.execute_parallel(tasks)
        else:
            results = await self.execute_sequential(tasks)
        
        # Synthesize results
        synthesized = await self.synthesize_results(results, query)
        
        logger.info(f"Orchestration complete for query: {query}")
        
        return synthesized
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of execution records
        """
        history = []
        
        for result in self.execution_history[-limit:]:
            history.append({
                "task_id": result.task_id,
                "agent_type": result.agent_type.value,
                "status": result.status,
                "execution_time_ms": result.execution_time_ms,
                "tokens_used": result.tokens_used,
                "cost_estimate": result.cost_estimate,
                "executed_at": result.executed_at.isoformat()
            })
        
        return history
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get statistics about agent execution.
        
        Returns:
            Agent statistics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time_ms": 0,
                "total_tokens_used": 0,
                "total_cost": 0.0
            }
        
        total = len(self.execution_history)
        successful = len([r for r in self.execution_history if r.status == "success"])
        failed = len([r for r in self.execution_history if r.status == "failed"])
        
        avg_time = sum(r.execution_time_ms for r in self.execution_history) / total
        total_tokens = sum(r.tokens_used for r in self.execution_history)
        total_cost = sum(r.cost_estimate for r in self.execution_history)
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_execution_time_ms": avg_time,
            "total_tokens_used": total_tokens,
            "total_cost": total_cost
        }


# Convenience function
async def orchestrate_query(
    query: str,
    workspace_id: str,
    db_session=None,
    execution_mode: Optional[ExecutionMode] = None
) -> Dict[str, Any]:
    """
    Orchestrate a query across multiple agents.
    
    Args:
        query: Intelligence query
        workspace_id: Workspace ID
        db_session: Database session
        execution_mode: Execution mode
        
    Returns:
        Orchestration result
    """
    orchestrator = OrchestratorAgent(db_session)
    return await orchestrator.orchestrate(query, workspace_id, execution_mode)
