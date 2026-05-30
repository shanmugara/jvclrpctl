#!/bin/bash
# Uninstall script for JVC-LRP Runner systemd service

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}=== JVC-LRP Runner Systemd Service Uninstall ===${NC}\n"

# Check if service exists
if [[ ! -f /etc/systemd/system/jvc-lrp-runner.service ]]; then
    echo -e "${YELLOW}Service is not installed.${NC}"
    exit 0
fi

# Confirm uninstall
read -p "Are you sure you want to uninstall the JVC-LRP Runner service? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Stop the service if running
if systemctl is-active --quiet jvc-lrp-runner.service; then
    echo "Stopping service..."
    sudo systemctl stop jvc-lrp-runner.service
    echo -e "${GREEN}✓${NC} Service stopped\n"
fi

# Disable the service
if systemctl is-enabled --quiet jvc-lrp-runner.service 2>/dev/null; then
    echo "Disabling service..."
    sudo systemctl disable jvc-lrp-runner.service
    echo -e "${GREEN}✓${NC} Service disabled\n"
fi

# Remove the service file
echo "Removing service file..."
sudo rm /etc/systemd/system/jvc-lrp-runner.service
echo -e "${GREEN}✓${NC} Service file removed\n"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd reloaded\n"

echo -e "${GREEN}=== Uninstall Complete ===${NC}\n"
echo "The service has been removed."
echo "Your project files remain unchanged."
echo ""
