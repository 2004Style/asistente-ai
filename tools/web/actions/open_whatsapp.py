"""
Opens WhatsApp Web, manages chats, sends messages, or reads messages from a contact.
Supports multi-platform (Linux, Windows, macOS) and multi-desktop environments.
"""
import urllib.parse
import logging
import asyncio
import subprocess
import sys
from typing import Any, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from tools.manifest import ToolManifest
from tools.web.browser_utils import open_browser_url
from host.detector import detect_system
from tools.clipboard_utils import (
    get_platform_modifiers,
    read_clipboard_text,
    write_clipboard_text,
    paste_text_via_gui
)

logger = logging.getLogger("OpenWhatsappTool")

class OpenWhatsappInput(BaseModel):
    phone: Optional[str] = Field(None, description="Optional phone number (with country code, e.g. '51999999999').")
    contact_name: Optional[str] = Field(None, description="Optional contact name to search on WhatsApp Web.")
    message: Optional[str] = Field(None, description="Optional message text to type, send or pre-fill.")
    action: str = Field(
        "open_whatsapp",
        description="The action to perform: 'open_whatsapp' (just open page), 'open_chat' (open chat with contact/phone), 'send_message' (type and send message), or 'read_messages' (read last messages from current or specified chat)."
    )
    browser: str = Field("default", description="The specific browser to use: 'default', 'chrome', 'firefox', 'brave', 'chromium', or 'edge'.")

async def copy_chat_history() -> str:
    """Simulates selecting all and copying chat history to read messages."""
    import pyautogui
    ctrl, _ = get_platform_modifiers()
    width, height = pyautogui.size()
    
    # Click chat history area (typically center-right)
    logger.info("Clicking chat area to focus message list...")
    pyautogui.click(int(width * 0.65), int(height * 0.5))
    await asyncio.sleep(0.5)
    
    # Select all messages
    pyautogui.hotkey(ctrl, 'a')
    await asyncio.sleep(0.5)
    
    # Copy messages
    pyautogui.hotkey(ctrl, 'c')
    await asyncio.sleep(0.5)
    
    # Click message input box to clear selection
    pyautogui.click(int(width * 0.65), int(height * 0.95))
    return read_clipboard_text()

class OpenWhatsappTool(BaseTool):
    manifest = ToolManifest(
        name="open_whatsapp",
        description=(
            "Opens WhatsApp Web. Can open a chat directly if a phone number or contact_name is provided. "
            "Supports typing/sending messages and reading messages from the chat."
        ),
        arguments_schema=OpenWhatsappInput,
        permission_level="medium",
        risk="critical"
    )

    async def execute(self, **kwargs) -> Any:
        phone = kwargs.get("phone")
        contact_name = kwargs.get("contact_name")
        message = kwargs.get("message")
        action = kwargs.get("action", "open_whatsapp").lower().strip()
        browser = kwargs.get("browser", "default").lower().strip()

        # Sanitize phone if provided
        if phone:
            phone = "".join(c for c in phone if c.isdigit() or c == "+")

        url = "https://web.whatsapp.com/"
        open_res = None

        # Determine browser/URL flow
        if phone:
            quoted_msg = ""
            if message and action != "send_message":
                # Only pre-fill URL if we aren't doing direct send message via keyboard
                quoted_msg = urllib.parse.quote(message)
            
            url = f"https://web.whatsapp.com/send?phone={phone}"
            if quoted_msg:
                url += f"&text={quoted_msg}"
                
            logger.info(f"Opening WhatsApp Chat with phone {phone}: {url}")
            open_res = open_browser_url(url, browser)
            if "error" in open_res:
                return open_res
            
            # Wait for WhatsApp Web to load
            logger.info("Waiting 12 seconds for WhatsApp Web to load chat...")
            await asyncio.sleep(12.0)

        elif contact_name:
            logger.info(f"Opening WhatsApp Web to search contact: {contact_name}")
            open_res = open_browser_url(url, browser)
            if "error" in open_res:
                return open_res
            
            logger.info("Waiting 12 seconds for WhatsApp Web to load...")
            await asyncio.sleep(12.0)
            
            try:
                import pyautogui
                ctrl, alt = get_platform_modifiers()
                # Focus search box using standard shortcut (Ctrl+Alt+/ on Win/Linux, Cmd+Option+/ on macOS)
                logger.info("Focusing search box...")
                pyautogui.hotkey(ctrl, alt, '/')
                await asyncio.sleep(1.0)
                
                # Type contact name
                logger.info(f"Typing contact name: {contact_name}")
                await paste_text_via_gui(contact_name)
                await asyncio.sleep(1.5)
                
                # Press enter to open chat
                pyautogui.press('enter')
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Failed searching contact via GUI: {e}")
                return {"error": f"Failed to find contact: {e}"}
        else:
            # No target specified: perform action on existing window
            logger.info("No phone or contact name specified. Performing action on current window.")
            if action in ["send_message", "read_messages"]:
                pass
            else:
                open_res = open_browser_url(url, browser)
                return open_res

        # Execute actions: send_message or read_messages
        if action == "send_message":
            if not message:
                return {"error": "Missing message content to send."}
            try:
                import pyautogui
                logger.info(f"Pasting and sending message: {message}")
                # Ensure input is focused (click input bar)
                width, height = pyautogui.size()
                pyautogui.click(int(width * 0.65), int(height * 0.95))
                await asyncio.sleep(0.5)
                
                await paste_text_via_gui(message)
                pyautogui.press('enter')
                
                return {
                    "status": "success",
                    "action": "send_message",
                    "recipient": phone or contact_name or "current_chat",
                    "message_sent": message,
                    "browser": open_res.get("browser_used") if open_res else "default",
                    "warning": open_res.get("warning") if open_res else None
                }
            except Exception as e:
                logger.error(f"Failed to auto-send message: {e}")
                return {"error": f"Failed to send message: {e}"}

        elif action == "read_messages":
            try:
                logger.info("Attempting to read chat history...")
                chat_text = await copy_chat_history()
                
                # Return the read text
                return {
                    "status": "success",
                    "action": "read_messages",
                    "recipient": phone or contact_name or "current_chat",
                    "messages": chat_text,
                    "browser": open_res.get("browser_used") if open_res else "default",
                    "warning": open_res.get("warning") if open_res else None
                }
            except Exception as e:
                logger.error(f"Failed to read messages: {e}")
                return {"error": f"Failed to read messages: {e}"}

        # Default action: open_chat / open_whatsapp
        return {
            "status": "success",
            "action": "open_chat" if (phone or contact_name) else "open_whatsapp",
            "recipient": phone or contact_name,
            "browser": open_res.get("browser_used") if open_res else "default",
            "warning": open_res.get("warning") if open_res else None
        }
