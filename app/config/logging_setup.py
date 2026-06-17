"""
Dynamic logging configuration for routing subsystem logs to separate files.
"""
import logging
from pathlib import Path

class SubsystemRoutingHandler(logging.Handler):
    """
    Custom logging handler that routes log records to separate files 
    based on the logger name (subsystem category).
    """
    def __init__(self, log_dir: Path, formatter: logging.Formatter):
        super().__init__()
        self.log_dir = log_dir
        self.formatter = formatter
        self.handlers = {}
        
    def get_handler_for_category(self, category: str) -> logging.FileHandler:
        if category not in self.handlers:
            f_path = self.log_dir / f"{category}.log"
            h = logging.FileHandler(f_path, mode="w", encoding="utf-8")
            h.setFormatter(self.formatter)
            self.handlers[category] = h
        return self.handlers[category]
        
    def emit(self, record):
        name = record.name.lower()
        
        # Routing classification rules
        if any(x in name for x in ["voice", "stt", "tts", "vosk", "whisper", "piper", "edge"]):
            category = "voice"
        elif any(x in name for x in ["vision", "yolo", "clip", "screen", "camera", "detect"]):
            category = "vision"
        elif any(x in name for x in ["llm", "openai", "gemini", "anthropic", "openrouter", "ollama", "local"]):
            # Specific STT/TTS goes to voice, model providers go to llm
            if any(x in name for x in ["stt", "tts"]):
                category = "voice"
            else:
                category = "llm"
        elif "memory" in name:
            category = "memory"
        elif any(x in name for x in ["daemon", "scheduler", "task", "runtime", "health"]):
            category = "runtime"
        elif any(x in name for x in ["assistant", "agent", "planner", "executor", "state", "event", "bus"]):
            category = "core"
        elif "cli" in name:
            category = "cli"
        else:
            category = "app"
            
        try:
            handler = self.get_handler_for_category(category)
            handler.emit(record)
        except Exception:
            self.handleError(record)
        
    def close(self):
        for h in self.handlers.values():
            try:
                h.close()
            except Exception:
                pass
        self.handlers.clear()
        super().close()

def setup_logging(log_dir: str = "data/logs"):
    """Set up log formatting and routing loggers to dedicated files."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    # 1. Console stream handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Central catch-all file handler (assistant.log)
    general_file = log_path / "assistant.log"
    general_handler = logging.FileHandler(general_file, mode="w", encoding="utf-8")
    general_handler.setFormatter(formatter)
    root_logger.addHandler(general_handler)
    
    # 3. Subsystem routing handler (dynamic split)
    routing_handler = SubsystemRoutingHandler(log_path, formatter)
    root_logger.addHandler(routing_handler)
