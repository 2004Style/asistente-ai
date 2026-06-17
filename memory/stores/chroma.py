"""
Chroma‑based vector store for memories.
"""
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ChromaStore")

class ChromaStore:
    def __init__(self, persist_directory: str = "data/db/chroma"):
        self.persist_directory = persist_directory
        self._fallback = None
        self._collection = None
        
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._client.get_or_create_collection("rbot_memories")
            logger.info("ChromaDB vector store initialized successfully.")
        except ImportError:
            logger.warning("chromadb is not installed. Falling back to FileSystemStore.")
            from memory.stores.filesystem import FileSystemStore
            self._fallback = FileSystemStore(file_path="data/db/chroma_fallback.json")

    def add(self, doc_id: str, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self._fallback is not None:
            self._fallback.add(doc_id, vector, text, metadata)
            return
            
        flat_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    flat_meta[k] = v
                else:
                    flat_meta[k] = json.dumps(v)
        
        self._collection.add(
            embeddings=[vector],
            documents=[text],
            metadatas=[flat_meta] if flat_meta else None,
            ids=[doc_id]
        )

    def delete(self, doc_id: str) -> None:
        if self._fallback is not None:
            self._fallback.delete(doc_id)
            return
        self._collection.delete(ids=[doc_id])

    def clear(self) -> None:
        if self._fallback is not None:
            self._fallback.clear()
            return
        try:
            self._client.delete_collection("rbot_memories")
            self._collection = self._client.get_or_create_collection("rbot_memories")
        except Exception as e:
            logger.error(f"Failed to clear Chroma store: {e}")

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        if self._fallback is not None:
            return self._fallback.search(query_vector, limit)
            
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=limit
        )
        
        formatted = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            ids = results["ids"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
            
            for doc_id, doc, meta, dist in zip(ids, docs, metadatas, distances):
                unflattened_meta = {}
                if meta:
                    for k, v in meta.items():
                        if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                            try:
                                unflattened_meta[k] = json.loads(v)
                            except Exception:
                                unflattened_meta[k] = v
                        else:
                            unflattened_meta[k] = v
                            
                score = 1.0 / (1.0 + dist)
                formatted.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": unflattened_meta,
                    "score": score
                })
        return formatted
