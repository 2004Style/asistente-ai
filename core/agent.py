"""
Agent module containing routing and action decision logic.
Supports context-aware intent routing.
"""
import logging
from typing import Optional, Dict, Any, List
from llm.base import BaseLLMProvider
from llm.message import Message

logger = logging.getLogger("Agent")

class Agent:
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    async def decide_intent(self, user_request: str, history: Optional[List[Message]] = None) -> Dict[str, Any]:
        """Decide if a request is conversational or needs tool execution (plan), considering recent history."""
        vision_keywords = ["cámara", "camara", "webcam", "yolo", "veo", "ves", "mano", "detecta", "analiza", "analizar", "pantalla", "pantallas", "imagen"]
        system_keywords = ["abre", "listar", "ver", "archivo", "ventana", "nota", "descarga", "crea", "documento", "reunión", "reunion", "programa", "proyecto", "tienda"]
        
        # Get active UI mode from daemon state
        active_mode = "core"
        try:
            from runtime import daemon
            active_mode = getattr(daemon, "_active_ui_mode", "core")
        except Exception:
            pass

        if not self.llm_provider:
            has_keywords = any(kw in user_request.lower() for kw in system_keywords + vision_keywords)
            return {
                "needs_plan": has_keywords,
                "reason": "fallback heuristic based on keywords"
            }

        # Build context description
        history_context = ""
        if history:
            history_context = "Historial reciente de la conversación:\n"
            for msg in history[-6:]:
                history_context += f"- {msg.role}: {msg.content}\n"
            history_context += "\n"

        prompt = (
            "Decide si la siguiente petición del usuario requiere interactuar con el sistema operativo, archivos o hardware "
            "(ej. listar ventanas, descargar archivos/videos, crear documentos Word/PDF, programar tareas/recordatorios, "
            "crear proyectos de código, tomar notas, tomar capturas de pantalla o analizar la cámara/webcam/imágenes) "
            "o si es solo una conversación/pregunta directa.\n\n"
            f"El modo visual actual de la interfaz del HUD es: '{active_mode}' (si el modo es 'camera' o 'screen' y el usuario pregunta 'qué ves' o qué hay, requiere plan/herramientas para inspeccionar).\n\n"
            f"{history_context}"
            f"Nueva petición a enrutar: '{user_request}'\n\n"
            "Responde estrictamente en formato JSON válido:\n"
            "{\n"
            "  \"needs_plan\": true/false,\n"
            "  \"reason\": \"explicación breve\"\n"
            "}"
        )

        try:
            from core.prompts import SYSTEM_BASE_PROMPT
            system_prompt = (
                f"{SYSTEM_BASE_PROMPT}\n\n"
                "Eres un enrutador inteligente. Decidirás si la petición requiere planeación/herramientas o si es meramente conversacional. Responde solo con JSON válido."
            )
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=prompt)
            ]
            response = await self.llm_provider.generate(messages, temperature=0.1)
            import json
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)
            logger.info(f"Agent decision: {data}")
            return data
        except Exception as e:
            logger.warning(f"Failed to decide intent using LLM: {e}")
            has_keywords = any(kw in user_request.lower() for kw in system_keywords + vision_keywords)
            return {
                "needs_plan": has_keywords,
                "reason": "exception fallback heuristic"
            }
