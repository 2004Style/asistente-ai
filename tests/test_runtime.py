"""
Unit tests for the assistant daemon runtime and instance locking.
"""
import os
import pytest
from fastapi.testclient import TestClient
from runtime.instance_lock import InstanceLock
from runtime.daemon import app
from app.bootstrap import bootstrap

def test_instance_lock(tmp_path):
    lock_file = tmp_path / "rbot.lock"
    
    lock1 = InstanceLock(lock_file=str(lock_file))
    lock2 = InstanceLock(lock_file=str(lock_file))
    
    # First acquire should succeed
    assert lock1.acquire() is True
    assert lock_file.exists()
    
    # Second acquire should fail
    assert lock2.acquire() is False
    
    # Release first lock
    lock1.release()
    assert not lock_file.exists()
    
    # Second should now succeed
    assert lock2.acquire() is True
    lock2.release()

def test_daemon_health_api():
    # Bootstrap the Container first so the daemon endpoint resolves dependencies successfully
    bootstrap()
    
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    
    res_config = client.get("/config")
    assert res_config.status_code == 200
    assert "app" in res_config.json()

def test_daemon_voice_config_update():
    bootstrap()
    client = TestClient(app)
    
    payload = {
        "llm": {
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "temperature": 0.8,
            "api_key": "some-key"
        },
        "voice": {
            "enabled": True,
            "push_to_talk": False,
            "stt_provider": "faster_whisper",
            "tts_provider": "edge_tts",
            "stt_model": "tiny",
            "tts_voice": "es-ES-ElviraNeural",
            "api_key": "voice-secret-key"
        },
        "security": {
            "min_permission_level": "medium",
            "require_confirmation": True
        },
        "app": {
            "name": "rbot-custom"
        },
        "memory": {
            "short_term_limit": 30
        }
    }
    
    from unittest.mock import patch
    with patch("runtime.daemon.update_yaml_file") as mock_update_yaml, \
         patch("runtime.daemon.update_env_file") as mock_update_env:
        res = client.post("/config", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        assert mock_update_yaml.call_count == 5
        assert mock_update_env.call_count == 2
    
    res_get = client.get("/config")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["voice"]["stt_model"] == "tiny"
    assert data["voice"]["tts_voice"] == "es-ES-ElviraNeural"
    assert data["voice"]["api_key"] == "voice-secret-key"

def test_daemon_preview_api(tmp_path):
    bootstrap()
    client = TestClient(app)
    
    # Non-existent file should return 404
    res = client.get("/api/preview?path=nonexistent.png")
    assert res.status_code == 404
    
    # Non-image file should return 400
    text_file = tmp_path / "test.txt"
    text_file.write_text("hello")
    res = client.get(f"/api/preview?path={text_file}")
    assert res.status_code == 400
    
    # Image file inside allowed temp directory should succeed
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n")
    res = client.get(f"/api/preview?path={img_file}")
    assert res.status_code == 200

def test_websocket_hud_interception():
    bootstrap()
    client = TestClient(app)
    
    with client.websocket_connect("/ws") as websocket:
        # Ignore initial state message
        initial_state = websocket.receive_json()
        assert initial_state["type"] == "state"
        
        # Send a user message (simulating text typed in the HUD)
        websocket.send_json({
            "message": "https://youtube.com/watch?v=xyz",
            "session_id": "test_session"
        })
        
        # We expect to receive a response with the acknowledgment string
        response = websocket.receive_json()
        assert response["type"] == "response"
        assert response["content"] == "[✔] Contenido recibido. Listo para instrucciones por voz."
        
        # Verify the message was indeed saved in the memory manager
        from app.container import Container
        memory_mgr = Container.resolve("memory_manager")
        messages = memory_mgr.get_messages("test_session")
        assert len(messages) > 0
        assert messages[-1].role == "user"
        assert "Pasted Payload: https://youtube.com/watch?v=xyz" in messages[-1].content



