#!/usr/bin/env python3
"""
Script used during installation to detect system details and write platforms.yml accordingly.
"""
import os
import sys
import yaml
from pathlib import Path

# Add root folder to sys.path
root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

from host.detector import detect_system

def main():
    print("Detecting system environment...")
    sys_info = detect_system()
    print(f"Detected OS: {sys_info['os']}")
    print(f"Detected Distro: {sys_info['distro']}")
    print(f"Detected Desktop: {sys_info['desktop']}")
    
    config_dir = root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    platforms_file = config_dir / "platforms.yml"
    
    platforms_data = {
        "default_platform": sys_info["os"],
        "desktop_environment": sys_info["desktop"]
    }
    
    with open(platforms_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(platforms_data, f, default_flow_style=False)
        
    print(f"Successfully wrote platform settings to {platforms_file}")
    
    # Save system info JSON profile to data/runtime/host-profile.json
    import json
    runtime_dir = root / "data" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    profile_file = runtime_dir / "host-profile.json"
    with open(profile_file, "w", encoding="utf-8") as f:
        json.dump(sys_info, f, indent=4)
    print(f"Successfully wrote host profile to {profile_file}")

if __name__ == "__main__":
    main()
