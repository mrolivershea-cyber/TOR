#!/bin/bash

#==============================================================================
# Tor Proxy Pool - Automatic Installation Script
# Version: 1.0.0
# Description: Fully automated installation of Tor proxy pool with 50-100 instances
# Usage: sudo ./install.sh [OPTIONS]
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
POOL_SIZE=50
SKIP_DOCKER=false
DEV_MODE=false
USE_SYSTEMD=true
PROJECT_NAME="tor-proxy-pool"
INSTALL_DIR="/opt/tor-proxy-pool"
DATA_DIR="/var/lib/tor-pool"
LOG_DIR="/var/log/tor-proxy-pool"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pool-size)
            POOL_SIZE="$2"
            shift 2
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            POOL_SIZE=10
            shift
            ;;
        --docker)
            USE_SYSTEMD=false
            shift
            ;;
        --help)
            echo "Usage: sudo ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --pool-size N       Number of Tor instances (default: 50)"
            echo "  --skip-docker       Skip Docker installation"
            echo "  --docker            Use Docker instead of systemd"
            echo "  --dev               Development mode (10 instances)"
            echo "  --help              Show this help"
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

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS"
        exit 1
    fi
    print_success "Detected OS: $OS $VER"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
    print_success "Running as root"
}

install_dependencies() {
    print_header "Installing Dependencies"
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                tor \
                python3 \
                python3-pip \
                python3-venv \
                postgresql \
                postgresql-contrib \
                redis-server \
                nginx \
                certbot \
                python3-certbot-nginx \
                git \
                curl \
                wget \
                nftables
            ;;
        centos|rhel|fedora)
            yum install -y \
                tor \
                python3 \
                python3-pip \
                postgresql \
                postgresql-server \
                redis \
                nginx \
                certbot \
                python3-certbot-nginx \
                git \
                curl \
                wget \
                nftables
            ;;
        *)
            print_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    print_success "Dependencies installed"
}

setup_directories() {
    print_header "Setting Up Directories"
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    
    chmod 755 "$INSTALL_DIR"
    chmod 700 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    
    print_success "Directories created"
}

setup_database() {
    print_header "Setting Up PostgreSQL"
    
    # Start PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE torproxy;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER torproxy WITH PASSWORD 'changeme';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE torproxy TO torproxy;" 2>/dev/null || true
    
    print_success "PostgreSQL configured"
    print_warning "Remember to change the database password in .env"
}

setup_redis() {
    print_header "Setting Up Redis"
    
    # Start Redis
    systemctl start redis
    systemctl enable redis
    
    print_success "Redis configured"
}

install_backend() {
    print_header "Installing Backend"
    
    # Copy files
    cp -r backend "$INSTALL_DIR/"
    
    # Create virtual environment
    cd "$INSTALL_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Generate secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env file
    cat > "$INSTALL_DIR/.env" <<EOF
APP_NAME=Tor Proxy Pool
DEBUG=false
API_SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=changeme
TOR_POOL_SIZE=$POOL_SIZE
EOF
    
    print_success "Backend installed"
}

setup_systemd() {
    print_header "Setting Up Systemd Services"
    
    # Backend service
    cat > /etc/systemd/system/tor-proxy-pool.service <<'EOF'
[Unit]
Description=Tor Proxy Pool Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tor-proxy-pool/backend
Environment="PATH=/opt/tor-proxy-pool/backend/venv/bin"
ExecStart=/opt/tor-proxy-pool/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    systemctl enable tor-proxy-pool
    
    print_success "Systemd services configured"
}

setup_nginx() {
    print_header "Setting Up Nginx"
    
    cat > /etc/nginx/sites-available/tor-proxy-pool <<'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/tor-proxy-pool /etc/nginx/sites-enabled/ 2>/dev/null || true
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload nginx
    nginx -t
    systemctl restart nginx
    systemctl enable nginx
    
    print_success "Nginx configured"
}

setup_firewall() {
    print_header "Setting Up Firewall"
    
    # This will be handled by the application
    print_success "Firewall will be configured by the application"
}

start_services() {
    print_header "Starting Services"
    
    systemctl start tor-proxy-pool
    
    print_success "Services started"
}

print_summary() {
    clear
    
    cat <<EOF

╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║               ✓  INSTALLATION COMPLETED SUCCESSFULLY  ✓         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

📊 Installation Summary:
   • Tor Pool Size: $POOL_SIZE instances
   • SOCKS Ports: 30000-$((30000 + POOL_SIZE - 1))
   • Control Ports: 40000-$((40000 + POOL_SIZE - 1))
   • Install Directory: $INSTALL_DIR
   • Data Directory: $DATA_DIR
   • Log Directory: $LOG_DIR

🌐 Access Information:
   • Admin Panel: http://$(hostname -I | awk '{print $1}')
   • API Docs: http://$(hostname -I | awk '{print $1}')/api/docs
   • Metrics: http://$(hostname -I | awk '{print $1}')/metrics

🔐 Default Credentials:
   • Username: admin
   • Password: admin
   ⚠️  YOU MUST CHANGE THE PASSWORD ON FIRST LOGIN!

📝 Next Steps:
   1. Access the admin panel
   2. Change the default admin password
   3. Configure firewall whitelists (optional)
   4. Set up TLS with Let's Encrypt (recommended)
   5. Configure alerts (email/Telegram)

📚 Useful Commands:
   • Check status: systemctl status tor-proxy-pool
   • View logs: journalctl -u tor-proxy-pool -f
   • Restart service: systemctl restart tor-proxy-pool
   • Uninstall: sudo ./uninstall.sh

📖 Documentation: See docs/ directory

EOF
}

main() {
    clear
    
    cat <<"EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║            🔐  TOR PROXY POOL - AUTOMATED INSTALLER  🔐         ║
║                                                                  ║
║     Professional SOCKS5 proxy pool with 50-100 instances        ║
║     Complete with Admin Panel, API, and Monitoring              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
    
    echo ""
    echo "Installation will begin with ${POOL_SIZE} Tor instances"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."
    
    check_root
    detect_os
    install_dependencies
    setup_directories
    setup_database
    setup_redis
    install_backend
    
    if [ "$USE_SYSTEMD" = true ]; then
        setup_systemd
    fi
    
    setup_nginx
    setup_firewall
    
    if [ "$USE_SYSTEMD" = true ]; then
        start_services
    fi
    
    print_summary
}

main "$@"