# Security Guide

This guide covers security best practices and configuration for Tor Proxy Pool.

## Initial Security Setup

### 1. Change Default Password

**Critical**: The default admin credentials (admin/admin) must be changed immediately after installation.

1. Navigate to the admin panel
2. Log in with admin/admin
3. You will be forced to change the password
4. Choose a strong password (12+ characters, mixed case, numbers, symbols)

### 2. Enable Two-Factor Authentication

Enable 2FA for all admin users:

```bash
# Enable 2FA in .env
ENABLE_2FA=true
```

Then in the admin panel:
1. Go to Settings → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)
4. Enter verification code to confirm

### 3. Configure IP Whitelists

Restrict access to known IP addresses:

```bash
# Panel access whitelist
PANEL_WHITELIST=192.168.1.0/24,10.0.0.5

# SOCKS proxy whitelist
SOCKS_WHITELIST=192.168.1.0/24
```

**Warning**: Be careful not to lock yourself out. The system will warn you if your current IP is not in the whitelist.

## Firewall Configuration

### Auto-Detection

The system automatically detects and uses available firewall backends:

```bash
FIREWALL_BACKEND=auto
```

Detection order:
1. firewalld
2. ufw
3. nftables
4. iptables

### Manual Backend Selection

```bash
# Use specific backend
FIREWALL_BACKEND=nftables  # or iptables, ufw, firewalld
```

### Firewall Rules

The firewall automatically:
- Allows loopback traffic
- Allows established connections
- Restricts panel access to whitelist
- Restricts SOCKS access to whitelist
- **Blocks Tor control ports from external access**
- Allows SSH (port 22)
- Rate-limits ICMP

### Testing Firewall

```bash
# Verify control ports are blocked externally
nmap -p 40000-40099 your-server-ip

# Should show: filtered or closed
```

## TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# Configure domain
DOMAIN=proxy.example.com
TLS_ENABLE=true

# Obtain certificate
sudo certbot --nginx -d proxy.example.com

# Auto-renewal is configured automatically
```

### Using Self-Signed Certificate

For development only:

```bash
# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem

# Configure in .env
TLS_ENABLE=true
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

## Security Headers

The following security headers are automatically applied:

- **HSTS**: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **X-Frame-Options**: `DENY`
- **X-Content-Type-Options**: `nosniff`
- **X-XSS-Protection**: `1; mode=block`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **CSP**: Content Security Policy configured

## Rate Limiting

### API Rate Limiting

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Login Brute Force Protection

```bash
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
```

After 5 failed attempts, the account is locked for 15 minutes.

## Audit Logging

All security events are logged:

- Login attempts (success/failure)
- Password changes
- 2FA setup/verification
- Configuration changes
- Firewall updates
- Token creation/revocation

View audit logs:

```bash
# Via API
curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/audit/logs

# Via database
sudo -u postgres psql -d torproxy -c "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## Export Token Security

### Token Configuration

```bash
# Token expiration (minutes)
EXPORT_TOKEN_TTL_MIN=60

# Bind tokens to IP address
EXPORT_TOKEN_IP_BIND=true
```

### Token Best Practices

1. Use short TTL for sensitive environments
2. Enable IP binding for additional security
3. Revoke tokens immediately when no longer needed
4. Regularly audit active tokens
5. Use descriptive names for tokens

### Revoking Tokens

```bash
# Via API
curl -X DELETE -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/export/tokens/<token_id>

# Via database
sudo -u postgres psql -d torproxy -c \
    "UPDATE export_tokens SET is_revoked=true WHERE id=<token_id>;"
```

## Tor Security

### Control Port Protection

**Critical**: Tor control ports MUST NOT be accessible externally.

The firewall automatically blocks ports 40000-40099 from external access. Verify:

```bash
# From external machine
nmap -p 40000-40099 your-server-ip
# Should show: filtered

# From localhost (should work)
telnet localhost 40000
```

### Circuit Isolation

Each Tor instance runs independently with its own:
- Data directory
- SOCKS port
- Control port
- Circuit

This provides natural isolation between connections.

## Security Monitoring

### Enable Alerts

```bash
# Email alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@example.com

# Telegram alerts
ALERT_TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Alert Conditions

Alerts are sent for:
- Node failure threshold exceeded (default 20%)
- Firewall rule application failures
- TLS certificate expiration (default 30 days)
- Brute force attempts (5+ failed logins)

### Prometheus Monitoring

Monitor security metrics:

```prometheus
# Failed authentication attempts
auth_attempts_total{result="failure"}

# Account lockouts
auth_attempts_total{result="locked"}

# Node health
tor_nodes_up / tor_nodes_total
```

## Regular Security Maintenance

### Weekly Tasks

1. Review audit logs for suspicious activity
2. Check for failed login attempts
3. Review active export tokens
4. Verify firewall rules are active

### Monthly Tasks

1. Update system packages
2. Review user accounts and permissions
3. Test backup and restore procedures
4. Verify TLS certificate validity
5. Review and update IP whitelists

### Quarterly Tasks

1. Rotate API secret key
2. Review and update security policies
3. Conduct security audit
4. Update dependencies

## Emergency Procedures

### Suspected Compromise

1. **Immediately**:
   ```bash
   # Stop all services
   sudo systemctl stop tor-proxy-pool
   
   # Block all traffic
   sudo iptables -P INPUT DROP
   sudo iptables -P FORWARD DROP
   ```

2. **Investigate**:
   ```bash
   # Check audit logs
   sudo journalctl -u tor-proxy-pool -n 1000
   
   # Check active connections
   sudo netstat -tupn
   
   # Check for unauthorized files
   sudo find /opt/tor-proxy-pool -type f -mtime -1
   ```

3. **Recovery**:
   - Change all passwords
   - Regenerate API secret key
   - Revoke all export tokens
   - Review and update firewall rules
   - Restore from clean backup if necessary

### Locked Out

If you lock yourself out due to whitelist:

1. Access server via console/KVM
2. Edit `.env` and remove whitelist entries
3. Restart service: `sudo systemctl restart tor-proxy-pool`
4. Add your IP to whitelist via admin panel
5. Reapply firewall rules

## Security Checklist

- [ ] Changed default admin password
- [ ] Enabled 2FA for all admin users
- [ ] Configured IP whitelists
- [ ] Enabled TLS with valid certificate
- [ ] Verified HSTS is enabled
- [ ] Confirmed control ports are blocked externally
- [ ] Enabled and tested alerts
- [ ] Configured rate limiting
- [ ] Regular audit log reviews scheduled
- [ ] Backup procedures tested
- [ ] Security monitoring dashboard created
- [ ] Emergency procedures documented and tested

## Security Contact

For security issues, please:
1. Do NOT open a public issue
2. Contact via secure channel
3. Provide detailed information
4. Wait for confirmation before disclosure
