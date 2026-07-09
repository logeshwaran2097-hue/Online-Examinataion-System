/* ==========================================================================
   Online Examination System - Client Actions
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 0. Auto-inject CSRF token into every POST form (fixes Flask-WTF CSRF globally)
    injectCSRFTokens();

    // 1. Theme Configuration (Dark / Light Mode)
    initTheme();

    // 2. Sidebar Toggle Handler
    initSidebar();

    // 3. Password Visibility Toggle
    initPasswordToggle();

    // 4. Custom Option Selections in Exams
    initExamOptions();

    // 5. Auto-dismiss alerts
    initAlertDismissal();

    // 6. Live Clock (if present)
    initLiveClock();

    // 7. Notification badge pop animation
    animateNotificationBadge();
});

/**
 * Auto-inject CSRF hidden token into every POST form on the page.
 * Reads the token from <meta name="csrf-token"> set in base.html.
 */
function injectCSRFTokens() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) return;
    const token = meta.getAttribute('content');
    document.querySelectorAll('form[method="POST"], form[method="post"]').forEach(form => {
        // Only add if not already present
        if (!form.querySelector('input[name="csrf_token"]')) {
            const input = document.createElement('input');
            input.type  = 'hidden';
            input.name  = 'csrf_token';
            input.value = token;
            form.prepend(input);
        }
    });
}

/**
 * Setup Light/Dark Mode toggle and persistence
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeToggleUI(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggleUI(newTheme);
        });
    }
}

function updateThemeToggleUI(theme) {
    const icon = document.querySelector('#theme-toggle i');
    if (!icon) return;
    if (theme === 'dark') {
        icon.className = 'fa-solid fa-sun';
        icon.setAttribute('title', 'Switch to Light Mode');
    } else {
        icon.className = 'fa-solid fa-moon';
        icon.setAttribute('title', 'Switch to Dark Mode');
    }
}

/**
 * Responsive Sidebar toggling for dashboards
 * Includes mobile dark overlay support.
 */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');

    // Create overlay element dynamically if sidebar exists
    let overlay = document.getElementById('sidebar-overlay');
    if (!overlay && sidebar) {
        overlay = document.createElement('div');
        overlay.id = 'sidebar-overlay';
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    function openSidebar() {
        sidebar.classList.remove('collapsed');
        if (overlay) overlay.classList.add('active');
    }

    function closeSidebar() {
        sidebar.classList.add('collapsed');
        if (overlay) overlay.classList.remove('active');
    }

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (sidebar.classList.contains('collapsed')) {
                openSidebar();
            } else {
                closeSidebar();
            }
        });
    }

    // Close sidebar on overlay click (mobile)
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
}

/**
 * Show/Hide password field toggle
 */
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);
            const icon = btn.querySelector('i');
            
            if (passwordInput && icon) {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    icon.className = 'fa-solid fa-eye-slash';
                } else {
                    passwordInput.type = 'password';
                    icon.className = 'fa-solid fa-eye';
                }
            }
        });
    });
}

/**
 * Handle custom visual states for exam options (div options instead of radio dots)
 */
function initExamOptions() {
    const options = document.querySelectorAll('.option-container');
    options.forEach(option => {
        option.addEventListener('click', () => {
            // Find parent question block
            const questionBlock = option.closest('.question-block');
            if (questionBlock) {
                // Clear selection within this question
                questionBlock.querySelectorAll('.option-container').forEach(opt => {
                    opt.classList.remove('selected');
                    const radio = opt.querySelector('input[type="radio"]');
                    if (radio) radio.checked = false;
                });
                
                // Select active option
                option.classList.add('selected');
                const activeRadio = option.querySelector('input[type="radio"]');
                if (activeRadio) {
                    activeRadio.checked = true;
                    // Trigger custom events if needed
                    activeRadio.dispatchEvent(new Event('change'));
                }
            }
        });
    });
}

/**
 * Automatically dismiss notifications after 5 seconds
 */
function initAlertDismissal() {
    const alerts = document.querySelectorAll('.alert-auto-dismiss');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Countdown timer module for exams
 * @param {number} durationSeconds - Initial duration in seconds
 * @param {string} displayId - Id of HTML element to update
 * @param {function} onComplete - Callback executed when timer hits zero
 */
function startCountdownTimer(durationSeconds, displayId, onComplete) {
    let timeLeft = durationSeconds;
    const displayElement = document.getElementById(displayId);
    
    if (!displayElement) return;

    function updateTimer() {
        const hours = Math.floor(timeLeft / 3600);
        const minutes = Math.floor((timeLeft % 3600) / 60);
        const seconds = timeLeft % 60;
        
        let displayStr = '';
        if (hours > 0) {
            displayStr += `${String(hours).padStart(2, '0')}:`;
        }
        displayStr += `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        displayElement.textContent = displayStr;
        
        // Visual warning when time is low (< 5 minutes)
        if (timeLeft < 300) {
            const pill = displayElement.closest('.timer-pill');
            if (pill) {
                pill.style.background = 'linear-gradient(135deg, #ef4444, #b91c1c)';
                pill.classList.add('animate-pulse');
            }
        }
        
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            if (typeof onComplete === 'function') {
                onComplete();
            }
        } else {
            timeLeft--;
        }
    }
    
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
    return timerInterval;
}

/**
 * Live clock display (for top navigation bar)
 */
function initLiveClock() {
    const clockEl = document.getElementById('live-clock');
    if (!clockEl) return;

    function tick() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-IN', {
            hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
        });
    }
    tick();
    setInterval(tick, 1000);
}

/**
 * Plays a brief scale pop on notification badges if count > 0.
 */
function animateNotificationBadge() {
    const badge = document.querySelector('.notif-badge');
    if (badge && parseInt(badge.textContent) > 0) {
        badge.classList.add('animate-badge-pop');
        setTimeout(() => badge.classList.remove('animate-badge-pop'), 400);
    }
}
