"""
Command‑line interface entry point for the assistant.

Provides subcommands to run, start, stop and inspect the assistant service.
"""
import argparse
import sys
from cli.commands.run import run_cmd
from cli.commands.start import start_cmd
from cli.commands.stop import stop_cmd
from cli.commands.status import status_cmd
from cli.commands.install import install_cmd
from cli.commands.logs import logs_cmd
from cli.commands.restart import restart_cmd

def main():
    parser = argparse.ArgumentParser(description="rbot CLI - Asistente de Escritorio de IA")
    subparsers = parser.add_subparsers(dest="command", help="Comandos de rbot")

    subparsers.add_parser("run", help="Iniciar asistente en primer plano (desarrollo/depuración)")
    subparsers.add_parser("start", help="Iniciar servicio en segundo plano (daemon)")
    subparsers.add_parser("stop", help="Detener servicio en segundo plano")
    subparsers.add_parser("status", help="Comprobar el estado del servicio rbot")
    subparsers.add_parser("logs", help="Mostrar últimas líneas del log")
    subparsers.add_parser("restart", help="Reiniciar el servicio rbot")
    subparsers.add_parser("install", help="Registrar la app en systemd o inicio automático")

    args = parser.parse_args()

    if args.command == "run":
        run_cmd()
    elif args.command == "start":
        start_cmd()
    elif args.command == "stop":
        stop_cmd()
    elif args.command == "status":
        status_cmd()
    elif args.command == "logs":
        logs_cmd()
    elif args.command == "restart":
        restart_cmd()
    elif args.command == "install":
        install_cmd()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
