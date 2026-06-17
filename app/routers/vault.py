"""
Vault Router - Smart Memory System

Endpoints for vault operations: search, add facts, quality scoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import VaultFactRequest, VaultFactResponse, VaultSearchRequest, VaultSearchResponse
from app.models import VaultFact, MemoryQualityScore
from app.agents.vault_agent import VaultAgent
from app.embeddings import get_embedding_manager
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/facts", response_model=VaultFactResponse, status_code=status.HTTP_201_CREATED)
async def add_fact(
    request: VaultFactRequest,
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """
    Add a fact to the vault.
    
    Args:
        request: Vault fact request
        workspace_id: Workspace ID
        db: Database session
        
    Returns:
        Created fact
    """
    try:
        # Generate embedding for the fact
        embedding_manager = get_embedding_manager()
        embedding = embedding_manager.embed_text(request.fact)
        
        # Create vault fact
        vault_fact = VaultFact(
            workspace_id=workspace_id,
            fact=request.fact,
            source=request.source,
            source_url=request.source_url,
            category=request.category,
            tags=request.tags,
            embedding=embedding
        )
        
        db.add(vault_fact)
        db.flush()
        
        # Create quality score
        quality_score = MemoryQualityScore(
            fact_id=vault_fact.id,
            source_credibility=0.7,  # Default credibility
            recency_score=1.0,  # New facts have high recency
            conflict_score=0.0,  # No conflicts initially
            overall_score=0.7
        )
        
        db.add(quality_score)
        db.commit()
        db.refresh(vault_fact)
        
        logger.info(f"Added fact to vault: {vault_fact.id}")
        
        return vault_fact
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding fact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/facts/{fact_id}", response_model=VaultFactResponse)
async def get_fact(fact_id: str, db: Session = Depends(get_db)):
    """
    Get a fact from the vault.
    
    Args:
        fact_id: Fact ID
        db: Database session
        
    Returns:
        Fact details
    """
    fact = db.query(VaultFact).filter(VaultFact.id == fact_id).first()
    
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fact not found"
        )
    
    return fact


@router.get("/search", response_model=VaultSearchResponse)
async def search_vault(
    query: str,
    workspace_id: str,
    hops: int = 1,
    db: Session = Depends(get_db)
):
    """
    Search vault facts using semantic similarity.
    
    Args:
        query: Search query
        workspace_id: Workspace ID
        hops: Number of retrieval hops (1-5)
        db: Database session
        
    Returns:
        Search results with facts and reasoning
    """
    try:
        # Validate hops
        hops = max(1, min(hops, 5))
        
        # Create vault agent
        agent = VaultAgent(db_session=db)
        
        # Query vault
        mode = "multi-hop" if hops > 1 else "single-hop"
        result = await agent.query_vault(query, workspace_id, mode=mode)
        
        # Extract facts and reasoning
        facts = [VaultFactResponse(**f) for f in result.get("facts", [])]
        reasoning_chain = [t["thought"] for t in result.get("thoughts", [])]
        confidence = result.get("confidence", 0.0)
        
        logger.info(f"Vault search: {query} - {len(facts)} facts, confidence: {confidence:.2f}")
        
        return VaultSearchResponse(
            facts=facts,
            reasoning_chain=reasoning_chain,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error searching vault: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/facts/{fact_id}", response_model=VaultFactResponse)
async def update_fact(
    fact_id: str,
    request: VaultFactRequest,
    db: Session = Depends(get_db)
):
    """
    Update a fact in the vault.
    
    Args:
        fact_id: Fact ID
        request: Updated fact data
        db: Database session
        
    Returns:
        Updated fact
    """
    try:
        fact = db.query(VaultFact).filter(VaultFact.id == fact_id).first()
        
        if not fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fact not found"
            )
        
        # Update fields
        fact.fact = request.fact
        fact.source = request.source
        fact.source_url = request.source_url
        fact.category = request.category
        fact.tags = request.tags
        fact.updated_at = datetime.utcnow()
        
        # Regenerate embedding
        embedding_manager = get_embedding_manager()
        fact.embedding = embedding_manager.embed_text(request.fact)
        
        db.commit()
        db.refresh(fact)
        
        logger.info(f"Updated fact: {fact_id}")
        
        return fact
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating fact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(fact_id: str, db: Session = Depends(get_db)):
    """
    Delete a fact from the vault.
    
    Args:
        fact_id: Fact ID
        db: Database session
    """
    try:
        fact = db.query(VaultFact).filter(VaultFact.id == fact_id).first()
        
        if not fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fact not found"
            )
        
        db.delete(fact)
        db.commit()
        
        logger.info(f"Deleted fact: {fact_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting fact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats")
async def get_vault_stats(workspace_id: str, db: Session = Depends(get_db)):
    """
    Get vault statistics for a workspace.
    
    Args:
        workspace_id: Workspace ID
        db: Database session
        
    Returns:
        Vault statistics
    """
    try:
        # Count facts
        total_facts = db.query(VaultFact).filter(
            VaultFact.workspace_id == workspace_id
        ).count()
        
        # Calculate average quality
        avg_quality = db.query(
            db.func.avg(MemoryQualityScore.overall_score)
        ).join(
            VaultFact, MemoryQualityScore.fact_id == VaultFact.id
        ).filter(
            VaultFact.workspace_id == workspace_id
        ).scalar()
        
        avg_quality = avg_quality or 0.0
        
        return {
            "workspace_id": workspace_id,
            "total_facts": total_facts,
            "average_quality": float(avg_quality),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting vault stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
