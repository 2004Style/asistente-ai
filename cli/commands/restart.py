"""
Command to restart the assistant daemon.
"""
import time
from cli.commands.stop import stop_cmd
from cli.commands.start import start_cmd

def restart_cmd():
    print("Reiniciando rbot daemon...")
    stop_cmd()
    time.sleep(1.5)
    start_cmd()
