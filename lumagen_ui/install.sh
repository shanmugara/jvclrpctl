#!/bin/bash

# Installation script for Lumagen Web UI

set -e

echo "=========================================="
echo "Lumagen Web UI Installation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
echo "Installing for user: $ACTUAL_USER"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $SCRIPT_DIR"

# Install system dependencies
echo ""
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv

# Add user to dialout group for serial port access
echo ""
echo "Adding $ACTUAL_USER to dialout group..."
usermod -a -G dialout "$ACTUAL_USER"
echo "Note: User needs to log out and back in for group changes to take effect"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if [ -d "$SCRIPT_DIR/../venv" ]; then
    echo "Using existing virtual environment..."
    VENV_PATH="$SCRIPT_DIR/../venv"
else
    echo "Creating new virtual environment..."
    sudo -u "$ACTUAL_USER" python3 -m venv "$SCRIPT_DIR/venv"
    VENV_PATH="$SCRIPT_DIR/venv"
fi

sudo -u "$ACTUAL_USER" "$VENV_PATH/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Install systemd service
echo ""
echo "Installing systemd service..."

# Update service file paths for current installation
SERVICE_FILE="/etc/systemd/system/lumagen-ui.service"
cp "$SCRIPT_DIR/lumagen-ui.service" "$SERVICE_FILE"

# Replace placeholder paths with actual paths
HOME_DIR=$(eval echo "~$ACTUAL_USER")
sed -i "s|/home/pi|$HOME_DIR|g" "$SERVICE_FILE"
sed -i "s|User=pi|User=$ACTUAL_USER|g" "$SERVICE_FILE"

# Reload systemd
systemctl daemon-reload

# Enable service
echo ""
echo "Enabling lumagen-ui service..."
systemctl enable lumagen-ui.service

# Check serial ports
echo ""
echo "Available serial ports:"
ls -l /dev/ttyUSB* 2>/dev/null || echo "No USB serial devices found"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit $SCRIPT_DIR/app.py to set correct LUMAGEN_PORT"
echo "2. User $ACTUAL_USER needs to log out and back in for serial port access"
echo "3. Start the service: sudo systemctl start lumagen-ui.service"
echo "4. Check status: sudo systemctl status lumagen-ui.service"
echo "5. View logs: sudo journalctl -u lumagen-ui.service -f"
echo ""
echo "Web UI will be available at:"
echo "  http://localhost:5001"
echo "  http://$(hostname -I | awk '{print $1}'):5001"
echo ""
