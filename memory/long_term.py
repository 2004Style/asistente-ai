"""
Long-term memory using SQLite for persistence.
"""
import os
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from llm.message import Message
from memory.embeddings import EmbeddingService

logger = logging.getLogger("LongTermMemory")

class LongTermMemory:
    def __init__(self, db_path: str = "data/db/assistant.db"):
        self.db_path = db_path
        self._init_db()
        self.embeddings = EmbeddingService()
        self.vector_store = self._init_vector_store()

    def _init_vector_store(self):
        try:
            from app.container import Container
            config = Container.resolve("config")
            store_type = config.memory.vector_store_type
        except Exception:
            store_type = "sqlite"

        if store_type == "chroma":
            from memory.stores.chroma import ChromaStore
            return ChromaStore()
        elif store_type == "qdrant":
            from memory.stores.qdrant import QdrantStore
            return QdrantStore()
        elif store_type == "filesystem":
            from memory.stores.filesystem import FileSystemStore
            return FileSystemStore()
        else:
            from memory.stores.sqlite import SQLiteStore
            # Use a separate database file or the same one for sqlite vector store
            return SQLiteStore(self.db_path)

    def _get_connection(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize SQLite tables for messages and long-term search items."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create memories table (vector mock storage / keyword search)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
        finally:
            conn.close()

    def save_message(self, session_id: str, message: Message) -> None:
        """Save a message to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            tool_calls_str = json.dumps(message.tool_calls) if message.tool_calls else None
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
                (session_id, message.role, message.content, tool_calls_str)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")
        finally:
            conn.close()

    def get_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Load conversation history from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        messages = []
        try:
            cursor.execute(
                "SELECT role, content, tool_calls FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            for role, content, tool_calls_str in rows:
                tool_calls = json.loads(tool_calls_str) if tool_calls_str else None
                messages.append(Message(role=role, content=content, tool_calls=tool_calls))
        except Exception as e:
            logger.error(f"Failed to load messages from database: {e}")
        finally:
            conn.close()
        return messages

    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Store a semantic text entry in memory and vector store."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            metadata_str = json.dumps(metadata) if metadata else None
            cursor.execute(
                "INSERT INTO memories (content, metadata) VALUES (?, ?)",
                (content, metadata_str)
            )
            doc_id = str(cursor.lastrowid)
            conn.commit()
            
            # Save to vector store
            vector = self.embeddings.get_embedding(content)
            self.vector_store.add(doc_id, vector, content, metadata)
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
        finally:
            conn.close()

    def _keyword_search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform simple keyword-based search over stored memories."""
        conn = self._get_connection()
        cursor = conn.cursor()
        results = []
        try:
            # Simple LIKE keyword match
            search_query = f"%{query}%"
            cursor.execute(
                "SELECT content, metadata FROM memories WHERE content LIKE ? LIMIT ?",
                (search_query, limit)
            )
            rows = cursor.fetchall()
            for content, metadata_str in rows:
                metadata = json.loads(metadata_str) if metadata_str else {}
                results.append({"content": content, "metadata": metadata})
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
        finally:
            conn.close()
        return results

    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search vector store first; fall back to keyword search if empty or failed."""
        try:
            query_vector = self.embeddings.get_embedding(query)
            results = self.vector_store.search(query_vector, limit)
            if results:
                return results
        except Exception as e:
            logger.error(f"Vector search failed, falling back to keyword search: {e}")
        
        # Fallback to keyword search
        return self._keyword_search_memories(query, limit)
