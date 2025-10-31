# 🔐 Tor Proxy Pool - Professional Management System

A comprehensive, enterprise-grade Tor SOCKS5 proxy pool management system with web-based admin panel, API, monitoring, and advanced security features.

## ✨ Features

### Core Functionality
- **Dynamic Tor Pool**: 50-100 Tor instances with automatic scaling
- **SOCKS5 Proxies**: Full SOCKS5 support on dedicated ports
- **Circuit Rotation**: Automatic and manual NEWNYM support
- **Country Selection**: Exit node country filtering with StrictNodes
- **Health Monitoring**: Real-time health checks and auto-restart

### Security Features
- **Multi-Backend Firewall**: Auto-detection and support for nftables, iptables, UFW, firewalld
- **IP Whitelisting**: Separate whitelists for admin panel and SOCKS proxies
- **2FA Authentication**: TOTP-based two-factor authentication
- **Forced Password Change**: First-time admin password change requirement
- **Rate Limiting**: Brute-force protection with account lockout
- **TLS/SSL**: Let's Encrypt integration with HSTS
- **Security Headers**: Full CSP, X-Frame-Options, HSTS headers
- **Control Port Protection**: Tor control ports blocked from external access

### Admin Panel
- **Modern Web UI**: React-based responsive interface
- **Real-time Monitoring**: Live node status and metrics
- **Configuration Management**: Update settings without server restart
- **Export System**: Signed tokens with TTL and optional IP binding
- **Audit Logging**: Complete activity logs with severity levels

### Monitoring & Alerts
- **Prometheus Metrics**: `/metrics` endpoint with comprehensive metrics
- **JSON Logging**: Structured logging with rotation
- **Email Alerts**: SMTP-based notifications
- **Telegram Alerts**: Webhook integration
- **Alert Conditions**:
  - Node failure threshold exceeded
  - Firewall rule application failures
  - TLS certificate expiration
  - Brute-force attack detection

### Export & API
- **Export Formats**: TXT, CSV, JSON
- **Token-Based Access**: Secure signed tokens with expiration
- **IP Binding**: Optional IP-based access control
- **RESTful API**: Complete FastAPI-based REST API
- **OpenAPI Docs**: Automatic API documentation

## 📋 Requirements

- **OS**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or compatible
- **RAM**: Minimum 4GB (8GB recommended for 100 nodes)
- **CPU**: 2+ cores recommended
- **Disk**: 10GB+ free space
- **Python**: 3.8 or higher
- **Database**: PostgreSQL 12+
- **Cache**: Redis 5+

## 🚀 Quick Installation

### One-Command Install

```bash
sudo ./install.sh
```

### Custom Installation

```bash
# Install with specific pool size
sudo ./install.sh --pool-size 100

# Development mode (10 instances)
sudo ./install.sh --dev

# Using Docker
sudo ./install.sh --docker
```

## 📚 Installation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--pool-size N` | Number of Tor instances | 50 |
| `--dev` | Development mode | false |
| `--docker` | Use Docker instead of systemd | false |
| `--skip-docker` | Skip Docker installation | false |
| `--help` | Show help message | - |

## ⚙️ Configuration

Configuration is managed through environment variables in `.env`:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

### Key Configuration Options

```ini
# Firewall Backend
FIREWALL_BACKEND=auto  # auto | nftables | iptables | ufw | firewalld

# TLS Configuration
TLS_ENABLE=true
DOMAIN=proxy.example.com

# 2FA
ENABLE_2FA=true

# Export Tokens
EXPORT_TOKEN_TTL_MIN=60
EXPORT_TOKEN_IP_BIND=false

# Whitelists (comma-separated)
PANEL_WHITELIST=192.168.1.0/24,10.0.0.5
SOCKS_WHITELIST=

# Tor Configuration
TOR_POOL_SIZE=50
TOR_COUNTRIES=US,DE  # Leave empty for any country
TOR_STRICT_NODES=true

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@example.com
ALERT_TELEGRAM_ENABLED=false
```

## 🔒 Security Best Practices

1. **Change Default Password**: Always change admin password on first login
2. **Enable 2FA**: Enable two-factor authentication for all admin users
3. **Configure Whitelists**: Restrict access to known IP addresses
4. **Enable TLS**: Use Let's Encrypt for production deployments
5. **Regular Updates**: Keep system and dependencies updated
6. **Monitor Alerts**: Configure email/Telegram alerts
7. **Review Logs**: Regularly check audit logs for suspicious activity

## 🌐 Port Usage

| Service | Port Range | Description |
|---------|------------|-------------|
| Admin Panel | 8000 | Web UI and API |
| SOCKS Proxies | 30000-30099 | Tor SOCKS5 proxies |
| Control Ports | 40000-40099 | Tor control (localhost only) |
| Metrics | 9090 | Prometheus metrics |
| PostgreSQL | 5432 | Database (localhost only) |
| Redis | 6379 | Cache (localhost only) |

## 🔧 Management Commands

### Service Management

```bash
# Check status
systemctl status tor-proxy-pool

# Start service
systemctl start tor-proxy-pool

# Stop service
systemctl stop tor-proxy-pool

# Restart service
systemctl restart tor-proxy-pool

# View logs
journalctl -u tor-proxy-pool -f
```

### Application Logs

```bash
# View application logs
tail -f /var/log/tor-proxy-pool/app.log

# View with jq (for JSON logs)
tail -f /var/log/tor-proxy-pool/app.log | jq
```

## 📊 API Usage

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=newpassword"

# Returns: {"access_token": "...", "token_type": "bearer"}
```

### List Nodes

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/
```

### Rotate All Circuits

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/rotate
```

### Scale Pool

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/scale?new_size=75
```

### Create Export Token

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/export/tokens \
  -d "description=My Software"
```

### Download Proxy List

```bash
# TXT format
curl http://localhost:8000/api/v1/export/download/txt?token=<export_token>

# CSV format
curl http://localhost:8000/api/v1/export/download/csv?token=<export_token>

# JSON format
curl http://localhost:8000/api/v1/export/download/json?token=<export_token>
```

## 📈 Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

- `tor_nodes_total` - Total number of configured nodes
- `tor_nodes_up` - Number of healthy nodes
- `tor_node_latency_ms` - Node latency in milliseconds
- `tor_newnym_total` - Total NEWNYM signals sent
- `tor_restarts_total` - Total node restarts
- `api_requests_total` - API request count
- `auth_attempts_total` - Authentication attempts

### Grafana Dashboard

Import the provided Grafana dashboard from `monitoring/grafana/dashboard.json`

## 🔄 Backup & Restore

### Backup

```bash
# Backup database
pg_dump -U torproxy torproxy > backup.sql

# Backup configuration
cp .env .env.backup

# Backup data directory
tar -czf tor-pool-data.tar.gz /var/lib/tor-pool
```

### Restore

```bash
# Restore database
psql -U torproxy torproxy < backup.sql

# Restore configuration
cp .env.backup .env

# Restore data directory
tar -xzf tor-pool-data.tar.gz -C /
```

## 🚨 Emergency Procedures

### All Nodes Down

1. Check system resources: `htop`, `df -h`
2. Check Tor process: `ps aux | grep tor`
3. Check logs: `journalctl -u tor-proxy-pool -n 100`
4. Restart service: `systemctl restart tor-proxy-pool`

### Firewall Lockout

If you lock yourself out:

1. Access server via console/KVM
2. Temporarily disable firewall: `systemctl stop nftables` (or appropriate backend)
3. Fix whitelist configuration
4. Reapply firewall: `systemctl start nftables`

### Database Connection Issues

```bash
# Check PostgreSQL status
systemctl status postgresql

# Test connection
psql -U torproxy -d torproxy -h localhost

# Reset password if needed
sudo -u postgres psql -c "ALTER USER torproxy PASSWORD 'newpassword';"
```

## 🗑️ Uninstallation

### Complete Removal

```bash
sudo ./uninstall.sh
```

### Keep Data and Logs

```bash
sudo ./uninstall.sh --keep-data --keep-logs
```

## 🧪 Testing

Run the test suite:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

## 📖 Documentation

Detailed documentation available in the `docs/` directory:

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Documentation](docs/api.md)
- [Security Guide](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Support

For issues, questions, or contributions:

- GitHub Issues: [Create an issue](https://github.com/mrolivershea-cyber/TOR/issues)
- Documentation: See `docs/` directory

## 📝 License

This project is provided as-is for security and privacy purposes.

## ⚠️ Disclaimer

This software is provided for legitimate privacy and security purposes. Users are responsible for compliance with all applicable laws and regulations. The use of Tor should respect the Tor Project's guidelines and terms of service.
