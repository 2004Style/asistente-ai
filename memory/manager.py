"""
Orchestrates short-term memory, database persistence, and vector/semantic stores.
"""
from typing import List, Dict, Any, Optional
from llm.message import Message
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.summarizer import ConversationSummarizer
from llm.base import BaseLLMProvider

class MemoryManager:
    def __init__(self, db_path: str = "data/db/assistant.db", short_term_limit: int = 20, llm_provider: Optional[BaseLLMProvider] = None):
        self.short_term = ShortTermMemory(limit=short_term_limit)
        self.long_term = LongTermMemory(db_path=db_path)
        self.summarizer = ConversationSummarizer(llm_provider=llm_provider)

    def add_message(self, session_id: str, message: Message) -> None:
        """Add message to short term memory and persist to SQLite database."""
        self.short_term.add_message(message)
        self.long_term.save_message(session_id, message)

    def get_messages(self, session_id: str) -> List[Message]:
        """Get the active list of messages in short-term memory. Fallback to long-term database if empty."""
        messages = self.short_term.get_messages()
        if not messages:
            # Hydrate short-term from database
            db_msgs = self.long_term.get_messages(session_id, limit=self.short_term.limit)
            for m in db_msgs:
                self.short_term.add_message(m)
            messages = self.short_term.get_messages()
        return messages

    def clear(self) -> None:
        """Clear memory cache."""
        self.short_term.clear()

    def add_semantic_note(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add note or fact to long term searchable memories."""
        self.long_term.add_memory(content, metadata)

    def search_semantic_notes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search long term memories for matching information."""
        return self.long_term.search_memories(query, limit)

    async def summarize_history(self, session_id: str) -> str:
        """Generate a summary of the active conversation session."""
        msgs = self.get_messages(session_id)
        return await self.summarizer.summarize(msgs)
