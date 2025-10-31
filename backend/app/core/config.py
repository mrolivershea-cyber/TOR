"""
Application configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Tor Proxy Pool"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    API_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Admin credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"  # Must be changed on first login
    REQUIRE_PASSWORD_CHANGE: bool = True
    
    # 2FA
    ENABLE_2FA: bool = True
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "torproxy"
    POSTGRES_USER: str = "torproxy"
    POSTGRES_PASSWORD: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Tor Pool
    TOR_POOL_SIZE: int = 50
    TOR_BASE_SOCKS_PORT: int = 30000
    TOR_BASE_CTRL_PORT: int = 40000
    TOR_DATA_DIR: str = "/var/lib/tor-pool"
    
    # Tor Configuration
    TOR_COUNTRIES: Optional[List[str]] = None  # e.g., ["US", "DE"]
    TOR_STRICT_NODES: bool = True
    
    # Auto Rotation
    AUTO_ROTATE_ENABLED: bool = True
    AUTO_ROTATE_INTERVAL: int = 600  # seconds
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = 60
    HEALTH_CHECK_TIMEOUT: int = 10
    MAX_FAILED_CHECKS: int = 3
    
    # Firewall
    FIREWALL_BACKEND: str = "auto"  # auto | nftables | iptables | ufw | firewalld
    
    # Whitelist
    PANEL_WHITELIST: Optional[List[str]] = None  # IP addresses/CIDR
    SOCKS_WHITELIST: Optional[List[str]] = None  # IP addresses/CIDR
    
    # TLS
    TLS_ENABLE: bool = True
    DOMAIN: Optional[str] = None
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    # Export Tokens
    EXPORT_TOKEN_TTL_MIN: int = 60
    EXPORT_TOKEN_IP_BIND: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | text
    LOG_FILE: str = "/var/log/tor-proxy-pool/app.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 10
    
    # Alerts
    ALERT_EMAIL_ENABLED: bool = False
    ALERT_EMAIL_TO: Optional[str] = None
    ALERT_EMAIL_FROM: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    ALERT_TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Alert thresholds
    ALERT_NODE_DOWN_THRESHOLD: float = 0.2  # 20% nodes down
    ALERT_TLS_EXPIRY_DAYS: int = 30
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Brute force protection
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
