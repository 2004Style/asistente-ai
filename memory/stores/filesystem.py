"""
FileSystem‑based vector store for memories.
"""
import json
import os
import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("FileSystemStore")

class FileSystemStore:
    def __init__(self, file_path: str = "data/db/vector_store.json"):
        self.file_path = file_path
        self._ensure_dir()
        self._data = self._load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load FileSystemStore data: {e}")
            return {}

    def _save(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save FileSystemStore data: {e}")

    def add(self, doc_id: str, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._data[doc_id] = {
            "vector": vector,
            "text": text,
            "metadata": metadata or {}
        }
        self._save()

    def delete(self, doc_id: str) -> None:
        if doc_id in self._data:
            del self._data[doc_id]
            self._save()

    def clear(self) -> None:
        self._data.clear()
        self._save()

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        for doc_id, item in self._data.items():
            try:
                vector = item["vector"]
                text = item["text"]
                metadata = item["metadata"]
                
                # Compute Cosine Similarity
                dot_product = sum(a * b for a, b in zip(query_vector, vector))
                norm_a = math.sqrt(sum(a * a for a in query_vector))
                norm_b = math.sqrt(sum(b * b for b in vector))
                
                similarity = dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
                results.append({
                    "id": doc_id,
                    "content": text,
                    "metadata": metadata,
                    "score": similarity
                })
            except Exception as e:
                logger.error(f"Error calculating similarity in FileSystemStore: {e}")

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
