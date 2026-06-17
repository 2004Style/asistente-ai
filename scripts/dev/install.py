#!/usr/bin/env python3
"""
Cross‑platform installation helper for the AI assistant.

Detects the system environment, initializes configurations, seeds the DB, and installs OS services.
"""
import os
import shutil
import sys
from pathlib import Path

# Add root folder to sys.path
root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

from scripts.dev.detect_system import main as run_detection
from scripts.dev.seed import main as run_seeding
from services.manager import get_service_installer

def create_developer_symlinks():
    """Create symlinks from OS standard locations to local configs/data folders."""
    import sys
    import subprocess
    
    # 1. Resolve standard OS directories
    home = Path.home()
    if sys.platform == "win32":
        appdata = Path(os.getenv("APPDATA", str(home / "AppData" / "Roaming")))
        localappdata = Path(os.getenv("LOCALAPPDATA", str(home / "AppData" / "Local")))
        os_config_dir = appdata / "rbot"
        os_data_dir = localappdata / "rbot"
    elif sys.platform == "darwin":
        lib_support = home / "Library" / "Application Support" / "rbot"
        os_config_dir = lib_support / "config"
        os_data_dir = lib_support / "data"
    else:
        os_config_dir = Path(os.getenv("XDG_CONFIG_HOME", str(home / ".config"))) / "rbot"
        os_data_dir = Path(os.getenv("XDG_DATA_HOME", str(home / ".local" / "share"))) / "rbot"
        
    # Source workspace folders
    ws_configs = root / "configs"
    ws_data = root / "data"
    
    print("\n--- Creating Developer Symlinks ---")
    for src, dst in [(ws_configs, os_config_dir), (ws_data, os_data_dir)]:
        need_create = True
        if dst.exists() or dst.is_symlink() or os.path.islink(dst):
            try:
                if dst.is_symlink() or os.path.islink(dst):
                    try:
                        if dst.resolve() == src.resolve():
                            need_create = False
                    except Exception:
                        pass
                
                if need_create:
                    if dst.is_symlink() or os.path.islink(dst):
                        os.unlink(dst)
                    elif dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
            except Exception as e:
                print(f"Warning: Could not remove existing destination {dst}: {e}")
                if need_create:
                    continue
                
        if need_create:
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                if sys.platform == "win32":
                    subprocess.run(f'mklink /J "{dst}" "{src}"', shell=True, check=True, stdout=subprocess.DEVNULL)
                else:
                    os.symlink(src, dst)
                print(f"  [OK] Symlink created: {dst} -> {src}")
            except Exception as e:
                print(f"  [ERROR] Failed to create symlink {dst} -> {src}: {e}")

def main():
    print("=========================================")
    print("      rbot AI Assistant Installation     ")
    print("=========================================")
    
    # 1. Initialize env file inside configs folder
    env_file = root / "configs" / ".env"
    env_example = root / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("Creating .env from .env.example...")
            shutil.copy(str(env_example), str(env_file))
        else:
            print("Creating blank .env file...")
            with open(env_file, "w") as f:
                f.write("OPENAI_API_KEY=\nGEMINI_API_KEY=\n")
    else:
        print(".env already exists, skipping copy.")
        
    # Create developer symlinks
    create_developer_symlinks()
        
    # 2. Run system detection
    print("\n--- Running System Detection ---")
    try:
        run_detection()
    except Exception as e:
        print(f"Error during system detection: {e}", file=sys.stderr)
        
    # 3. Seed database
    print("\n--- Seeding Database ---")
    try:
        run_seeding()
    except Exception as e:
        print(f"Error during database seeding: {e}", file=sys.stderr)
        
    # 4. Install background OS service
    print("\n--- Installing Background Service ---")
    try:
        installer = get_service_installer()
        success = installer.install()
        if success:
            print("Background service installed successfully.")
        else:
            print("Background service installation reported failure (might require manual startup or permissions).")
    except Exception as e:
        print(f"Failed to install service: {e}", file=sys.stderr)
        
    print("\n=========================================")
    print("Installation complete! You can start the assistant using 'rbot start' or run locally using 'scripts/dev/dev.py'.")
    print("=========================================")

if __name__ == "__main__":
    main()
