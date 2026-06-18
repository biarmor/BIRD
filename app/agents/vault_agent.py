"""
Vault Agent - Smart Memory System

Implements Agentic RAG with multi-hop retrieval, semantic search, and memory quality scoring.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievedFact:
    """Retrieved fact with metadata."""
    fact: str
    source: str
    confidence: float
    recency_score: float
    source_credibility: float
    overall_quality: float
    created_at: datetime
    id: Optional[str] = None


class VaultAgent:
    """
    Vault Agent - Intelligent Memory Management
    
    Capabilities:
    - Single-hop semantic retrieval
    - Multi-hop reasoning over retrieved facts
    - Memory quality scoring and optimization
    - Conflict detection and resolution
    - Continuous memory refinement
    """
    
    def __init__(self, db_session=None, chromadb_client=None, llm_client=None):
        """
        Initialize Vault Agent.
        
        Args:
            db_session: SQLAlchemy database session
            chromadb_client: ChromaDB client for embeddings
            llm_client: Ollama client
        """
        self.db_session = db_session
        self.chromadb_client = chromadb_client
        from app.embeddings import get_chromadb_manager
        self.chromadb_manager = get_chromadb_manager()
        from app.services.llm_service import get_llm_client
        self.llm_client = llm_client or get_llm_client()
        self.thoughts = []
    
    def add_thought(self, thought: str):
        """Add a thought to the reasoning chain."""
        self.thoughts.append({
            "timestamp": datetime.utcnow().isoformat(),
            "thought": thought
        })
        logger.info(f"Vault thought: {thought}")
    
    async def add_fact(
        self,
        fact: str,
        workspace_id: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Any:
        """Add a fact to the vault."""
        from app.embeddings import get_embedding_manager
        from app.models import VaultFact, MemoryQualityScore
        from app.database import DatabaseManager
        
        embedding_manager = get_embedding_manager()
        embedding = embedding_manager.embed_text(fact)
        
        vault_fact = VaultFact(
            workspace_id=workspace_id,
            fact=fact,
            source=source,
            source_url=source_url,
            category=category,
            tags=tags,
            embedding=embedding
        )
        
        db = self.db_session
        created_session = False
        if db is None:
            db = DatabaseManager.get_session()
            created_session = True
            
        try:
            # Ensure owner user exists to satisfy Workspace foreign key
            from app.models import User, Workspace
            owner_id = "default-owner-id"
            owner = db.query(User).filter(User.id == owner_id).first()
            if not owner:
                owner = User(
                    id=owner_id,
                    username="default-owner",
                    email="owner@example.com",
                    hashed_password="mock-password"
                )
                db.add(owner)
                db.flush()
                
            # Ensure workspace exists to satisfy VaultFact foreign key
            workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                workspace = Workspace(
                    id=workspace_id,
                    owner_id=owner_id,
                    name="Default Workspace"
                )
                db.add(workspace)
                db.flush()

            db.add(vault_fact)
            db.flush()
            
            # Create quality score
            quality_score = MemoryQualityScore(
                fact_id=vault_fact.id,
                source_credibility=0.7,
                recency_score=1.0,
                conflict_score=0.0,
                overall_score=0.7
            )
            db.add(quality_score)
            db.commit()
            
            # If ChromaDB collection is initialized, add document
            try:
                collection = self.chromadb_manager.get_or_create_collection()
                if collection is not None:
                    self.chromadb_manager.add_documents(
                        documents=[fact],
                        ids=[vault_fact.id],
                        embeddings=[embedding],
                        metadatas=[{
                            "workspace_id": workspace_id,
                            "category": category or "",
                            "source": source or "",
                            "source_url": source_url or ""
                        }]
                    )
            except Exception as e:
                logger.error(f"Error adding to ChromaDB in add_fact: {e}")
                
            db.refresh(vault_fact)
            return vault_fact
        except Exception as e:
            db.rollback()
            logger.error(f"Error in vault_agent add_fact: {e}")
            raise
        finally:
            if created_session:
                db.close()

    async def search_vault(
        self,
        query: str,
        workspace_id: str,
        max_hops: int = 1
    ) -> Dict[str, Any]:
        """Search the vault and format findings for E2E tests."""
        mode = "multi-hop" if max_hops > 1 else "single-hop"
        result = await self.query_vault(query, workspace_id, mode=mode)
        # Map facts to a findings list for E2E test assertions
        result["findings"] = [f["fact"] for f in result["facts"]]
        return result

    async def retrieve_facts(
        self,
        query: str,
        workspace_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[RetrievedFact]:
        """
        Retrieve facts using semantic similarity search.
        
        Args:
            query: Search query
            workspace_id: Workspace ID
            top_k: Number of top results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of retrieved facts
        """
        self.add_thought(f"Retrieving facts for query: {query}")
        
        db = self.db_session
        created_session = False
        if db is None:
            from app.database import DatabaseManager
            db = DatabaseManager.get_session()
            created_session = True
            
        try:
            from app.models import VaultFact
            from app.embeddings import get_embedding_manager
            
            # Get query embedding
            embedding_manager = get_embedding_manager()
            query_embedding = embedding_manager.embed_text(query)
            
            # Try to query ChromaDB first
            try:
                collection = self.chromadb_manager.get_or_create_collection()
                if collection is not None:
                    results = self.chromadb_manager.query(
                        query_embedding=query_embedding,
                        n_results=top_k,
                        where={"workspace_id": workspace_id}
                    )
                    if results and results.get("ids") and results["ids"][0]:
                        chroma_ids = results["ids"][0]
                        distances = results.get("distances", [[]])[0]
                        
                        scored_facts = []
                        for idx, fact_id in enumerate(chroma_ids):
                            f = db.query(VaultFact).filter(VaultFact.id == fact_id).first()
                            if f:
                                distance = distances[idx] if idx < len(distances) else 0.0
                                similarity = 1.0 - distance
                                
                                # Fallback word overlap
                                if embedding_manager.model is None:
                                    query_words = {w.strip(".,?!;:") for w in query.lower().split() if w.strip(".,?!;:")}
                                    fact_words = {w.strip(".,?!;:") for w in f.fact.lower().split() if w.strip(".,?!;:")}
                                    if query_words and fact_words:
                                        intersection = query_words.intersection(fact_words)
                                        overlap_sim = len(intersection) / len(query_words)
                                        if overlap_sim > 0:
                                            similarity = max(similarity, 0.5 + 0.5 * overlap_sim)
                                            
                                if similarity >= similarity_threshold:
                                    credibility = 0.7
                                    recency = 1.0
                                    conflict = 0.0
                                    overall_quality = 0.7
                                    if f.quality_score:
                                        credibility = f.quality_score.source_credibility
                                        recency = f.quality_score.recency_score
                                        conflict = f.quality_score.conflict_score
                                        overall_quality = f.quality_score.overall_score
                                        
                                    retrieved = RetrievedFact(
                                        fact=f.fact,
                                        source=f.source or "Unknown",
                                        confidence=similarity,
                                        recency_score=recency,
                                        source_credibility=credibility,
                                        overall_quality=overall_quality,
                                        created_at=f.created_at,
                                        id=f.id
                                    )
                                    scored_facts.append(retrieved)
                        scored_facts.sort(key=lambda x: x.confidence, reverse=True)
                        retrieved_facts = scored_facts[:top_k]
                        self.add_thought(f"Retrieved {len(retrieved_facts)} facts from ChromaDB")
                        return retrieved_facts
            except Exception as e:
                logger.error(f"Error querying ChromaDB in retrieve_facts: {e}")

            # Query all facts for this workspace (Fallback)
            db_facts = db.query(VaultFact).filter(VaultFact.workspace_id == workspace_id).all()
            
            if not db_facts:
                return []
                
            scored_facts = []
            for f in db_facts:
                if f.embedding:
                    # Calculate similarity
                    similarity = embedding_manager.cosine_similarity(query_embedding, f.embedding)
                    
                    # Fallback to word overlap similarity if mock embeddings are used
                    if embedding_manager.model is None:
                        query_words = {w.strip(".,?!;:") for w in query.lower().split() if w.strip(".,?!;:")}
                        fact_words = {w.strip(".,?!;:") for w in f.fact.lower().split() if w.strip(".,?!;:")}
                        if query_words and fact_words:
                            intersection = query_words.intersection(fact_words)
                            overlap_sim = len(intersection) / len(query_words)
                            if overlap_sim > 0:
                                similarity = max(similarity, 0.5 + 0.5 * overlap_sim)
                                
                    if similarity >= similarity_threshold:
                        # Fetch quality score
                        credibility = 0.7
                        recency = 1.0
                        conflict = 0.0
                        overall_quality = 0.7
                        if f.quality_score:
                            credibility = f.quality_score.source_credibility
                            recency = f.quality_score.recency_score
                            conflict = f.quality_score.conflict_score
                            overall_quality = f.quality_score.overall_score
                            
                        retrieved = RetrievedFact(
                            fact=f.fact,
                            source=f.source or "Unknown",
                            confidence=similarity,
                            recency_score=recency,
                            source_credibility=credibility,
                            overall_quality=overall_quality,
                            created_at=f.created_at,
                            id=f.id
                        )
                        scored_facts.append(retrieved)
            
            # Sort by confidence descending
            scored_facts.sort(key=lambda x: x.confidence, reverse=True)
            retrieved_facts = scored_facts[:top_k]
            
            self.add_thought(f"Retrieved {len(retrieved_facts)} facts (fallback)")
            return retrieved_facts
        finally:
            if created_session:
                db.close()
    
    async def multi_hop_retrieval(
        self,
        initial_query: str,
        workspace_id: str,
        hops: int = 2,
        top_k_per_hop: int = 3
    ) -> Tuple[List[RetrievedFact], List[str]]:
        """
        Multi-hop retrieval for complex reasoning.
        
        Args:
            initial_query: Initial search query
            workspace_id: Workspace ID
            hops: Number of retrieval hops
            top_k_per_hop: Top results per hop
            
        Returns:
            Tuple of (all_retrieved_facts, reasoning_chain)
        """
        self.add_thought(f"Starting multi-hop retrieval with {hops} hops")
        
        all_facts = []
        reasoning_chain = []
        current_query = initial_query
        
        for hop in range(hops):
            self.add_thought(f"Hop {hop + 1}: Searching for '{current_query}'")
            
            # Retrieve facts for current query
            facts = await self.retrieve_facts(
                query=current_query,
                workspace_id=workspace_id,
                top_k=top_k_per_hop
            )
            
            all_facts.extend(facts)
            reasoning_chain.append(f"Hop {hop + 1}: Found {len(facts)} facts")
            
            # Generate next query based on retrieved facts
            if facts and hop < hops - 1:
                current_query = await self._generate_next_query(facts, current_query)
                self.add_thought(f"Generated next query: {current_query}")
        
        self.add_thought(f"Multi-hop retrieval complete: {len(all_facts)} total facts")
        return all_facts, reasoning_chain
    
    async def _generate_next_query(self, facts: List[RetrievedFact], current_query: str) -> str:
        """
        Generate next query based on retrieved facts using Ollama if healthy.
        """
        if not facts:
            return current_query
            
        try:
            if await self.llm_client.is_healthy():
                facts_text = "; ".join([f.fact for f in facts[:3]])
                prompt = (
                    f"Given the initial search query: '{current_query}' and the retrieved facts: '{facts_text}', "
                    f"generate a new search query that will help retrieve complementary or missing information to answer the initial query. "
                    f"Return ONLY the new query string, with no other explanation."
                )
                response = await self.llm_client.generate(
                    prompt=prompt,
                    system="You are a query expansion engine. Return only a short search query."
                )
                if "response" in response:
                    new_query = response["response"].strip().strip('"\'')
                    if new_query:
                        return new_query
        except Exception as e:
            logger.warning(f"Ollama next query generation failed, falling back to concatenation: {e}")
            
        return f"{current_query} AND {facts[0].fact[:50]}"
    
    def calculate_memory_quality_score(
        self,
        source_credibility: float,
        recency_score: float,
        conflict_score: float,
        retrieval_count: int = 0
    ) -> float:
        """
        Calculate overall memory quality score.
        
        Args:
            source_credibility: Source credibility (0-1)
            recency_score: Recency score (0-1, time-decay)
            conflict_score: Conflict score (0-1, 0 = no conflicts)
            retrieval_count: Number of times retrieved
            
        Returns:
            Overall quality score (0-1)
        """
        # Weighted average of quality metrics
        weights = {
            "credibility": 0.4,
            "recency": 0.3,
            "conflict": 0.2,
            "popularity": 0.1
        }
        
        # Conflict score is inverted (lower is better)
        conflict_quality = 1.0 - conflict_score
        
        # Popularity score based on retrieval count (0-1)
        popularity_score = min(retrieval_count / 10.0, 1.0)
        
        overall_score = (
            weights["credibility"] * source_credibility +
            weights["recency"] * recency_score +
            weights["conflict"] * conflict_quality +
            weights["popularity"] * popularity_score
        )
        
        return min(max(overall_score, 0.0), 1.0)
    
    def calculate_recency_score(self, created_at: datetime, decay_days: int = 30) -> float:
        """
        Calculate recency score with time decay.
        
        Args:
            created_at: Fact creation timestamp
            decay_days: Days until score reaches 0.5
            
        Returns:
            Recency score (0-1)
        """
        age_days = (datetime.utcnow() - created_at).days
        
        # Exponential decay with half-life of decay_days: score = exp(-age * ln(2) / decay_days)
        import math
        recency = math.exp(-age_days * math.log(2) / decay_days)
        
        return min(max(recency, 0.0), 1.0)
    
    def detect_conflicts(
        self,
        facts: List[RetrievedFact],
        similarity_threshold: float = 0.65
    ) -> List[Tuple[RetrievedFact, RetrievedFact, float]]:
        """
        Detect conflicting facts in retrieved set.
        """
        conflicts = []
        from app.embeddings import get_embedding_manager
        embedding_manager = get_embedding_manager()
        
        for i in range(len(facts)):
            for j in range(i + 1, len(facts)):
                f1 = facts[i]
                f2 = facts[j]
                
                # Check semantic similarity
                emb1 = embedding_manager.embed_text(f1.fact)
                emb2 = embedding_manager.embed_text(f2.fact)
                similarity = embedding_manager.cosine_similarity(emb1, emb2)
                
                # Fallback word-overlap
                if embedding_manager.model is None:
                    words1 = {w.strip(".,?!;:") for w in f1.fact.lower().split() if w.strip(".,?!;:")}
                    words2 = {w.strip(".,?!;:") for w in f2.fact.lower().split() if w.strip(".,?!;:")}
                    if words1 and words2:
                        intersection = words1.intersection(words2)
                        overlap = len(intersection) / min(len(words1), len(words2))
                        similarity = max(similarity, overlap)
                
                if similarity >= similarity_threshold:
                    f1_words = f1.fact.lower().split()
                    f2_words = f2.fact.lower().split()
                    
                    negations = {"not", "no", "never", "un", "non", "failed", "incorrect"}
                    f1_neg = any(w in negations for w in f1_words)
                    f2_neg = any(w in negations for w in f2_words)
                    
                    has_contradicting_words = (f1_neg != f2_neg)
                    
                    import re
                    nums1 = set(re.findall(r'\b\d+\b', f1.fact))
                    nums2 = set(re.findall(r'\b\d+\b', f2.fact))
                    has_different_numbers = False
                    if nums1 and nums2 and nums1 != nums2:
                        has_different_numbers = True
                    
                    if has_contradicting_words or has_different_numbers:
                        conflict_score = similarity * 0.8 + 0.2
                        conflicts.append((f1, f2, min(conflict_score, 1.0)))
                        
        if conflicts:
            self.add_thought(f"Detected {len(conflicts)} potential conflicts")
        
        return conflicts
    
    async def semantic_deduplication(
        self,
        facts: List[RetrievedFact],
        similarity_threshold: float = 0.85
    ) -> List[RetrievedFact]:
        """
        Remove duplicate or near-duplicate facts.
        """
        self.add_thought(f"Deduplicating {len(facts)} facts")
        if not facts:
            return []
            
        from app.embeddings import get_embedding_manager
        embedding_manager = get_embedding_manager()
        
        deduplicated = []
        
        for f in facts:
            is_dup = False
            for dup in deduplicated:
                emb1 = embedding_manager.embed_text(f.fact)
                emb2 = embedding_manager.embed_text(dup.fact)
                similarity = embedding_manager.cosine_similarity(emb1, emb2)
                
                # Fallback word-overlap
                if embedding_manager.model is None:
                    words1 = {w.strip(".,?!;:") for w in f.fact.lower().split() if w.strip(".,?!;:")}
                    words2 = {w.strip(".,?!;:") for w in dup.fact.lower().split() if w.strip(".,?!;:")}
                    if words1 and words2:
                        intersection = words1.intersection(words2)
                        overlap = len(intersection) / min(len(words1), len(words2))
                        similarity = max(similarity, overlap)
                        
                if similarity >= similarity_threshold:
                    is_dup = True
                    # Keep the one with higher overall quality
                    if f.overall_quality > dup.overall_quality:
                        dup.fact = f.fact
                        dup.confidence = max(dup.confidence, f.confidence)
                        dup.overall_quality = f.overall_quality
                    break
            if not is_dup:
                deduplicated.append(f)
                
        return deduplicated
    
    async def query_vault(
        self,
        query: str,
        workspace_id: str,
        mode: str = "single-hop"
    ) -> Dict[str, Any]:
        """
        Query the vault with specified mode.
        
        Args:
            query: Search query
            workspace_id: Workspace ID
            mode: Query mode (single-hop, multi-hop, debate)
            
        Returns:
            Query result with facts and reasoning
        """
        self.thoughts = []  # Reset thoughts
        self.add_thought(f"Starting vault query: {query}")
        
        if mode == "single-hop":
            facts = await self.retrieve_facts(query, workspace_id)
        elif mode == "multi-hop":
            facts, reasoning_chain = await self.multi_hop_retrieval(query, workspace_id)
        else:
            facts = await self.retrieve_facts(query, workspace_id)
            reasoning_chain = []
        
        # Deduplicate facts
        facts = await self.semantic_deduplication(facts)
        
        # Detect conflicts
        conflicts = self.detect_conflicts(facts)
        
        result = {
            "query": query,
            "mode": mode,
            "facts": [
                {
                    "fact": f.fact,
                    "source": f.source,
                    "confidence": f.confidence,
                    "quality_score": f.overall_quality,
                    "created_at": f.created_at.isoformat()
                }
                for f in facts
            ],
            "conflicts": [
                {
                    "fact1": c[0].fact,
                    "fact2": c[1].fact,
                    "conflict_score": c[2]
                }
                for c in conflicts
            ],
            "thoughts": self.thoughts,
            "total_facts_retrieved": len(facts),
            "confidence": sum(f.confidence for f in facts) / len(facts) if facts else 0.0
        }
        
        self.add_thought(f"Query complete: {len(facts)} facts, confidence: {result['confidence']:.2f}")
        
        return result
    
    def get_low_quality_facts(
        self,
        workspace_id: str,
        quality_threshold: float = 0.5
    ) -> List[str]:
        """
        Get facts below quality threshold for cleanup.
        """
        db = self.db_session
        created_session = False
        if db is None:
            from app.database import DatabaseManager
            db = DatabaseManager.get_session()
            created_session = True
            
        try:
            from app.models import VaultFact, MemoryQualityScore
            low_quality = db.query(VaultFact).join(MemoryQualityScore).filter(
                VaultFact.workspace_id == workspace_id,
                MemoryQualityScore.overall_score < quality_threshold
            ).all()
            return [f.id for f in low_quality]
        finally:
            if created_session:
                db.close()
    
    async def cleanup_memory(self, workspace_id: str):
        """
        Cleanup low-quality facts from vault.
        """
        self.add_thought(f"Starting memory cleanup for workspace: {workspace_id}")
        
        low_quality_facts = self.get_low_quality_facts(workspace_id)
        
        if low_quality_facts:
            self.add_thought(f"Removing {len(low_quality_facts)} low-quality facts")
            db = self.db_session
            created_session = False
            if db is None:
                from app.database import DatabaseManager
                db = DatabaseManager.get_session()
                created_session = True
                
            try:
                from app.models import VaultFact
                # Delete from ChromaDB
                try:
                    collection = self.chromadb_manager.get_or_create_collection()
                    if collection is not None:
                        collection.delete(ids=low_quality_facts)
                except Exception as e:
                    logger.error(f"Error deleting from ChromaDB in cleanup_memory: {e}")
                        
                # Delete from SQLite
                db.query(VaultFact).filter(VaultFact.id.in_(low_quality_facts)).delete(synchronize_session=False)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error in cleanup_memory: {e}")
            finally:
                if created_session:
                    db.close()
                    
        self.add_thought("Memory cleanup complete")


# Convenience functions
async def query_vault_facts(
    query: str,
    workspace_id: str,
    db_session=None,
    chromadb_client=None,
    mode: str = "single-hop"
) -> Dict[str, Any]:
    """
    Query vault facts.
    
    Args:
        query: Search query
        workspace_id: Workspace ID
        db_session: Database session
        chromadb_client: ChromaDB client
        mode: Query mode
        
    Returns:
        Query result
    """
    agent = VaultAgent(db_session, chromadb_client)
    return await agent.query_vault(query, workspace_id, mode)
