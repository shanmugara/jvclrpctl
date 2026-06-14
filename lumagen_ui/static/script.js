// Lumagen Web UI JavaScript

// API Base URL
const API_BASE = '';

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Update status indicator
function updateStatus(message, success = true) {
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.getElementById('status-indicator');
    const color = success ? '#4CAF50' : '#f44336';
    statusText.textContent = message;
    statusIndicator.style.backgroundColor = color;
    statusIndicator.style.boxShadow = `0 0 8px ${color}`;
}

// Generic API call function
async function callAPI(endpoint, method = 'POST') {
    try {
        updateStatus('Sending command...', true);
        const response = await fetch(API_BASE + endpoint, { method });
        const data = await response.json();
        
        if (data.success) {
            updateStatus('Command successful', true);
            showToast('Command executed successfully', 'success');
            return data;
        } else {
            updateStatus('Command failed', false);
            showToast(`Error: ${data.error || 'Unknown error'}`, 'error');
            return null;
        }
    } catch (error) {
        updateStatus('Connection error', false);
        showToast(`Error: ${error.message}`, 'error');
        console.error('API Error:', error);
        return null;
    }
}

// Power Control
async function powerControl(action) {
    const actionText = action === 'on' ? 'Powering On' : 'Entering Standby';
    updateStatus(actionText, true);
    await callAPI(`/api/power/${action}`);
}

// Input Selection
async function selectInput(inputNum) {
    updateStatus(`Selecting Input ${inputNum}`, true);
    await callAPI(`/api/input/${inputNum}`);
}

// Memory Selection
async function selectMemory(memory) {
    updateStatus(`Selecting Memory ${memory}`, true);
    await callAPI(`/api/memory/${memory}`);
}

// Aspect Ratio
async function setAspect(aspect) {
    updateStatus(`Setting aspect to ${aspect}`, true);
    await callAPI(`/api/aspect/${aspect}`);
}

// Zoom Control
async function zoomControl(action) {
    updateStatus(`Zoom ${action}`, true);
    await callAPI(`/api/zoom/${action}`);
}

// Output Mode
async function setOutput(mode) {
    updateStatus(`Setting output to ${mode}`, true);
    await callAPI(`/api/output/${mode}`);
}

// Test Pattern
async function testPattern(action) {
    updateStatus(`Test pattern: ${action}`, true);
    await callAPI(`/api/test-pattern/${action}`);
}

// Save Configuration
async function saveConfig() {
    updateStatus('Saving configuration...', true);
    const result = await callAPI('/api/save');
    if (result) {
        showToast('Configuration saved successfully!', 'success');
    }
}

// Get Status
async function getStatus() {
    try {
        updateStatus('Fetching status...', true);
        const response = await fetch(API_BASE + '/api/status', { method: 'GET' });
        const data = await response.json();
        
        if (data.success) {
            const statusDisplay = document.getElementById('status-display');
            statusDisplay.innerHTML = `
<strong>Current Input:</strong> ${data.current_input}

<strong>Status:</strong>
${data.status}

<strong>Info:</strong>
${data.info}
            `.trim();
            updateStatus('Status retrieved', true);
            showToast('Status updated', 'success');
        } else {
            updateStatus('Failed to get status', false);
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        updateStatus('Connection error', false);
        showToast(`Error: ${error.message}`, 'error');
        console.error('Status Error:', error);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Only trigger if not typing in an input field
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    switch(event.key) {
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
            selectInput(parseInt(event.key));
            break;
        case 'a':
        case 'A':
            selectMemory('A');
            break;
        case 'b':
        case 'B':
            selectMemory('B');
            break;
        case 'c':
        case 'C':
            selectMemory('C');
            break;
        case 'd':
        case 'D':
            selectMemory('D');
            break;
        case '+':
        case '=':
            zoomControl('in');
            break;
        case '-':
        case '_':
            zoomControl('out');
            break;
        case 's':
        case 'S':
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                saveConfig();
            }
            break;
    }
});

// ── HDR Automation ────────────────────────────────────────────────────────

function _applyAutomationStatus(data) {
    const indicator = document.getElementById('automation-indicator');
    const statusText = document.getElementById('automation-status-text');
    const contentEl = document.getElementById('automation-content');
    const btn = document.getElementById('automation-toggle-btn');

    if (!indicator) return;

    if (data.running) {
        indicator.style.backgroundColor = '#4CAF50';
        indicator.style.boxShadow = '0 0 8px #4CAF50';
        statusText.textContent = 'Running';
        btn.textContent = 'Stop';
        btn.classList.remove('btn-start');
        btn.classList.add('btn-stop');
    } else {
        indicator.style.backgroundColor = '#888';
        indicator.style.boxShadow = 'none';
        statusText.textContent = 'Stopped';
        btn.textContent = 'Start';
        btn.classList.remove('btn-stop');
        btn.classList.add('btn-start');
    }

    const modeLabels = { HDR: 'HDR', SDR: 'SDR', NA: '—', ERR: 'ERR' };
    contentEl.textContent = data.content ? (modeLabels[data.content] || data.content) : '';
}

async function pollAutomationStatus() {
    try {
        const resp = await fetch('/api/automation/status', { method: 'GET' });
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.success) _applyAutomationStatus(data);
    } catch (_) { /* network hiccup — silently skip */ }
}

async function toggleAutomation() {
    const btn = document.getElementById('automation-toggle-btn');
    const isRunning = btn.classList.contains('btn-stop');
    const endpoint = isRunning ? '/api/automation/stop' : '/api/automation/start';
    try {
        const resp = await fetch(endpoint, { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            _applyAutomationStatus(data);
            showToast(data.running ? 'Automation started' : 'Automation stopped',
                      data.running ? 'success' : 'info');
        } else {
            showToast(`Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (e) {
        showToast(`Error: ${e.message}`, 'error');
    }
}

// Initialize on load
window.addEventListener('load', () => {
    updateStatus('Ready', true);
    pollAutomationStatus();
    setInterval(pollAutomationStatus, 5000);
    console.log('Lumagen Web UI initialized');
});
