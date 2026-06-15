#!/bin/bash
# Install lumagen-ui as a production systemd service (Gunicorn).
# Usage: sudo ./install.sh

set -e

# ── Colours ───────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }
step()  { echo -e "\n${BOLD}── $* ──${NC}"; }

# ── Must run as root ──────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    error "Run with sudo: sudo $0"
    exit 1
fi

ACTUAL_USER="${SUDO_USER:-$USER}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
SERVICE_NAME="lumagen-ui"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Lumagen + JVC Web UI — Install         ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
info "Install user : $ACTUAL_USER"
info "Install dir  : $SCRIPT_DIR"
echo ""

# ── Configuration prompts ─────────────────────────────────────────────────
step "Configuration"

read -rp "  Lumagen serial port  [/dev/ttyUSB0]: " LUMAGEN_PORT
LUMAGEN_PORT="${LUMAGEN_PORT:-/dev/ttyUSB0}"

read -rp "  JVC projector IP     [192.168.100.240]: " JVC_HOST
JVC_HOST="${JVC_HOST:-192.168.100.240}"

read -rp "  Web UI port          [5001]: " UI_PORT
UI_PORT="${UI_PORT:-5001}"

echo ""
info "Lumagen port : $LUMAGEN_PORT"
info "JVC host     : ${JVC_HOST:-not configured}"
info "UI port      : $UI_PORT"
echo ""
read -rp "Proceed? [Y/n]: " CONFIRM
[[ "${CONFIRM:-Y}" =~ ^[Yy]$ ]] || { warn "Aborted."; exit 0; }

# ── System packages ───────────────────────────────────────────────────────
step "System packages"
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv
info "python3-pip and python3-venv installed"

# ── Log directory ─────────────────────────────────────────────────────────
step "Log directory"
mkdir -p /var/log/jvclrpctl
chown "$ACTUAL_USER" /var/log/jvclrpctl
info "Log directory: /var/log/jvclrpctl (owner: $ACTUAL_USER)"

# ── Serial port access ────────────────────────────────────────────────────
step "Serial port permissions"
usermod -a -G dialout "$ACTUAL_USER"
info "Added $ACTUAL_USER to dialout group (re-login required to take effect)"

# ── Python virtual environment ────────────────────────────────────────────
step "Python virtual environment"
if [ ! -d "$VENV" ]; then
    info "Creating venv at $VENV"
    sudo -u "$ACTUAL_USER" python3 -m venv "$VENV"
else
    info "Using existing venv at $VENV"
fi

info "Installing Python dependencies (including gunicorn)..."
sudo -u "$ACTUAL_USER" "$VENV/bin/pip" install --quiet --upgrade pip
sudo -u "$ACTUAL_USER" "$VENV/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
info "Dependencies installed"

# ── Generate systemd service ──────────────────────────────────────────────
step "Systemd service"

# Build optional JVC_HOST line
if [ -n "$JVC_HOST" ]; then
    JVC_ENV_LINE="Environment=\"JVC_HOST=$JVC_HOST\""
else
    JVC_ENV_LINE="# JVC_HOST not configured — set to enable JVC controls"
fi

cat > "$SERVICE_DEST" <<EOF
[Unit]
Description=Lumagen + JVC Web Control UI
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
Environment="LUMAGEN_PORT=$LUMAGEN_PORT"
$JVC_ENV_LINE
ExecStart=$VENV/bin/gunicorn \\
    --workers 1 \\
    --worker-class gthread \\
    --threads 4 \\
    --bind 0.0.0.0:$UI_PORT \\
    --timeout 30 \\
    --access-logfile /dev/stderr \\
    app:app
Restart=always
RestartSec=10
StandardOutput=tty
StandardError=journal
TTYPath=/dev/tty1
TTYReset=no
TTYVHangup=no

[Install]
WantedBy=multi-user.target
EOF

info "Service file written to $SERVICE_DEST"

# ── Enable and start ──────────────────────────────────────────────────────
step "Enabling and starting service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    echo ""
    echo -e "${GREEN}${BOLD}✓ Service is running!${NC}"
    echo ""
    echo -e "  Web UI:  ${BOLD}http://${IP}:${UI_PORT}${NC}"
    echo -e "  Logs:    journalctl -u $SERVICE_NAME -f"
    echo -e "  Status:  systemctl status $SERVICE_NAME"
else
    error "Service failed to start. Check logs:"
    echo "  journalctl -u $SERVICE_NAME -n 30"
    exit 1
fi

echo ""
echo -e "${YELLOW}Note:${NC} $ACTUAL_USER must log out and back in for serial port access"
echo -e "      if this is a fresh installation."
echo ""
