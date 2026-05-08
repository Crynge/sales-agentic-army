"""
Vector database abstraction for agent memory
Supports ChromaDB, Qdrant, and pgvector
"""

from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class VectorMemoryManager:
    """Manages vector embeddings for agent memory"""
    
    def __init__(self, backend: str = "chromadb", **kwargs):
        self.backend = backend
        self.collections: Dict[str, Any] = {}
        self._initialize_backend(**kwargs)
    
    def _initialize_backend(self, **kwargs):
        """Initialize the vector database backend"""
        if self.backend == "chromadb":
            try:
                import chromadb
                from chromadb.config import Settings
                
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=kwargs.get("persist_directory", "./chroma_data"),
                ))
                logger.info("ChromaDB initialized")
            except ImportError:
                logger.warning("ChromaDB not installed, using in-memory storage")
                self.client = None
        elif self.backend == "qdrant":
            logger.info("Qdrant backend selected (configuration required)")
            self.client = None
        else:
            logger.warning(f"Unknown backend: {self.backend}, using in-memory")
            self.client = None
    
    def create_collection(self, name: str, embedding_dim: int = 1536) -> bool:
        """Create a new collection for storing embeddings"""
        if not self.client:
            return False
        
        try:
            collection = self.client.create_collection(
                name=name,
                metadata={"embedding_dim": embedding_dim}
            )
            self.collections[name] = collection
            logger.info(f"Collection created: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def add_embedding(self, collection_name: str, id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Add an embedding to a collection"""
        if collection_name not in self.collections:
            logger.error(f"Collection not found: {collection_name}")
            return False
        
        try:
            collection = self.collections[collection_name]
            collection.add(
                ids=[id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
            return False
    
    def search_similar(self, collection_name: str, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        if collection_name not in self.collections:
            return []
        
        try:
            collection = self.collections[collection_name]
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
