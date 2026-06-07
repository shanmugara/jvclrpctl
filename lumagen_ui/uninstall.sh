#!/bin/bash

# Uninstallation script for Lumagen Web UI

set -e

echo "=========================================="
echo "Lumagen Web UI Uninstallation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Stop the service if running
echo "Stopping lumagen-ui service..."
systemctl stop lumagen-ui.service 2>/dev/null || echo "Service not running"

# Disable the service
echo "Disabling lumagen-ui service..."
systemctl disable lumagen-ui.service 2>/dev/null || echo "Service not enabled"

# Remove service file
echo "Removing service file..."
rm -f /etc/systemd/system/lumagen-ui.service

# Reload systemd
systemctl daemon-reload

echo ""
echo "=========================================="
echo "Uninstallation Complete!"
echo "=========================================="
echo ""
echo "The lumagen_ui directory and files have NOT been deleted."
echo "To remove them manually, run:"
echo "  rm -rf $(dirname "${BASH_SOURCE[0]}")"
echo ""
