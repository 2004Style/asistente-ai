"""
Implementation of the Gemini LLM provider.
"""
import json
import urllib.request
import urllib.error
import asyncio
from typing import List
from llm.base import BaseLLMProvider
from llm.message import Message

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash", temperature: float = 0.7):
        self.api_key = api_key
        if model and "gemini-1.5-flash" in model and "8b" not in model:
            model = "gemini-2.5-flash"
        self.model = model
        self.temperature = temperature

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, messages: List[Message], **kwargs) -> Message:
        if not self.api_key:
            return Message(
                role="assistant",
                content=f"[MOCK RESPONSE - Gemini API Key not configured]\nRespuesta simulada para Gemini '{self.model}':\nÚltimo mensaje: '{messages[-1].content}'"
            )

        # Convert roles: system, user, assistant -> user, model
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.temperature)
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        headers = {
            "Content-Type": "application/json"
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        def _send_request():
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                raise Exception(f"Gemini API error ({e.code}): {error_body}")
            except Exception as e:
                raise Exception(f"Failed to communicate with Gemini: {str(e)}")

        try:
            res_data = await asyncio.to_thread(_send_request)
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return Message(role="assistant", content=text)
        except Exception as e:
            return Message(
                role="assistant",
                content=f"Error calling Gemini API: {str(e)}"
            )
