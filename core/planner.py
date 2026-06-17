"""
Planner component to sequence tool calls and actions for complex tasks.
Supports context-aware parameter extraction from conversation history.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from llm.base import BaseLLMProvider
from llm.message import Message

logger = logging.getLogger("Planner")

class Planner:
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    async def generate_plan(self, user_request: str, tools_metadata: List[Dict[str, Any]], history: Optional[List[Message]] = None) -> List[Dict[str, Any]]:
        """Generate a sequential plan (list of steps) using the LLM, resolving context from history."""
        # Get active UI mode from daemon state
        active_mode = "core"
        try:
            from runtime import daemon
            active_mode = getattr(daemon, "_active_ui_mode", "core")
        except Exception:
            pass

        if not self.llm_provider:
            return [{"tool": "list_notes", "arguments": {}}]

        from core.prompts import SPANISH_TOOL_DESCRIPTIONS
        tools_description = ""
        for tool in tools_metadata:
            desc = SPANISH_TOOL_DESCRIPTIONS.get(tool['name'], tool['description'])
            tools_description += f"- Nombre: {tool['name']}\n  Descripción: {desc}\n  Esquema de argumentos (en JSON Schema): {tool['schema']}\n\n"

        # Build context description
        history_context = ""
        if history:
            history_context = "Historial reciente de la conversación:\n"
            for msg in history[-6:]:
                history_context += f"- {msg.role}: {msg.content}\n"
            history_context += "\n"

        prompt = (
            "Dada la petición del usuario y el historial de la conversación, genera un plan secuencial de pasos para resolverla usando únicamente las herramientas disponibles.\n"
            "IMPORTANTE: Si la petición del usuario se refiere a datos del historial (por ejemplo, 'el enlace que te pasé', 'el texto anterior', 'el archivo creado', etc.), "
            "busca y extrae la información real (como URLs, nombres de archivos, textos) del historial e inyéctala directamente en los argumentos de la herramienta.\n\n"
            f"El modo visual actual de la interfaz del HUD es: '{active_mode}'\n"
            f"REGLA CRÍTICA: Si el usuario dice algo ambiguo como 'qué ves' o 'qué hay aquí':\n"
            f"- Si el modo actual es 'camera', DEBES llamar a 'inspect_camera'.\n"
            f"- Si el modo actual es 'screen', DEBES llamar a 'inspect_screen'.\n\n"
            f"{history_context}"
            f"Nueva petición: '{user_request}'\n\n"
            f"Herramientas disponibles:\n{tools_description}\n"
            "Formato de respuesta: Devuelve estrictamente un arreglo JSON de objetos, donde cada objeto tenga 'tool' (nombre) y 'arguments' (diccionario de parámetros).\n"
            "Ejemplo:\n"
            "[\n"
            "  {\"tool\": \"download_media\", \"arguments\": {\"url\": \"https://example.com/file.pdf\", \"format\": \"file\"}}\n"
            "]\n"
            "No incluyas bloques de código markdown como ```json. Devuelve solo el JSON válido."
        )

        try:
            logger.info("Generating plan using LLM with context")
            from core.prompts import SYSTEM_BASE_PROMPT, TOOLS_INSTRUCTIONS, SAFETY_GUARDRAILS
            system_prompt = (
                f"{SYSTEM_BASE_PROMPT}\n\n"
                f"{TOOLS_INSTRUCTIONS}\n\n"
                f"{SAFETY_GUARDRAILS}\n\n"
                "Eres un planificador experto. Tu única tarea es recibir una petición y estructurar un plan secuencial de pasos usando las herramientas en base a las reglas anteriores. Responde solo con JSON válido, sin Markdown."
            )
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=prompt)
            ]
            response = await self.llm_provider.generate(messages, temperature=0.1)
            content = response.content.strip()
            
            if content.startswith("```json"):
                content = content.replace("```json", "", 1)
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            steps = json.loads(content)
            if isinstance(steps, list):
                logger.info(f"Successfully generated plan with {len(steps)} steps: {steps}")
                return steps
        except Exception as e:
            logger.error(f"Failed to generate plan via LLM: {e}", exc_info=True)
        
        return [{"tool": "list_notes", "arguments": {}}]
