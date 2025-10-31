#!/bin/bash
# Simple one-command start script for Connexa Proxy Admin Panel
# Usage: ./START.sh

set -e

echo "=============================================="
echo "Connexa Proxy - Quick Start"
echo "=============================================="
echo ""

# Install dependencies if needed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing dependencies (fastapi, uvicorn)..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user fastapi uvicorn
    else
        echo "Installing pip3..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        else
            echo "Error: Please install python3-pip manually"
            exit 1
        fi
        pip3 install --user fastapi uvicorn
    fi
    echo ""
fi

# Get server IP
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo "Starting admin panel..."
echo ""
echo "=============================================="
echo "Admin panel will be available at:"
echo "  → http://localhost:8000"
echo "  → http://$SERVER_IP:8000"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo "=============================================="
echo ""

# Run the test server
python3 test_server.py
