#!/bin/bash

#==============================================================================
# Tor Proxy Pool - Uninstallation Script
# Version: 1.0.0
# Description: Complete removal of Tor proxy pool
# Usage: sudo ./uninstall.sh [OPTIONS]
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
KEEP_DATA=false
KEEP_LOGS=false
INSTALL_DIR="/opt/tor-proxy-pool"
DATA_DIR="/var/lib/tor-pool"
LOG_DIR="/var/log/tor-proxy-pool"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-data)
            KEEP_DATA=true
            shift
            ;;
        --keep-logs)
            KEEP_LOGS=true
            shift
            ;;
        --help)
            echo "Usage: sudo ./uninstall.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --keep-data    Keep data directory"
            echo "  --keep-logs    Keep log files"
            echo "  --help         Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $(printf '%-54s' "$1")║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
    print_success "Running as root"
}

stop_services() {
    print_header "Stopping Services"
    
    systemctl stop tor-proxy-pool 2>/dev/null || true
    systemctl disable tor-proxy-pool 2>/dev/null || true
    
    print_success "Services stopped"
}

remove_systemd() {
    print_header "Removing Systemd Services"
    
    rm -f /etc/systemd/system/tor-proxy-pool.service
    systemctl daemon-reload
    
    print_success "Systemd services removed"
}

remove_nginx() {
    print_header "Removing Nginx Configuration"
    
    rm -f /etc/nginx/sites-available/tor-proxy-pool
    rm -f /etc/nginx/sites-enabled/tor-proxy-pool
    
    nginx -t && systemctl reload nginx || true
    
    print_success "Nginx configuration removed"
}

remove_database() {
    print_header "Removing Database"
    
    read -p "Do you want to remove the PostgreSQL database? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE IF EXISTS torproxy;" 2>/dev/null || true
        sudo -u postgres psql -c "DROP USER IF EXISTS torproxy;" 2>/dev/null || true
        print_success "Database removed"
    else
        print_warning "Database kept"
    fi
}

remove_files() {
    print_header "Removing Files"
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        print_success "Installation directory removed"
    fi
    
    # Remove data directory
    if [ "$KEEP_DATA" = false ]; then
        if [ -d "$DATA_DIR" ]; then
            rm -rf "$DATA_DIR"
            print_success "Data directory removed"
        fi
    else
        print_warning "Data directory kept at $DATA_DIR"
    fi
    
    # Remove log directory
    if [ "$KEEP_LOGS" = false ]; then
        if [ -d "$LOG_DIR" ]; then
            rm -rf "$LOG_DIR"
            print_success "Log directory removed"
        fi
    else
        print_warning "Log directory kept at $LOG_DIR"
    fi
}

clean_firewall() {
    print_header "Cleaning Firewall Rules"
    
    # Remove nftables rules if exists
    if [ -f /etc/nftables/tor-proxy-pool.nft ]; then
        rm -f /etc/nftables/tor-proxy-pool.nft
        nft flush ruleset 2>/dev/null || true
    fi
    
    print_success "Firewall rules cleaned"
}

print_summary() {
    clear
    
    cat <<EOF

╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║            ✓  UNINSTALLATION COMPLETED SUCCESSFULLY  ✓          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

📊 Uninstallation Summary:
   • Services stopped and disabled
   • System files removed
   • Nginx configuration removed

EOF

    if [ "$KEEP_DATA" = true ]; then
        echo "   • Data directory kept: $DATA_DIR"
    else
        echo "   • Data directory removed"
    fi
    
    if [ "$KEEP_LOGS" = true ]; then
        echo "   • Log directory kept: $LOG_DIR"
    else
        echo "   • Log directory removed"
    fi
    
    cat <<EOF

Thank you for using Tor Proxy Pool!

EOF
}

main() {
    clear
    
    cat <<"EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🔐  TOR PROXY POOL - UNINSTALLER  🔐                   ║
║                                                                  ║
║                    ⚠️  WARNING  ⚠️                              ║
║                                                                  ║
║     This will remove Tor Proxy Pool from your system!          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    read -p "Are you sure you want to uninstall? (yes/NO): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
    
    check_root
    stop_services
    remove_systemd
    remove_nginx
    remove_database
    remove_files
    clean_firewall
    print_summary
}

main "$@"
