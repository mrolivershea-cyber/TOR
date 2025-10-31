"""
Prometheus metrics
"""
from prometheus_client import Counter, Gauge, Histogram

# Tor nodes metrics
tor_nodes_total = Gauge(
    'tor_nodes_total',
    'Total number of Tor nodes in pool'
)

tor_nodes_up = Gauge(
    'tor_nodes_up',
    'Number of healthy Tor nodes'
)

tor_node_latency = Gauge(
    'tor_node_latency_ms',
    'Latency of Tor node in milliseconds',
    ['node_id']
)

tor_newnym_total = Counter(
    'tor_newnym_total',
    'Total number of NEWNYM signals sent',
    ['node_id']
)

tor_restarts_total = Counter(
    'tor_restarts_total',
    'Total number of Tor node restarts',
    ['node_id']
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Auth metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['result']  # success, failure, locked
)

# Export metrics
export_tokens_active = Gauge(
    'export_tokens_active',
    'Number of active export tokens'
)

export_downloads_total = Counter(
    'export_downloads_total',
    'Total export downloads',
    ['format']  # txt, csv, json
)
