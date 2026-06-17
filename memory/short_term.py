"""
Short-term memory management for the AI assistant.
"""
from typing import List
from llm.message import Message

class ShortTermMemory:
    def __init__(self, limit: int = 20):
        self.limit = limit
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to short-term memory, keeping the size within the limit."""
        self.messages.append(message)
        if len(self.messages) > self.limit:
            # Keep system messages if any, otherwise pop from head
            # A common strategy is to keep the first message if it is system
            if self.messages[0].role == "system":
                self.messages.pop(1)
            else:
                self.messages.pop(0)

    def get_messages(self) -> List[Message]:
        """Retrieve all messages in short-term memory."""
        return self.messages

    def clear(self) -> None:
        """Clear the short-term memory."""
        self.messages.clear()
