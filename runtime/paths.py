"""
Defines dynamic, platform-appropriate config, data, and cache paths for the runtime.
"""
import os
import sys
from pathlib import Path

APP_NAME = "rbot"
HOME = Path.home()

# Check if running tests
is_testing = "pytest" in sys.modules or os.getenv("TESTING") == "true"

if is_testing:
    # Isolated test environment to avoid modifying user's dev/prod configs/data
    root_path = Path(__file__).parent.parent.resolve()
    CONFIG_DIR = root_path / "tests" / "configs"
    DATA_DIR = root_path / "tests" / "data"
    CACHE_DIR = DATA_DIR / "cache"
    LOG_DIR = DATA_DIR / "logs"
    ENV_FILE_PATH = CONFIG_DIR / ".env"
else:
    # Production/Distribution mode: follow OS specifications
    # Developers simulate this by symlinking CONFIG_DIR and DATA_DIR to the workspace.
    if sys.platform == "win32":
        # Windows standard directories
        appdata = Path(os.getenv("APPDATA", str(HOME / "AppData" / "Roaming")))
        localappdata = Path(os.getenv("LOCALAPPDATA", str(HOME / "AppData" / "Local")))
        CONFIG_DIR = appdata / APP_NAME
        DATA_DIR = localappdata / APP_NAME
    elif sys.platform == "darwin":
        # macOS standard directories
        lib_support = HOME / "Library" / "Application Support" / APP_NAME
        CONFIG_DIR = lib_support / "config"
        DATA_DIR = lib_support / "data"
    else:
        # Linux standard directories (XDG Specifications)
        CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", str(HOME / ".config"))) / APP_NAME
        DATA_DIR = Path(os.getenv("XDG_DATA_HOME", str(HOME / ".local" / "share"))) / APP_NAME
        
    CACHE_DIR = DATA_DIR / "cache"
    LOG_DIR = DATA_DIR / "logs"
    ENV_FILE_PATH = CONFIG_DIR / ".env"

# Ensure runtime directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Ensure data subdirectories exist
(DATA_DIR / "db").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "models").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "notes").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "memories").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "runtime").mkdir(parents=True, exist_ok=True)

# Copy default config templates if they do not exist in CONFIG_DIR
default_configs_src = None
if getattr(sys, "frozen", False):
    # If running from a bundled package (PyInstaller/Nuitka)
    if hasattr(sys, "_MEIPASS"):
        default_configs_src = Path(sys._MEIPASS) / "configs"
else:
    # Running from source code
    default_configs_src = Path(__file__).parent.parent.resolve() / "configs"

if default_configs_src and default_configs_src.exists():
    for f in default_configs_src.glob("*.yml"):
        dest_file = CONFIG_DIR / f.name
        if not dest_file.exists():
            try:
                import shutil
                shutil.copy(str(f), str(dest_file))
            except Exception:
                pass
    
    # Copy manifests directory and keep it in sync
    manifests_src = default_configs_src / "manifests"
    if manifests_src.exists():
        manifests_dst = CONFIG_DIR / "manifests"
        try:
            import shutil
            manifests_dst.mkdir(parents=True, exist_ok=True)
            for f in manifests_src.glob("*.yml"):
                shutil.copy(str(f), str(manifests_dst / f.name))
        except Exception:
            pass

def resolve_path(path_str: str) -> Path:
    """
    Resolves relative path strings to absolute paths depending on the environment.
    If the path starts with 'data/', resolves it relative to DATA_DIR.
    If it starts with 'configs/', resolves it relative to CONFIG_DIR.
    """
    if not path_str:
        return DATA_DIR
        
    p = Path(path_str)
    if p.is_absolute():
        return p
        
    parts = p.parts
    if parts:
        if parts[0] == "data":
            return DATA_DIR / Path(*parts[1:])
        elif parts[0] == "configs":
            return CONFIG_DIR / Path(*parts[1:])
            
    return DATA_DIR / p
