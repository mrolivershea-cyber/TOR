# Configuration Reference

Complete reference for all configuration options in Tor Proxy Pool.

## Configuration File

Configuration is managed through environment variables in the `.env` file:

```bash
cp .env.example .env
nano .env
```

## Application Settings

### APP_NAME
- **Type**: String
- **Default**: `Tor Proxy Pool`
- **Description**: Application name shown in UI and logs

### DEBUG
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable debug mode (enables API docs, verbose logging)
- **Warning**: Never enable in production

### HOST
- **Type**: String
- **Default**: `0.0.0.0`
- **Description**: Host to bind the application to

### PORT
- **Type**: Integer
- **Default**: `8000`
- **Description**: Port to run the application on

## Security Settings

### API_SECRET_KEY
- **Type**: String
- **Required**: Yes
- **Description**: Secret key for JWT token signing
- **Generate**: `openssl rand -hex 32`
- **Warning**: Keep this secret and never commit to version control

### JWT_ALGORITHM
- **Type**: String
- **Default**: `HS256`
- **Description**: Algorithm for JWT token signing

### ACCESS_TOKEN_EXPIRE_MINUTES
- **Type**: Integer
- **Default**: `30`
- **Description**: Access token expiration time in minutes

### REFRESH_TOKEN_EXPIRE_DAYS
- **Type**: Integer
- **Default**: `7`
- **Description**: Refresh token expiration time in days

## Admin Account

### ADMIN_USERNAME
- **Type**: String
- **Default**: `admin`
- **Description**: Default admin username

### ADMIN_PASSWORD
- **Type**: String
- **Default**: `admin`
- **Description**: Default admin password
- **Warning**: Change on first login

### REQUIRE_PASSWORD_CHANGE
- **Type**: Boolean
- **Default**: `true`
- **Description**: Force password change on first login

## Two-Factor Authentication

### ENABLE_2FA
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable TOTP-based 2FA
- **Recommended**: Keep enabled for security

## Database Settings

### POSTGRES_HOST
- **Type**: String
- **Default**: `localhost`
- **Description**: PostgreSQL host

### POSTGRES_PORT
- **Type**: Integer
- **Default**: `5432`
- **Description**: PostgreSQL port

### POSTGRES_DB
- **Type**: String
- **Default**: `torproxy`
- **Description**: Database name

### POSTGRES_USER
- **Type**: String
- **Default**: `torproxy`
- **Description**: Database user

### POSTGRES_PASSWORD
- **Type**: String
- **Required**: Yes
- **Description**: Database password
- **Security**: Use strong password

## Redis Settings

### REDIS_HOST
- **Type**: String
- **Default**: `localhost`
- **Description**: Redis host

### REDIS_PORT
- **Type**: Integer
- **Default**: `6379`
- **Description**: Redis port

### REDIS_DB
- **Type**: Integer
- **Default**: `0`
- **Description**: Redis database number

### REDIS_PASSWORD
- **Type**: String
- **Optional**: Yes
- **Description**: Redis password (if authentication is enabled)

## Tor Pool Settings

### TOR_POOL_SIZE
- **Type**: Integer
- **Default**: `50`
- **Range**: 1-100
- **Description**: Number of Tor instances to run
- **Note**: Each instance uses ~50MB RAM

### TOR_BASE_SOCKS_PORT
- **Type**: Integer
- **Default**: `30000`
- **Description**: Starting port for SOCKS proxies
- **Range**: Ports 30000 to 30000+TOR_POOL_SIZE-1 will be used

### TOR_BASE_CTRL_PORT
- **Type**: Integer
- **Default**: `40000`
- **Description**: Starting port for Tor control
- **Range**: Ports 40000 to 40000+TOR_POOL_SIZE-1 will be used
- **Security**: These ports are blocked from external access

### TOR_DATA_DIR
- **Type**: String
- **Default**: `/var/lib/tor-pool`
- **Description**: Directory for Tor data files
- **Permissions**: Must be writable

## Tor Configuration

### TOR_COUNTRIES
- **Type**: List (comma-separated)
- **Optional**: Yes
- **Example**: `US,DE,FR`
- **Description**: Preferred exit node countries (ISO 3166-1 alpha-2 codes)
- **Note**: Leave empty for any country

### TOR_STRICT_NODES
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enforce strict country selection
- **Note**: If true, only exits from selected countries are used

## Auto Rotation

### AUTO_ROTATE_ENABLED
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable automatic circuit rotation

### AUTO_ROTATE_INTERVAL
- **Type**: Integer
- **Default**: `600`
- **Description**: Rotation interval in seconds (10 minutes)

## Health Monitoring

### HEALTH_CHECK_INTERVAL
- **Type**: Integer
- **Default**: `60`
- **Description**: Health check interval in seconds

### HEALTH_CHECK_TIMEOUT
- **Type**: Integer
- **Default**: `10`
- **Description**: Health check timeout in seconds

### MAX_FAILED_CHECKS
- **Type**: Integer
- **Default**: `3`
- **Description**: Max failed checks before restart

## Firewall Settings

### FIREWALL_BACKEND
- **Type**: String
- **Default**: `auto`
- **Options**: `auto`, `nftables`, `iptables`, `ufw`, `firewalld`, `none`
- **Description**: Firewall backend to use
- **Note**: `auto` detects the best available option

## IP Whitelists

### PANEL_WHITELIST
- **Type**: List (comma-separated)
- **Optional**: Yes
- **Example**: `192.168.1.0/24,10.0.0.5`
- **Description**: IP addresses/CIDR ranges allowed to access admin panel
- **Note**: Leave empty to allow all IPs (not recommended)

### SOCKS_WHITELIST
- **Type**: List (comma-separated)
- **Optional**: Yes
- **Example**: `192.168.1.0/24`
- **Description**: IP addresses/CIDR ranges allowed to use SOCKS proxies
- **Note**: Leave empty to allow all IPs

## TLS/SSL Settings

### TLS_ENABLE
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable TLS/SSL
- **Recommended**: Always enabled in production

### DOMAIN
- **Type**: String
- **Optional**: Yes
- **Example**: `proxy.example.com`
- **Description**: Domain name for Let's Encrypt
- **Note**: Leave empty for self-signed cert or HTTP only

### SSL_CERT_PATH
- **Type**: String
- **Optional**: Yes
- **Description**: Path to SSL certificate file

### SSL_KEY_PATH
- **Type**: String
- **Optional**: Yes
- **Description**: Path to SSL private key file

## Export Token Settings

### EXPORT_TOKEN_TTL_MIN
- **Type**: Integer
- **Default**: `60`
- **Description**: Export token time-to-live in minutes

### EXPORT_TOKEN_IP_BIND
- **Type**: Boolean
- **Default**: `false`
- **Description**: Bind export tokens to client IP
- **Security**: Enable for additional security

## CORS Settings

### CORS_ORIGINS
- **Type**: List (comma-separated)
- **Default**: `http://localhost:3000,http://localhost:8000`
- **Description**: Allowed CORS origins
- **Production**: Set to your actual frontend URLs

## Monitoring Settings

### ENABLE_METRICS
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable Prometheus metrics endpoint

### METRICS_PORT
- **Type**: Integer
- **Default**: `9090`
- **Description**: Port for metrics endpoint

## Logging Settings

### LOG_LEVEL
- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging level

### LOG_FORMAT
- **Type**: String
- **Default**: `json`
- **Options**: `json`, `text`
- **Description**: Log format
- **Recommended**: `json` for production

### LOG_FILE
- **Type**: String
- **Default**: `/var/log/tor-proxy-pool/app.log`
- **Description**: Log file path

### LOG_MAX_BYTES
- **Type**: Integer
- **Default**: `10485760` (10MB)
- **Description**: Maximum log file size before rotation

### LOG_BACKUP_COUNT
- **Type**: Integer
- **Default**: `10`
- **Description**: Number of rotated log files to keep

## Email Alert Settings

### ALERT_EMAIL_ENABLED
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable email alerts

### ALERT_EMAIL_TO
- **Type**: String
- **Required**: If email alerts enabled
- **Example**: `admin@example.com`
- **Description**: Email address to send alerts to

### ALERT_EMAIL_FROM
- **Type**: String
- **Required**: If email alerts enabled
- **Example**: `alerts@example.com`
- **Description**: Email address to send alerts from

### SMTP_HOST
- **Type**: String
- **Required**: If email alerts enabled
- **Example**: `smtp.gmail.com`
- **Description**: SMTP server hostname

### SMTP_PORT
- **Type**: Integer
- **Default**: `587`
- **Description**: SMTP server port

### SMTP_USER
- **Type**: String
- **Optional**: Yes
- **Description**: SMTP username (if authentication required)

### SMTP_PASSWORD
- **Type**: String
- **Optional**: Yes
- **Description**: SMTP password (if authentication required)

### SMTP_TLS
- **Type**: Boolean
- **Default**: `true`
- **Description**: Use TLS for SMTP connection

## Telegram Alert Settings

### ALERT_TELEGRAM_ENABLED
- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable Telegram alerts

### TELEGRAM_BOT_TOKEN
- **Type**: String
- **Required**: If Telegram alerts enabled
- **Description**: Telegram bot token from @BotFather

### TELEGRAM_CHAT_ID
- **Type**: String
- **Required**: If Telegram alerts enabled
- **Description**: Telegram chat ID to send alerts to

## Alert Threshold Settings

### ALERT_NODE_DOWN_THRESHOLD
- **Type**: Float
- **Default**: `0.2`
- **Range**: 0.0-1.0
- **Description**: Alert when this percentage of nodes are down
- **Example**: `0.2` = Alert when 20% nodes are down

### ALERT_TLS_EXPIRY_DAYS
- **Type**: Integer
- **Default**: `30`
- **Description**: Alert when TLS cert expires in this many days

## Rate Limiting Settings

### RATE_LIMIT_ENABLED
- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable API rate limiting
- **Recommended**: Always enabled

### RATE_LIMIT_PER_MINUTE
- **Type**: Integer
- **Default**: `60`
- **Description**: Maximum requests per minute per IP

## Brute Force Protection

### MAX_LOGIN_ATTEMPTS
- **Type**: Integer
- **Default**: `5`
- **Description**: Maximum failed login attempts before lockout

### LOGIN_LOCKOUT_MINUTES
- **Type**: Integer
- **Default**: `15`
- **Description**: Account lockout duration in minutes

## Example Production Configuration

```ini
# Production settings
APP_NAME=Tor Proxy Pool
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Security
API_SECRET_KEY=your-generated-secret-key-here
ENABLE_2FA=true

# Database
POSTGRES_HOST=db.internal
POSTGRES_PASSWORD=secure-db-password

# Tor Pool
TOR_POOL_SIZE=100
TOR_COUNTRIES=US,DE,FR
TOR_STRICT_NODES=true

# Firewall
FIREWALL_BACKEND=nftables
PANEL_WHITELIST=203.0.113.0/24
SOCKS_WHITELIST=203.0.113.0/24

# TLS
TLS_ENABLE=true
DOMAIN=proxy.example.com

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=admin@example.com
SMTP_HOST=smtp.example.com
SMTP_USER=alerts@example.com
SMTP_PASSWORD=smtp-password

ALERT_TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Rate limiting
RATE_LIMIT_ENABLED=true
MAX_LOGIN_ATTEMPTS=5
```

## Reloading Configuration

After changing configuration:

```bash
# Restart service
sudo systemctl restart tor-proxy-pool

# Or with Docker
docker-compose restart backend
```

Some settings (like whitelists) can be updated via API without restart.
