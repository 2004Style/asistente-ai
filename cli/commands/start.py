"""
Command to start the assistant daemon in the background.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

def start_cmd():
    print("Iniciando rbot daemon en segundo plano...")
    from runtime.paths import resolve_path
    
    # Ensure logs folder exists
    logs_dir = resolve_path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    lock_file = resolve_path("data/rbot.lock")
    if lock_file.exists():
        print("Aviso: El lockfile ya existe. Podría haber otra instancia ejecutándose o no se cerró limpiamente.")
        print(f"Ruta lockfile: {lock_file}")
        # Let's check if the process actually exists
        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0) # sends dummy signal to check process life
            print(f"Error: rbot ya se está ejecutando con PID {pid}.")
            return
        except (ProcessLookupError, ValueError, FileNotFoundError):
            print("El proceso previo ya no existe, eliminando lockfile viejo e iniciando...")
            try:
                os.remove(lock_file)
            except Exception:
                pass

    stdout_path = logs_dir / "daemon.stdout.log"
    stderr_path = logs_dir / "daemon.stderr.log"
    
    stdout_file = open(stdout_path, "w")
    stderr_file = open(stderr_path, "w")

    root = Path(__file__).parent.parent.parent.resolve()
    
    # In frozen mode, sys.executable is the compiled binary itself, and we start the daemon with subcommand 'run'
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "run"]
    else:
        cmd = [sys.executable, str(root / "app" / "main.py")]

    # Launch daemon asynchronously
    proc = subprocess.Popen(
        cmd,
        stdout=stdout_file,
        stderr=stderr_file,
        cwd=str(root) if not getattr(sys, "frozen", False) else str(logs_dir.parent),
        preexec_fn=os.setpgrp if sys.platform != "win32" else None
    )
    
    # Wait for the lockfile to be created to verify startup success
    time.sleep(2)
    
    if lock_file.exists():
        with open(lock_file, "r") as f:
            pid = f.read().strip()
        print(f"¡rbot daemon iniciado con éxito! PID={pid}")
    else:
        print("Error: El daemon no se pudo iniciar. Revisa los logs en:")
        print(f"  Stdout: {stdout_path}")
        print(f"  Stderr: {stderr_path}")
