#!/usr/bin/env bash
# Strict mode
set -euo pipefail

# Determine project directory (root is parent of scripts directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "WARNING: .venv directory not found. Trying global python..."
fi

echo "Running package builder script..."
python scripts/package.py

echo "Build process complete."
