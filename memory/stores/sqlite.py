"""
SQLite‑backed vector store for memories.
"""
import sqlite3
import json
import math
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SQLiteStore")

class SQLiteStore:
    def __init__(self, db_path: str = "data/db/vector_store.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_store_items (
                    id TEXT PRIMARY KEY,
                    vector TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLiteStore table: {e}")
        finally:
            conn.close()

    def add(self, doc_id: str, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            vector_str = json.dumps(vector)
            metadata_str = json.dumps(metadata) if metadata else None
            cursor.execute(
                "INSERT OR REPLACE INTO vector_store_items (id, vector, text, metadata) VALUES (?, ?, ?, ?)",
                (doc_id, vector_str, text, metadata_str)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to add item to SQLiteStore: {e}")
        finally:
            conn.close()

    def delete(self, doc_id: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM vector_store_items WHERE id = ?", (doc_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete item from SQLiteStore: {e}")
        finally:
            conn.close()

    def clear(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM vector_store_items")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear SQLiteStore: {e}")
        finally:
            conn.close()

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, vector, text, metadata FROM vector_store_items")
            rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to query SQLiteStore: {e}")
            return []
        finally:
            conn.close()

        results = []
        for doc_id, vector_str, text, metadata_str in rows:
            try:
                vector = json.loads(vector_str)
                metadata = json.loads(metadata_str) if metadata_str else {}
                
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
                logger.error(f"Error processing row in SQLiteStore: {e}")

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
