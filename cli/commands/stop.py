"""
Command to stop the background assistant daemon.
"""
import os
import signal
from pathlib import Path

def stop_cmd():
    print("Deteniendo rbot daemon...")
    from runtime.paths import resolve_path
    lock_file = resolve_path("data/rbot.lock")
    
    if not lock_file.exists():
        print("No se encontró ninguna instancia activa (el lockfile no existe).")
        return
        
    try:
        with open(lock_file, "r") as f:
            pid = int(f.read().strip())
        
        print(f"Enviando señal SIGTERM al proceso {pid}...")
        os.kill(pid, signal.SIGTERM)
        print("Señal enviada con éxito.")
    except ProcessLookupError:
        print("El proceso no existía en ejecución. Limpiando lockfile huérfano...")
        try:
            os.remove(lock_file)
        except Exception:
            pass
    except Exception as e:
        print(f"Error al detener el daemon: {e}")
