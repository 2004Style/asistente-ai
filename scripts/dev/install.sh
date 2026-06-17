#!/usr/bin/env bash
# Strict mode
set -euo pipefail

echo "========================================="
echo "   rbot AI Assistant Bash Setup Wrapper  "
echo "========================================="

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed on this system." >&2
    exit 1
fi

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing/updating dependencies in virtual environment..."
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -e .

python3 scripts/dev/install.py

echo "Setup wrapper finished."
