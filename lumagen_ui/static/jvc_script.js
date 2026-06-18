// JVC Projector Web UI

// ── Power LED ─────────────────────────────────────────────────────────────────

function _setJvcLed(state) {
    const el = document.getElementById('jvc-power-led');
    if (!el) return;
    el.classList.remove('led-on', 'led-off');
    if (state === 'on')  el.classList.add('led-on');
    if (state === 'off') el.classList.add('led-off');
}

async function pollJvcPower() {
    try {
        const resp = await fetch('/api/jvc/status', { method: 'GET' });
        if (!resp.ok) return;
        const d = await resp.json();
        if (d.success && d.power != null)
            _setJvcLed(String(d.power).toLowerCase() === 'on' ? 'on' : 'off');
    } catch (_) {}
}

// ─────────────────────────────────────────────────────────────────────────────

function confirmPower(action) {
    const label = action === 'on' ? 'Power ON' : 'Power OFF';
    if (!window.confirm(`${label} the JVC projector?`)) return;
    jvcPower(action);
}

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

function updateStatus(message, success = true) {
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.getElementById('status-indicator');
    const color = success ? '#4CAF50' : '#f44336';
    statusText.textContent = message;
    statusIndicator.style.backgroundColor = color;
    statusIndicator.style.boxShadow = `0 0 8px ${color}`;
}

async function callAPI(endpoint, method = 'POST') {
    try {
        updateStatus('Sending command…', true);
        const response = await fetch(endpoint, { method });
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
        return null;
    }
}

async function jvcPower(action) {
    updateStatus(action === 'on' ? 'Powering On…' : 'Powering Off…', true);
    const data = await callAPI(`/api/jvc/power/${action}`);
    if (data) _setJvcLed(action === 'on' ? 'on' : 'off');
}

async function jvcInput(source) {
    updateStatus(`Selecting ${source.toUpperCase()}…`, true);
    await callAPI(`/api/jvc/input/${source}`);
}

async function jvcPictureMode(mode) {
    updateStatus(`Setting picture mode…`, true);
    await callAPI(`/api/jvc/picture-mode/${mode}`);
}

async function jvcStatus() {
    try {
        updateStatus('Querying projector…', true);
        const response = await fetch('/api/jvc/status', { method: 'GET' });
        const data = await response.json();
        const display = document.getElementById('status-display');
        if (data.success) {
            display.textContent =
                `Power:         ${data.power}\n` +
                `Input:         ${data.input}\n` +
                `Picture Mode:  ${data.picture_mode}`;
            updateStatus('Status retrieved', true);
            showToast('Status updated', 'success');
        } else {
            display.textContent = `Error: ${data.error}`;
            updateStatus('Failed to get status', false);
            showToast(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        updateStatus('Connection error', false);
        showToast(`Error: ${error.message}`, 'error');
    }
}

window.addEventListener('load', () => {
    updateStatus('Ready', true);
    pollJvcPower();
    setInterval(pollJvcPower, 15000);
});
