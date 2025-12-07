#!/bin/bash
# install_service.sh
# Install the fireplace systemd service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/fireplace.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: fireplace.service not found in $SCRIPT_DIR"
    exit 1
fi

echo "Installing fireplace service..."

# Copy service file
sudo cp "$SERVICE_FILE" /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable fireplace

echo ""
echo "Service installed successfully!"
echo ""
echo "Commands:"
echo "  sudo systemctl start fireplace    # Start now"
echo "  sudo systemctl stop fireplace     # Stop"
echo "  sudo systemctl restart fireplace  # Restart"
echo "  sudo systemctl status fireplace   # Check status"
echo "  sudo journalctl -u fireplace -f   # View logs"
echo ""
echo "The service will start automatically on next boot."
