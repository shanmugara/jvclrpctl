// Lumagen Web UI — script.js

const API_BASE = '';

// ── Tab switching ─────────────────────────────────────────────────────────────

function switchTab(name) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.lumagen-tab').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    document.querySelector('.lumagen-tab[data-tab="' + name + '"]').classList.add('active');
    if (name === 'status') refreshStatus();
}

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

// ── Generic API helpers ───────────────────────────────────────────────────────

async function callAPI(endpoint, method = 'POST', body = null) {
    try {
        updateStatus('Sending command…', true);
        const opts = { method };
        if (body !== null) {
            opts.headers = { 'Content-Type': 'application/json' };
            opts.body = JSON.stringify(body);
        }
        const response = await fetch(API_BASE + endpoint, opts);
        const data = await response.json();
        if (data.success) {
            updateStatus('Command successful', true);
            showToast('Command sent', 'success');
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

// ── Power ─────────────────────────────────────────────────────────────────────

function confirmPowerControl(action) {
    const label = action === 'on' ? 'Power ON' : 'Standby';
    if (!confirm(`${label} the Lumagen Radiance?`)) return;
    callAPI(`/api/power/${action}`);
}

// ── Input / Memory / Zoom / Output / Save ─────────────────────────────────────

async function selectInput(n)   { updateStatus(`Selecting Input ${n}`, true); await callAPI(`/api/input/${n}`); }
async function selectMemory(m)  { updateStatus(`Selecting Memory ${m}`, true); await callAPI(`/api/memory/${m}`); }
async function zoomControl(a)   { updateStatus(`Zoom ${a}`, true); await callAPI(`/api/zoom/${a}`); }
async function setOutput(mode)  { updateStatus(`Output → ${mode}`, true); await callAPI(`/api/output/${mode}`); }
async function saveConfig()     { updateStatus('Saving…', true); await callAPI('/api/save'); }
async function setAspect(asp)   { updateStatus(`Aspect → ${asp}`, true); await callAPI(`/api/aspect/${encodeURIComponent(asp)}`); }

// ── Navigation ────────────────────────────────────────────────────────────────

async function navigate(action) { await callAPI(`/api/navigate/${action}`); }

async function sendDigit(d) {
    updateStatus(`Sending digit ${d}`, true);
    await callAPI(`/api/navigate/digit_${d}`);
}

// ── Test Patterns ─────────────────────────────────────────────────────────────

async function sendPattern(group, sub) {
    const ire = parseInt(document.getElementById('pattern-ire')?.value || '100', 10);
    updateStatus(`Pattern ${group},${sub} @ ${ire} IRE`, true);
    await callAPI('/api/test-pattern-full', 'POST', { group, sub, ire });
}

async function patternOff() {
    updateStatus('Exiting pattern', true);
    await callAPI('/api/test-pattern/off');
}

// ── Settings: Game Mode ───────────────────────────────────────────────────────

async function setGameMode(state) {
    updateStatus(`Game mode → ${state ? 'On' : 'Off'}`, true);
    const data = await callAPI(`/api/game-mode/${state}`);
    if (data) _applyGameModeUI(data.game_mode);
}

function _applyGameModeUI(on) {
    document.getElementById('game-off-btn')?.classList.toggle('active-off', !on);
    document.getElementById('game-on-btn')?.classList.toggle('active-on',   on);
}

// ── Settings: HDMI Hotplug ────────────────────────────────────────────────────

async function hdmiHotplug(inputId) {
    updateStatus(`Hotplug HDMI ${inputId}`, true);
    await callAPI(`/api/hdmi-hotplug/${inputId}`);
}

// ── Settings: Sharpness ───────────────────────────────────────────────────────

let _sharpEnabled = true;
let _sharpLevel = 4;
let _sharpSens = 'N';

function selectSharpEnable(en) {
    _sharpEnabled = en;
    document.getElementById('sharp-on')?.classList.toggle('active', en);
    document.getElementById('sharp-off')?.classList.toggle('active', !en);
}

function selectSharpLevel(lv) {
    _sharpLevel = lv;
    document.querySelectorAll('#sharp-levels .sel-btn').forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.val) === lv);
    });
}

function selectSharpSens(s) {
    _sharpSens = s;
    document.getElementById('sens-N')?.classList.toggle('active', s === 'N');
    document.getElementById('sens-H')?.classList.toggle('active', s === 'H');
}

async function applySharpness() {
    updateStatus('Applying sharpness…', true);
    await callAPI('/api/sharpness', 'POST', {
        enabled: _sharpEnabled,
        level: _sharpLevel,
        sensitivity: _sharpSens,
    });
}

// ── Settings: Output Format ───────────────────────────────────────────────────

async function setOutputFormat(fmt) {
    const names = { 0: 'YCbCr 4:2:2', 1: 'YCbCr 4:4:4', 2: 'RGB Video', 3: 'RGB PC', 8: 'Auto Max', 9: 'Auto' };
    updateStatus(`Output format → ${names[fmt] || fmt}`, true);
    await callAPI(`/api/output-format/${fmt}`);
}

// ── Settings: CMS / Style ─────────────────────────────────────────────────────

const _cmsState = { mode: 'K', cms_sdr: 'K', cms_hdr: 'K', style: 'K' };

function cmsSelect(group, val, btn) {
    _cmsState[group] = val;
    const container = btn.closest('.selector-btns');
    if (container) {
        container.querySelectorAll('.sel-btn').forEach(b => b.classList.remove('active'));
    }
    btn.classList.add('active');
}

async function applyCmsStyle() {
    updateStatus('Applying CMS / Style…', true);
    await callAPI('/api/cms-style', 'POST', { ..._cmsState });
}

// ── Settings: PIP ─────────────────────────────────────────────────────────────

async function pipControl(action) {
    updateStatus(`PIP → ${action}`, true);
    await callAPI(`/api/pip/${action}`);
}

// ── Settings: Deinterlace ─────────────────────────────────────────────────────

async function setDeinterlace(mode) {
    const names = { 0: 'Auto', 1: 'Film', 2: 'Video' };
    updateStatus(`Deinterlace → ${names[mode]}`, true);
    const data = await callAPI(`/api/deinterlace/${mode}`);
    if (data) {
        [0, 1, 2].forEach(m => {
            document.getElementById(`deint-${m}`)?.classList.toggle('active-mode', m === mode);
        });
    }
}

// ── Status Tab ────────────────────────────────────────────────────────────────

let _statusAutoTimer = null;

function toggleStatusAutoRefresh(on) {
    if (_statusAutoTimer) { clearInterval(_statusAutoTimer); _statusAutoTimer = null; }
    if (on) _statusAutoTimer = setInterval(refreshStatus, 5000);
}

function _sv(id, val, fallback = '—') {
    const el = document.getElementById(id);
    if (el) el.textContent = (val !== undefined && val !== null && val !== '') ? val : fallback;
}

function _badge(id, text, cls) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = `<span class="badge ${cls}">${text}</span>`;
}

async function refreshStatus() {
    try {
        updateStatus('Fetching status…', true);
        const resp = await fetch(API_BASE + '/api/rich-status', { method: 'GET' });
        const d = await resp.json();
        if (!d.success) { updateStatus('Status error', false); return; }

        // Source
        _sv('ss-input-status', d.input_status);
        const inp = (d.virtual_input && d.physical_input)
            ? `Virtual ${d.virtual_input} → Physical ${d.physical_input}` : '—';
        _sv('ss-input', inp);
        _sv('ss-source-detail', d.source_detail);
        _badge('ss-hdr', d.hdr_label || '—', d.hdr ? 'badge-hdr' : 'badge-sdr');

        const aspNls = d.input_aspect
            ? `${d.input_aspect}${d.nls_mode ? ' + NLS' : ''}`
            : (d.source_aspect ? `${d.source_aspect}:1` : '—');
        _sv('ss-aspect', aspNls);
        _sv('ss-scan', d.source_scan);

        // Output
        _sv('ss-out-mode', d.output_mode_name);
        const outRes = (d.output_resolution && d.output_rate)
            ? `${d.output_resolution}p @ ${d.output_rate} Hz` : '—';
        _sv('ss-out-res', outRes);
        _sv('ss-out-fmt', d.output_format);
        _sv('ss-out-cs', d.output_colorspace);
        _sv('ss-out-asp', d.output_aspect ? `${d.output_aspect}` : '—');
        _sv('ss-cms-style',
            (d.cms !== undefined && d.style !== undefined) ? `CMS ${d.cms}  /  Style ${d.style}` : '—');
        _sv('ss-out-scan', d.output_scan);

        // Device
        _sv('ss-model', d.model);
        _sv('ss-firmware', d.firmware);
        _sv('ss-serial', d.serial);
        _badge('ss-game-mode',
            d.game_mode === undefined ? '—' : (d.game_mode ? 'On' : 'Off'),
            d.game_mode ? 'badge-on' : 'badge-off');

        updateStatus('Status updated', true);
    } catch (e) {
        updateStatus('Status fetch error', false);
    }
}

// ── HDR Automation ────────────────────────────────────────────────────────────

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
    } catch (_) {}
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

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', (event) => {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
    switch (event.key) {
        case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8':
            selectInput(parseInt(event.key)); break;
        case 'a': case 'A': selectMemory('A'); break;
        case 'b': case 'B': selectMemory('B'); break;
        case 'c': case 'C': selectMemory('C'); break;
        case 'd': case 'D': selectMemory('D'); break;
        case '+': case '=': zoomControl('in'); break;
        case '-': case '_': zoomControl('out'); break;
        case 's': case 'S':
            if (event.ctrlKey || event.metaKey) { event.preventDefault(); saveConfig(); }
            break;
        case 'ArrowUp':    navigate('up');    break;
        case 'ArrowDown':  navigate('down');  break;
        case 'ArrowLeft':  navigate('left');  break;
        case 'ArrowRight': navigate('right'); break;
        case 'Enter':      navigate('ok');    break;
        case 'Escape':     navigate('exit');  break;
        case 'm': case 'M': navigate('menu'); break;
    }
});

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('load', () => {
    updateStatus('Ready', true);
    pollAutomationStatus();
    setInterval(pollAutomationStatus, 5000);
});
