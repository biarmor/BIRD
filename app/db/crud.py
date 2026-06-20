from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.models import VaultFact, MemoryQualityScore

class VaultCRUD:
    def create_vault_fact(
        self,
        db: Session,
        fact_id: str,
        workspace_id: int,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        fact_type: str
    ):
        fact_obj = VaultFact(
            id=fact_id,
            workspace_id=str(workspace_id),
            fact=text,
            source=metadata.get("source"),
            source_url=metadata.get("url"),
            category=fact_type,
            tags=None,
            embedding=embedding
        )
        db.add(fact_obj)
        
        # Add memory quality score to avoid join issues if needed
        quality = MemoryQualityScore(
            fact_id=fact_id,
            source_credibility=1.0,
            recency_score=1.0,
            conflict_score=0.0,
            overall_score=1.0
        )
        db.add(quality)
        
        db.commit()
        return fact_obj

    def search_vault_facts(
        self,
        db: Session,
        workspace_id: int,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Retrieve facts for workspace
        facts = db.query(VaultFact).filter(VaultFact.workspace_id == str(workspace_id)).all()
        
        results = []
        for fact in facts:
            score = 0.5
            if fact.embedding and query_embedding:
                # Basic cosine similarity
                dot_product = sum(a * b for a, b in zip(query_embedding, fact.embedding))
                norm_q = sum(a * a for a in query_embedding) ** 0.5
                norm_f = sum(b * b for b in fact.embedding) ** 0.5
                if norm_q > 0 and norm_f > 0:
                    score = dot_product / (norm_q * norm_f)
            
            results.append({
                "id": fact.id,
                "text": fact.fact,
                "metadata": {
                    "source": fact.source,
                    "url": fact.source_url,
                    "category": fact.category
                },
                "score": score
            })
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

vault = VaultCRUD()
