"""
Unit tests for the core logic of the assistant.
"""
import pytest
import asyncio
from core.events import EventBus
from core.state_manager import StateManager, AssistantState
from core.context import ConversationContext

def test_context():
    ctx = ConversationContext(conversation_id="test_session")
    assert ctx.conversation_id == "test_session"
    
    ctx.set("key", "value")
    assert ctx.get("key") == "value"
    assert ctx.get("missing", "default") == "default"
    
    ctx.remove("key")
    assert ctx.get("key") is None
    
    ctx.clear()
    assert len(ctx.variables) == 0

@pytest.mark.anyio
async def test_event_bus():
    bus = EventBus()
    received_events = []

    async def callback(data):
        received_events.append(data)

    bus.subscribe("test_event", callback)
    await bus.publish("test_event", {"payload": "data"})
    
    assert len(received_events) == 1
    assert received_events[0]["payload"] == "data"
    
    bus.unsubscribe("test_event", callback)
    await bus.publish("test_event", {"payload": "more_data"})
    
    assert len(received_events) == 1 # unsubscribed, so no change

@pytest.mark.anyio
async def test_state_manager():
    bus = EventBus()
    state_mgr = StateManager(event_bus=bus)
    assert state_mgr.state == AssistantState.IDLE
    
    transitions = []
    async def state_cb(data):
        transitions.append(data)
        
    bus.subscribe("state_changed", state_cb)
    
    await state_mgr.transition_to(AssistantState.THINKING)
    assert state_mgr.state == AssistantState.THINKING
    
    assert len(transitions) == 1
    assert transitions[0]["old_state"] == "idle"
    assert transitions[0]["new_state"] == "thinking"
