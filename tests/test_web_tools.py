"""
Unit tests for the new and enhanced web, file, workspace, and applications tools subsystem.
Supports testing multi-platform (Linux, Windows, macOS) and multi-desktop adapters.
"""
import sys
import os
from unittest.mock import MagicMock, patch

# Mock GUI and clipboard libraries at the module level to prevent X11 server requirements during testing
mock_pyautogui = MagicMock()
mock_pyautogui.size.return_value = (1920, 1080)
sys.modules['pyautogui'] = mock_pyautogui
sys.modules['pyperclip'] = MagicMock()

import pytest
from pathlib import Path
from tools.web.actions.open_youtube import OpenYoutubeTool
from tools.web.actions.open_whatsapp import OpenWhatsappTool, get_platform_modifiers
from tools.web.actions.web_search_direct import WebSearchDirectTool
from tools.web.actions.google_maps import GoogleMapsTool
from tools.web.actions.download_media import DownloadMediaTool
from tools.files.actions.create_word_document import CreateWordDocumentTool
from tools.files.actions.create_pdf_document import CreatePDFDocumentTool
from tools.workspace.actions.create_project import CreateProjectTool
from tools.applications.actions.schedule_reminder import ScheduleReminderTool
from tools.window.actions.inspect_image import InspectImageTool
from tools.web.browser_utils import open_browser_url, find_browser_binary

@pytest.mark.anyio
@patch("tools.web.browser_utils.shutil.which")
@patch("tools.web.browser_utils.subprocess.Popen")
@patch("tools.web.browser_utils.webbrowser.open")
async def test_browser_utils_fallback(mock_webbrowser, mock_popen, mock_which):
    # Case 1: Browser is installed
    mock_which.return_value = "/usr/bin/firefox"
    res = open_browser_url("https://example.com", "firefox")
    assert res["status"] == "success"
    assert res["browser_used"] == "firefox"
    assert "warning" not in res
    mock_popen.assert_called_once()
    
    # Case 2: Browser is not installed, fallback to default
    mock_popen.reset_mock()
    mock_which.return_value = None
    res = open_browser_url("https://example.com", "chrome")
    assert res["status"] == "success"
    assert res["browser_used"] == "default"
    assert "warning" in res
    assert "no se encuentra instalado" in res["warning"]
    mock_webbrowser.assert_called_once_with("https://example.com")

@patch("tools.web.browser_utils.sys.platform", "darwin")
@patch("tools.web.browser_utils.os.path.exists")
def test_find_browser_macos(mock_exists):
    # Mock that Firefox Mac app exists
    mock_exists.side_effect = lambda path: "/Applications/Firefox.app" in path
    
    res = find_browser_binary("firefox")
    assert res["found"] is True
    assert res["cmd"] == ["open", "-a", "Firefox"]

@patch("tools.web.browser_utils.sys.platform", "win32")
@patch("tools.web.browser_utils.os.path.exists")
@patch("tools.web.browser_utils.shutil.which")
def test_find_browser_windows(mock_which, mock_exists):
    mock_which.return_value = None
    # Mock that Chrome EXE exists in C:\\Program Files
    mock_exists.side_effect = lambda path: "Google\\Chrome\\Application\\chrome.exe" in path
    
    res = find_browser_binary("chrome")
    assert res["found"] is True
    assert "chrome.exe" in res["cmd"][0]

@patch("tools.clipboard_utils.detect_system")
def test_whatsapp_modifiers(mock_detect):
    # Case 1: macOS
    mock_detect.return_value = {"os": "macos", "distro": "macos", "desktop": "aqua"}
    ctrl, alt = get_platform_modifiers()
    assert ctrl == "command"
    assert alt == "option"
    
    # Case 2: Linux
    mock_detect.return_value = {"os": "linux", "distro": "arch", "desktop": "hyprland"}
    ctrl, alt = get_platform_modifiers()
    assert ctrl == "ctrl"
    assert alt == "alt"

@pytest.mark.anyio
@patch("tools.web.actions.open_youtube.scrape_youtube_first_result")
@patch("tools.web.actions.open_youtube.open_browser_url")
async def test_youtube_tool_play(mock_open_browser, mock_scrape):
    mock_scrape.return_value = "dQw4w9WgXcQ"
    mock_open_browser.return_value = {"status": "success", "browser_used": "default", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    
    tool = OpenYoutubeTool()
    result = await tool.execute(query="never gonna give you up", action="play", browser="default")
    
    assert result["status"] == "success"
    assert result["action"] == "play"
    assert result["video_id"] == "dQw4w9WgXcQ"
    assert "watch?v=dQw4w9WgXcQ" in result["url"]
    mock_scrape.assert_called_once_with("never gonna give you up")

@pytest.mark.anyio
@patch("tools.web.actions.open_youtube.open_browser_url")
async def test_youtube_tool_search(mock_open_browser):
    mock_open_browser.return_value = {"status": "success", "browser_used": "chrome", "url": "https://www.youtube.com/results?search_query=python%20tutorial"}
    
    tool = OpenYoutubeTool()
    result = await tool.execute(query="python tutorial", action="search", browser="chrome")
    
    assert result["status"] == "success"
    assert result["action"] == "search"
    assert "results?search_query=python%20tutorial" in result["url"]

@pytest.mark.anyio
@patch("tools.web.actions.open_whatsapp.open_browser_url")
@patch("tools.web.actions.open_whatsapp.paste_text_via_gui")
async def test_whatsapp_tool_send_message_phone(mock_paste, mock_open_browser):
    mock_open_browser.return_value = {"status": "success", "browser_used": "default"}
    
    tool = OpenWhatsappTool()
    # Mock the sleep during wait
    with patch("asyncio.sleep", return_value=None):
        result = await tool.execute(phone="+51999999999", message="Hola", action="send_message")
        
    assert result["status"] == "success"
    assert result["action"] == "send_message"
    assert result["recipient"] == "+51999999999"
    mock_paste.assert_called_once_with("Hola")

@pytest.mark.anyio
@patch("tools.web.actions.open_whatsapp.open_browser_url")
@patch("tools.web.actions.open_whatsapp.paste_text_via_gui")
async def test_whatsapp_tool_open_chat_contact(mock_paste, mock_open_browser):
    mock_open_browser.return_value = {"status": "success", "browser_used": "brave"}
    
    tool = OpenWhatsappTool()
    with patch("asyncio.sleep", return_value=None):
        result = await tool.execute(contact_name="Juan Perez", action="open_chat", browser="brave")
        
    assert result["status"] == "success"
    assert result["action"] == "open_chat"
    assert result["recipient"] == "Juan Perez"
    mock_paste.assert_called_once_with("Juan Perez")

@pytest.mark.anyio
@patch("urllib.request.urlopen")
async def test_web_search_direct(mock_urlopen):
    # Mock HTML response from DuckDuckGo
    mock_response = MagicMock()
    mock_response.read.return_value = b"""
    <html>
    <body>
        <div class="result">
            <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fpython.org">Python Programming Language</a>
            <div class="result__snippet">The official home of the Python Programming Language.</div>
        </div>
        <div class="result">
            <a class="result__a" href="/l/?uddg=https%3A%2F%2Fwikipedia.org%2Fwiki%2FPython">Python Wikipedia</a>
            <div class="result__snippet">Python is a high-level programming language.</div>
        </div>
    </body>
    </html>
    """
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    tool = WebSearchDirectTool()
    result = await tool.execute(query="python", max_results=2)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Python Programming Language"
    assert result["results"][0]["link"] == "https://python.org"
    assert result["results"][0]["snippet"] == "The official home of the Python Programming Language."
    assert result["results"][1]["link"] == "https://wikipedia.org/wiki/Python"

@pytest.mark.anyio
@patch("tools.web.actions.google_maps.open_browser_url")
async def test_google_maps_directions(mock_open_browser):
    mock_open_browser.side_effect = lambda url, browser: {"status": "success", "browser_used": browser, "url": url}
    
    tool = GoogleMapsTool()
    result = await tool.execute(action="directions", origin="Madrid", destination="Barcelona", travel_mode="driving")
    
    assert result["status"] == "success"
    assert "maps/dir/" in result["url"]
    assert "origin=Madrid" in result["url"]
    assert "destination=Barcelona" in result["url"]
    assert "travelmode=driving" in result["url"]

@pytest.mark.anyio
@patch("tools.web.actions.download_media.download_youtube_media")
@patch("tools.web.actions.download_media.download_generic_file")
async def test_download_media(mock_download_generic, mock_download_yt, tmp_path):
    mock_download_yt.return_value = str(tmp_path / "song.mp3")
    mock_download_generic.return_value = str(tmp_path / "document.pdf")
    
    tool = DownloadMediaTool()
    
    # Test YouTube Download
    res_yt = await tool.execute(url="https://youtube.com/watch?v=123", format="mp3", output_dir=str(tmp_path))
    assert res_yt["status"] == "success"
    assert "song.mp3" in res_yt["filename"]
    
    # Test Generic file download
    res_generic = await tool.execute(url="https://example.com/document.pdf", format="file", output_dir=str(tmp_path))
    assert res_generic["status"] == "success"
    assert "document.pdf" in res_generic["filename"]

@pytest.mark.anyio
async def test_create_word_document(tmp_path):
    tool = CreateWordDocumentTool()
    res = await tool.execute(
        title="Reporte de Prueba",
        content="# Sección 1\nEsto es un párrafo.\n## Subsección 1.1\nOtro párrafo.",
        output_dir=str(tmp_path),
        filename="test_report.docx"
    )
    assert res["status"] == "success"
    assert Path(res["file_path"]).exists()

@pytest.mark.anyio
async def test_create_pdf_document(tmp_path):
    tool = CreatePDFDocumentTool()
    res = await tool.execute(
        title="Reporte PDF de Prueba",
        content="# Sección PDF\nContenido de prueba para el PDF.",
        output_dir=str(tmp_path),
        filename="test_report.pdf"
    )
    assert res["status"] == "success"
    assert Path(res["file_path"]).exists()

@pytest.mark.anyio
async def test_create_project(tmp_path):
    tool = CreateProjectTool()
    files = [
        {"path": "index.html", "content": "<h1>Tienda</h1>"},
        {"path": "css/styles.css", "content": "body { color: blue; }"}
    ]
    res = await tool.execute(
        project_name="my_store",
        files=files,
        base_dir=str(tmp_path)
    )
    assert res["status"] == "success"
    assert (tmp_path / "my_store" / "index.html").exists()
    assert (tmp_path / "my_store" / "css" / "styles.css").exists()

@pytest.mark.anyio
@patch("app.container.Container.resolve")
async def test_schedule_reminder(mock_resolve):
    from unittest.mock import AsyncMock
    from datetime import datetime
    mock_rem_mgr = MagicMock()
    mock_rem_mgr.set_reminder = AsyncMock(return_value=datetime(2026, 6, 17, 11, 0, 0))
    
    # Configure container mock
    mock_resolve.return_value = mock_rem_mgr
    
    tool = ScheduleReminderTool()
    
    # Calculate a valid future date
    future_iso = "2028-06-17T11:00:00"
    res = await tool.execute(
        text="Reunión importante",
        datetime_str=future_iso
    )
    assert res["status"] == "success"
    assert res["text"] == "Reunión importante"

@pytest.mark.anyio
@patch("app.container.Container.resolve")
@patch("urllib.request.urlopen")
async def test_inspect_image(mock_urlopen, mock_resolve):
    from unittest.mock import AsyncMock
    # Mock visual models inside vision_manager
    mock_vision_mgr = MagicMock()
    mock_vision_mgr.yolo.detect.return_value = [{"label": "cat"}]
    mock_vision_mgr.classify_scene = AsyncMock(return_value="A cat sitting on a couch")
    mock_resolve.return_value = mock_vision_mgr
    
    # Mock remote image request
    mock_response = MagicMock()
    mock_response.read.return_value = b"image_data_bytes"
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    tool = InspectImageTool()
    res = await tool.execute(image_path="https://example.com/cat.jpg")
    
    assert res["status"] == "success"
    assert "cat" in res["detected_objects"]
    assert res["description"] == "A cat sitting on a couch"
