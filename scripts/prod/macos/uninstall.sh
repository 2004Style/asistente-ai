#!/usr/bin/env bash
echo "Stopping launchd service..."
~/.local/bin/rbot stop || true

echo "Unregistering macOS Launch Agent..."
~/.local/bin/rbot uninstall || true

echo "Removing files..."
rm -f ~/.local/bin/rbot

echo "========================================="
echo "  rbot has been successfully uninstalled."
echo "========================================="
