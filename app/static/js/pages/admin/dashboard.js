import { qs, qsa } from '../../utils/dom.js';

function setupCountdown(root = document) {
    const countdownEl = qs(root, '[data-dashboard-countdown]');
    if (!countdownEl) {
        return;
    }

    const targetIso = countdownEl.dataset.countdownTarget;
    if (!targetIso) {
        return;
    }

    const daysEl = qs(countdownEl, '[data-countdown-days]');
    const hoursEl = qs(countdownEl, '[data-countdown-hours]');
    const minutesEl = qs(countdownEl, '[data-countdown-minutes]');
    const statusWrapper = countdownEl.closest('.dashboard-event-card__status');
    const statusLabel = statusWrapper ? qs(statusWrapper, '.dashboard-event-card__status-label') : null;
    const targetDate = new Date(targetIso);

    if (Number.isNaN(targetDate.getTime())) {
        return;
    }

    const pad = (value) => String(value).padStart(2, '0');

    const teardownToLive = () => {
        if (!statusWrapper) {
            return;
        }
        if (statusLabel) {
            statusLabel.remove();
        }
        const live = document.createElement('div');
        live.className = 'dashboard-event-card__live';
        live.setAttribute('role', 'status');

        const dot = document.createElement('span');
        dot.className = 'dashboard-event-card__live-dot';
        dot.setAttribute('aria-hidden', 'true');

        const text = document.createElement('span');
        text.className = 'dashboard-event-card__live-text';
        text.textContent = 'Идёт сейчас';

        live.append(dot, text);
        countdownEl.replaceWith(live);
    };

    const updateCountdown = () => {
        const now = new Date();
        const diffMs = targetDate.getTime() - now.getTime();

        if (diffMs <= 0) {
            teardownToLive();
            return false;
        }

        const totalMinutes = Math.floor(diffMs / 60000);
        const totalHours = Math.floor(totalMinutes / 60);
        const days = Math.floor(totalHours / 24);
        const hours = totalHours % 24;
        const minutes = totalMinutes % 60;

        if (daysEl) {
            daysEl.textContent = pad(days);
        }
        if (hoursEl) {
            hoursEl.textContent = pad(hours);
        }
        if (minutesEl) {
            minutesEl.textContent = pad(minutes);
        }
        return true;
    };

    if (!updateCountdown()) {
        return;
    }

    const timerId = window.setInterval(() => {
        const keepRunning = updateCountdown();
        if (!keepRunning) {
            window.clearInterval(timerId);
        }
    }, 30000);
}

function setupTeacherSearch(root = document) {
    const searchInput = qs(root, '[data-dashboard-search-input]');
    const clearButton = qs(root, '[data-dashboard-search-clear]');
    const teacherCards = qsa(root, '[data-teacher-card]');
    const noResults = qs(root, '[data-dashboard-no-results]');

    if (!searchInput || !teacherCards.length) {
        return;
    }

    const applyFilter = () => {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        teacherCards.forEach((card) => {
            const haystack = card.dataset.teacherSearch || '';
            const matches = !query || haystack.includes(query);
            card.hidden = !matches;
            card.classList.toggle('teacher-card--hidden', !matches);
            if (matches) {
                visibleCount += 1;
            }
        });

        if (noResults) {
            noResults.hidden = visibleCount > 0;
        }
    };

    searchInput.addEventListener('input', applyFilter);

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            applyFilter();
            searchInput.focus();
        });
    }

    applyFilter();
}

function initAdminDashboard(root = document) {
    setupCountdown(root);
    setupTeacherSearch(root);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initAdminDashboard(), { once: true });
} else {
    initAdminDashboard();
}

export { initAdminDashboard };
