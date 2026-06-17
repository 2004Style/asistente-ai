"""
Command to check the status of the assistant service.
"""
import urllib.request
import json
from pathlib import Path

def status_cmd():
    from runtime.paths import resolve_path
    lock_file = resolve_path("data/rbot.lock")
    
    if lock_file.exists():
        try:
            with open(lock_file, "r") as f:
                pid = f.read().strip()
            print("● rbot.service - AI Assistant Daemon")
            print(f"   Status: ACTIVO (Corriendo con PID {pid})")
            
            # Query local HTTP API health
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    print(f"   API: OK (Estado del asistente: {data.get('state')})")
            except Exception:
                print("   API: No responde (el puerto 8000 podría estar ocupado o iniciándose)")
        except Exception as e:
            print(f"Error al leer el estado: {e}")
    else:
        print("● rbot.service - AI Assistant Daemon")
        print("   Status: INACTIVO")
