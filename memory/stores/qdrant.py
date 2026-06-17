"""
Qdrant‑based vector store for memories.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("QdrantStore")

class QdrantStore:
    def __init__(self, path: str = "data/db/qdrant"):
        self.path = path
        self._fallback = None
        self._collection_name = "rbot_memories"
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            self._client = QdrantClient(path=self.path)
            
            # Ensure collection exists
            collections = self._client.get_collections().collections
            collection_names = [col.name for col in collections]
            if self._collection_name not in collection_names:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
            logger.info("Qdrant vector store initialized successfully.")
        except ImportError:
            logger.warning("qdrant-client is not installed. Falling back to FileSystemStore.")
            from memory.stores.filesystem import FileSystemStore
            self._fallback = FileSystemStore(file_path="data/db/qdrant_fallback.json")

    def add(self, doc_id: str, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._fallback is not None:
            self._fallback.add(doc_id, vector, text, metadata)
            return
            
        from qdrant_client.models import PointStruct
        
        payload = {
            "text": text,
            "metadata": metadata or {}
        }
        
        # Ensure doc_id is numeric or uuid format for qdrant
        # If it is numeric string, cast to int
        point_id = None
        try:
            point_id = int(doc_id)
        except ValueError:
            # Generate a numeric hash of doc_id for Qdrant if it's not an integer
            point_id = hash(doc_id) & 0xffffffff
            
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    def delete(self, doc_id: str) -> None:
        if self._fallback is not None:
            self._fallback.delete(doc_id)
            return
            
        try:
            point_id = int(doc_id)
        except ValueError:
            point_id = hash(doc_id) & 0xffffffff
            
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=[point_id]
        )

    def clear(self) -> None:
        if self._fallback is not None:
            self._fallback.clear()
            return
            
        from qdrant_client.models import Distance, VectorParams
        try:
            self._client.delete_collection(self._collection_name)
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        except Exception as e:
            logger.error(f"Failed to clear Qdrant store: {e}")

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        if self._fallback is not None:
            return self._fallback.search(query_vector, limit)
            
        hits = self._client.search(
            collection_name=self._collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        formatted = []
        for hit in hits:
            payload = hit.payload or {}
            formatted.append({
                "id": str(hit.id),
                "content": payload.get("text", ""),
                "metadata": payload.get("metadata", {}),
                "score": hit.score
            })
        return formatted
