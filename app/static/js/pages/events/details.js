import { qs, qsa } from '../../utils/dom.js';

function setupEventsDetails(root = document) {
    const modal = qs(root, '[data-event-details-modal]');
    const eventsGrid = qs(root, '.events-grid');

    if (!modal || !eventsGrid) {
        return null;
    }

    const overlay = qs(modal, '.event-details-modal__overlay');
    const closeButtons = qsa(modal, '[data-event-details-close]');
    const titleEl = qs(modal, '[data-event-details-title]');
    const statusBadgeEl = qs(modal, '[data-event-details-status]');
    const statusContainerEl = qs(modal, '[data-event-details-status-container]');
    const statusHintEl = qs(modal, '[data-event-details-status-hint]');
    const periodEl = qs(modal, '[data-event-details-period]');
    const consultationsEl = qs(modal, '[data-event-details-consultations]');
    const durationEl = qs(modal, '[data-event-details-duration]');
    const consultationDurationHighlight = qs(modal, '[data-event-details-highlight-consultation-duration]');
    const consultationDurationEl = qs(modal, '[data-event-details-consultation-duration]');
    const teachersSection = qs(modal, '[data-event-details-teachers-section]');
    const teachersList = qs(modal, '[data-event-details-teachers]');
    const metaContainer = qs(modal, '[data-event-details-meta]');
    const statsSection = qs(modal, '[data-event-details-stats-section]');
    const statsContainer = qs(modal, '[data-event-details-stats]');
    const bookingsSection = qs(modal, '[data-event-details-bookings-section]');
    const bookingsContainer = qs(modal, '[data-event-details-bookings]');

    let lastFocusedElement = null;

    const clearChildren = (container) => {
        if (!container) {
            return;
        }
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
    };

    const renderMeta = (metaItems) => {
        clearChildren(metaContainer);
        if (!metaContainer) {
            return;
        }
        if (!metaItems || !metaItems.length) {
            metaContainer.insertAdjacentHTML('beforeend', '<p class="event-details-modal__empty">Нет данных</p>');
            return;
        }
        metaItems.forEach((item) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'event-details-modal__meta-item';

            const label = document.createElement('span');
            label.className = 'event-details-modal__meta-label';
            label.textContent = item.label || '';

            const value = document.createElement('span');
            value.className = 'event-details-modal__meta-value';
            value.textContent = item.value || '';

            wrapper.append(label, value);
            metaContainer.appendChild(wrapper);
        });
    };

    const renderStats = (stats) => {
        if (!statsContainer || !statsSection) {
            return;
        }
        clearChildren(statsContainer);
        if (!stats || !stats.length) {
            statsSection.style.display = 'none';
            return;
        }
        statsSection.style.display = '';
        stats.forEach((stat) => {
            const item = document.createElement('div');
            item.className = 'event-details-modal__stats-item';

            const value = document.createElement('span');
            value.className = 'event-details-modal__stats-value';
            value.textContent = stat.value || '0';

            const label = document.createElement('span');
            label.className = 'event-details-modal__stats-label';
            label.textContent = stat.label || '';

            item.append(value, label);
            statsContainer.appendChild(item);
        });
    };

    const renderBookings = (bookings) => {
        if (!bookingsContainer || !bookingsSection) {
            return;
        }
        clearChildren(bookingsContainer);
        if (!bookings || !bookings.length) {
            bookingsSection.style.display = 'none';
            return;
        }
        bookingsSection.style.display = '';
        bookings.forEach((booking) => {
            const item = document.createElement('li');
            item.className = 'event-details-modal__bookings-item';

            const building = document.createElement('span');
            building.className = 'event-details-modal__booking-building';
            building.textContent = booking.building || '';

            item.appendChild(building);

            if (booking.rooms && booking.rooms.length) {
                const rooms = document.createElement('span');
                rooms.className = 'event-details-modal__booking-rooms';
                rooms.textContent = booking.rooms.join(', ');
                item.appendChild(rooms);
            }

            bookingsContainer.appendChild(item);
        });
    };

    const openModal = (detail) => {
        if (!detail) {
            return;
        }

        lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;

        if (titleEl) {
            titleEl.textContent = detail.title || 'Мероприятие';
        }

        if (statusBadgeEl) {
            const baseClass = 'management-badge event-details-modal__status-badge';
            const modifier = detail.statusModifier ? ` management-badge--${detail.statusModifier}` : '';
            statusBadgeEl.className = `${baseClass}${modifier}`;
            statusBadgeEl.textContent = detail.status || '';
        }

        if (statusHintEl) {
            statusHintEl.textContent = detail.statusHint || '';
            statusHintEl.style.display = detail.statusHint ? '' : 'none';
        }

        if (statusContainerEl) {
            statusContainerEl.style.display = detail.status ? '' : 'none';
        }

        if (periodEl) {
            periodEl.textContent = detail.period || '';
        }

        if (consultationsEl) {
            consultationsEl.textContent = detail.consultations != null ? detail.consultations : '0';
        }

        if (durationEl) {
            durationEl.textContent = detail.durationMinutes != null ? detail.durationMinutes : '0';
        }

        if (consultationDurationEl) {
            consultationDurationEl.textContent = detail.consultationDurationMinutes != null
                ? detail.consultationDurationMinutes
                : '0';
        }

        if (consultationDurationHighlight) {
            consultationDurationHighlight.style.display = detail.consultationDurationMinutes != null ? '' : 'none';
        }

        if (teachersList && teachersSection) {
            while (teachersList.firstChild) {
                teachersList.removeChild(teachersList.firstChild);
            }
            const teacherNames = Array.isArray(detail.teacherNames) ? detail.teacherNames : [];
            if (!teacherNames.length) {
                teachersSection.style.display = 'none';
            } else {
                teachersSection.style.display = '';
                teacherNames.forEach((teacherName) => {
                    const item = document.createElement('li');
                    item.className = 'event-details-modal__teacher-item';
                    item.textContent = teacherName;
                    teachersList.appendChild(item);
                });
            }
        }

        renderMeta(detail.meta);
        renderStats(detail.stats);
        renderBookings(detail.bookings);

        modal.setAttribute('data-open', 'true');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('no-scroll');

        const focusTarget = titleEl || modal.querySelector('button, [href], input, textarea, select');
        window.requestAnimationFrame(() => {
            if (focusTarget && typeof focusTarget.focus === 'function') {
                focusTarget.focus();
            }
        });
    };

    const closeModal = () => {
        modal.removeAttribute('data-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('no-scroll');

        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            lastFocusedElement.focus();
        }
    };

    const resolveCardFromEvent = (event) => {
        if (event.target.closest('[data-action]')) {
            return null;
        }
        if (event.target.closest('.management-card__menu')) {
            return null;
        }
        return event.target.closest('[data-event-card]');
    };

    eventsGrid.addEventListener('click', (event) => {
        const card = resolveCardFromEvent(event);
        if (!card) {
            return;
        }
        const payload = card.dataset.eventDetail;
        if (!payload) {
            return;
        }
        try {
            const detail = JSON.parse(payload);
            openModal(detail);
        } catch (error) {
            console.error('Failed to parse event detail payload', error);
        }
    });

    eventsGrid.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') {
            return;
        }
        const card = event.target.closest('[data-event-card]');
        if (!card) {
            return;
        }
        event.preventDefault();
        const payload = card.dataset.eventDetail;
        if (!payload) {
            return;
        }
        try {
            const detail = JSON.parse(payload);
            openModal(detail);
        } catch (error) {
            console.error('Failed to parse event detail payload', error);
        }
    });

    closeButtons.forEach((button) => {
        button.addEventListener('click', closeModal);
    });

    if (overlay) {
        overlay.addEventListener('click', closeModal);
    }

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.hasAttribute('data-open')) {
            closeModal();
        }
    });

    return {
        open: openModal,
        close: closeModal,
    };
}

export { setupEventsDetails };
