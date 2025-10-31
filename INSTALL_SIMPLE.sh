#!/bin/bash
set -e

echo "=============================================="
echo "Tor Proxy Pool - Simple Installation"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Install Python and pip
echo "Step 1: Installing Python and pip..."
case $OS in
    ubuntu|debian)
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
        ;;
    centos|rhel|fedora)
        sudo yum install -y python3 python3-pip
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
        exit 1
        ;;
esac

# Install FastAPI and uvicorn for test server
echo ""
echo "Step 2: Installing FastAPI and uvicorn..."
pip3 install fastapi uvicorn --user

# Test installation
echo ""
echo "Step 3: Testing installation..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Warning: FastAPI/uvicorn not found in path${NC}"
    echo "Trying alternative installation..."
    sudo pip3 install fastapi uvicorn
fi

# Create systemd service for test server
echo ""
echo "Step 4: Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/tor-proxy-test.service"
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Tor Proxy Pool Test Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/test_server.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Service file created: $SERVICE_FILE${NC}"

# Reload systemd and start service
echo ""
echo "Step 5: Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable tor-proxy-test
sudo systemctl start tor-proxy-test

# Check status
echo ""
echo "Step 6: Checking service status..."
sleep 2
if sudo systemctl is-active --quiet tor-proxy-test; then
    echo -e "${GREEN}✓ Service is running!${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs..."
    sudo journalctl -u tor-proxy-test -n 20 --no-pager
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=============================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "Admin panel is available at:"
echo -e "  ${GREEN}http://localhost:8000${NC}"
echo -e "  ${GREEN}http://$SERVER_IP:8000${NC}"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "Service commands:"
echo "  Status:  sudo systemctl status tor-proxy-test"
echo "  Stop:    sudo systemctl stop tor-proxy-test"
echo "  Start:   sudo systemctl start tor-proxy-test"
echo "  Restart: sudo systemctl restart tor-proxy-test"
echo "  Logs:    sudo journalctl -u tor-proxy-test -f"
echo ""
echo "NOTE: This is a TEST server for verifying the admin panel."
echo "      It does NOT provide actual Tor proxy functionality."
echo "      See QUICKSTART.md for full installation."
echo ""
