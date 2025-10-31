# Installation Guide

This guide covers the installation process for Tor Proxy Pool on various Linux distributions.

## Prerequisites

Before installing, ensure your system meets the following requirements:

- **Operating System**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or compatible
- **RAM**: Minimum 4GB, 8GB recommended for 100 nodes
- **CPU**: 2+ cores recommended
- **Disk**: 10GB+ free space
- **Root Access**: Required for installation

## Automatic Installation

The easiest way to install is using the automated installer:

```bash
sudo ./install.sh
```

This will:
1. Detect your operating system
2. Install all dependencies
3. Set up PostgreSQL and Redis
4. Install and configure the backend
5. Set up systemd services
6. Configure Nginx reverse proxy
7. Apply firewall rules

## Manual Installation

### 1. Install Dependencies

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
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
```

#### CentOS/RHEL

```bash
sudo yum install -y \
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
```

### 2. Setup PostgreSQL

```bash
# Initialize database (CentOS/RHEL only)
sudo postgresql-setup --initdb

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE torproxy;
CREATE USER torproxy WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE torproxy TO torproxy;
EOF
```

### 3. Setup Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. Install Backend

```bash
# Create directories
sudo mkdir -p /opt/tor-proxy-pool
sudo mkdir -p /var/lib/tor-pool
sudo mkdir -p /var/log/tor-proxy-pool

# Copy files
sudo cp -r backend /opt/tor-proxy-pool/

# Create virtual environment
cd /opt/tor-proxy-pool/backend
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Create .env file
cat > /opt/tor-proxy-pool/.env <<EOF
API_SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=your_secure_password
TOR_POOL_SIZE=50
EOF
```

### 6. Setup Systemd Service

```bash
# Create service file
sudo cat > /etc/systemd/system/tor-proxy-pool.service <<'EOF'
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

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tor-proxy-pool
sudo systemctl start tor-proxy-pool
```

### 7. Configure Nginx

```bash
# Create Nginx configuration
sudo cat > /etc/nginx/sites-available/tor-proxy-pool <<'EOF'
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

# Enable site
sudo ln -s /etc/nginx/sites-available/tor-proxy-pool /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Docker Installation

For Docker-based deployment:

```bash
# Build and start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

## Post-Installation

1. **Access the Admin Panel**: Navigate to `http://your-server-ip/`
2. **Login**: Use default credentials (admin/admin)
3. **Change Password**: You will be forced to change the password
4. **Configure Settings**: Update configuration as needed
5. **Enable TLS**: Set up Let's Encrypt if using a domain
6. **Configure Firewall**: Set up IP whitelists

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status tor-proxy-pool

# View logs
sudo journalctl -u tor-proxy-pool -n 100

# Check dependencies
sudo systemctl status postgresql
sudo systemctl status redis
```

### Database Connection Failed

```bash
# Test database connection
psql -U torproxy -h localhost -d torproxy

# Check PostgreSQL logs
sudo journalctl -u postgresql -n 50
```

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process or change port in .env
```

## Verification

After installation, verify everything is working:

```bash
# Check service status
sudo systemctl status tor-proxy-pool

# Test API
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics

# Check Tor nodes
sudo systemctl status tor@*
```

## Next Steps

- [Configure TLS](security.md#tls-configuration)
- [Set up Alerts](configuration.md#alerts)
- [Configure Firewall](security.md#firewall-configuration)
- [Enable 2FA](security.md#two-factor-authentication)
