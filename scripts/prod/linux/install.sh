#!/usr/bin/env bash
set -e
echo "Installing rbot for Linux user..."
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications

cp rbot ~/.local/bin/rbot
chmod +x ~/.local/bin/rbot
cp rbot.desktop ~/.local/share/applications/rbot.desktop

echo "Registering systemd user service..."
~/.local/bin/rbot install

echo "Starting systemd service..."
~/.local/bin/rbot start

echo "========================================="
echo "  rbot has been successfully installed!"
echo "  Location: ~/.local/bin/rbot"
echo "  Note: Ensure ~/.local/bin is in your PATH."
echo "  You can launch the UI by running 'rbot start'."
echo "========================================="
