"""
Main assistant orchestrator class managing conversation flow and state transitions.
"""
import logging
from typing import Dict, Any, List
from app.container import Container
from llm.message import Message
from core.state_manager import AssistantState

logger = logging.getLogger("Assistant")

class Assistant:
    def __init__(self):
        pass

    async def chat(self, user_text: str, session_id: str = "default") -> str:
        """Process a user message, run agent logic, execute plans if needed, and return response."""
        import re
        event_bus = Container.resolve("event_bus")
        state_mgr = Container.resolve("state_manager")
        memory_mgr = Container.resolve("memory_manager")
        llm = Container.resolve("llm_provider")
        agent = Container.resolve("agent")
        planner = Container.resolve("planner")
        executor = Container.resolve("executor")
        registry = Container.resolve("tool_registry")

        # Intercept voice/text UI commands directly to trigger UI events
        user_clean = user_text.lower().strip()
        ui_command = None
        response_text = None
        
        # Check if the user is requesting an activation/show/open action (without "ver" which is ambiguous)
        is_open_intent = any(kw in user_clean for kw in [
            "abrir", "mostrar", "activar", "entrar al", "iniciar", "pon ", "coloca", 
            "cambia", "cambiar", "modo", "show", "open", "activa", "visualizar"
        ])
        # Check if the user is requesting a close/hide/stop action
        is_close_intent = any(kw in user_clean for kw in [
            "cerrar", "ocultar", "desactivar", "minimizar", "quitar", "salir de", "apagar", "apaga", 
            "close", "hide", "desactiva", "quita", "oculta"
        ])

        # Resolve active UI mode dynamically
        active_mode = "core"
        try:
            from runtime import daemon
            active_mode = getattr(daemon, "_active_ui_mode", "core")
        except Exception:
            pass

        # Check if the user is requesting a generic close command (e.g. "desactiva modo", "quítalo")
        is_generic_close = user_clean in [
            "desactiva", "desactiva modo", "desactivar", "desactivar modo", 
            "cerrar", "cerrar modo", "ocultar", "quitar", "salir", "apagar"
        ] or (is_close_intent and len(user_clean.split()) <= 3 and not any(kw in user_clean for kw in ["camara", "cámara", "pantalla", "escritorio", "screen", "configuracion", "configuración", "ajustes", "opciones", "hud"]))

        if is_generic_close:
            if active_mode == "camera":
                ui_command = "hide_camera"
                response_text = "Desactivando el modo cámara."
            elif active_mode == "screen":
                ui_command = "hide_screen"
                response_text = "Desactivando el modo pantalla."

        # If not resolved generically, check specific keywords
        if not ui_command:
            # Check config panel
            if any(kw in user_clean for kw in ["configuracion", "configuración", "ajustes", "opciones"]):
                if is_close_intent or any(kw in user_clean for kw in ["cerrar", "ocultar", "salir", "close", "hide", "desactivar", "desactiva"]):
                    ui_command = "close_config"
                    response_text = "Cerrando el panel de configuración."
                else:
                    ui_command = "open_config"
                    response_text = "Abriendo el panel de configuración."
            # Check camera mode
            elif any(kw in user_clean for kw in ["camara", "cámara", "webcam"]):
                if is_close_intent:
                    ui_command = "hide_camera"
                    response_text = "Desactivando el modo cámara."
                elif is_open_intent or user_clean in ["camara", "cámara", "webcam", "modo camara", "modo cámara"]:
                    ui_command = "show_camera"
                    response_text = "Activando el modo cámara."
            # Check screen mode
            elif any(kw in user_clean for kw in ["pantalla", "escritorio", "screen"]):
                if is_close_intent:
                    ui_command = "hide_screen"
                    response_text = "Desactivando el modo pantalla."
                elif is_open_intent or user_clean in ["pantalla", "escritorio", "screen", "modo pantalla", "modo screen"]:
                    ui_command = "show_screen"
                    response_text = "Activando el modo pantalla."
            # Check HUD
            elif any(kw in user_clean for kw in ["hud", "interfaz", "panel principal"]):
                if is_close_intent or any(kw in user_clean for kw in ["cerrar", "ocultar", "salir", "close", "hide"]):
                    ui_command = "close_hud"
                    response_text = "Ocultando el HUD principal."
                else:
                    ui_command = "open_hud"
                    response_text = "Abriendo el HUD principal."
            # Check Demo
            elif any(kw in user_clean for kw in ["demo", "demostracion", "demostración"]):
                if any(kw in user_clean for kw in ["detener", "parar", "cancelar", "stop", "desactivar", "desactiva"]):
                    ui_command = "stop_demo"
                    response_text = "Deteniendo la rotación de demostración."
                else:
                    ui_command = "start_demo"
                    response_text = "Iniciando la rotación de demostración de estados."

        if ui_command:
            # Publish UI command event
            await event_bus.publish("ui_command", {"action": ui_command})
            
            # Transition states to simulate speech and finish
            await state_mgr.transition_to(AssistantState.SPEAKING)
            user_msg = Message(role="user", content=user_text)
            memory_mgr.add_message(session_id, user_msg)
            
            response_msg = Message(role="assistant", content=response_text)
            memory_mgr.add_message(session_id, response_msg)
            await state_mgr.transition_to(AssistantState.IDLE)
            return response_text

        # 1. State: THINKING & log user message
        await state_mgr.transition_to(AssistantState.THINKING)
        
        user_message = Message(role="user", content=user_text)
        memory_mgr.add_message(session_id, user_message)

        # Get full conversation history
        history = memory_mgr.get_messages(session_id)

        # 2. Decide intent
        decision = await agent.decide_intent(user_text, history)
        
        if decision.get("needs_plan"):
            # 3. State: PLANNING
            await state_mgr.transition_to(AssistantState.PLANNING)
            
            # Prepare tools metadata
            tools_metadata = []
            for t in registry.list_tools():
                tools_metadata.append({
                    "name": t.manifest.name,
                    "description": t.manifest.description,
                    "schema": str(t.manifest.arguments_schema.model_json_schema())
                })

            # Generate steps
            steps = await planner.generate_plan(user_text, tools_metadata, history)
            
            # 4. State: EXECUTING
            await state_mgr.transition_to(AssistantState.EXECUTING)
            
            results = []
            for step in steps:
                t_name = step.get("tool")
                t_args = step.get("arguments") or {}
                
                # Execute tool
                tool_res = await executor.execute_tool(t_name, t_args, session_id)
                results.append({
                    "step": step,
                    "result": tool_res
                })

            # 5. State: THINKING (generating synthesis response)
            await state_mgr.transition_to(AssistantState.THINKING)
            
            prompt = (
                f"El usuario solicitó: '{user_text}'\n"
                "Para cumplir con esto, ejecutamos un plan con las siguientes herramientas y resultados:\n\n"
            )
            for idx, res in enumerate(results):
                prompt += f"Paso {idx+1}: Herramienta '{res['step']['tool']}' con argumentos {res['step']['arguments']}\n"
                prompt += f"Resultado: {res['result']}\n\n"
            
            prompt += "Genera una respuesta final detallada e informativa en español para el usuario basándote en los resultados anteriores y en la historia de la conversación."

            from core.prompts import SYSTEM_BASE_PROMPT, SAFETY_GUARDRAILS
            synthesis_messages = [
                Message(role="system", content=f"{SYSTEM_BASE_PROMPT}\n{SAFETY_GUARDRAILS}\nSintetiza los resultados del plan de manera amigable y clara en español, considerando el historial de la conversación."),
                *history[:-1], # Include history up to the current turn
                Message(role="user", content=prompt)
            ]
            
            try:
                response_msg = await llm.generate(synthesis_messages)
            except Exception as e:
                response_msg = Message(role="assistant", content=f"Error al generar la respuesta del plan: {e}")
            
            memory_mgr.add_message(session_id, response_msg)
            await state_mgr.transition_to(AssistantState.IDLE)
            return response_msg.content

        else:
            # 3. Conversational response
            await state_mgr.transition_to(AssistantState.THINKING)
            
            # Get full context history
            history = memory_mgr.get_messages(session_id)
            
            # Build conversation payload
            from core.prompts import SYSTEM_BASE_PROMPT, SAFETY_GUARDRAILS
            system_content = f"{SYSTEM_BASE_PROMPT}\n{SAFETY_GUARDRAILS}"
            conversation_payload = [
                Message(role="system", content=system_content),
                *history
            ]

            try:
                response_msg = await llm.generate(conversation_payload)
            except Exception as e:
                response_msg = Message(role="assistant", content=f"Error al conversar con el modelo: {e}")

            memory_mgr.add_message(session_id, response_msg)
            await state_mgr.transition_to(AssistantState.IDLE)
            return response_msg.content
