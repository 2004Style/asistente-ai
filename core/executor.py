"""
Executes tool actions, handles permission verification and records audit logs.
"""
import logging
from typing import Any, Dict, Optional
from app.container import Container
from security.confirmation import ConfirmationRequiredError

logger = logging.getLogger("Executor")

class Executor:
    def __init__(self):
        pass

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], session_id: str = "default") -> Dict[str, Any]:
        """Execute a tool by name with arguments, checking permissions and logging audit trail."""
        registry = Container.resolve("tool_registry")
        confirm_mgr = Container.resolve("confirmation_manager")
        audit_log = Container.resolve("audit_logger")
        event_bus = Container.resolve("event_bus")
        policy = Container.resolve("security_policy")

        tool = registry.get_tool(tool_name)
        if not tool:
            err_msg = f"Tool '{tool_name}' not found in registry."
            logger.error(err_msg)
            return {"error": err_msg}

        # Validate arguments against security policies first
        if not policy.validate_action(tool_name, arguments):
            err_msg = f"Security Policy Blocked execution of '{tool_name}' with args: {arguments}"
            audit_log.log_action(tool_name, arguments, tool.manifest.permission_level, approved=False, status="blocked_by_policy", result=err_msg)
            await event_bus.publish("tool_blocked_by_policy", {"tool": tool_name, "session_id": session_id, "error": err_msg})
            return {"error": "Action blocked by security policy."}

        # Check permission level and confirmation
        permission_level = tool.manifest.permission_level
        
        # Publish starting event
        await event_bus.publish("tool_start", {"tool": tool_name, "arguments": arguments, "session_id": session_id})

        approved = False
        try:
            # Request confirmation (will prompt CLI or raise ConfirmationRequiredError if daemon)
            approved = await confirm_mgr.request_confirmation(tool_name, arguments, permission_level)
            
            if not approved:
                audit_log.log_action(tool_name, arguments, permission_level, approved=False, status="denied")
                await event_bus.publish("tool_denied", {"tool": tool_name, "session_id": session_id})
                return {"error": f"Execution of tool '{tool_name}' was denied by user."}

            # If approved, run
            # Validate input arguments against Pydantic schema in manifest
            try:
                validated_args = tool.manifest.arguments_schema(**arguments).model_dump()
            except Exception as val_err:
                err_msg = f"Argument validation failed: {val_err}"
                audit_log.log_action(tool_name, arguments, permission_level, approved=True, status="failed", result=err_msg)
                await event_bus.publish("tool_error", {"tool": tool_name, "error": err_msg, "session_id": session_id})
                return {"error": err_msg}

            logger.info(f"Executing tool {tool_name} with {validated_args}")
            result = await tool.execute(**validated_args)
            
            # Log success
            audit_log.log_action(tool_name, validated_args, permission_level, approved=True, status="success", result=result)
            await event_bus.publish("tool_success", {"tool": tool_name, "result": result, "session_id": session_id})
            return {"result": result}

        except ConfirmationRequiredError as cre:
            # Re-raise to let API layer pause and prompt UI
            audit_log.log_action(tool_name, arguments, permission_level, approved=False, status="pending_confirmation")
            await event_bus.publish("tool_pending_confirmation", {"tool": tool_name, "arguments": arguments, "session_id": session_id})
            raise cre
        except Exception as e:
            err_msg = f"Tool execution failed: {str(e)}"
            logger.error(err_msg, exc_info=True)
            audit_log.log_action(tool_name, arguments, permission_level, approved=approved, status="failed", result=err_msg)
            await event_bus.publish("tool_error", {"tool": tool_name, "error": err_msg, "session_id": session_id})
            return {"error": err_msg}
