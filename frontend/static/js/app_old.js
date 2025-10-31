// API Configuration
const API_BASE = '/api/v1';
let authToken = localStorage.getItem('token');
let currentUser = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        checkAuth();
    }
});

// Show message
function showMessage(text, type = 'info') {
    const msg = document.getElementById('message');
    msg.textContent = text;
    msg.className = 'message show';
    msg.style.background = type === 'error' ? '#f56565' : type === 'success' ? '#48bb78' : '#2d3748';
    setTimeout(() => msg.classList.remove('show'), 3000);
}

// API request helper
async function apiRequest(endpoint, options = {}) {
    const url = API_BASE + endpoint;
    const headers = {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` }),
        ...options.headers
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        
        return data;
    } catch (error) {
        showMessage(error.message, 'error');
        throw error;
    }
}

// Login
async function login(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const totpToken = document.getElementById('totp-token').value;
    
    try {
        const body = { username, password };
        if (totpToken) body.totp_token = totpToken;
        
        const data = await fetch(API_BASE + '/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(r => r.json());
        
        if (data.access_token) {
            authToken = data.access_token;
            localStorage.setItem('token', authToken);
            
            if (data.require_password_change) {
                showPasswordChangeSection();
            } else {
                await loadDashboard();
            }
        } else if (data.detail && data.detail.includes('2FA')) {
            document.getElementById('totp-group').style.display = 'block';
            showMessage('Enter 2FA code', 'info');
        }
    } catch (error) {
        document.getElementById('login-error').textContent = error.message || 'Login failed';
    }
}

// Change password
async function changePassword(event) {
    event.preventDefault();
    const oldPassword = document.getElementById('old-password').value;
    const newPassword = document.getElementById('new-password').value;
    
    try {
        await fetch(API_BASE + '/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
        });
        
        showMessage('Password changed successfully', 'success');
        await loadDashboard();
    } catch (error) {
        document.getElementById('password-error').textContent = 'Password change failed';
    }
}

// Check authentication
async function checkAuth() {
    try {
        currentUser = await apiRequest('/auth/me');
        if (currentUser.require_password_change) {
            showPasswordChangeSection();
        } else {
            await loadDashboard();
        }
    } catch (error) {
        logout();
    }
}

// Show sections
function showLoginSection() {
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('password-change-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('user-info').style.display = 'none';
}

function showPasswordChangeSection() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('password-change-section').style.display = 'block';
    document.getElementById('dashboard-section').style.display = 'none';
}

async function loadDashboard() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('password-change-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'block';
    document.getElementById('user-info').style.display = 'flex';
    document.getElementById('username').textContent = currentUser?.username || 'Admin';
    
    await refreshData();
}

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    showLoginSection();
}

// Refresh data
async function refreshData() {
    await Promise.all([
        loadStats(),
        loadNodes(),
        loadConfig(),
        loadTokens()
    ]);
}

// Load statistics
async function loadStats() {
    try {
        const stats = await apiRequest('/nodes/stats/summary');
        document.getElementById('total-nodes').textContent = stats.total_nodes;
        document.getElementById('healthy-nodes').textContent = stats.healthy_nodes;
        document.getElementById('health-percent').textContent = stats.health_percentage.toFixed(1) + '%';
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load nodes
async function loadNodes() {
    try {
        const data = await apiRequest('/nodes/');
        const list = document.getElementById('nodes-list');
        list.innerHTML = '';
        
        data.nodes.forEach(node => {
            const card = document.createElement('div');
            card.className = `node-card ${node.is_healthy ? 'healthy' : 'unhealthy'}`;
            card.innerHTML = `
                <div class="node-info">
                    <strong>${node.node_id}</strong><br>
                    SOCKS: ${node.socks_port} | Control: ${node.control_port}<br>
                    ${node.exit_ip ? `Exit: ${node.exit_ip} (${node.exit_country || 'Unknown'})` : 'No exit info'}
                </div>
                <div class="node-actions">
                    <button onclick="rotateNode('${node.node_id}')" class="btn btn-secondary">🔄 Rotate</button>
                </div>
            `;
            list.appendChild(card);
        });
    } catch (error) {
        console.error('Failed to load nodes:', error);
    }
}

// Load configuration
async function loadConfig() {
    try {
        const config = await apiRequest('/config/');
        const info = document.getElementById('config-info');
        info.innerHTML = `
            <div><strong>Pool Size:</strong> ${config.tor_pool_size}</div>
            <div><strong>Base SOCKS Port:</strong> ${config.tor_base_socks_port}</div>
            <div><strong>Countries:</strong> ${config.tor_countries?.join(', ') || 'Any'}</div>
            <div><strong>Auto Rotate:</strong> ${config.auto_rotate_enabled ? 'Enabled' : 'Disabled'}</div>
            <div><strong>Firewall:</strong> ${config.firewall_backend}</div>
            <div><strong>TLS:</strong> ${config.tls_enable ? 'Enabled' : 'Disabled'}</div>
            <div><strong>Domain:</strong> ${config.domain || 'None'}</div>
        `;
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// Load tokens
async function loadTokens() {
    try {
        const data = await apiRequest('/export/tokens');
        const list = document.getElementById('tokens-list');
        list.innerHTML = '';
        
        data.tokens.forEach(token => {
            const card = document.createElement('div');
            card.className = 'token-card';
            card.innerHTML = `
                <div><strong>ID:</strong> ${token.id}</div>
                <div><strong>Description:</strong> ${token.description || 'N/A'}</div>
                <div><strong>Expires:</strong> ${new Date(token.expires_at).toLocaleString()}</div>
                <div><strong>Status:</strong> ${token.is_revoked ? 'Revoked' : 'Active'}</div>
                <div><strong>Uses:</strong> ${token.use_count}</div>
                ${!token.is_revoked ? `<button onclick="revokeToken(${token.id})" class="btn btn-danger">Revoke</button>` : ''}
            `;
            list.appendChild(card);
        });
    } catch (error) {
        console.error('Failed to load tokens:', error);
    }
}

// Actions
async function rotateAll() {
    try {
        await apiRequest('/nodes/rotate', { method: 'POST' });
        showMessage('All circuits rotated', 'success');
        await refreshData();
    } catch (error) {
        showMessage('Failed to rotate circuits', 'error');
    }
}

async function rotateNode(nodeId) {
    try {
        await apiRequest(`/nodes/${nodeId}/rotate`, { method: 'POST' });
        showMessage(`Circuit rotated for ${nodeId}`, 'success');
        await loadNodes();
    } catch (error) {
        showMessage('Failed to rotate circuit', 'error');
    }
}

async function scalePool() {
    const size = parseInt(document.getElementById('scale-size').value);
    if (size < 1 || size > 100) {
        showMessage('Pool size must be between 1 and 100', 'error');
        return;
    }
    
    try {
        await apiRequest(`/nodes/scale?new_size=${size}`, { method: 'POST' });
        showMessage(`Pool scaled to ${size} nodes`, 'success');
        await refreshData();
    } catch (error) {
        showMessage('Failed to scale pool', 'error');
    }
}

async function applyFirewall() {
    try {
        await apiRequest('/config/firewall/apply', { method: 'POST' });
        showMessage('Firewall rules applied', 'success');
    } catch (error) {
        showMessage('Failed to apply firewall rules', 'error');
    }
}

async function createToken() {
    const description = document.getElementById('token-description').value;
    try {
        const body = {};
        if (description) body.description = description;
        
        const data = await fetch(API_BASE + '/export/tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(body)
        }).then(r => r.json());
        
        const card = document.createElement('div');
        card.className = 'token-card';
        card.innerHTML = `
            <div><strong>New Token Created!</strong></div>
            <div class="token-value">${data.token}</div>
            <div><strong>Expires:</strong> ${new Date(data.expires_at).toLocaleString()}</div>
            <div><strong>Download URLs:</strong></div>
            <div>TXT: /api/v1/export/download/txt?token=${data.token}</div>
            <div>CSV: /api/v1/export/download/csv?token=${data.token}</div>
            <div>JSON: /api/v1/export/download/json?token=${data.token}</div>
        `;
        document.getElementById('tokens-list').prepend(card);
        document.getElementById('token-description').value = '';
        showMessage('Token created successfully', 'success');
    } catch (error) {
        showMessage('Failed to create token', 'error');
    }
}

async function revokeToken(tokenId) {
    if (!confirm('Revoke this token?')) return;
    
    try {
        await apiRequest(`/export/tokens/${tokenId}`, { method: 'DELETE' });
        showMessage('Token revoked', 'success');
        await loadTokens();
    } catch (error) {
        showMessage('Failed to revoke token', 'error');
    }
}

// Tab switching
function showTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}
