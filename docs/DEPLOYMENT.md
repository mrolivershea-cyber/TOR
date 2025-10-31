# Deployment Guide

Complete guide for deploying Tor Proxy Pool to production.

## Pre-Deployment Checklist

- [ ] Server meets minimum requirements (4GB RAM, 2 CPU cores)
- [ ] Domain name configured (if using TLS)
- [ ] DNS records pointing to server
- [ ] Firewall rules reviewed
- [ ] Backup strategy planned
- [ ] Monitoring configured
- [ ] Alert contacts configured

## Quick Deployment

### 1. Clone Repository

```bash
git clone https://github.com/mrolivershea-cyber/TOR.git
cd TOR
```

### 2. Run Installation

```bash
sudo ./install.sh
```

### 3. Configure Environment

```bash
sudo nano /opt/tor-proxy-pool/.env
```

Key settings to configure:
- `API_SECRET_KEY` - Generate new: `openssl rand -hex 32`
- `POSTGRES_PASSWORD` - Use strong password
- `PANEL_WHITELIST` - Restrict to your IP
- `DOMAIN` - Your domain name (if using TLS)

### 4. Setup TLS (Production)

```bash
sudo certbot --nginx -d your-domain.com
```

### 5. Start Service

```bash
sudo systemctl start tor-proxy-pool
sudo systemctl enable tor-proxy-pool
```

### 6. Verify Installation

```bash
# Check service status
sudo systemctl status tor-proxy-pool

# Run health check
sudo /opt/tor-proxy-pool/scripts/health-check.sh

# Test API
curl http://localhost:8000/health
```

## Production Configuration

### Security Hardening

1. **Change Default Credentials**
   - Login at `https://your-domain.com`
   - Default: admin/admin
   - Change immediately on first login

2. **Enable 2FA**
   - Go to Settings → Security
   - Enable 2FA
   - Scan QR code with authenticator app

3. **Configure Whitelists**
   ```ini
   PANEL_WHITELIST=your.office.ip/32
   SOCKS_WHITELIST=your.app.server/32
   ```

4. **Enable TLS**
   ```ini
   TLS_ENABLE=true
   DOMAIN=proxy.example.com
   ```

5. **Configure Alerts**
   ```ini
   ALERT_EMAIL_ENABLED=true
   ALERT_EMAIL_TO=admin@example.com
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=alerts@example.com
   SMTP_PASSWORD=your-app-password
   ```

### Performance Tuning

For 100 nodes:

```ini
# Increase pool size
TOR_POOL_SIZE=100

# Optimize rotation
AUTO_ROTATE_INTERVAL=1800  # 30 minutes

# Database connection pooling
# Edit backend/app/db/session.py
pool_size=20
max_overflow=40
```

### High Availability Setup

For production HA:

1. **Load Balancer**
   - Use Nginx/HAProxy in front
   - Multiple backend instances
   - Health check endpoint: `/health`

2. **Database**
   - PostgreSQL replication
   - Automatic failover
   - Regular backups

3. **Redis**
   - Redis Sentinel for HA
   - Or Redis Cluster

4. **Monitoring**
   - Prometheus + Grafana
   - Alert manager
   - Uptime monitoring

## Docker Deployment

### Using Docker Compose

```bash
# Generate secret key
echo "API_SECRET_KEY=$(openssl rand -hex 32)" > .env
echo "POSTGRES_PASSWORD=secure_password" >> .env

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Docker Swarm (Production)

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml tor-proxy-pool

# Scale backend
docker service scale tor-proxy-pool_backend=3

# Check status
docker stack ps tor-proxy-pool
```

## Kubernetes Deployment

Basic Kubernetes deployment:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tor-proxy-pool
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tor-proxy-pool
  template:
    metadata:
      labels:
        app: tor-proxy-pool
    spec:
      containers:
      - name: backend
        image: tor-proxy-pool:latest
        env:
        - name: POSTGRES_HOST
          value: postgres-service
        - name: REDIS_HOST
          value: redis-service
        ports:
        - containerPort: 8000
        - containerPort: 30000-30099
```

## Backup Strategy

### Automated Backups

```bash
# Setup daily backup cron
sudo crontab -e

# Add:
0 2 * * * /opt/tor-proxy-pool/scripts/backup.sh /var/backups/tor-proxy-pool
```

### Backup to Remote Storage

```bash
# After backup, sync to S3
aws s3 sync /var/backups/tor-proxy-pool s3://your-bucket/tor-proxy-pool/

# Or to remote server
rsync -avz /var/backups/tor-proxy-pool/ backup-server:/backups/
```

## Monitoring Setup

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tor-proxy-pool'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the provided dashboard:
1. Open Grafana
2. Go to Dashboards → Import
3. Upload `monitoring/grafana/dashboard.json`

### Alert Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: tor_proxy_pool
    rules:
      - alert: HighNodeFailureRate
        expr: (tor_nodes_total - tor_nodes_up) / tor_nodes_total > 0.2
        for: 5m
        annotations:
          summary: "High node failure rate"
      
      - alert: APIHighLatency
        expr: api_request_duration_seconds > 5
        for: 5m
        annotations:
          summary: "API latency too high"
```

## Scaling Strategies

### Vertical Scaling

Increase server resources:
- More RAM for more Tor nodes
- More CPU cores for better performance
- Faster disk for database

```ini
# Scale to 100 nodes
TOR_POOL_SIZE=100

# Requires:
# - 8GB RAM minimum
# - 4 CPU cores
# - 20GB disk space
```

### Horizontal Scaling

Multiple server setup:
1. Central database (PostgreSQL cluster)
2. Shared Redis cache
3. Multiple backend instances with load balancer
4. Distributed Tor nodes

## Troubleshooting Deployment

### Service Won't Start

```bash
# Check logs
sudo journalctl -u tor-proxy-pool -n 50

# Test manually
cd /opt/tor-proxy-pool/backend
source venv/bin/activate
python -m uvicorn app.main:app
```

### Database Connection Issues

```bash
# Test connection
psql -U torproxy -h localhost -d torproxy

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check credentials in .env
grep POSTGRES /opt/tor-proxy-pool/.env
```

### Tor Nodes Not Starting

```bash
# Check Tor is installed
which tor

# Check data directory
ls -la /var/lib/tor-pool/

# Check logs
tail -f /var/lib/tor-pool/tor-0000/notice.log
```

## Post-Deployment

### Regular Maintenance

1. **Weekly**
   - Review audit logs
   - Check node health
   - Verify backups

2. **Monthly**
   - Update system packages
   - Review security alerts
   - Check disk usage
   - Rotate old logs

3. **Quarterly**
   - Security audit
   - Performance review
   - Capacity planning
   - Update documentation

### Performance Monitoring

Key metrics to watch:
- Node health percentage (>95%)
- API response time (<200ms)
- Database connections
- Memory usage
- Disk usage

### Security Audits

Regular checks:
- Review audit logs for suspicious activity
- Check for failed login attempts
- Verify firewall rules are active
- Scan for vulnerabilities
- Update dependencies

## Rollback Procedure

If deployment fails:

```bash
# Stop new version
sudo systemctl stop tor-proxy-pool

# Restore from backup
sudo /opt/tor-proxy-pool/scripts/restore.sh /var/backups/tor-proxy-pool/latest.tar.gz

# Start service
sudo systemctl start tor-proxy-pool

# Verify
curl http://localhost:8000/health
```

## Support

For deployment assistance:
- Check documentation in `docs/`
- Review troubleshooting guide
- Open GitHub issue with deployment logs

## Production Checklist

Final verification before going live:

- [ ] Default password changed
- [ ] 2FA enabled
- [ ] TLS/SSL configured and tested
- [ ] Firewall rules applied
- [ ] IP whitelists configured
- [ ] Alerts configured and tested
- [ ] Backups automated and tested
- [ ] Monitoring dashboard set up
- [ ] Health check script runs successfully
- [ ] API responds correctly
- [ ] All Tor nodes are healthy
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Emergency procedures documented
- [ ] Support contacts configured

Congratulations on deploying Tor Proxy Pool! 🎉
