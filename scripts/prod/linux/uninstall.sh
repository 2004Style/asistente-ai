#!/usr/bin/env bash
echo "Stopping systemd service..."
~/.local/bin/rbot stop || true

echo "Unregistering systemd user service..."
~/.local/bin/rbot uninstall || true

echo "Removing files..."
rm -f ~/.local/bin/rbot
rm -f ~/.local/share/applications/rbot.desktop

echo "========================================="
echo "  rbot has been successfully uninstalled."
echo "========================================="
