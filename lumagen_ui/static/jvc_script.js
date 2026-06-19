'use strict';

// ── Tab switching ────────────────────────────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.lumagen-tab').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById('tab-' + name);
    if (panel) panel.classList.add('active');
    const btn = document.querySelector('[data-tab="' + name + '"]');
    if (btn) btn.classList.add('active');
    if (name === 'status') jvcRefreshStatus();
    if (name === 'image')  jvcSyncImage();
}

// ── Status bar ───────────────────────────────────────────────────────────────
function setStatus(msg, type) {
    const bar = document.getElementById('status-indicator');
    const txt = document.getElementById('status-text');
    if (txt) txt.textContent = msg;
    if (bar) {
        bar.style.background = type === 'error' ? '#f44336'
                             : type === 'ok'    ? '#4caf50'
                             :                    '#ffa726';
    }
}

// ── Toast ────────────────────────────────────────────────────────────────────
let _toastTimer = null;
function showToast(msg, type) {
    let t = document.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); }
    t.textContent = msg;
    t.className = 'toast ' + (type === 'error' ? 'error' : 'success');
    clearTimeout(_toastTimer);
    _toastTimer = setTimeout(() => { if (t.parentNode) t.remove(); }, 3200);
}

// ── Generic API call ─────────────────────────────────────────────────────────
async function jvcApi(method, path, body) {
    setStatus('Sending…', 'busy');
    try {
        const opts = { method };
        if (body !== undefined) {
            opts.headers = { 'Content-Type': 'application/json' };
            opts.body = JSON.stringify(body);
        }
        const r = await fetch(path, opts);
        const data = await r.json();
        if (r.ok && (data.ok || data.success || data.status === 'ok')) {
            setStatus('OK', 'ok');
            showToast(data.message || 'OK', 'ok');
            return data;
        } else {
            const msg = data.error || data.message || 'Command failed';
            setStatus(msg, 'error');
            showToast(msg, 'error');
            return null;
        }
    } catch (e) {
        setStatus('Network error', 'error');
        showToast('Network error: ' + e.message, 'error');
        return null;
    }
}

// ── Power ────────────────────────────────────────────────────────────────────
function confirmPower(state) {
    const label = state === 'on' ? 'power ON' : 'power OFF';
    if (!confirm('Send ' + label + ' command to JVC projector?')) return;
    jvcApi('POST', '/api/jvc/power/' + state).then(data => {
        if (!data) return;
        const led = document.getElementById('jvc-power-led');
        if (!led) return;
        led.classList.toggle('led-on', state === 'on');
        led.classList.toggle('led-off', state === 'off');
    });
}

// ── Input ────────────────────────────────────────────────────────────────────
function jvcInput(inp) {
    jvcApi('POST', '/api/jvc/input/' + inp);
}

// ── Picture Mode ─────────────────────────────────────────────────────────────
function jvcPictureMode(mode) {
    jvcApi('POST', '/api/jvc/picture-mode/' + mode);
}

// ── Color Profile ────────────────────────────────────────────────────────────
function jvcColorProfile(val) {
    jvcApi('POST', '/api/jvc/color-profile/' + val);
}

// ── Color Temperature ────────────────────────────────────────────────────────
function jvcColorTemp(val) {
    jvcApi('POST', '/api/jvc/color-temp/' + val);
}

// ── Gamma Table ──────────────────────────────────────────────────────────────
function jvcGamma(val) {
    jvcApi('POST', '/api/jvc/gamma/' + val);
}

// ── Lens Aperture ────────────────────────────────────────────────────────────
function jvcLensAperture(val) {
    jvcApi('POST', '/api/jvc/lens-aperture/' + val);
}

// ── Low Latency ──────────────────────────────────────────────────────────────
function jvcLowLatency(state) {
    jvcApi('POST', '/api/jvc/low-latency/' + state);
}

// ── Clear Motion Drive ───────────────────────────────────────────────────────
function jvcClearMotion(val) {
    jvcApi('POST', '/api/jvc/clear-motion/' + val);
}

// ── Motion Enhance ───────────────────────────────────────────────────────────
function jvcMotionEnhance(val) {
    jvcApi('POST', '/api/jvc/motion-enhance/' + val);
}

// ── Lamp Power ───────────────────────────────────────────────────────────────
function jvcLampPower(val) {
    jvcApi('POST', '/api/jvc/lamp-power/' + val);
}

// ── 8K e-shift ───────────────────────────────────────────────────────────────
function jvc8kEshift(state) {
    jvcApi('POST', '/api/jvc/8k-eshift/' + state);
}

// ── Auto Tone Mapping ────────────────────────────────────────────────────────
function jvcAutoToneMap(state) {
    jvcApi('POST', '/api/jvc/auto-tone-map/' + state);
}

// ── Image Adjustments ────────────────────────────────────────────────────────
const _adjValues = {
    contrast: null, brightness: null, color: null,
    tint: null, nr: null, enhance: null, smooth: null,
};
const _adjLimits = {
    contrast:   [-50, 50],
    brightness: [-50, 50],
    color:      [-50, 50],
    tint:       [-50, 50],
    nr:         [0, 60],
    enhance:    [0, 20],
    smooth:     [0, 10],
};

function _setAdjDisplay(param, val) {
    _adjValues[param] = val;
    const el = document.getElementById('adj-' + param);
    if (el) el.textContent = (val !== null ? val : '?');
}

async function imgStep(param, delta) {
    const cur = _adjValues[param];
    const [lo, hi] = _adjLimits[param];
    let next = (cur !== null ? cur : 0) + delta;
    next = Math.max(lo, Math.min(hi, next));

    const data = await jvcApi('POST', '/api/jvc/image-adjust', { param, val: next });
    if (data) _setAdjDisplay(param, next);
}

async function jvcSyncImage() {
    setStatus('Reading image values…', 'busy');
    try {
        const r = await fetch('/api/jvc/image-values');
        const data = await r.json();
        if (!r.ok || !data.success) {
            setStatus(data.error || 'Read failed', 'error');
            showToast('Could not read image values', 'error');
            return;
        }
        const vals = data.values || {};
        for (const [k, v] of Object.entries(vals)) {
            if (k in _adjValues) _setAdjDisplay(k, v);
        }
        setStatus('Image values synced', 'ok');
        showToast('Image values synced', 'ok');
    } catch (e) {
        setStatus('Network error', 'error');
        showToast('Network error: ' + e.message, 'error');
    }
}

// ── Lens hold controls ───────────────────────────────────────────────────────
let _lensActive = null;

function _lensBtn(action) {
    return document.querySelector('[onmousedown*="' + action + '"]');
}

function lensStart(action) {
    if (_lensActive && _lensActive !== action) lensStop(_lensActive);
    _lensActive = action;
    const btn = _lensBtn(action);
    if (btn) btn.classList.add('holding');
    jvcApi('POST', '/api/jvc/lens/' + encodeURIComponent(action) + '/1');
}

function lensStop(action) {
    if (_lensActive === action) _lensActive = null;
    const btn = _lensBtn(action);
    if (btn) btn.classList.remove('holding');
    jvcApi('POST', '/api/jvc/lens/' + encodeURIComponent(action) + '/0');
}

// ── Lens Lock ────────────────────────────────────────────────────────────────
function jvcLensLock(state) {
    jvcApi('POST', '/api/jvc/lens-lock/' + state);
}

// ── HDMI Level ───────────────────────────────────────────────────────────────
function jvcHdmiLevel(val) {
    jvcApi('POST', '/api/jvc/hdmi-level/' + val);
}

// ── HDMI Color Space ─────────────────────────────────────────────────────────
function jvcHdmiColorspace(val) {
    jvcApi('POST', '/api/jvc/hdmi-colorspace/' + val);
}

// ── Aspect ───────────────────────────────────────────────────────────────────
function jvcAspect(val) {
    jvcApi('POST', '/api/jvc/aspect/' + val);
}

// ── Anamorphic ───────────────────────────────────────────────────────────────
function jvcAnamorphic(val) {
    jvcApi('POST', '/api/jvc/anamorphic/' + val);
}

// ── Install Style ────────────────────────────────────────────────────────────
function jvcInstallStyle(val) {
    jvcApi('POST', '/api/jvc/install-style/' + val);
}

// ── High Altitude ────────────────────────────────────────────────────────────
function jvcHighAltitude(state) {
    jvcApi('POST', '/api/jvc/high-altitude/' + state);
}

// ── Eco Mode ─────────────────────────────────────────────────────────────────
function jvcEcoMode(state) {
    jvcApi('POST', '/api/jvc/eco-mode/' + state);
}

// ── Off Timer ────────────────────────────────────────────────────────────────
function jvcOffTimer(val) {
    jvcApi('POST', '/api/jvc/off-timer/' + val);
}

// ── Back Color ───────────────────────────────────────────────────────────────
function jvcBackColor(val) {
    jvcApi('POST', '/api/jvc/back-color/' + val);
}

// ── Status tab ───────────────────────────────────────────────────────────────
let _jvcAutoRefreshTimer = null;

function _setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = (val != null ? val : '—');
}

async function jvcRefreshStatus() {
    setStatus('Reading status…', 'busy');
    try {
        const r = await fetch('/api/jvc/full-status');
        const data = await r.json();
        if (!r.ok || data.error) {
            setStatus(data.error || 'Read failed', 'error');
            return;
        }
        _setText('js-power',  data.power);
        _setText('js-input',  data.input);
        _setText('js-pm',     data.picture_mode);
        _setText('js-source', data.source);
        _setText('js-hdr',    data.hdr_type);
        _setText('js-la',     data.lens_aperture);
        _setText('js-lp',     data.lamp_power);
        _setText('js-ll',     data.low_latency);
        _setText('js-il',     data.hdmi_level);
        _setText('js-model',  data.model);
        _setText('js-sw',     data.software);
        _setText('js-lamp',   data.lamp_time);

        const led = document.getElementById('jvc-power-led');
        if (led) {
            const on = (data.power || '').toLowerCase().includes('on');
            led.classList.toggle('led-on', on);
            led.classList.toggle('led-off', !on);
        }
        setStatus('Status updated', 'ok');
    } catch (e) {
        setStatus('Network error', 'error');
    }
}

function toggleJvcAutoRefresh(enabled) {
    clearInterval(_jvcAutoRefreshTimer);
    if (enabled) {
        _jvcAutoRefreshTimer = setInterval(jvcRefreshStatus, 30000);
    }
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setStatus('Ready', 'ok');
    fetch('/api/jvc/status')
        .then(r => r.json())
        .then(data => {
            if (!data || data.error) return;
            const led = document.getElementById('jvc-power-led');
            if (!led) return;
            const on = (data.power || '').toLowerCase().includes('on');
            led.classList.toggle('led-on', on);
            led.classList.toggle('led-off', !on);
        })
        .catch(() => {});
});
