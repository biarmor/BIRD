"""
Intelligence Router - Multi-Agent Analysis

Endpoints for intelligence queries using multi-agent orchestration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import IntelligenceQueryRequest, IntelligenceQueryResponse, QueryMode
from app.models import IntelligenceQuery, ReasoningChain
from app.agents.orchestrator_agent import orchestrate_query, ExecutionMode
from app.agents.reasoning_agent import reason_about_query
from app.agents.debate_agent import debate_conclusion
from datetime import datetime
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=IntelligenceQueryResponse, status_code=status.HTTP_201_CREATED)
async def analyze_intelligence(
    request: IntelligenceQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze intelligence query using multi-agent orchestration.
    
    Args:
        request: Intelligence query request
        db: Database session
        
    Returns:
        Query result
    """
    try:
        query_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"Starting intelligence analysis: {query_id}")
        logger.info(f"Query: {request.query}")
        logger.info(f"Mode: {request.mode}")
        
        # Determine execution mode
        execution_mode = None
        if request.mode == QueryMode.ORCHESTRATOR_WORKER:
            execution_mode = ExecutionMode.PARALLEL
        elif request.mode == QueryMode.ADAPTIVE_PLANNING:
            execution_mode = ExecutionMode.ADAPTIVE
        elif request.mode == QueryMode.DEBATE:
            execution_mode = ExecutionMode.SEQUENTIAL
        
        # Execute orchestration
        result = await orchestrate_query(
            query=request.query,
            workspace_id=request.workspace_id,
            db_session=db,
            execution_mode=execution_mode
        )
        
        # Calculate execution time
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Create intelligence query record
        intelligence_query = IntelligenceQuery(
            id=query_id,
            workspace_id=request.workspace_id,
            query=request.query,
            mode=request.mode.value,
            status="completed",
            result=result,
            execution_time_ms=execution_time_ms,
            token_count=result.get("total_tokens", 0),
            cost_estimate=result.get("total_cost", 0.0),
            completed_at=datetime.utcnow()
        )
        
        db.add(intelligence_query)
        
        # Save reasoning steps to database for explainability
        findings = result.get("findings", [])
        step_number = 1
        
        # If findings is a single dict or not a list, wrap it in a list
        if isinstance(findings, dict):
            findings = [findings]
            
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            
            agent_type = finding.get("agent", "orchestrator")
            
            # If the agent has specific reasoning steps inside its result dict
            if "reasoning_steps" in finding and isinstance(finding["reasoning_steps"], list):
                for step in finding["reasoning_steps"]:
                    if not isinstance(step, dict):
                        continue
                    
                    premise = step.get("premise", "")
                    conclusion = step.get("conclusion", "")
                    text = f"{premise} -> {conclusion}" if premise else conclusion
                    
                    chain_step = ReasoningChain(
                        id=str(uuid.uuid4()),
                        query_id=query_id,
                        step_number=step_number,
                        agent_type=agent_type,
                        reasoning_text=text,
                        confidence=step.get("confidence", 0.8)
                    )
                    db.add(chain_step)
                    step_number += 1
            # If the agent has a reasoning_chain list of strings
            elif "reasoning_chain" in finding and isinstance(finding["reasoning_chain"], list):
                for chain_str in finding["reasoning_chain"]:
                    chain_step = ReasoningChain(
                        id=str(uuid.uuid4()),
                        query_id=query_id,
                        step_number=step_number,
                        agent_type=agent_type,
                        reasoning_text=chain_str,
                        confidence=finding.get("confidence", 0.9)
                    )
                    db.add(chain_step)
                    step_number += 1
            # Otherwise construct a summary step for this agent
            else:
                text = finding.get("findings") or finding.get("conclusion") or f"Executed analysis via {agent_type} agent."
                chain_step = ReasoningChain(
                    id=str(uuid.uuid4()),
                    query_id=query_id,
                    step_number=step_number,
                    agent_type=agent_type,
                    reasoning_text=str(text),
                    confidence=finding.get("confidence", 0.8)
                )
                db.add(chain_step)
                step_number += 1
        
        db.commit()
        db.refresh(intelligence_query)
        
        logger.info(f"Intelligence analysis complete: {query_id}")
        logger.info(f"Execution time: {execution_time_ms}ms")
        logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
        
        return intelligence_query
    
    except Exception as e:
        logger.error(f"Error analyzing intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


from typing import List

@router.get("/", response_model=List[IntelligenceQueryResponse])
async def list_queries(workspace_id: str, db: Session = Depends(get_db)):
    """
    List all intelligence queries for a workspace.
    """
    queries = db.query(IntelligenceQuery).filter(
        IntelligenceQuery.workspace_id == workspace_id
    ).order_by(IntelligenceQuery.created_at.desc()).all()
    return queries


@router.get("/{query_id}", response_model=IntelligenceQueryResponse)
async def get_query_result(query_id: str, db: Session = Depends(get_db)):
    """
    Get intelligence query result.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Query result
    """
    query = db.query(IntelligenceQuery).filter(IntelligenceQuery.id == query_id).first()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )
    
    return query


@router.get("/{query_id}/reasoning")
async def get_reasoning_chain(query_id: str, db: Session = Depends(get_db)):
    """
    Get reasoning chain for a query.
    
    Args:
        query_id: Query ID
        db: Database session
        
    Returns:
        Reasoning chain
    """
    try:
        reasoning_steps = db.query(ReasoningChain).filter(
            ReasoningChain.query_id == query_id
        ).order_by(ReasoningChain.step_number).all()
        
        if not reasoning_steps:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reasoning chain not found"
            )
        
        return {
            "query_id": query_id,
            "steps": [
                {
                    "step_number": step.step_number,
                    "agent_type": step.agent_type,
                    "reasoning_text": step.reasoning_text,
                    "evidence": step.evidence,
                    "confidence": step.confidence,
                    "created_at": step.created_at.isoformat()
                }
                for step in reasoning_steps
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving reasoning chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reason")
async def reason_about_topic(
    query: str,
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Perform reasoning analysis on a topic.
    
    Args:
        query: Topic to reason about
        workspace_id: Workspace ID
        db: Database session
        
    Returns:
        Reasoning result
    """
    try:
        logger.info(f"Reasoning about: {query}")
        
        context = {
            "workspace_id": workspace_id,
            "query": query
        }
        
        result = await reason_about_query(query, context, db_session=db)
        
        logger.info(f"Reasoning complete: confidence={result.get('overall_confidence', 0):.2f}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error reasoning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debate")
async def debate_topic(
    conclusion: str,
    workspace_id: str,
    num_rounds: int = 3,
    db: Session = Depends(get_db)
):
    """
    Debate a conclusion through multiple perspectives.
    
    Args:
        conclusion: Conclusion to debate
        workspace_id: Workspace ID
        num_rounds: Number of debate rounds
        db: Database session
        
    Returns:
        Debate result
    """
    try:
        logger.info(f"Debating: {conclusion}")
        
        # Validate rounds
        num_rounds = max(1, min(num_rounds, 5))
        
        context = {
            "workspace_id": workspace_id,
            "conclusion": conclusion
        }
        
        result = await debate_conclusion(conclusion, context, db_session=db, num_rounds=num_rounds)
        
        logger.info(f"Debate complete: consensus={result.get('final_consensus', 0):.2f}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error debating: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats")
async def get_intelligence_stats(workspace_id: str, db: Session = Depends(get_db)):
    """
    Get intelligence analysis statistics.
    
    Args:
        workspace_id: Workspace ID
        db: Database session
        
    Returns:
        Statistics
    """
    try:
        total_queries = db.query(IntelligenceQuery).filter(
            IntelligenceQuery.workspace_id == workspace_id
        ).count()
        
        completed_queries = db.query(IntelligenceQuery).filter(
            IntelligenceQuery.workspace_id == workspace_id,
            IntelligenceQuery.status == "completed"
        ).count()
        
        failed_queries = db.query(IntelligenceQuery).filter(
            IntelligenceQuery.workspace_id == workspace_id,
            IntelligenceQuery.status == "failed"
        ).count()
        
        # Calculate average execution time
        avg_time = db.query(
            db.func.avg(IntelligenceQuery.execution_time_ms)
        ).filter(
            IntelligenceQuery.workspace_id == workspace_id
        ).scalar()
        
        # Calculate total cost
        total_cost = db.query(
            db.func.sum(IntelligenceQuery.cost_estimate)
        ).filter(
            IntelligenceQuery.workspace_id == workspace_id
        ).scalar()
        
        return {
            "workspace_id": workspace_id,
            "total_queries": total_queries,
            "completed_queries": completed_queries,
            "failed_queries": failed_queries,
            "success_rate": completed_queries / total_queries if total_queries > 0 else 0.0,
            "average_execution_time_ms": avg_time or 0,
            "total_cost": total_cost or 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting intelligence stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
