"""
Adaptive Planning Agent - Dynamic Task Scheduling and Plan Adjustment

Implements adaptive planning with real-time adjustments based on execution results.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class PlanStatus(str, Enum):
    """Plan execution status."""
    CREATED = "created"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ADJUSTED = "adjusted"


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PlanTask:
    """Single task in an adaptive plan."""
    id: str
    name: str
    agent_type: str
    priority: TaskPriority
    estimated_time_ms: int
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    actual_time_ms: int = 0
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ExecutionPlan:
    """Adaptive execution plan."""
    id: str
    query: str
    tasks: List[PlanTask]
    status: PlanStatus = PlanStatus.CREATED
    total_estimated_time_ms: int = 0
    total_actual_time_ms: int = 0
    adjustments_made: int = 0
    confidence_score: float = 0.0
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        # Calculate total estimated time
        self.total_estimated_time_ms = sum(t.estimated_time_ms for t in self.tasks)


class AdaptivePlanningAgent:
    """
    Adaptive Planning Agent - Dynamic Task Scheduling and Plan Adjustment
    
    Capabilities:
    - Dynamic task scheduling
    - Real-time plan adjustment
    - Dependency management
    - Resource optimization
    - Confidence-based prioritization
    - Performance tracking
    """
    
    def __init__(self, db_session=None):
        """
        Initialize Adaptive Planning Agent.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.active_plans = {}
        self.plan_history = []
    
    async def create_plan(
        self,
        query: str,
        workspace_id: str,
        agents_needed: List[str],
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create an adaptive execution plan.
        
        Args:
            query: Intelligence query
            workspace_id: Workspace ID
            agents_needed: List of agents needed
            context: Context information
            
        Returns:
            Execution plan
        """
        logger.info(f"Creating adaptive plan for query: {query}")
        
        plan_id = f"plan-{workspace_id}-{datetime.utcnow().timestamp()}"
        
        # Create tasks
        tasks = await self._create_tasks(query, agents_needed, context)
        
        # Establish dependencies
        tasks = await self._establish_dependencies(tasks)
        
        # Calculate task priorities
        tasks = await self._calculate_priorities(tasks, context)
        
        # Create plan
        plan = ExecutionPlan(
            id=plan_id,
            query=query,
            tasks=tasks
        )
        
        self.active_plans[plan_id] = plan
        
        logger.info(f"Created plan {plan_id} with {len(tasks)} tasks")
        logger.info(f"Estimated total time: {plan.total_estimated_time_ms}ms")
        
        return plan
    
    async def _create_tasks(
        self,
        query: str,
        agents_needed: List[str],
        context: Dict[str, Any]
    ) -> List[PlanTask]:
        """Create tasks for the plan."""
        tasks = []
        
        for idx, agent_type in enumerate(agents_needed):
            task = PlanTask(
                id=f"task-{idx}",
                name=f"{agent_type} analysis",
                agent_type=agent_type,
                priority=TaskPriority.MEDIUM,
                estimated_time_ms=1000 + (idx * 500)  # Estimate increases with complexity
            )
            tasks.append(task)
        
        return tasks
    
    async def _establish_dependencies(self, tasks: List[PlanTask]) -> List[PlanTask]:
        """Establish task dependencies."""
        # Placeholder: In production, analyze query to determine dependencies
        # For now, tasks are independent
        return tasks
    
    async def _calculate_priorities(
        self,
        tasks: List[PlanTask],
        context: Dict[str, Any]
    ) -> List[PlanTask]:
        """Calculate task priorities based on context."""
        for idx, task in enumerate(tasks):
            # First task is critical
            if idx == 0:
                task.priority = TaskPriority.CRITICAL
            # Last task is low priority
            elif idx == len(tasks) - 1:
                task.priority = TaskPriority.LOW
            else:
                task.priority = TaskPriority.HIGH
        
        return tasks
    
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute an adaptive plan with real-time adjustments.
        
        Args:
            plan: Execution plan
            
        Returns:
            Execution result
        """
        logger.info(f"Executing plan: {plan.id}")
        
        plan.status = PlanStatus.EXECUTING
        start_time = datetime.utcnow()
        
        try:
            # Execute tasks
            results = await self._execute_tasks(plan)
            
            # Evaluate execution
            evaluation = await self._evaluate_execution(plan, results)
            
            # Adjust plan if needed
            if evaluation["needs_adjustment"]:
                logger.info(f"Plan adjustment needed: {evaluation['reason']}")
                await self._adjust_plan(plan, evaluation)
                plan.status = PlanStatus.ADJUSTED
            
            # Calculate metrics
            plan.total_actual_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            plan.confidence_score = evaluation["confidence"]
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.utcnow()
            
            self.plan_history.append(plan)
            
            logger.info(f"Plan execution complete: {plan.id}")
            logger.info(f"Actual time: {plan.total_actual_time_ms}ms")
            logger.info(f"Confidence: {plan.confidence_score:.2f}")
            
            return {
                "plan_id": plan.id,
                "status": plan.status.value,
                "results": results,
                "evaluation": evaluation,
                "adjustments_made": plan.adjustments_made,
                "total_time_ms": plan.total_actual_time_ms,
                "confidence": plan.confidence_score
            }
        
        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            plan.status = PlanStatus.FAILED
            plan.completed_at = datetime.utcnow()
            raise
    
    async def _execute_tasks(self, plan: ExecutionPlan) -> List[Dict[str, Any]]:
        """Execute all tasks in the plan."""
        results = []
        
        # Group tasks by dependencies
        independent_tasks = [t for t in plan.tasks if not t.dependencies]
        dependent_tasks = [t for t in plan.tasks if t.dependencies]
        
        # Execute independent tasks in parallel
        if independent_tasks:
            logger.info(f"Executing {len(independent_tasks)} independent tasks in parallel")
            independent_results = await asyncio.gather(
                *[self._execute_task(t) for t in independent_tasks]
            )
            results.extend(independent_results)
        
        # Execute dependent tasks sequentially
        for task in dependent_tasks:
            logger.info(f"Executing dependent task: {task.id}")
            result = await self._execute_task(task)
            results.append(result)
        
        return results
    
    async def _execute_task(self, task: PlanTask) -> Dict[str, Any]:
        """Execute a single task."""
        start_time = datetime.utcnow()
        task.status = "executing"
        
        try:
            # Simulate task execution
            await asyncio.sleep(0.1)
            
            task.actual_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            result = {
                "task_id": task.id,
                "name": task.name,
                "agent_type": task.agent_type,
                "status": task.status,
                "actual_time_ms": task.actual_time_ms,
                "result": f"Result from {task.agent_type}"
            }
            
            task.result = result
            
            return result
        
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            raise
    
    async def _evaluate_execution(
        self,
        plan: ExecutionPlan,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate plan execution."""
        successful_tasks = len([r for r in results if r.get("status") == "completed"])
        total_tasks = len(plan.tasks)
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Check for performance issues
        total_actual_time = sum(t.actual_time_ms for t in plan.tasks)
        time_variance = abs(total_actual_time - plan.total_estimated_time_ms) / plan.total_estimated_time_ms
        
        needs_adjustment = time_variance > 0.3 or success_rate < 0.8
        
        evaluation = {
            "successful_tasks": successful_tasks,
            "total_tasks": total_tasks,
            "success_rate": success_rate,
            "total_actual_time_ms": total_actual_time,
            "time_variance": time_variance,
            "needs_adjustment": needs_adjustment,
            "reason": self._get_adjustment_reason(time_variance, success_rate),
            "confidence": success_rate * 0.8 + (1 - time_variance) * 0.2
        }
        
        return evaluation
    
    def _get_adjustment_reason(self, time_variance: float, success_rate: float) -> str:
        """Get reason for plan adjustment."""
        if success_rate < 0.8:
            return "Low success rate"
        elif time_variance > 0.3:
            return "Significant time variance"
        else:
            return "Performance optimization"
    
    async def _adjust_plan(
        self,
        plan: ExecutionPlan,
        evaluation: Dict[str, Any]
    ):
        """Adjust plan based on evaluation."""
        logger.info(f"Adjusting plan: {plan.id}")
        
        # Increase priority of failed tasks
        for task in plan.tasks:
            if task.status == "failed":
                task.priority = TaskPriority.CRITICAL
        
        # Reduce estimated time if execution was faster
        if evaluation["time_variance"] < 0:
            for task in plan.tasks:
                task.estimated_time_ms = int(task.estimated_time_ms * 0.9)
        
        plan.adjustments_made += 1
        logger.info(f"Plan adjusted: {plan.adjustments_made} adjustments made")
    
    async def replan_on_failure(
        self,
        plan: ExecutionPlan,
        failed_task_id: str,
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create a new plan when a task fails.
        
        Args:
            plan: Original plan
            failed_task_id: ID of failed task
            context: Context information
            
        Returns:
            New execution plan
        """
        logger.info(f"Replanning after failure of task: {failed_task_id}")
        
        # Find failed task
        failed_task = next((t for t in plan.tasks if t.id == failed_task_id), None)
        
        if not failed_task:
            logger.warning(f"Failed task not found: {failed_task_id}")
            return plan
        
        # Create alternative plan
        alternative_agents = await self._find_alternative_agents(failed_task.agent_type, context)
        
        if alternative_agents:
            # Create new plan with alternative agents
            new_plan = await self.create_plan(
                query=plan.query,
                workspace_id=plan.id.split("-")[1],
                agents_needed=alternative_agents,
                context=context
            )
            
            logger.info(f"Created alternative plan: {new_plan.id}")
            return new_plan
        
        return plan
    
    async def _find_alternative_agents(
        self,
        failed_agent_type: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Find alternative agents for a failed task."""
        # Placeholder: In production, use agent registry
        alternatives = {
            "vault": ["reasoning", "debate"],
            "reasoning": ["debate", "vault"],
            "debate": ["reasoning", "vault"]
        }
        
        return alternatives.get(failed_agent_type, [])
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a plan."""
        plan = self.active_plans.get(plan_id)
        
        if not plan:
            return None
        
        return {
            "plan_id": plan.id,
            "query": plan.query,
            "status": plan.status.value,
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status,
                    "priority": t.priority.value,
                    "estimated_time_ms": t.estimated_time_ms,
                    "actual_time_ms": t.actual_time_ms
                }
                for t in plan.tasks
            ],
            "total_estimated_time_ms": plan.total_estimated_time_ms,
            "total_actual_time_ms": plan.total_actual_time_ms,
            "adjustments_made": plan.adjustments_made,
            "confidence_score": plan.confidence_score,
            "created_at": plan.created_at.isoformat(),
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
        }
    
    def get_plan_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get plan execution history."""
        history = []
        
        for plan in self.plan_history[-limit:]:
            history.append({
                "plan_id": plan.id,
                "query": plan.query,
                "status": plan.status.value,
                "total_tasks": len(plan.tasks),
                "total_time_ms": plan.total_actual_time_ms,
                "adjustments_made": plan.adjustments_made,
                "confidence": plan.confidence_score,
                "completed_at": plan.completed_at.isoformat() if plan.completed_at else None
            })
        
        return history


# Convenience function
async def create_and_execute_plan(
    query: str,
    workspace_id: str,
    agents_needed: List[str],
    context: Dict[str, Any],
    db_session=None
) -> Dict[str, Any]:
    """
    Create and execute an adaptive plan.
    
    Args:
        query: Intelligence query
        workspace_id: Workspace ID
        agents_needed: List of agents needed
        context: Context information
        db_session: Database session
        
    Returns:
        Execution result
    """
    agent = AdaptivePlanningAgent(db_session)
    plan = await agent.create_plan(query, workspace_id, agents_needed, context)
    return await agent.execute_plan(plan)
