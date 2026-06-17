"""
Summarizes conversation history when it exceeds the active token limit.
"""
from typing import List, Optional
from llm.base import BaseLLMProvider
from llm.message import Message

class ConversationSummarizer:
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    async def summarize(self, messages: List[Message]) -> str:
        """Summarize conversation messages using LLM or fallback."""
        if not messages:
            return ""
            
        if not self.llm_provider:
            # Simple text fallback
            recent_usr = [m.content for m in messages if m.role == "user"]
            return f"Resumen local: Conversación con {len(messages)} mensajes. Último tema: {recent_usr[-1] if recent_usr else 'ninguno'}"

        prompt = (
            "Resume la siguiente conversación de forma muy breve (máximo 2 párrafos). "
            "Enfócate en las decisiones tomadas y en los detalles importantes de las tareas realizadas:\n\n"
        )
        for msg in messages:
            prompt += f"{msg.role.upper()}: {msg.content}\n"

        try:
            summary_msg = await self.llm_provider.generate([
                Message(role="system", content="Eres un asistente sintetizador."),
                Message(role="user", content=prompt)
            ])
            return summary_msg.content.strip()
        except Exception as e:
            return f"Error al generar resumen: {e}"
