"""
Environment variable loader for sensitive settings.

Reads from a `.env` file or system environment variables.
"""
import os
from dotenv import load_dotenv

# Load .env file if it exists
from runtime.paths import ENV_FILE_PATH
load_dotenv(dotenv_path=str(ENV_FILE_PATH))

def get_env(key: str, default: str = None) -> str:
    """Retrieve an environment variable value."""
    return os.getenv(key, default)
