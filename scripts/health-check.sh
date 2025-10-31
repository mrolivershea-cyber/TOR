#!/bin/bash

#==============================================================================
# Tor Proxy Pool - Health Check Script
# Version: 1.0.0
# Description: Check system health and report issues
# Usage: ./health-check.sh
#==============================================================================

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is not running"
        return 1
    fi
}

check_port() {
    local port=$1
    local name=$2
    if netstat -tuln | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} Port $port ($name) is listening"
        return 0
    else
        echo -e "${RED}✗${NC} Port $port ($name) is not listening"
        return 1
    fi
}

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           Tor Proxy Pool - Health Check Report                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# System resources
echo "System Resources:"
echo "  CPU Load: $(uptime | awk -F'load average:' '{ print $2 }')"
echo "  Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo ""

# Services
echo "Services:"
check_service tor-proxy-pool
check_service postgresql
check_service redis
check_service nginx
echo ""

# Ports
echo "Ports:"
check_port 8000 "Backend API"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 80 "HTTP"
echo ""

# API health
echo "API Health:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API is responding"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo -e "${RED}✗${NC} API is not responding"
fi
echo ""

# Tor nodes
echo "Tor Nodes:"
TOR_COUNT=$(ps aux | grep -c '[t]or.*SocksPort 3')
echo "  Running Tor processes: $TOR_COUNT"
if [ "$TOR_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Tor nodes are running"
else
    echo -e "${RED}✗${NC} No Tor nodes detected"
fi
echo ""

# Database
echo "Database:"
if sudo -u postgres psql -d torproxy -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Database connection successful"
    USERS=$(sudo -u postgres psql -d torproxy -t -c "SELECT COUNT(*) FROM users" 2>/dev/null | xargs)
    NODES=$(sudo -u postgres psql -d torproxy -t -c "SELECT COUNT(*) FROM tor_nodes" 2>/dev/null | xargs)
    echo "  Users: $USERS"
    echo "  Nodes: $NODES"
else
    echo -e "${RED}✗${NC} Database connection failed"
fi
echo ""

# Recent errors
echo "Recent Errors (last 10):"
sudo journalctl -u tor-proxy-pool -p err -n 10 --no-pager | tail -n 5

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                       Health Check Complete                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
