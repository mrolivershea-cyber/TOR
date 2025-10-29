#!/bin/bash
# Auto-deployment script - creates all project files
set -e

echo "Creating Tor Proxy Pool complete file structure..."

# Create directories
mkdir -p backend/app backend/tests
mkdir -p frontend/src/components frontend/src/api frontend/public
mkdir -p tor nginx/ssl monitoring scripts docs

echo "✓ Directories created"
echo ""
echo "To complete installation:"
echo "1. Copy all files from the GitHub conversation"
echo "2. Or clone and use manual setup"
echo "3. Run: sudo ./install.sh"
echo ""
echo "Visit: https://github.com/mrolivershea-cyber/TOR"