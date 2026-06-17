"""
Command to run the assistant in the foreground (development mode).
"""
import logging
from app.main import main

def run_cmd():
    print("Iniciando rbot en modo primer plano...")
    main()
