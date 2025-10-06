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
    const currentStepInput = modalForm ? qs(modalForm, 'input[name="current_step"]') : null;
    const submitButton = modalForm ? qs(modalForm, 'button[type="submit"]') : null;

    const stepper = qs(modal, '[data-event-stepper]');
    const stepButtons = stepper ? qsa(stepper, '[data-event-step-button]') : [];
    const stagesContainer = qs(modal, '[data-event-stages]');
    const stageElements = stagesContainer ? qsa(stagesContainer, '[data-event-stage]') : [];
    const navigation = qs(modal, '[data-event-navigation]');
    const nextButton = navigation ? qs(navigation, '[data-event-step-next]') : null;
    const prevButton = navigation ? qs(navigation, '[data-event-step-prev]') : null;
    const teacherSelectAll = qs(modal, '[data-event-teachers-select-all]');
    const teacherCountEl = qs(modal, '[data-event-teachers-count]');
    const teacherList = qs(modal, '[data-event-teachers-list]');
    const focusableSelectors = 'input, select, textarea, button, [href], [tabindex]:not([tabindex="-1"])';

    const steps = stageElements
        .map((stage) => stage.dataset.eventStage)
        .filter((value, index, array) => typeof value === 'string' && value && array.indexOf(value) === index);

    const primaryStep = steps[0] || 'basic';
    const finalStep = steps[steps.length - 1] || primaryStep;

    let currentStep = (currentStepInput && currentStepInput.value) ? currentStepInput.value : primaryStep;
    if (!steps.includes(currentStep)) {
        currentStep = primaryStep;
    }
    if (currentStepInput) {
        currentStepInput.value = currentStep;
    }

    let lastFocusedElement = null;
    const END_PREVIEW_PLACEHOLDER = '—';

    const teacherCheckboxes = () => qsa(modal, '[data-event-teacher-checkbox]');

    const sanitizeStep = (value) => {
        const stepValue = typeof value === 'string' && value ? value : primaryStep;
        return steps.includes(stepValue) ? stepValue : primaryStep;
    };

    const getSelectedTeacherIds = () => teacherCheckboxes()
        .filter((checkbox) => checkbox.checked)
        .map((checkbox) => checkbox.value);

    const clearTeacherErrorHighlight = () => {
        if (!teacherList) {
            return;
        }
        if (teacherList.dataset.errorTimeout) {
            window.clearTimeout(Number(teacherList.dataset.errorTimeout));
            delete teacherList.dataset.errorTimeout;
        }
        teacherList.classList.remove('events-modal__teachers-list--error');
    };

    const updateTeachersUI = () => {
        const checkboxes = teacherCheckboxes();
        const total = checkboxes.length;
        const selected = checkboxes.filter((checkbox) => checkbox.checked).length;

        if (teacherCountEl) {
            teacherCountEl.textContent = String(selected);
        }

        if (teacherSelectAll) {
            if (total === 0) {
                teacherSelectAll.checked = false;
                teacherSelectAll.indeterminate = false;
                teacherSelectAll.disabled = true;
            } else {
                teacherSelectAll.disabled = false;
                teacherSelectAll.checked = selected === total && total > 0;
                teacherSelectAll.indeterminate = selected > 0 && selected < total;
            }
        }

        if (teacherList && selected > 0) {
            clearTeacherErrorHighlight();
        }
    };

    const markTeachersError = () => {
        if (!teacherList) {
            return;
        }
        teacherList.classList.add('events-modal__teachers-list--error');
        if (teacherList.dataset.errorTimeout) {
            window.clearTimeout(Number(teacherList.dataset.errorTimeout));
        }
        const timeoutId = window.setTimeout(() => {
            clearTeacherErrorHighlight();
        }, 1600);
        teacherList.dataset.errorTimeout = String(timeoutId);
    };

    const applyTeacherSelection = (teacherIds) => {
        const checkboxes = teacherCheckboxes();
        if (!checkboxes.length) {
            return;
        }

        if (teacherIds == null) {
            checkboxes.forEach((checkbox) => {
                checkbox.checked = true;
            });
            updateTeachersUI();
            return;
        }

        let selection = teacherIds;
        if (typeof selection === 'string') {
            selection = selection
                .split(',')
                .map((value) => value.trim())
                .filter(Boolean);
        }

        if (!Array.isArray(selection)) {
            selection = [selection];
        }

        const selectionSet = new Set(selection.map((item) => String(item)));

        checkboxes.forEach((checkbox) => {
            checkbox.checked = selectionSet.has(String(checkbox.value));
        });

        updateTeachersUI();
    };

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

    const focusFirstElementForStep = (stepValue) => {
        const stage = stageElements.find((element) => element.dataset.eventStage === stepValue);
        if (!stage) {
            return;
        }
        const focusTarget = qs(stage, 'input, select, textarea, button:not([type="submit"])');
        if (focusTarget && typeof focusTarget.focus === 'function') {
            focusTarget.focus();
        }
    };

    const setStep = (value, { focus = false } = {}) => {
        const nextStep = sanitizeStep(value);
        currentStep = nextStep;

        if (currentStepInput) {
            currentStepInput.value = nextStep;
        }

        stageElements.forEach((stage) => {
            const stageValue = stage.dataset.eventStage;
            const isActive = stageValue === nextStep;
            stage.classList.toggle('events-modal__stage--active', isActive);
            stage.setAttribute('aria-hidden', isActive ? 'false' : 'true');
        });

        stepButtons.forEach((button) => {
            const stepValue = button.dataset.eventStepValue;
            const isActive = stepValue === nextStep;
            button.classList.toggle('events-modal__step--active', isActive);
            button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });

        if (prevButton) {
            const disablePrev = nextStep === primaryStep;
            prevButton.disabled = disablePrev;
            prevButton.classList.toggle('events-modal__nav-button--disabled', disablePrev);
        }

        if (nextButton) {
            const isLast = nextStep === finalStep;
            nextButton.hidden = isLast || steps.length <= 1;
        }

        if (submitButton) {
            const isLast = nextStep === finalStep;
            submitButton.hidden = steps.length > 1 && !isLast;
        }

        if (navigation) {
            navigation.hidden = steps.length <= 1;
        }

        if (focus) {
            window.setTimeout(() => focusFirstElementForStep(nextStep), 10);
        }
    };

    const normalizeMode = (mode) => (mode === 'update' ? 'update' : 'create');

    const validateBasicStep = () => {
        const requiredInputs = [nameInput, startInput, consultationsInput, durationInput].filter(Boolean);
        if (!requiredInputs.length) {
            return true;
        }
        for (const input of requiredInputs) {
            if (!input.checkValidity()) {
                input.reportValidity();
                return false;
            }
        }
        return true;
    };

    const validateTeacherSelection = () => {
        const checkboxes = teacherCheckboxes();
        if (!checkboxes.length) {
            return true;
        }
        const hasSelection = checkboxes.some((checkbox) => checkbox.checked);
        if (!hasSelection) {
            markTeachersError();
        }
        return hasSelection;
    };

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

        if (Object.prototype.hasOwnProperty.call(data, 'teacherIds')) {
            applyTeacherSelection(data.teacherIds);
        } else {
            updateTeachersUI();
        }

        const nextStep = Object.prototype.hasOwnProperty.call(data, 'step') ? data.step : currentStep;
        setStep(nextStep);

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
            teacherIds: getSelectedTeacherIds(),
            step: currentStepInput && currentStepInput.value ? currentStepInput.value : currentStep,
        };
        const payload = { ...defaults, ...data };
        setModalMode(mode, payload);
        modal.setAttribute('data-open', 'true');
        document.body.classList.add('no-scroll');

        window.setTimeout(() => focusFirstElementForStep(currentStep), 10);
    };

    const closeModal = () => {
        modal.removeAttribute('data-open');
        document.body.classList.remove('no-scroll');

        setStep(primaryStep);
        updateTeachersUI();

        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
            lastFocusedElement.focus();
        } else if (openButton && typeof openButton.focus === 'function') {
            openButton.focus();
        }
    };

    setStep(currentStep);
    updateTeachersUI();

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
                teacherIds: null,
                step: primaryStep,
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

    const goToNextStep = () => {
        if (!steps.length) {
            return;
        }
        const currentIndex = steps.indexOf(currentStep);
        const nextIndex = Math.min(currentIndex + 1, steps.length - 1);
        const nextStep = steps[nextIndex];
        if (currentIndex === nextIndex) {
            return;
        }
        if (currentStep === primaryStep && !validateBasicStep()) {
            return;
        }
        setStep(nextStep, { focus: true });
    };

    const goToPreviousStep = () => {
        if (!steps.length) {
            return;
        }
        const currentIndex = steps.indexOf(currentStep);
        const prevIndex = Math.max(currentIndex - 1, 0);
        const prevStep = steps[prevIndex];
        if (currentIndex === prevIndex) {
            return;
        }
        setStep(prevStep, { focus: true });
    };

    if (nextButton) {
        nextButton.addEventListener('click', goToNextStep);
    }

    if (prevButton) {
        prevButton.addEventListener('click', goToPreviousStep);
    }

    stepButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const targetStep = sanitizeStep(button.dataset.eventStepValue);
            if (targetStep === currentStep) {
                return;
            }
            const currentIndex = steps.indexOf(currentStep);
            const targetIndex = steps.indexOf(targetStep);
            if (currentIndex < targetIndex && currentStep === primaryStep && !validateBasicStep()) {
                return;
            }
            setStep(targetStep, { focus: true });
        });
    });

    teacherCheckboxes().forEach((checkbox) => {
        checkbox.addEventListener('change', () => {
            updateTeachersUI();
        });
    });

    if (teacherSelectAll) {
        teacherSelectAll.addEventListener('change', () => {
            const shouldSelect = Boolean(teacherSelectAll.checked);
            teacherCheckboxes().forEach((checkbox) => {
                checkbox.checked = shouldSelect;
            });
            updateTeachersUI();
        });
    }

    if (modalForm) {
        modalForm.addEventListener('submit', (event) => {
            if (currentStep !== finalStep) {
                event.preventDefault();
                if (currentStep === primaryStep && !validateBasicStep()) {
                    return;
                }
                setStep(finalStep, { focus: true });
                return;
            }

            if (!validateTeacherSelection()) {
                event.preventDefault();
            }
        });
    }

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
            teacherIds: getSelectedTeacherIds(),
            step: currentStepInput && currentStepInput.value ? currentStepInput.value : currentStep,
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
