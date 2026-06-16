// JVC Projector Web UI

const HOLD_DURATION = 3000;

function isMobileDevice() {
    return navigator.maxTouchPoints > 0 || /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

function setupLongPress(button, action) {
    let startTime = null;
    let rafId = null;

    function cancel() {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
        startTime = null;
        button.classList.remove('holding');
        button.style.setProperty('--hold-progress', 0);
    }

    button.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startTime = performance.now();
        button.classList.add('holding');

        function animate() {
            const progress = Math.min((performance.now() - startTime) / HOLD_DURATION, 1);
            button.style.setProperty('--hold-progress', progress);
            if (progress < 1) {
                rafId = requestAnimationFrame(animate);
            } else {
                cancel();
                if (navigator.vibrate) navigator.vibrate(50);
                action();
            }
        }
        rafId = requestAnimationFrame(animate);
    }, { passive: false });

    button.addEventListener('touchend', cancel);
    button.addEventListener('touchcancel', cancel);
}

function initPowerButtons() {
    const btnOn  = document.getElementById('btn-power-on');
    const btnOff = document.getElementById('btn-power-off');
    if (isMobileDevice()) {
        document.getElementById('power-hold-hint').style.display = 'block';
        setupLongPress(btnOn,  () => jvcPower('on'));
        setupLongPress(btnOff, () => jvcPower('off'));
    } else {
        btnOn.addEventListener('click',  () => jvcPower('on'));
        btnOff.addEventListener('click', () => jvcPower('off'));
    }
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
    await callAPI(`/api/jvc/power/${action}`);
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
    initPowerButtons();
});
