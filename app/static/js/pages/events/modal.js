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
    const nameInput = qs(modal, '#event_name');
    const consultationsInput = qs(modal, '#event_consultations_count');
    const startInput = qs(modal, '#event_start_time');
    const durationInput = qs(modal, '#event_consultation_duration');
    const endPreview = qs(modal, '[data-event-end-preview]');
    const formTypeInput = modalForm ? qs(modalForm, 'input[name="form_type"]') : null;
    const eventIdInput = modalForm ? qs(modalForm, 'input[name="event_id"]') : null;
    const submitButton = modalForm ? qs(modalForm, 'button[type="submit"]') : null;
    const focusableSelectors = 'input, select, textarea, button, [href], [tabindex]:not([tabindex="-1"])';

    let lastFocusedElement = null;
    const END_PREVIEW_PLACEHOLDER = '—';

    const parsePositiveInteger = (value) => {
        if (typeof value !== 'string') {
            return null;
        }
        const trimmed = value.trim();
        if (!trimmed) {
            return null;
        }
        const parsed = Number.parseInt(trimmed, 10);
        if (Number.isNaN(parsed) || parsed <= 0) {
            return null;
        }
        return parsed;
    };

    const parseLocalDateTime = (value) => {
        if (typeof value !== 'string' || !value) {
            return null;
        }
        const [datePart, timePart] = value.split('T');
        if (!datePart || !timePart) {
            return null;
        }
        const [year, month, day] = datePart.split('-').map((part) => Number.parseInt(part, 10));
        const [hour, minute] = timePart.split(':').map((part) => Number.parseInt(part, 10));
        if ([year, month, day, hour, minute].some((part) => Number.isNaN(part))) {
            return null;
        }
        return new Date(year, month - 1, day, hour, minute, 0, 0);
    };

    const formatDateTime = (date) => {
        if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
            return '';
        }
        const twoDigits = (num) => String(num).padStart(2, '0');
        const day = twoDigits(date.getDate());
        const month = twoDigits(date.getMonth() + 1);
        const year = date.getFullYear();
        const hours = twoDigits(date.getHours());
        const minutes = twoDigits(date.getMinutes());
        return `${day}.${month}.${year} ${hours}:${minutes}`;
    };

    const setEndPreviewText = (value) => {
        if (!endPreview) {
            return;
        }
        const text = value || END_PREVIEW_PLACEHOLDER;
        endPreview.textContent = text;
        if (Object.prototype.hasOwnProperty.call(endPreview, 'value')) {
            endPreview.value = text;
        }
    };

    const updateEndPreview = ({
        start,
        consultations,
        duration,
        fallback,
    } = {}) => {
        if (!endPreview) {
            return;
        }

        const startValue = typeof start === 'string' ? start : startInput ? startInput.value : '';
        const consultationsValue =
            typeof consultations === 'string' ? consultations : consultationsInput ? consultationsInput.value : '';
        const durationValue = typeof duration === 'string' ? duration : durationInput ? durationInput.value : '';
        const fallbackTextRaw = typeof fallback === 'string' ? fallback : '';
        const fallbackText = (() => {
            if (!fallbackTextRaw) {
                return '';
            }
            const fallbackDate = parseLocalDateTime(fallbackTextRaw);
            if (fallbackDate) {
                return formatDateTime(fallbackDate);
            }
            return fallbackTextRaw;
        })();

        const consultationsCount = parsePositiveInteger(consultationsValue);
        const consultationDuration = parsePositiveInteger(durationValue);
        const startDate = parseLocalDateTime(startValue);

        if (!startDate || !consultationsCount || !consultationDuration) {
            setEndPreviewText(fallbackText);
            return;
        }

        const totalMinutes = consultationsCount * consultationDuration;
        if (!Number.isFinite(totalMinutes) || totalMinutes <= 0) {
            setEndPreviewText(fallbackText);
            return;
        }

        const endDate = new Date(startDate.getTime() + totalMinutes * 60_000);
        setEndPreviewText(formatDateTime(endDate));
    };

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
        if (nameInput && Object.prototype.hasOwnProperty.call(data, 'name')) {
            const { name } = data;
            nameInput.value = typeof name === 'string' ? name : name ? String(name) : '';
        }
        if (consultationsInput && Object.prototype.hasOwnProperty.call(data, 'consultations')) {
            const { consultations } = data;
            consultationsInput.value = typeof consultations === 'string'
                ? consultations
                : consultations != null
                    ? String(consultations)
                    : '1';
        }
        if (startInput && 'start' in data) {
            startInput.value = data.start || '';
        }
        if (durationInput && Object.prototype.hasOwnProperty.call(data, 'consultationDuration')) {
            const { consultationDuration } = data;
            durationInput.value = typeof consultationDuration === 'string'
                ? consultationDuration
                : consultationDuration != null
                    ? String(consultationDuration)
                    : '1';
        }

        const fallbackEnd = Object.prototype.hasOwnProperty.call(data, 'calculatedEnd')
            ? data.calculatedEnd
            : Object.prototype.hasOwnProperty.call(data, 'end')
                ? data.end
                : '';

        updateEndPreview({
            start: Object.prototype.hasOwnProperty.call(data, 'start') ? data.start : undefined,
            consultations: Object.prototype.hasOwnProperty.call(data, 'consultations') ? data.consultations : undefined,
            duration: Object.prototype.hasOwnProperty.call(data, 'consultationDuration') ? data.consultationDuration : undefined,
            fallback: fallbackEnd,
        });

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
            name: nameInput ? nameInput.value : '',
            consultations: consultationsInput ? consultationsInput.value : '1',
            consultationDuration: durationInput ? durationInput.value : '15',
            start: startInput ? startInput.value : '',
            end: '',
            durationMinutes: '',
            calculatedEnd:
                endPreview && typeof endPreview.value === 'string' && endPreview.value
                    ? endPreview.value
                    : endPreview && endPreview.textContent
                        ? endPreview.textContent
                        : '',
        };
        const payload = { ...defaults, ...data };
        setModalMode(mode, payload);
        modal.setAttribute('data-open', 'true');
        document.body.classList.add('no-scroll');

        const focusTarget = nameInput || startInput || qs(modal, 'input, select, textarea');
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
            openModal('create', {
                eventId: '',
                name: '',
                consultations: '1',
                consultationDuration: '15',
                start: '',
                end: '',
                durationMinutes: '',
                calculatedEnd: '',
            });
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

    const recomputeEndPreview = () => {
        updateEndPreview();
    };

    [startInput, consultationsInput, durationInput]
        .filter((input) => input)
        .forEach((input) => {
            input.addEventListener('input', recomputeEndPreview);
            input.addEventListener('change', recomputeEndPreview);
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
        const nameValue = nameInput ? nameInput.value : '';
        const consultationsValue = consultationsInput ? consultationsInput.value : '1';
        const consultationDurationValue = durationInput ? durationInput.value : '15';
        const startValue = startInput ? startInput.value : '';
        const calculatedEndValue =
            endPreview && typeof endPreview.value === 'string' && endPreview.value
                ? endPreview.value
                : endPreview && endPreview.textContent
                    ? endPreview.textContent
                    : '';
        openModal(defaultMode, {
            eventId,
            name: nameValue,
            consultations: consultationsValue,
            consultationDuration: consultationDurationValue,
            start: startValue,
            calculatedEnd: calculatedEndValue,
        });
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
