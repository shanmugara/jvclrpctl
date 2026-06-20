// Configuration page — config_script.js

const _autoConfig = { hdr_mode: 'USER3', sdr_mode: 'USER1', automation_enabled: true };

// ── Toast & status bar ────────────────────────────────────────────────────────

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
    if (statusText) statusText.textContent = message;
    if (statusIndicator) {
        statusIndicator.style.backgroundColor = color;
        statusIndicator.style.boxShadow = `0 0 8px ${color}`;
    }
}

async function callAPI(endpoint, method = 'POST', body = null) {
    try {
        updateStatus('Sending…', true);
        const opts = { method };
        if (body !== null) {
            opts.headers = { 'Content-Type': 'application/json' };
            opts.body = JSON.stringify(body);
        }
        const response = await fetch(endpoint, opts);
        const data = await response.json();
        if (data.success) {
            updateStatus('Done', true);
            return data;
        } else {
            updateStatus('Error', false);
            showToast(`Error: ${data.error || 'Unknown error'}`, 'error');
            return null;
        }
    } catch (e) {
        updateStatus('Connection error', false);
        showToast(`Error: ${e.message}`, 'error');
        return null;
    }
}

// ── Picture mode selector ─────────────────────────────────────────────────────

function autoSelectMode(group, val, btn) {
    _autoConfig[group] = val;
    const container = btn.closest('.selector-btns');
    if (container) container.querySelectorAll('.sel-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

function autoSelectEnable(enabled, btn) {
    _autoConfig.automation_enabled = enabled;
    const container = btn.closest('.selector-btns');
    if (container) container.querySelectorAll('.sel-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

// ── Load / Apply ──────────────────────────────────────────────────────────────

async function loadAutomationConfig() {
    try {
        const resp = await fetch('/api/automation/config', { method: 'GET' });
        if (!resp.ok) return;
        const d = await resp.json();
        if (!d.success) return;

        const set = (id, val) => { const el = document.getElementById(id); if (el && val != null) el.value = val; };
        set('cfg-jvc-host',      d.jvc_host);
        set('cfg-jvc-port',      d.jvc_port);
        set('cfg-lumagen-port',  d.lumagen_port);
        set('cfg-poll-interval', d.poll_interval);
        set('cfg-settle-time',   d.settle_time);

        const pathEl = document.getElementById('cfg-file-path');
        if (pathEl) pathEl.textContent = d.config_file || '—';

        _autoConfig.hdr_mode = d.hdr_mode || 'USER3';
        _autoConfig.sdr_mode = d.sdr_mode || 'USER1';
        _autoConfig.automation_enabled = d.automation_enabled !== false;
        ['hdr', 'sdr'].forEach(t => {
            const mode = _autoConfig[`${t}_mode`];
            document.querySelectorAll(`#auto-${t}-mode-btns .sel-btn`).forEach(b => {
                b.classList.toggle('active', b.dataset.val === mode);
            });
        });
        const onBtn  = document.getElementById('auto-enable-on');
        const offBtn = document.getElementById('auto-enable-off');
        if (onBtn && offBtn) {
            onBtn.classList.toggle('active',  _autoConfig.automation_enabled);
            offBtn.classList.toggle('active', !_autoConfig.automation_enabled);
        }

        updateStatus('Config loaded', true);
    } catch (_) {}
}

async function applyAutomationConfig() {
    const g = id => document.getElementById(id)?.value?.trim();
    const body = {
        jvc_host:           g('cfg-jvc-host'),
        jvc_port:           parseInt(g('cfg-jvc-port') || '20554'),
        lumagen_port:       g('cfg-lumagen-port'),
        poll_interval:      parseInt(g('cfg-poll-interval') || '30'),
        settle_time:        parseInt(g('cfg-settle-time') || '4'),
        hdr_mode:           _autoConfig.hdr_mode,
        sdr_mode:           _autoConfig.sdr_mode,
        automation_enabled: _autoConfig.automation_enabled,
    };
    const data = await callAPI('/api/automation/config', 'POST', body);
    if (data) showToast('Configuration saved', 'success');
}

// ── Log viewer ────────────────────────────────────────────────────────────────

let _logRefreshTimer = null;

async function loadLogs() {
    try {
        const resp = await fetch('/api/logs?lines=200');
        if (!resp.ok) return;
        const d = await resp.json();
        const el = document.getElementById('log-viewer');
        if (!el) return;
        if (!d.success) { el.textContent = `Error: ${d.error}`; return; }
        if (!d.lines || d.lines.length === 0) {
            el.textContent = d.note || 'No log entries.';
            return;
        }
        el.textContent = d.lines.join('');
        el.scrollTop = el.scrollHeight;
        const pathEl = document.getElementById('log-file-path');
        if (pathEl && d.path) pathEl.textContent = d.path;
    } catch (_) {}
}

function toggleLogAutoRefresh(enabled) {
    clearInterval(_logRefreshTimer);
    if (enabled) _logRefreshTimer = setInterval(loadLogs, 10000);
}

function clearLogDisplay() {
    const el = document.getElementById('log-viewer');
    if (el) el.textContent = '';
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('load', () => {
    updateStatus('Ready', true);
    loadAutomationConfig();
    loadLogs();
    _logRefreshTimer = setInterval(loadLogs, 10000);
});
