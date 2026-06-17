"""
Embedding Utilities

Handles text embeddings using sentence-transformers for semantic search.
"""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embeddings for semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding manager.
        
        Args:
            model_name: Sentence-transformers model name
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using mock embeddings")
            self.model = None
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.model is None:
            # Mock embedding for testing
            return [0.0] * 384
        
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple text strings.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            # Mock embeddings for testing
            return [[0.0] * 384 for _ in texts]
        
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        v1 = np.array(embedding1)
        v2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Normalize to 0-1 range
        return (similarity + 1) / 2
    
    def find_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[tuple]:
        """
        Find similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []
        
        for idx, candidate in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate)
            
            if similarity >= threshold:
                similarities.append((idx, similarity))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return similarities[:top_k]


class ChromaDBManager:
    """Manages ChromaDB collections for vector storage."""
    
    def __init__(self, db_path: str = "./data/chromadb"):
        """
        Initialize ChromaDB manager.
        
        Args:
            db_path: Path to ChromaDB storage
        """
        self.db_path = db_path
        self.client = None
        self.collection = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=self.db_path)
            logger.info(f"Initialized ChromaDB at {self.db_path}")
        except ImportError:
            logger.warning("chromadb not installed, using mock storage")
            self.client = None
    
    def get_or_create_collection(
        self,
        collection_name: str = "bird_intelligence"
    ) -> Any:
        """
        Get or create a ChromaDB collection.
        
        Args:
            collection_name: Name of collection
            
        Returns:
            ChromaDB collection
        """
        if self.client is None:
            return None
        
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Got or created collection: {collection_name}")
            return self.collection
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return None
    
    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Add documents to collection.
        
        Args:
            documents: List of document texts
            ids: List of document IDs
            embeddings: List of document embeddings
            metadatas: List of metadata dicts
            
        Returns:
            Success status
        """
        if self.collection is None:
            logger.warning("Collection not initialized")
            return False
        
        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas or [{}] * len(documents)
            )
            logger.info(f"Added {len(documents)} documents to collection")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query collection by embedding.
        
        Args:
            query_embedding: Query embedding
            n_results: Number of results
            where: Filter conditions
            
        Returns:
            Query results
        """
        if self.collection is None:
            logger.warning("Collection not initialized")
            return {"ids": [], "documents": [], "distances": []}
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return {"ids": [], "documents": [], "distances": []}
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of collection
            
        Returns:
            Success status
        """
        if self.client is None:
            return False
        
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False


# Global instances
_embedding_manager = None
_chromadb_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create global embedding manager."""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager


def get_chromadb_manager(db_path: str = "./data/chromadb") -> ChromaDBManager:
    """Get or create global ChromaDB manager."""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager(db_path)
    return _chromadb_manager
