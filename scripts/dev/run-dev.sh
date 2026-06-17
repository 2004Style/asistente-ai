#!/usr/bin/env bash
# Script to run the AI assistant in development mode with auto-reload.

# Determine project directory (root is parent of scripts directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/../.."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "WARNING: .venv directory not found. Trying global python..."
fi

# Run the dev script
python scripts/dev/dev.py
