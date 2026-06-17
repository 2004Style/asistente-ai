"""
Bootstrap module for the AI assistant.

This module initializes registries and connects components such as tools, memory stores, LLM providers and vision modules.
"""
import logging
from app.config.loader import load_config
from app.container import Container
from core.events import EventBus
from core.state_manager import StateManager
from host.registry import get_host_adapter
from llm.router import get_llm_provider
from tools.registry import load_default_tools
from security.confirmation import ConfirmationManager
from security.audit import AuditLogger
from security.policy import SecurityPolicy
from security.sandbox import CommandSandbox
from memory.manager import MemoryManager
from core.executor import Executor
from core.planner import Planner
from core.agent import Agent
from core.assistant import Assistant
from voice.manager import VoiceManager
from interfaces.voice_controller import VoiceController
from vision.manager import VisionManager
from automation.tasks_queue import TaskQueue
from automation.scheduler import Scheduler
from automation.reminders import ReminderManager

logger = logging.getLogger("Bootstrap")

def bootstrap() -> None:
    """Initialize the assistant components and register singletons in Container."""
    # Limit CPU thread utilization for PyTorch, NumPy, OpenBLAS etc. to keep system fluid
    import os
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["MKL_NUM_THREADS"] = "2"
    os.environ["OPENBLAS_NUM_THREADS"] = "2"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
    os.environ["NUMEXPR_NUM_THREADS"] = "2"
    
    try:
        import torch
        try:
            torch.set_num_threads(2)
        except RuntimeError:
            pass
        try:
            torch.set_num_interop_threads(2)
        except RuntimeError:
            pass
        logger.info("PyTorch CPU thread limit set to 2.")
    except ImportError:
        pass

    logger.info("Initializing system bootstrap...")

    # 1. Load config
    config = load_config()
    Container.register("config", config)

    # Initialize dynamic routed logging using the configured log directory
    from app.config.logging_setup import setup_logging
    from runtime.paths import resolve_path
    log_dir = "data/logs"
    if hasattr(config, "app") and hasattr(config.app, "log_dir") and config.app.log_dir:
        log_dir = config.app.log_dir
    setup_logging(str(resolve_path(log_dir)))

    # 2. Event Bus
    event_bus = EventBus()
    Container.register("event_bus", event_bus)

    # 3. State Manager
    state_mgr = StateManager(event_bus=event_bus)
    Container.register("state_manager", state_mgr)

    # 4. Host Platform Adapter
    platform_adapter = get_host_adapter()
    Container.register("platform_adapter", platform_adapter)

    # 5. LLM Provider
    llm_provider = get_llm_provider(config.llm)
    Container.register("llm_provider", llm_provider)

    # 6. Tool Registry
    tool_registry = load_default_tools()
    Container.register("tool_registry", tool_registry)

    # 7. Security layers (Confirmation & Audit)
    confirm_mgr = ConfirmationManager(
        min_permission_level=config.security.min_permission_level,
        require_confirmation=config.security.require_confirmation,
        event_bus=event_bus
    )
    Container.register("confirmation_manager", confirm_mgr)
    
    security_policy = SecurityPolicy()
    Container.register("security_policy", security_policy)
    
    sandbox = CommandSandbox(policy=security_policy)
    Container.register("sandbox", sandbox)
    
    audit_logger = AuditLogger()
    Container.register("audit_logger", audit_logger)

    # 8. Memory Manager
    memory_mgr = MemoryManager(
        db_path=str(resolve_path(config.memory.db_path)),
        short_term_limit=config.memory.short_term_limit,
        llm_provider=llm_provider
    )
    Container.register("memory_manager", memory_mgr)

    # 9. Core Orchestration Components
    executor = Executor()
    Container.register("executor", executor)
    
    planner = Planner(llm_provider=llm_provider)
    Container.register("planner", planner)
    
    agent = Agent(llm_provider=llm_provider)
    Container.register("agent", agent)
    
    assistant = Assistant()
    Container.register("assistant", assistant)

    # 10. Voice Subsystem
    voice_mgr = VoiceManager()
    Container.register("voice_manager", voice_mgr)
    
    voice_ctrl = VoiceController()
    Container.register("voice_controller", voice_ctrl)

    # 11. Vision Subsystem
    vision_mgr = VisionManager()
    Container.register("vision_manager", vision_mgr)

    # 12. Automation Subsystem
    task_queue = TaskQueue()
    Container.register("task_queue", task_queue)

    scheduler = Scheduler()
    Container.register("scheduler", scheduler)

    reminder_manager = ReminderManager()
    Container.register("reminder_manager", reminder_manager)

    logger.info("Bootstrap finished successfully. All systems nominal.")
