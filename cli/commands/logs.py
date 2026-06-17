"""
Command to display the latest logs of the assistant.
"""
import sys
from pathlib import Path

def logs_cmd():
    from runtime.paths import resolve_path
    log_file = resolve_path("data/logs/assistant.log")
    
    if not log_file.exists():
        print("No se encontraron logs de rbot en la ruta:")
        print(f"  {log_file}")
        return
        
    print(f"--- Mostrando últimas 50 líneas de {log_file} ---")
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for line in lines[-50:]:
                sys.stdout.write(line)
    except Exception as e:
        print(f"Error al leer el archivo de log: {e}")
