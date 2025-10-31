// API Configuration
const API_BASE = '/api/v1';
let authToken = localStorage.getItem('token');
let currentUser = null;
let optionsMenuOpen = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        checkAuth();
    }
    
    // Close options menu when clicking outside
    document.addEventListener('click', (e) => {
        if (optionsMenuOpen && !e.target.closest('#options-btn') && !e.target.closest('#options-menu')) {
            document.getElementById('options-menu').style.display = 'none';
            optionsMenuOpen = false;
        }
    });
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
                showChangePasswordModal();
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

// Options menu
function showOptionsMenu() {
    const menu = document.getElementById('options-menu');
    optionsMenuOpen = !optionsMenuOpen;
    menu.style.display = optionsMenuOpen ? 'block' : 'none';
}

// Modals
function showChangePasswordModal() {
    document.getElementById('password-modal').style.display = 'flex';
    optionsMenuOpen = false;
    document.getElementById('options-menu').style.display = 'none';
}

function showWhitelistModal() {
    document.getElementById('whitelist-modal').style.display = 'flex';
    loadWhitelist();
    optionsMenuOpen = false;
    document.getElementById('options-menu').style.display = 'none';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
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
        closeModal('password-modal');
        document.getElementById('old-password').value = '';
        document.getElementById('new-password').value = '';
    } catch (error) {
        document.getElementById('password-error').textContent = 'Password change failed';
    }
}

// IP Whitelist management
async function loadWhitelist() {
    try {
        const data = await apiRequest('/config/whitelist');
        const list = document.getElementById('whitelist-list');
        list.innerHTML = '';
        
        if (data.whitelist && data.whitelist.length > 0) {
            data.whitelist.forEach(ip => {
                const item = document.createElement('div');
                item.className = 'whitelist-item';
                item.innerHTML = `
                    <span>${ip}</span>
                    <button onclick="removeWhitelistIP('${ip}')" class="btn btn-sm btn-danger">Remove</button>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = '<p style="color:#718096;font-size:13px;">No whitelist IPs configured. Add IPs to restrict access.</p>';
        }
    } catch (error) {
        console.error('Failed to load whitelist:', error);
    }
}

async function addWhitelistIP() {
    const ip = document.getElementById('whitelist-ip').value.trim();
    if (!ip) {
        showMessage('Please enter an IP address', 'error');
        return;
    }
    
    try {
        await apiRequest('/config/whitelist', {
            method: 'POST',
            body: JSON.stringify({ ip })
        });
        showMessage('IP added to whitelist', 'success');
        document.getElementById('whitelist-ip').value = '';
        await loadWhitelist();
    } catch (error) {
        showMessage('Failed to add IP to whitelist', 'error');
    }
}

async function removeWhitelistIP(ip) {
    if (!confirm(`Remove ${ip} from whitelist?`)) return;
    
    try {
        await apiRequest(`/config/whitelist/${encodeURIComponent(ip)}`, {
            method: 'DELETE'
        });
        showMessage('IP removed from whitelist', 'success');
        await loadWhitelist();
    } catch (error) {
        showMessage('Failed to remove IP from whitelist', 'error');
    }
}

// Check authentication
async function checkAuth() {
    try {
        currentUser = await apiRequest('/auth/me');
        if (currentUser.require_password_change) {
            showChangePasswordModal();
        } else {
            await loadDashboard();
        }
    } catch (error) {
        logout();
    }
}

// Show sections
function showLoginSection() {
    document.getElementById('login-section').style.display = 'flex';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('user-info').style.display = 'none';
}

async function loadDashboard() {
    document.getElementById('login-section').style.display = 'none';
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
        loadNodesTable(),
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

// Load nodes as table
async function loadNodesTable() {
    try {
        const data = await apiRequest('/nodes/');
        const tbody = document.getElementById('nodes-table-body');
        tbody.innerHTML = '';
        
        if (data.nodes && data.nodes.length > 0) {
            data.nodes.forEach(node => {
                const tr = document.createElement('tr');
                tr.className = node.is_healthy ? 'healthy' : 'unhealthy';
                tr.innerHTML = `
                    <td><strong>${node.node_id}</strong></td>
                    <td>${node.socks_port}</td>
                    <td>${node.control_port}</td>
                    <td>${node.exit_ip || 'N/A'}</td>
                    <td>${node.exit_country || 'Unknown'}</td>
                    <td>
                        <span class="status-badge ${node.is_healthy ? 'status-healthy' : 'status-unhealthy'}">
                            ${node.is_healthy ? '✓ Healthy' : '✗ Unhealthy'}
                        </span>
                    </td>
                    <td>
                        <button onclick="rotateNode('${node.node_id}')" class="btn btn-sm btn-secondary">🔄 Rotate</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#718096;">No nodes available</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load nodes:', error);
        const tbody = document.getElementById('nodes-table-body');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#f56565;">Failed to load nodes</td></tr>';
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
        
        if (data.tokens && data.tokens.length > 0) {
            data.tokens.forEach(token => {
                const card = document.createElement('div');
                card.className = 'token-card';
                card.innerHTML = `
                    <div><strong>ID:</strong> ${token.id}</div>
                    <div><strong>Description:</strong> ${token.description || 'N/A'}</div>
                    <div><strong>Expires:</strong> ${new Date(token.expires_at).toLocaleString()}</div>
                    <div><strong>Status:</strong> ${token.is_revoked ? 'Revoked' : 'Active'}</div>
                    <div><strong>Uses:</strong> ${token.use_count}</div>
                    ${!token.is_revoked ? `<button onclick="revokeToken(${token.id})" class="btn btn-sm btn-danger">Revoke</button>` : ''}
                `;
                list.appendChild(card);
            });
        } else {
            list.innerHTML = '<p style="color:#718096;font-size:13px;">No tokens created yet.</p>';
        }
    } catch (error) {
        console.error('Failed to load tokens:', error);
    }
}

// Bottom tabs
function showBottomTab(tabName) {
    // Hide all panels
    document.getElementById('config-panel').style.display = 'none';
    document.getElementById('export-panel').style.display = 'none';
    
    // Remove active class from all buttons
    document.querySelectorAll('.bottom-tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Show selected panel
    const panel = document.getElementById(`${tabName}-panel`);
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        event.target.classList.add('active');
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
        await loadNodesTable();
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
        
        showMessage('Token created successfully', 'success');
        document.getElementById('token-description').value = '';
        await loadTokens();
    } catch (error) {
        showMessage('Failed to create token', 'error');
    }
}

async function revokeToken(tokenId) {
    if (!confirm('Are you sure you want to revoke this token?')) return;
    
    try {
        await apiRequest(`/export/tokens/${tokenId}/revoke`, { method: 'POST' });
        showMessage('Token revoked', 'success');
        await loadTokens();
    } catch (error) {
        showMessage('Failed to revoke token', 'error');
    }
}

// Show Configuration Panel (Modal)
function showConfigPanel() {
    loadConfig();
    document.getElementById('config-modal').style.display = 'flex';
}

// Show Export Panel (Modal)
function showExportPanel() {
    loadTokens();
    document.getElementById('export-modal').style.display = 'flex';
}

// Set Exit Countries
async function setExitCountries() {
    const select = document.getElementById('exit-countries');
    const countries = Array.from(select.selectedOptions).map(opt => opt.value);
    
    if (countries.length === 0) {
        showMessage('Please select at least one country', 'error');
        return;
    }
    
    try {
        await apiRequest('/config/tor/countries', {
            method: 'POST',
            body: JSON.stringify({ countries: countries.join(','), strict_nodes: true })
        });
        showMessage(`Exit countries set to: ${countries.join(', ')}`, 'success');
        await refreshData();
    } catch (error) {
        showMessage('Failed to set exit countries', 'error');
    }
}
