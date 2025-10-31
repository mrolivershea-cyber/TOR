# API Documentation

Complete API reference for Tor Proxy Pool REST API.

## Base URL

```
http://your-server:8000/api/v1
```

## Authentication

All API endpoints (except `/auth/login`) require JWT authentication.

### Login

**POST** `/auth/login`

Request:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword&totp_token=123456"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "require_password_change": false
}
```

### Using Token

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/v1/nodes/
```

## Endpoints

### Authentication

#### Change Password

**POST** `/auth/change-password`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/auth/change-password \
  -d "old_password=current&new_password=newpass"
```

#### Setup 2FA

**POST** `/auth/setup-2fa`

Returns QR code and secret for TOTP setup.

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/auth/setup-2fa
```

Response:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "uri": "otpauth://totp/..."
}
```

#### Verify 2FA

**POST** `/auth/verify-2fa`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/auth/verify-2fa \
  -d "totp_token=123456"
```

#### Get Current User

**GET** `/auth/me`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/auth/me
```

### Nodes Management

#### List All Nodes

**GET** `/nodes/`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/
```

Response:
```json
{
  "total": 50,
  "nodes": [
    {
      "node_id": "tor-0000",
      "socks_port": 30000,
      "control_port": 40000,
      "is_healthy": true,
      "exit_ip": "185.220.101.1",
      "exit_country": "DE"
    }
  ]
}
```

#### Get Node Details

**GET** `/nodes/{node_id}`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/tor-0000
```

#### Rotate All Circuits

**POST** `/nodes/rotate`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/rotate
```

#### Rotate Single Circuit

**POST** `/nodes/{node_id}/rotate`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/tor-0000/rotate
```

#### Scale Pool

**POST** `/nodes/scale`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/nodes/scale?new_size=75"
```

#### Get Statistics

**GET** `/nodes/stats/summary`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/nodes/stats/summary
```

Response:
```json
{
  "total_nodes": 50,
  "healthy_nodes": 48,
  "unhealthy_nodes": 2,
  "health_percentage": 96.0,
  "countries": {
    "US": 15,
    "DE": 20,
    "FR": 13
  }
}
```

### Configuration

#### Get Configuration

**GET** `/config/`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/config/
```

#### Update Panel Whitelist

**PUT** `/config/whitelist/panel`

```bash
curl -X PUT -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/config/whitelist/panel \
  -d '["192.168.1.0/24", "10.0.0.5"]'
```

#### Update SOCKS Whitelist

**PUT** `/config/whitelist/socks`

```bash
curl -X PUT -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/config/whitelist/socks \
  -d '["192.168.1.0/24"]'
```

#### Apply Firewall Rules

**POST** `/config/firewall/apply`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/config/firewall/apply
```

### Export Tokens

#### Create Export Token

**POST** `/export/tokens`

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/export/tokens \
  -d "description=My Software"
```

Response:
```json
{
  "token": "abc123def456...",
  "expires_at": "2024-01-01T12:00:00",
  "description": "My Software"
}
```

#### List Export Tokens

**GET** `/export/tokens`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/export/tokens
```

#### Revoke Export Token

**DELETE** `/export/tokens/{token_id}`

```bash
curl -X DELETE -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/export/tokens/1
```

#### Download Proxy List (TXT)

**GET** `/export/download/txt`

```bash
curl "http://localhost:8000/api/v1/export/download/txt?token=<export_token>" \
  -o proxies.txt
```

Output format:
```
127.0.0.1:30000
127.0.0.1:30001
127.0.0.1:30002
```

#### Download Proxy List (CSV)

**GET** `/export/download/csv`

```bash
curl "http://localhost:8000/api/v1/export/download/csv?token=<export_token>" \
  -o proxies.csv
```

Output format:
```csv
host,port,exit_ip,exit_country,is_healthy
127.0.0.1,30000,185.220.101.1,DE,true
127.0.0.1,30001,185.220.101.2,US,true
```

#### Download Proxy List (JSON)

**GET** `/export/download/json`

```bash
curl "http://localhost:8000/api/v1/export/download/json?token=<export_token>"
```

Response:
```json
{
  "proxies": [
    {
      "host": "127.0.0.1",
      "port": 30000,
      "exit_ip": "185.220.101.1",
      "exit_country": "DE",
      "is_healthy": true
    }
  ],
  "total": 50,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Metrics

#### Get Application Metrics

**GET** `/metrics/`

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/metrics/
```

Response:
```json
{
  "nodes": {
    "total": 50,
    "healthy": 48,
    "unhealthy": 2,
    "health_percentage": 96.0
  }
}
```

### Prometheus Metrics

**GET** `/metrics` (no authentication required)

```bash
curl http://localhost:8000/metrics
```

Available metrics:
- `tor_nodes_total` - Total configured nodes
- `tor_nodes_up` - Healthy nodes
- `tor_node_latency_ms{node_id}` - Node latency
- `tor_newnym_total{node_id}` - NEWNYM count
- `tor_restarts_total{node_id}` - Restart count
- `api_requests_total{method,endpoint,status}` - API requests
- `auth_attempts_total{result}` - Auth attempts
- `export_tokens_active` - Active export tokens

### Health Check

**GET** `/health`

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "tor_pool_size": 50
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found

```json
{
  "detail": "Node tor-0999 not found"
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- General API: 60 requests/minute
- Login endpoint: 5 requests/minute
- Export download: 10 requests/minute

## Python Client Example

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    data={
        'username': 'admin',
        'password': 'password'
    }
)
token = response.json()['access_token']

# Get nodes
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/nodes/',
    headers=headers
)
nodes = response.json()['nodes']

# Rotate circuit
response = requests.post(
    'http://localhost:8000/api/v1/nodes/tor-0000/rotate',
    headers=headers
)
```

## JavaScript Client Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'admin',
    password: 'password'
  })
});
const { access_token } = await loginResponse.json();

// Get nodes
const nodesResponse = await fetch('http://localhost:8000/api/v1/nodes/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
const { nodes } = await nodesResponse.json();

// Download proxy list
const proxiesResponse = await fetch(
  `http://localhost:8000/api/v1/export/download/json?token=${exportToken}`
);
const proxies = await proxiesResponse.json();
```

## OpenAPI/Swagger

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Note: API docs are only available when `DEBUG=true`.
