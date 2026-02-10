/* ============================================
   ROAST MY CODE — Client-side Logic
   ============================================ */

const MAX_CHARS = 15000;
const MAX_LINES = 500;

document.addEventListener('DOMContentLoaded', () => {
    initModeToggle();
    initSeverityChips();
    initCodeInput();
    initFormSubmit();
    initScoreAnimation();
});

/* --- Mode Toggle --- */

function initModeToggle() {
    const roastBtn = document.getElementById('mode-roast');
    const seriousBtn = document.getElementById('mode-serious');
    const modeInput = document.getElementById('mode-input');
    const severitySelector = document.getElementById('severity-selector');
    const submitBtn = document.getElementById('submit-btn');

    if (!roastBtn || !seriousBtn) return;

    roastBtn.addEventListener('click', () => {
        roastBtn.classList.add('active');
        seriousBtn.classList.remove('active');
        modeInput.value = 'roast';
        severitySelector.classList.remove('hidden');
        document.documentElement.setAttribute('data-mode', 'roast');
        if (submitBtn) {
            submitBtn.querySelector('.btn-text').textContent = 'Roast My Human Code \u{1F525}';
        }
    });

    seriousBtn.addEventListener('click', () => {
        seriousBtn.classList.add('active');
        roastBtn.classList.remove('active');
        modeInput.value = 'serious';
        severitySelector.classList.add('hidden');
        document.documentElement.setAttribute('data-mode', 'serious');
        if (submitBtn) {
            submitBtn.querySelector('.btn-text').textContent = 'Start Serious Review \u{1F4CB}';
        }
    });
}

/* --- Severity Chips --- */

function initSeverityChips() {
    const chips = document.querySelectorAll('.severity-option input');
    chips.forEach(input => {
        input.addEventListener('change', () => {
            document.querySelectorAll('.severity-chip').forEach(c => c.classList.remove('active'));
            input.nextElementSibling.classList.add('active');
        });
    });
}

/* --- Code Input --- */

function initCodeInput() {
    const codeInput = document.getElementById('code-input');
    const charCount = document.getElementById('char-count');
    const lineCount = document.getElementById('line-count');
    const codeStats = document.getElementById('code-stats');

    if (!codeInput) return;

    function updateStats() {
        const code = codeInput.value;
        const chars = code.length;
        const lines = code ? code.split('\n').length : 0;

        charCount.textContent = chars.toLocaleString();
        lineCount.textContent = lines.toLocaleString();

        // Color coding
        if (chars > MAX_CHARS * 0.9 || lines > MAX_LINES * 0.9) {
            codeStats.className = 'code-stats danger';
        } else if (chars > MAX_CHARS * 0.7 || lines > MAX_LINES * 0.7) {
            codeStats.className = 'code-stats warning';
        } else {
            codeStats.className = 'code-stats';
        }
    }

    codeInput.addEventListener('input', updateStats);

    // Tab key inserts a tab instead of focusing next element
    codeInput.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = codeInput.selectionStart;
            const end = codeInput.selectionEnd;
            codeInput.value = codeInput.value.substring(0, start) + '    ' + codeInput.value.substring(end);
            codeInput.selectionStart = codeInput.selectionEnd = start + 4;
            updateStats();
        }
    });

    updateStats();
}

/* --- Form Validation & Submit --- */

function validateInput(code) {
    if (!code.trim()) {
        return { valid: false, msg: "Paste some code first. We can't roast nothing." };
    }
    if (code.length > MAX_CHARS) {
        return { valid: false, msg: `Too long (${code.length.toLocaleString()} chars). Max is ${MAX_CHARS.toLocaleString()}.` };
    }
    if (code.split('\n').length > MAX_LINES) {
        return { valid: false, msg: `Too many lines (${code.split('\n').length}). Max is ${MAX_LINES}. Paste the worst part.` };
    }
    return { valid: true };
}

function initFormSubmit() {
    const form = document.getElementById('roast-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        const codeInput = document.getElementById('code-input');
        const errorDiv = document.getElementById('validation-error');
        const submitBtn = document.getElementById('submit-btn');

        const result = validateInput(codeInput.value);
        if (!result.valid) {
            e.preventDefault();
            errorDiv.textContent = result.msg;
            errorDiv.style.display = 'block';
            return;
        }

        errorDiv.style.display = 'none';

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').style.display = 'none';
        submitBtn.querySelector('.btn-loading').style.display = 'inline';
    });
}

/* --- Score Animation (Result Page) --- */

function initScoreAnimation() {
    const gauge = document.getElementById('score-gauge');
    if (!gauge) return;

    const score = parseInt(gauge.dataset.score) || 0;
    const scoreNumber = document.getElementById('score-number');
    const gaugeFill = document.getElementById('gauge-fill');

    // Animate the gauge fill
    // The arc length is about 251 units (half circle with radius 80)
    const fillAmount = (score / 100) * 251;
    setTimeout(() => {
        gaugeFill.style.strokeDashoffset = 251 - fillAmount;
    }, 100);

    // Animate the number counting up
    let current = 0;
    const duration = 1500;
    const startTime = performance.now();

    function animateNumber(timestamp) {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        current = Math.round(eased * score);
        scoreNumber.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(animateNumber);
        }
    }

    requestAnimationFrame(animateNumber);
}
