"""
Implementation of the Local/Ollama LLM provider.
"""
import json
import urllib.request
import urllib.error
import asyncio
from typing import List
from llm.base import BaseLLMProvider
from llm.message import Message

class LocalProvider(BaseLLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3", temperature: float = 0.7):
        self.host = host
        self.model = model
        self.temperature = temperature

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, messages: List[Message], **kwargs) -> Message:
        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in messages
            ],
            "options": {
                "temperature": kwargs.get("temperature", self.temperature)
            },
            "stream": False
        }

        headers = {"Content-Type": "application/json"}

        def _send_request():
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as e:
                # If local Ollama connection fails, raise exception or fallback
                raise e

        try:
            res_data = await asyncio.to_thread(_send_request)
            choice = res_data["message"]
            return Message(
                role="assistant",
                content=choice.get("content") or ""
            )
        except Exception as e:
            return Message(
                role="assistant",
                content=f"[MOCK RESPONSE - Local Ollama at {self.host} connection failed]\n"
                        f"Mensaje recibido: '{messages[-1].content}'.\n"
                        f"Detalle del error de conexión: {str(e)}"
            )
