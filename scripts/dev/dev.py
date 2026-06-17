#!/usr/bin/env python3
"""
Development helper for running the assistant locally.

Provides shortcuts to start the assistant in development mode with live reload, etc.
"""
import subprocess
import sys
from pathlib import Path
import os
import shutil

# Add root folder to sys.path
root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

from app.config.loader import load_config

def create_developer_symlinks():
    """Create symlinks from OS standard locations to local configs/data folders."""
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
    
    print("Checking/Creating Developer Symlinks...")
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
    create_developer_symlinks()
    print("Starting development environment...")
    
    try:
        config = load_config()
        host = config.app.host
        port = config.app.port
    except Exception:
        host = "127.0.0.1"
        port = 8000
        
    print(f"Server starting on http://{host}:{port} with live reload...")
    
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", host, 
        "--port", str(port), 
        "--reload"
    ]
    
    # Run from root folder
    os.chdir(root)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nDevelopment server stopped by user.")
    except Exception as e:
        print(f"Error starting development server: {e}")

if __name__ == "__main__":
    main()
