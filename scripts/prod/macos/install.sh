#!/usr/bin/env bash
set -e
echo "Installing rbot for macOS user..."
mkdir -p ~/.local/bin

cp rbot ~/.local/bin/rbot
chmod +x ~/.local/bin/rbot

echo "Registering macOS Launch Agent..."
~/.local/bin/rbot install

echo "Starting launchd service..."
~/.local/bin/rbot start

echo "========================================="
echo "  rbot has been successfully installed!"
echo "  Location: ~/.local/bin/rbot"
echo "  Note: Ensure ~/.local/bin is in your PATH."
echo "========================================="
