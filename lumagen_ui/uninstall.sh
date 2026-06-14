#!/bin/bash
# Remove the lumagen-ui systemd service.
# Usage: sudo ./uninstall.sh

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[✗]${NC} Run with sudo: sudo $0"
    exit 1
fi

SERVICE_NAME="lumagen-ui"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Lumagen + JVC Web UI — Uninstall       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
warn "This will stop and remove the $SERVICE_NAME systemd service."
warn "Application files and the venv will NOT be deleted."
echo ""
read -rp "Proceed? [y/N]: " CONFIRM
[[ "${CONFIRM:-N}" =~ ^[Yy]$ ]] || { warn "Aborted."; exit 0; }

echo ""
info "Stopping service..."
systemctl stop "$SERVICE_NAME" 2>/dev/null || warn "Service was not running"

info "Disabling service..."
systemctl disable "$SERVICE_NAME" 2>/dev/null || warn "Service was not enabled"

info "Removing service file..."
rm -f "$SERVICE_FILE"

systemctl daemon-reload

echo ""
echo -e "${GREEN}${BOLD}✓ Service removed.${NC}"
echo ""
echo "Application files remain at: $(dirname "${BASH_SOURCE[0]}")"
echo "To reinstall:  sudo $(dirname "${BASH_SOURCE[0]}")/install.sh"
echo ""
