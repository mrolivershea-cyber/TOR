# Troubleshooting Guide

Common issues and their solutions for Tor Proxy Pool.

## Installation Issues

### "Package not found" during installation

**Problem**: Required packages are not available in repositories.

**Solution**:
```bash
# Update package lists
sudo apt-get update

# For CentOS/RHEL, enable EPEL repository
sudo yum install epel-release
sudo yum update
```

### PostgreSQL fails to start

**Problem**: PostgreSQL not initialized or permission issues.

**Solution**:
```bash
# For CentOS/RHEL - initialize database
sudo postgresql-setup --initdb

# Check PostgreSQL status
sudo systemctl status postgresql

# Check logs
sudo journalctl -u postgresql -n 50

# Fix permissions
sudo chown -R postgres:postgres /var/lib/pgsql
```

### Python dependency conflicts

**Problem**: Conflicting Python package versions.

**Solution**:
```bash
# Create fresh virtual environment
cd /opt/tor-proxy-pool/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Service Issues

### Service fails to start

**Problem**: Service won't start after installation.

**Solution**:
```bash
# Check service status
sudo systemctl status tor-proxy-pool

# View detailed logs
sudo journalctl -u tor-proxy-pool -n 100 --no-pager

# Check configuration
cd /opt/tor-proxy-pool/backend
source venv/bin/activate
python -m app.main  # Test manually

# Common issues:
# 1. Missing .env file
# 2. Database connection failed
# 3. Port already in use
```

### Service keeps restarting

**Problem**: Service restarts constantly.

**Solution**:
```bash
# Check logs for errors
sudo journalctl -u tor-proxy-pool -f

# Common causes:
# 1. Database not accessible
# 2. Redis not running
# 3. Configuration error
# 4. Port already in use

# Check dependencies
sudo systemctl status postgresql redis

# Test database connection
psql -U torproxy -h localhost -d torproxy

# Check port availability
sudo lsof -i :8000
```

## Tor Issues

### Tor nodes won't start

**Problem**: Tor instances fail to start.

**Solution**:
```bash
# Check Tor is installed
which tor
tor --version

# Test Tor manually
tor -f /tmp/test-torrc

# Check data directory permissions
sudo ls -la /var/lib/tor-pool
sudo chown -R root:root /var/lib/tor-pool
sudo chmod 700 /var/lib/tor-pool/*

# Check port availability
sudo netstat -tulpn | grep -E "(30000|40000)"
```

### Tor nodes fail to bootstrap

**Problem**: Tor instances start but can't connect to Tor network.

**Solution**:
```bash
# Check internet connectivity
ping -c 3 8.8.8.8

# Check if Tor ports are blocked
curl https://check.torproject.org/

# Check Tor logs
tail -f /var/lib/tor-pool/tor-0000/notice.log

# Try manual bootstrap
tor --SocksPort 9999 --ControlPort 9998 --DataDirectory /tmp/tor-test

# Common issues:
# 1. Firewall blocking outbound connections
# 2. ISP blocking Tor
# 3. System clock not synchronized
```

### Country-specific exits not working

**Problem**: Can't get exits from specific countries.

**Solution**:
```bash
# Verify country codes are correct (ISO 3166-1 alpha-2)
# Correct: US, DE, FR
# Incorrect: USA, GER, FRA

# Check .env configuration
cat .env | grep TOR_COUNTRIES

# Try with StrictNodes=0 temporarily
TOR_STRICT_NODES=false

# Check available exits
curl https://onionoo.torproject.org/summary?search=flag:exit

# Note: Some countries have few exits
# - Increase circuit timeout
# - Use multiple countries
# - Disable StrictNodes if too restrictive
```

## Database Issues

### "Connection refused" to database

**Problem**: Can't connect to PostgreSQL.

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U torproxy -h localhost -d torproxy

# Check pg_hba.conf
sudo cat /etc/postgresql/*/main/pg_hba.conf

# Should have:
# local   all   torproxy   md5
# host    all   torproxy   127.0.0.1/32   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### "Password authentication failed"

**Problem**: Wrong database password.

**Solution**:
```bash
# Reset password
sudo -u postgres psql -c "ALTER USER torproxy PASSWORD 'newpassword';"

# Update .env
nano /opt/tor-proxy-pool/.env
# Change POSTGRES_PASSWORD=newpassword

# Restart service
sudo systemctl restart tor-proxy-pool
```

### Migration errors

**Problem**: Database migration fails.

**Solution**:
```bash
cd /opt/tor-proxy-pool/backend
source venv/bin/activate

# Check current revision
alembic current

# View migration history
alembic history

# Upgrade to latest
alembic upgrade head

# If failed, rollback and retry
alembic downgrade -1
alembic upgrade head
```

## Firewall Issues

### Locked out after whitelist configuration

**Problem**: Can't access admin panel after setting whitelist.

**Solution**:
```bash
# Access via console/KVM (not SSH)
# Option 1: Disable firewall temporarily
sudo systemctl stop nftables  # or iptables/ufw/firewalld

# Option 2: Edit configuration
sudo nano /opt/tor-proxy-pool/.env
# Remove or fix PANEL_WHITELIST

# Restart service
sudo systemctl restart tor-proxy-pool

# Re-enable firewall
sudo systemctl start nftables
```

### Firewall rules not applying

**Problem**: Firewall rules don't take effect.

**Solution**:
```bash
# Check firewall backend
systemctl status nftables
systemctl status firewalld
systemctl status ufw

# Manual rule check (nftables)
sudo nft list ruleset

# Manual rule check (iptables)
sudo iptables -L -n -v

# Reapply rules via API
curl -X POST -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/config/firewall/apply

# Check application logs
sudo journalctl -u tor-proxy-pool | grep firewall
```

### SOCKS ports not accessible

**Problem**: Can't connect to SOCKS proxies.

**Solution**:
```bash
# Check firewall allows SOCKS ports
sudo nft list ruleset | grep 30000

# Test SOCKS connection
curl --socks5 127.0.0.1:30000 https://check.torproject.org/api/ip

# Check if whitelist is blocking you
# Add your IP to SOCKS_WHITELIST in .env

# Check Tor node is running
sudo ps aux | grep "tor.*30000"
```

## Authentication Issues

### Can't login with default credentials

**Problem**: admin/admin doesn't work.

**Solution**:
```bash
# Check if admin user exists
sudo -u postgres psql -d torproxy -c "SELECT * FROM users WHERE username='admin';"

# Reset admin password
cd /opt/tor-proxy-pool/backend
source venv/bin/activate
python3 <<EOF
from app.core.security import get_password_hash
print(get_password_hash('newpassword'))
EOF

# Update in database
sudo -u postgres psql -d torproxy -c \
    "UPDATE users SET hashed_password='<hash_from_above>' WHERE username='admin';"
```

### 2FA not working

**Problem**: TOTP codes not accepted.

**Solution**:
```bash
# Check system time is synchronized
timedatectl status

# Synchronize time if needed
sudo timedatectl set-ntp true

# TOTP requires accurate time (±30 seconds)
# Verify time zone is correct
sudo timedatectl set-timezone America/New_York

# Disable 2FA temporarily (emergency)
sudo -u postgres psql -d torproxy -c \
    "UPDATE users SET totp_enabled=false WHERE username='admin';"
```

### Account locked after failed attempts

**Problem**: Account locked due to brute force protection.

**Solution**:
```bash
# Unlock account
sudo -u postgres psql -d torproxy -c \
    "UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE username='admin';"

# Or wait for lockout period to expire (default 15 minutes)
```

## Performance Issues

### High CPU usage

**Problem**: System CPU usage is very high.

**Solution**:
```bash
# Check which processes are using CPU
top
htop

# Reduce pool size if needed
nano /opt/tor-proxy-pool/.env
# Set lower TOR_POOL_SIZE

# Increase circuit timeout
# Add to torrc template:
# CircuitBuildTimeout 60

# Disable auto-rotation temporarily
AUTO_ROTATE_ENABLED=false
```

### High memory usage

**Problem**: System running out of memory.

**Solution**:
```bash
# Check memory usage
free -h

# Each Tor instance uses ~50MB
# For 100 nodes: ~5GB minimum required

# Reduce pool size
nano /opt/tor-proxy-pool/.env
TOR_POOL_SIZE=50  # or lower

# Add swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow proxy connections

**Problem**: Connections through proxies are very slow.

**Solution**:
```bash
# Check node health
curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/nodes/stats/summary

# Restart unhealthy nodes
curl -X POST -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/nodes/rotate

# Try different exit countries
# Some countries have faster exits
TOR_COUNTRIES=DE,NL,CH  # Central Europe typically fast

# Increase circuit timeout
CircuitBuildTimeout 60

# Check server bandwidth
speedtest-cli
```

## Network Issues

### Can't access admin panel remotely

**Problem**: Panel accessible on localhost but not remotely.

**Solution**:
```bash
# Check application is listening on correct interface
sudo netstat -tulpn | grep 8000
# Should show 0.0.0.0:8000, not 127.0.0.1:8000

# Check .env
HOST=0.0.0.0  # Not 127.0.0.1

# Check firewall allows port 8000
sudo iptables -L -n | grep 8000

# Check nginx configuration
sudo nginx -t
sudo systemctl status nginx

# Test from server
curl http://localhost:8000/health

# Test from remote
curl http://server-ip:8000/health
```

### SSL/TLS certificate errors

**Problem**: Browser shows certificate errors.

**Solution**:
```bash
# Check certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate paths in nginx
sudo nginx -t

# For self-signed certs, accept in browser
# Or use proper Let's Encrypt certificate
```

## Log Analysis

### Finding errors in logs

```bash
# Application logs
sudo journalctl -u tor-proxy-pool -p err -n 50

# All logs since last boot
sudo journalctl -u tor-proxy-pool -b

# Follow logs in real-time
sudo journalctl -u tor-proxy-pool -f

# Search for specific error
sudo journalctl -u tor-proxy-pool | grep "database"

# Tor node logs
tail -f /var/lib/tor-pool/tor-0000/notice.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

## Getting Help

If you're still having issues:

1. **Check logs**: `sudo journalctl -u tor-proxy-pool -n 100`
2. **Check documentation**: See other docs in `docs/` directory
3. **Verify configuration**: Review all `.env` settings
4. **Test dependencies**: Ensure PostgreSQL, Redis, Tor are working
5. **Create issue**: Open a GitHub issue with:
   - Error messages from logs
   - System information (OS, version)
   - Steps to reproduce
   - Configuration (redact sensitive info)

## Common Error Messages

### "Could not validate credentials"
- **Cause**: Invalid or expired JWT token
- **Solution**: Login again to get new token

### "Admin access required"
- **Cause**: Trying to access admin endpoint without admin privileges
- **Solution**: Login with admin account

### "Rate limit exceeded"
- **Cause**: Too many requests from same IP
- **Solution**: Wait 60 seconds or adjust rate limits

### "Token has expired"
- **Cause**: Export token past expiration time
- **Solution**: Create new export token

### "Node tor-XXXX not found"
- **Cause**: Node ID doesn't exist
- **Solution**: Check available nodes with `/api/v1/nodes/`

### "Failed to apply firewall rules"
- **Cause**: Insufficient permissions or firewall backend issue
- **Solution**: Check logs, ensure running as root, verify firewall backend

## Debug Mode

Enable debug mode for verbose logging (development only):

```bash
# Edit .env
DEBUG=true

# Restart service
sudo systemctl restart tor-proxy-pool

# API documentation now available at:
# http://localhost:8000/api/docs
```

**Warning**: Never enable debug mode in production!
