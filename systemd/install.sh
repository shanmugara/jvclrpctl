#!/bin/bash
# Installation script for JVC-LRP Runner systemd service on Raspberry Pi

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script's directory (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}=== JVC-LRP Runner Systemd Service Installation ===${NC}\n"

# Check if running on Raspberry Pi or Linux
if [[ ! -f /etc/os-release ]]; then
    echo -e "${RED}Error: This script requires a Linux system${NC}"
    exit 1
fi

# Get current user
CURRENT_USER=$(whoami)
echo -e "Installing for user: ${GREEN}${CURRENT_USER}${NC}"
echo -e "Project directory: ${GREEN}${PROJECT_DIR}${NC}\n"

# Check if venv exists
if [[ ! -d "${PROJECT_DIR}/venv" ]]; then
    echo -e "${RED}Error: Virtual environment not found at ${PROJECT_DIR}/venv${NC}"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Check if runner.py exists
if [[ ! -f "${PROJECT_DIR}/runner/runner.py" ]]; then
    echo -e "${RED}Error: runner/runner.py not found${NC}"
    exit 1
fi

# Create a temporary service file with correct paths
SERVICE_FILE="/tmp/jvc-lrp-runner.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=JVC-LRP Runner - HDR Mode Detection and Picture Mode Control
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
# Uncomment to enable debug mode
#Environment="DEBUG=true"
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/runner/runner.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} Generated service file with your paths\n"

# Copy service file
echo "Installing service file (requires sudo)..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/jvc-lrp-runner.service
sudo chmod 644 /etc/systemd/system/jvc-lrp-runner.service
echo -e "${GREEN}✓${NC} Service file installed\n"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd reloaded\n"

# Add user to dialout group for serial port access
echo "Adding user to dialout group for serial port access..."
if groups "$CURRENT_USER" | grep -q dialout; then
    echo -e "${GREEN}✓${NC} User already in dialout group"
else
    sudo usermod -a -G dialout "$CURRENT_USER"
    echo -e "${YELLOW}⚠${NC}  User added to dialout group. You may need to log out and back in."
fi
echo ""

# Ask if user wants to enable the service
read -p "Enable service to start on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable jvc-lrp-runner.service
    echo -e "${GREEN}✓${NC} Service enabled for auto-start on boot\n"
fi

# Ask if user wants to start the service now
read -p "Start service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start jvc-lrp-runner.service
    echo -e "${GREEN}✓${NC} Service started\n"
    sleep 2
    sudo systemctl status jvc-lrp-runner.service --no-pager -l
fi

# Clean up
rm "$SERVICE_FILE"

echo ""
echo -e "${GREEN}=== Installation Complete ===${NC}\n"
echo "Useful commands:"
echo "  View status:        sudo systemctl status jvc-lrp-runner.service"
echo "  View logs:          sudo journalctl -u jvc-lrp-runner.service -f"
echo "  Stop service:       sudo systemctl stop jvc-lrp-runner.service"
echo "  Start service:      sudo systemctl start jvc-lrp-runner.service"
echo "  Restart service:    sudo systemctl restart jvc-lrp-runner.service"
echo "  Disable auto-start: sudo systemctl disable jvc-lrp-runner.service"
echo ""
echo "For more information, see: docs/SYSTEMD_SERVICE.md"
echo ""
