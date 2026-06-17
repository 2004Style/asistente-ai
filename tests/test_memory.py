"""
Unit tests for the memory subsystem of the assistant.
"""
import os
import pytest
from llm.message import Message
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory

def test_short_term_memory_rolling():
    # Set limit to 3
    mem = ShortTermMemory(limit=3)
    
    mem.add_message(Message(role="system", content="sys"))
    mem.add_message(Message(role="user", content="msg1"))
    mem.add_message(Message(role="assistant", content="reply1"))
    
    assert len(mem.get_messages()) == 3
    
    # Adding a 4th message should trigger rolling limit
    # Since first message is 'system', it should pop the second message (msg1)
    mem.add_message(Message(role="user", content="msg2"))
    
    msgs = mem.get_messages()
    assert len(msgs) == 3
    assert msgs[0].content == "sys"       # system remains
    assert msgs[1].content == "reply1"    # msg1 popped
    assert msgs[2].content == "msg2"

def test_long_term_memory_db(tmp_path):
    # Use temporary sqlite file
    db_file = tmp_path / "test_assistant.db"
    lt_mem = LongTermMemory(db_path=str(db_file))
    
    # Check tables initialized
    assert db_file.exists()
    
    # Save a message
    msg = Message(role="user", content="hello long term")
    lt_mem.save_message(session_id="test_session", message=msg)
    
    # Fetch messages
    history = lt_mem.get_messages(session_id="test_session")
    assert len(history) == 1
    assert history[0].role == "user"
    assert history[0].content == "hello long term"
    
    # Add searchable note
    lt_mem.add_memory(content="El color preferido del usuario es azul marino.", metadata={"category": "pref"})
    
    # Search notes
    results = lt_mem.search_memories(query="azul")
    assert len(results) == 1
    assert "azul marino" in results[0]["content"]
