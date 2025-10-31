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

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
        tab.style.display = 'none';
    });
    
    // Show selected tab
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
        targetTab.style.display = 'block';
    }
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Load data for the tab
    if (tabName === 'logs') {
        loadLogs();
    } else if (tabName === 'nodes') {
        loadNodes();
    }
}

// Enhanced node loading with status colors and simplified IDs
async function loadNodesEnhanced() {
    try {
        const data = await apiRequest('/nodes');
        const tbody = document.getElementById('nodes-table-body');
        
        if (!data.nodes || data.nodes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No nodes available</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.nodes.map((node, index) => {
            const nodeNum = index + 1;
            const status = getNodeStatus(node);
            const statusClass = `status-${status.type}`;
            const rowClass = `node-row-${status.type}`;
            const countryFlag = getCountryFlag(node.country);
            const serverIP = node.server_ip || window.location.hostname;
            
            return `
                <tr class="${rowClass}">
                    <td><strong>${nodeNum}</strong></td>
                    <td>${node.socks_port}</td>
                    <td>${node.control_port}</td>
                    <td>${node.exit_ip || 'Pending...'}</td>
                    <td><code>${serverIP}</code></td>
                    <td>${countryFlag} ${node.country || 'Unknown'}</td>
                    <td class="${statusClass}">${status.icon} ${status.label}</td>
                    <td>
                        <button onclick="rotateNode('${node.node_id}')" class="btn btn-sm btn-secondary">
                            🔄 Rotate
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading nodes:', error);
    }
}

// Determine node status with 5 states
function getNodeStatus(node) {
    if (!node.status) {
        return { type: 'paused', label: 'Paused', icon: '⏸' };
    }
    
    const status = node.status.toLowerCase();
    
    if (status.includes('rotating') || status.includes('changing')) {
        return { type: 'rotating', label: 'Rotating', icon: '🔄' };
    }
    
    if (!node.exit_ip || status.includes('down') || status.includes('error')) {
        return { type: 'unhealthy', label: 'Unhealthy', icon: '❌' };
    }
    
    if (node.latency_ms && node.latency_ms > 500) {
        return { type: 'slow', label: 'Slow', icon: '⚠️' };
    }
    
    if (status.includes('healthy') || status.includes('up') || node.exit_ip) {
        return { type: 'healthy', label: 'Healthy', icon: '✅' };
    }
    
    return { type: 'unhealthy', label: 'Unknown', icon: '❓' };
}

// Get country flag emoji
function getCountryFlag(countryCode) {
    if (!countryCode || countryCode.length !== 2) return '🌐';
    
    const flags = {
        'US': '🇺🇸', 'DE': '🇩🇪', 'GB': '🇬🇧', 'FR': '🇫🇷',
        'NL': '🇳🇱', 'CA': '🇨🇦', 'SE': '🇸🇪', 'CH': '🇨🇭',
        'JP': '🇯🇵', 'SG': '🇸🇬', 'AU': '🇦🇺', 'IT': '🇮🇹',
        'ES': '🇪🇸', 'PL': '🇵🇱', 'RU': '🇷🇺', 'BR': '🇧🇷'
    };
    
    return flags[countryCode.toUpperCase()] || '🌐';
}

// Load audit logs
let allLogs = [];

async function loadLogs() {
    try {
        // Mock data for now - replace with actual API call
        allLogs = generateMockLogs();
        displayLogs(allLogs);
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function generateMockLogs() {
    const actions = [
        { action: 'login', details: 'Successful login', user: 'admin' },
        { action: 'node_rotate', details: 'Rotated node #5', user: 'admin' },
        { action: 'node_scale', details: 'Scaled pool to 50 nodes', user: 'admin' },
        { action: 'config_change', details: 'Updated country list to US,DE', user: 'admin' },
        { action: 'firewall_update', details: 'Applied firewall rules', user: 'system' },
        { action: 'password_change', details: 'Changed password', user: 'admin' }
    ];
    
    return actions.map((log, index) => ({
        ...log,
        timestamp: new Date(Date.now() - (index * 600000)).toISOString(),
        ip: '192.168.1.' + (Math.floor(Math.random() * 255))
    }));
}

function displayLogs(logs) {
    const tbody = document.getElementById('logs-table-body');
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No logs available</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td class="log-timestamp">${new Date(log.timestamp).toLocaleString()}</td>
            <td class="log-user">${log.user}</td>
            <td class="log-action">${log.action.replace(/_/g, ' ').toUpperCase()}</td>
            <td class="log-details">${log.details}</td>
            <td class="log-ip">${log.ip}</td>
        </tr>
    `).join('');
}

function filterLogs() {
    const filter = document.getElementById('log-filter').value;
    const filtered = filter ? allLogs.filter(log => log.action === filter) : allLogs;
    displayLogs(filtered);
}

function refreshLogs() {
    loadLogs();
    showMessage('Logs refreshed', 'success');
}

// Override original loadNodes with enhanced version
const originalLoadNodes = window.loadNodes;
window.loadNodes = loadNodesEnhanced;

// Auto-refresh nodes every 30 seconds
let autoRefreshInterval = null;

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    
    autoRefreshInterval = setInterval(() => {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'nodes-tab') {
            loadNodesEnhanced();
        }
    }, 30000); // 30 seconds
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Start auto-refresh when dashboard loads
const originalLoadDashboard = window.loadDashboard;
if (originalLoadDashboard) {
    window.loadDashboard = async function() {
        await originalLoadDashboard();
        startAutoRefresh();
    };
}
