# Quick Start Guide

## САМЫЙ ПРОСТОЙ СПОСОБ (рекомендуется)

Используйте автоматический установщик:

```bash
cd TOR
chmod +x INSTALL_SIMPLE.sh
sudo ./INSTALL_SIMPLE.sh
```

Скрипт автоматически:
1. Установит Python и pip
2. Установит FastAPI и uvicorn
3. Создаст systemd сервис
4. Запустит тестовый сервер

После установки откройте: `http://your-server-ip:8000`
Логин: **admin** / **admin**

---

## Проблема: Не могу войти в админ-панель

Если вы не можете войти в админ-панель после установки, выполните следующие шаги:

### 1. Проверьте, что сервис запущен

```bash
sudo systemctl status tor-proxy-pool
```

Если сервис не запущен или показывает ошибки, проверьте логи:

```bash
sudo journalctl -u tor-proxy-pool -n 50
```

### 2. Минимальная установка (без полной настройки)

Если полная установка не работает, запустите минимальную версию:

```bash
cd /home/runner/work/TOR/TOR

# Установите только Python зависимости
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic asyncpg python-jose passlib bcrypt python-multipart

# Создайте минимальный .env файл
cat > ../.env << 'EOF'
DEBUG=true
API_SECRET_KEY=insecure-dev-key-change-in-production
POSTGRES_PASSWORD=changeme
TOR_POOL_SIZE=0
FIREWALL_BACKEND=none
ENABLE_2FA=false
EOF

# Запустите сервер напрямую
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Теперь откройте браузер: `http://your-server-ip:8000`

### 3. Проверьте доступность порта

```bash
# Проверьте, что порт 8000 открыт
sudo netstat -tulpn | grep 8000

# Проверьте firewall
sudo iptables -L -n | grep 8000
# или
sudo firewall-cmd --list-all
```

### 4. Создайте пользователя вручную

Если база данных работает, но нет пользователя:

```bash
cd /home/runner/work/TOR/TOR/backend
source venv/bin/activate

# Запустите Python
python3 << 'PYEOF'
import asyncio
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def create_admin():
    async with AsyncSessionLocal() as db:
        # Проверьте, существует ли пользователь
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if not user:
            # Создайте пользователя
            user = User(
                username="admin",
                hashed_password=get_password_hash("admin"),
                is_admin=True,
                is_active=True,
                require_password_change=True
            )
            db.add(user)
            await db.commit()
            print("Пользователь admin создан успешно!")
        else:
            print("Пользователь admin уже существует")

asyncio.run(create_admin())
PYEOF
```

### 5. Тестовый режим (без базы данных)

Если база данных не работает, можете запустить в тестовом режиме:

```bash
cd /home/runner/work/TOR/TOR/backend

# Создайте test_server.py
cat > test_server.py << 'EOF'
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

app = FastAPI()

# Serve static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/")
async def root():
    index_path = Path(__file__).parent.parent / "frontend" / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Admin panel not found"}

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "test"}

@app.post("/api/v1/auth/login")
async def test_login(username: str, password: str):
    if username == "admin" and password == "admin":
        return {
            "access_token": "test_token_12345",
            "token_type": "bearer",
            "require_password_change": False
        }
    return JSONResponse({"detail": "Invalid credentials"}, status_code=401)

@app.get("/api/v1/nodes/stats/summary")
async def test_stats():
    return {
        "total_nodes": 0,
        "healthy_nodes": 0,
        "unhealthy_nodes": 0,
        "health_percentage": 0,
        "countries": {}
    }

@app.get("/api/v1/nodes/")
async def test_nodes():
    return {"total": 0, "nodes": []}

@app.get("/api/v1/config/")
async def test_config():
    return {
        "tor_pool_size": 0,
        "tor_base_socks_port": 30000,
        "tor_countries": [],
        "auto_rotate_enabled": False,
        "firewall_backend": "none",
        "tls_enable": False,
        "domain": None
    }

@app.get("/api/v1/export/tokens")
async def test_tokens():
    return {"tokens": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Запустите тестовый сервер
python test_server.py
```

Теперь админ-панель должна работать на `http://your-server-ip:8000` с логином admin/admin (без реальной функциональности).

### 6. Проверьте доступ с внешнего IP

Убедитесь, что firewall не блокирует доступ:

```bash
# Временно разрешите порт 8000
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT

# Или для firewalld
sudo firewall-cmd --add-port=8000/tcp
```

### 7. Проверьте из браузера

Откройте: `http://195.26.255.18:8000`

Если видите "ERR_CONNECTION_REFUSED":
- Сервис не запущен
- Порт заблокирован firewall
- Приложение слушает только localhost (не 0.0.0.0)

Если видите пустую страницу:
- Проверьте консоль браузера (F12) на ошибки JavaScript
- Проверьте, что статические файлы доступны: `http://195.26.255.18:8000/static/css/style.css`

## Для поддержки

Если ничего не помогает, предоставьте:

1. Вывод `sudo systemctl status tor-proxy-pool`
2. Последние 50 строк логов: `sudo journalctl -u tor-proxy-pool -n 50`
3. Результат `curl http://localhost:8000/health`
4. Результат `ls -la /home/runner/work/TOR/TOR/frontend/static/`
