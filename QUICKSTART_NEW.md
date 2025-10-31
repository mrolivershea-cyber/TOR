# Tor Proxy Pool - Quick Start

## ⚡ EASIEST WAY TO START (1 Command)

```bash
cd TOR
./START.sh
```

**That's it!** The admin panel will start immediately.

Open in your browser: `http://your-server-ip:8000`  
Login: **admin** / **admin**

Press `Ctrl+C` to stop.

---

## 🔧 If START.sh Doesn't Work

### Manual Start (2 Commands)

```bash
# Install dependencies (only needed once)
pip3 install --user fastapi uvicorn

# Start the server
python3 test_server.py
```

Open: `http://your-server-ip:8000`

---

## 🐧 Run as Background Service (Optional)

If you want the server to run in the background:

```bash
# Install as systemd service
sudo ./INSTALL_SIMPLE.sh

# Manage service
sudo systemctl status tor-proxy-test
sudo systemctl restart tor-proxy-test
sudo journalctl -u tor-proxy-test -f  # View logs
```

---

## ❓ Troubleshooting

### "Command 'pip3' not found"

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y python3-pip

# CentOS/RHEL/Fedora
sudo yum install -y python3-pip
```

### "Import error: No module named 'fastapi'"

```bash
pip3 install --user fastapi uvicorn
```

### "Port 8000 already in use"

```bash
# Find and kill the process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Admin panel doesn't load

1. Check if server is running:
   ```bash
   ps aux | grep test_server
   ```

2. Check firewall (must allow port 8000):
   ```bash
   sudo ufw allow 8000
   # or
   sudo firewall-cmd --add-port=8000/tcp --permanent
   sudo firewall-cmd --reload
   ```

3. Check if you can access locally:
   ```bash
   curl http://localhost:8000
   ```

---

## 📖 What's Included

This test server provides:
- ✅ Working admin panel (HTML/CSS/JS)
- ✅ Login screen (admin/admin)
- ✅ Dashboard with mock statistics
- ✅ Node management interface
- ✅ Configuration viewer
- ✅ Export token management

**Note:** This is a TEST server for verifying the UI works.  
It does NOT provide actual Tor proxy functionality.  
For full Tor proxy pool, see `docs/installation.md`.

---

## 🚀 Next Steps

After verifying the admin panel works:

1. **Read** `docs/installation.md` for full installation
2. **Configure** `.env.example` → `.env` with your settings
3. **Install** PostgreSQL, Redis, and Tor for full functionality
4. **Deploy** using Docker or systemd for production

---

## 📞 Getting Help

If you're still having issues:

1. Check that Python 3.7+ is installed: `python3 --version`
2. Check that the TOR directory has `frontend/static/` folder
3. Look for errors in the console output
4. Check `sudo journalctl -u tor-proxy-test -f` for systemd logs

The test server is designed to work with minimal dependencies.  
If it doesn't start, there may be a Python or file system issue.
