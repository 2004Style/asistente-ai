"""
Unit tests for vision capture, object detection and image classification.
"""
import pytest
from vision.screen import capture_screenshot
from vision.camera import capture_camera
from vision.manager import VisionManager

def test_screenshot_png_header():
    # Capture screen (or fallback dummy)
    png_bytes = capture_screenshot()
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 8
    
    # Confirm standard PNG magic number header: 89 50 4E 47 0D 0A 1A 0A
    assert png_bytes.startswith(b'\x89PNG\r\n\x1a\n')

def test_camera_png_header():
    camera_bytes = capture_camera()
    assert isinstance(camera_bytes, bytes)
    assert len(camera_bytes) > 8
    assert camera_bytes.startswith(b'\x89PNG\r\n\x1a\n')

@pytest.mark.anyio
async def test_vision_manager_analysis():
    vision_mgr = VisionManager()
    
    # Analyze screen
    screen_info = await vision_mgr.analyze_screen()
    assert screen_info["source"] == "screen"
    assert "detected_objects" in screen_info
    assert len(screen_info["description"]) > 0
    
    # Analyze webcam
    cam_info = await vision_mgr.analyze_camera()
    assert cam_info["source"] == "camera"
    assert "detected_objects" in cam_info
    assert len(cam_info["description"]) > 0
