import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.base import BaseAgent
from app.embeddings import EmbeddingService
from app.db.crud import vault as vault_crud
from app.db.session import SessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VaultAgent(BaseAgent):
    """Vault Agent - Stores and retrieves intelligence in ChromaDB"""
    
    def __init__(self):
        super().__init__()
        self.embedding_service = EmbeddingService()

    def store(self, data: Dict[str, Any], workspace_id: int) -> Dict[str, Any]:
        """Store data in ChromaDB"""
        try:
            text = self._prepare_text(data)
            metadata = self._prepare_metadata(data, workspace_id)
            
            embedding = self.embedding_service.get_embedding(text)
            fact_id = str(uuid.uuid4())
            
            with SessionLocal() as db:
                vault_crud.create_vault_fact(
                    db=db,
                    fact_id=fact_id,
                    workspace_id=workspace_id,
                    text=text,
                    embedding=embedding,
                    metadata=metadata,
                    fact_type=metadata.get("type", "general")
                )
            
            return {
                "status": "success",
                "fact_id": fact_id,
                "thoughts": [f"💾 Stored fact in Vault: {fact_id[:8]}..."]
            }
            
        except Exception as e:
            logger.error(f"VaultAgent store error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def retrieve(self, query: str, workspace_id: int, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve similar data from ChromaDB"""
        try:
            query_embedding = self.embedding_service.get_embedding(query)
            
            with SessionLocal() as db:
                results = vault_crud.search_vault_facts(
                    db=db,
                    workspace_id=workspace_id,
                    query_embedding=query_embedding,
                    top_k=top_k
                )
            
            return {
                "status": "success",
                "results": results,
                "count": len(results),
                "thoughts": [
                    f"🔎 Retrieved {len(results)} facts from Vault",
                    "🧠 Using memory to enhance analysis"
                ]
            }
            
        except Exception as e:
            logger.error(f"VaultAgent retrieve error: {str(e)}")
            return {"status": "error", "error": str(e), "results": []}

    def _prepare_text(self, data: Dict) -> str:
        """Prepare text for storage"""
        parts = []
        if data.get("title"):
            parts.append(f"Title: {data['title']}")
        if data.get("description"):
            parts.append(f"Description: {data['description']}")
        if data.get("url"):
            parts.append(f"URL: {data['url']}")
        return "\n".join(parts)

    def _prepare_metadata(self, data: Dict, workspace_id: int) -> Dict:
        """Prepare metadata for storage"""
        return {
            "workspace_id": workspace_id,
            "source": data.get("source", "unknown"),
            "type": data.get("type", "general"),
            "timestamp": datetime.now().isoformat(),
            "url": data.get("url", ""),
            "title": data.get("title", "")
        }
