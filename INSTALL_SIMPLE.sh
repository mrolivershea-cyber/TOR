#!/bin/bash
set -e

echo "=============================================="
echo "Connexa Proxy - Simple Installation"
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
    OS_VERSION_ID=$VERSION_ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS $OS_VERSION_ID${NC}"
echo ""

# Install Python and pip
echo "Step 1: Installing Python and pip..."
case $OS in
    ubuntu|debian|linuxmint|pop)
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-pip python3-venv curl wget
        ;;
    centos|rhel)
        if [ "${OS_VERSION_ID%%.*}" -ge 8 ]; then
            sudo dnf install -y python3 python3-pip curl wget
        else
            sudo yum install -y python3 python3-pip curl wget
        fi
        ;;
    fedora)
        sudo dnf install -y python3 python3-pip curl wget
        ;;
    arch|manjaro)
        sudo pacman -Sy --noconfirm python python-pip curl wget
        ;;
    opensuse*|sles)
        sudo zypper install -y python3 python3-pip curl wget
        ;;
    alpine)
        sudo apk add --no-cache python3 py3-pip curl wget
        ;;
    *)
        echo -e "${YELLOW}Warning: Unsupported OS: $OS${NC}"
        echo "Attempting generic installation..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3 python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3 python3-pip
        else
            echo -e "${RED}Cannot install dependencies automatically${NC}"
            exit 1
        fi
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

SERVICE_FILE="/etc/systemd/system/connexa-proxy.service"
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Connexa Proxy Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/test_server.py
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Service file created: $SERVICE_FILE${NC}"

# Reload systemd and start service
echo ""
echo "Step 5: Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable connexa-proxy
sudo systemctl start connexa-proxy

# Check status
echo ""
echo "Step 6: Checking service status..."
sleep 3
if sudo systemctl is-active --quiet connexa-proxy; then
    echo -e "${GREEN}✓ Service is running!${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs..."
    sudo journalctl -u connexa-proxy -n 20 --no-pager
    echo ""
    echo "Trying to start manually for debugging..."
    python3 test_server.py &
    sleep 2
fi

# Get server IP
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
fi
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="your-server-ip"
fi

# Open firewall port
echo ""
echo "Step 7: Opening firewall port 8000..."
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
    sudo ufw allow 8000/tcp
    echo -e "${GREEN}✓ UFW rule added${NC}"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload
    echo -e "${GREEN}✓ Firewalld rule added${NC}"
elif command -v iptables &> /dev/null; then
    sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
    echo -e "${GREEN}✓ Iptables rule added${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${GREEN}Connexa Proxy Admin Panel is ready!${NC}"
echo ""
echo "Access the admin panel at:"
echo -e "  ${GREEN}→ http://localhost:8000${NC}"
echo -e "  ${GREEN}→ http://$SERVER_IP:8000${NC}"
echo ""
echo "Default credentials:"
echo -e "  ${YELLOW}Username: admin${NC}"
echo -e "  ${YELLOW}Password: admin${NC}"
echo ""
echo "Service management:"
echo "  Status:  sudo systemctl status connexa-proxy"
echo "  Stop:    sudo systemctl stop connexa-proxy"
echo "  Start:   sudo systemctl start connexa-proxy"
echo "  Restart: sudo systemctl restart connexa-proxy"
echo "  Logs:    sudo journalctl -u connexa-proxy -f"
echo ""
