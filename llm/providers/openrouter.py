"""
Implementation of the OpenRouter LLM provider.
"""
import json
import urllib.request
import urllib.error
import asyncio
from typing import List
from llm.base import BaseLLMProvider
from llm.message import Message

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "meta-llama/llama-3-8b-instruct:free", temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, messages: List[Message], **kwargs) -> Message:
        if not self.api_key:
            return Message(
                role="assistant",
                content=f"[MOCK RESPONSE - OpenRouter API Key not configured]\nRespuesta simulada para OpenRouter '{self.model}':\nÚltimo mensaje: '{messages[-1].content}'"
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in messages
            ],
            "temperature": kwargs.get("temperature", self.temperature)
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        def _send_request():
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                raise Exception(f"OpenRouter API error ({e.code}): {error_body}")
            except Exception as e:
                raise Exception(f"Failed to communicate with OpenRouter: {str(e)}")

        try:
            res_data = await asyncio.to_thread(_send_request)
            choice = res_data["choices"][0]["message"]
            return Message(
                role="assistant",
                content=choice.get("content") or ""
            )
        except Exception as e:
            return Message(
                role="assistant",
                content=f"Error calling OpenRouter API: {str(e)}"
            )
