import { qs, qsa } from '../../utils/dom.js';

function setupEventsModal(root = document) {
    const modal = qs(root, '[data-events-modal]');
    if (!modal) {
        return null;
    }

    const openButton = qs(root, '[data-events-add]');
    const closeButtons = qsa(modal, '[data-events-close]');
    const overlay = qs(modal, '.events-modal__overlay');
    const dialog = qs(modal, '.events-modal__dialog');
    const modalForm = qs(modal, 'form');
    const modalTitle = qs(modal, '#events-modal-title');
    const startInput = qs(modal, '#event_start_time');
    const endInput = qs(modal, '#event_end_time');
    const formTypeInput = modalForm ? qs(modalForm, 'input[name="form_type"]') : null;
    const eventIdInput = modalForm ? qs(modalForm, 'input[name="event_id"]') : null;
    const submitButton = modalForm ? qs(modalForm, 'button[type="submit"]') : null;
    const focusableSelectors = 'input, select, textarea, button, [href], [tabindex]:not([tabindex="-1"])';

    let lastFocusedElement = null;

    const normalizeMode = (mode) => (mode === 'update' ? 'update' : 'create');

    const setModalMode = (mode, data = {}) => {
        const normalizedMode = normalizeMode(mode);
        modal.dataset.mode = normalizedMode;

        if ('eventId' in data && data.eventId) {
            modal.dataset.eventId = data.eventId;
        } else {
            delete modal.dataset.eventId;
        }

        if (formTypeInput) {
            formTypeInput.value = normalizedMode;
        }
        if (eventIdInput && 'eventId' in data) {
            eventIdInput.value = data.eventId || '';
        }
        if (startInput && 'start' in data) {
            startInput.value = data.start || '';
        }
        if (endInput && 'end' in data) {
            endInput.value = data.end || '';
        }

        if (normalizedMode === 'update') {
            if (modalTitle) {
                modalTitle.textContent = 'Редактирование мероприятия';
            }
            if (submitButton) {
                submitButton.textContent = 'Сохранить изменения';
            }
        } else {
            if (modalTitle) {
                modalTitle.textContent = 'Создание мероприятия';
            }
            if (submitButton) {
                submitButton.textContent = 'Создать';
            }
        }
    };

    const openModal = (mode = modal.dataset.mode || 'create', data = {}) => {
        lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        const defaults = {
            eventId: '',
            start: startInput ? startInput.value : '',
            end: endInput ? endInput.value : '',
        };
        const payload = { ...defaults, ...data };
        setModalMode(mode, payload);
        modal.setAttribute('data-open', 'true');
        document.body.classList.add('no-scroll');

        const focusTarget = startInput || qs(modal, 'input, select, textarea');
        window.setTimeout(() => {
            if (focusTarget) {
                focusTarget.focus();
                if (
                    focusTarget instanceof HTMLInputElement ||
                    focusTarget instanceof HTMLTextAreaElement
                ) {
                    const length = focusTarget.value.length;
                    focusTarget.setSelectionRange(length, length);
                }
            }
        }, 10);
    };

    const closeModal = () => {
        modal.removeAttribute('data-open');
        document.body.classList.remove('no-scroll');

        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            lastFocusedElement.focus();
        } else if (openButton && typeof openButton.focus === 'function') {
            openButton.focus();
        }
    };

    if (openButton && !openButton.dataset.modalBound) {
        openButton.addEventListener('click', () => {
            openModal('create', { eventId: '', start: '', end: '' });
        });
        openButton.dataset.modalBound = 'true';
    }

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

    if (dialog) {
        modal.addEventListener('keydown', (event) => {
            if (event.key !== 'Tab' || !modal.hasAttribute('data-open')) {
                return;
            }

            const focusableElements = Array.from(
                dialog.querySelectorAll(focusableSelectors)
            ).filter((element) => !element.hasAttribute('disabled') && element.offsetParent !== null);

            if (!focusableElements.length) {
                return;
            }

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey && document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            } else if (!event.shiftKey && document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        });
    }

    if (modal.hasAttribute('data-open')) {
        const defaultMode = modal.dataset.mode || 'create';
        const eventId = modal.dataset.eventId || '';
        const startValue = startInput ? startInput.value : '';
        const endValue = endInput ? endInput.value : '';
        openModal(defaultMode, { eventId, start: startValue, end: endValue });
    }

    return {
        element: modal,
        form: modalForm,
        open(mode, data) {
            openModal(mode, data);
        },
        close() {
            closeModal();
        },
        setMode(mode, data) {
            setModalMode(mode, data);
        },
    };
}

export { setupEventsModal };
