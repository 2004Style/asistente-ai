"""
Implementation of the Anthropic LLM provider.
"""
import json
import urllib.request
import urllib.error
import asyncio
from typing import List
from llm.base import BaseLLMProvider
from llm.message import Message

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "claude-3-haiku-20240307", temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, messages: List[Message], **kwargs) -> Message:
        if not self.api_key:
            return Message(
                role="assistant",
                content=f"[MOCK RESPONSE - Anthropic API Key not configured]\nRespuesta simulada para Claude '{self.model}':\nÚltimo mensaje: '{messages[-1].content}'"
            )

        # Separate system messages from chat messages
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_msg += msg.content + "\n"
            else:
                chat_messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                })

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": 1024,
            "temperature": kwargs.get("temperature", self.temperature)
        }
        if system_msg:
            payload["system"] = system_msg.strip()

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        def _send_request():
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                raise Exception(f"Anthropic API error ({e.code}): {error_body}")
            except Exception as e:
                raise Exception(f"Failed to communicate with Anthropic: {str(e)}")

        try:
            res_data = await asyncio.to_thread(_send_request)
            text = res_data["content"][0]["text"]
            return Message(role="assistant", content=text)
        except Exception as e:
            return Message(
                role="assistant",
                content=f"Error calling Anthropic API: {str(e)}"
            )
