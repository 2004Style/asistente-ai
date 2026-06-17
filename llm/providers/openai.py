"""
Implementation of the OpenAI LLM provider.
Wraps the OpenAI API for use within the assistant.
"""
import json
import urllib.request
import urllib.error
import asyncio
from typing import List, Dict, Any
from llm.base import BaseLLMProvider
from llm.message import Message

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini", temperature: float = 0.7):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, messages: List[Message], **kwargs) -> Message:
        # Check if API key is provided
        if not self.api_key:
            # Fallback to mock response for testing/development
            return Message(
                role="assistant",
                content=f"[MOCK RESPONSE - OpenAI API Key not configured]\nRecibí tu mensaje. Aquí tienes una respuesta simulada para el modelo '{self.model}':\nÚltimo mensaje del usuario: '{messages[-1].content}'"
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {})
                } for msg in messages
            ],
            "temperature": kwargs.get("temperature", self.temperature)
        }

        # Handle tools if passed
        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            payload["tool_choice"] = kwargs["tool_choice"]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        def _send_request():
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                raise Exception(f"OpenAI API error ({e.code}): {error_body}")
            except Exception as e:
                raise Exception(f"Failed to communicate with OpenAI: {str(e)}")

        try:
            res_data = await asyncio.to_thread(_send_request)
            choice = res_data["choices"][0]["message"]
            
            tool_calls = choice.get("tool_calls")
            return Message(
                role="assistant",
                content=choice.get("content") or "",
                tool_calls=tool_calls
            )
        except Exception as e:
            return Message(
                role="assistant",
                content=f"Error calling OpenAI API: {str(e)}"
            )
