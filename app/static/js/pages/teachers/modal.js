import { qs, qsa } from '../../utils/dom.js';

function setupTeachersModal(root = document) {
    const modal = qs(root, '[data-teachers-modal]');
    if (!modal) {
        return null;
    }

    const openButton = qs(root, '[data-teachers-add]');
    const closeButtons = qsa(modal, '[data-teachers-close]');
    const overlay = qs(modal, '.teachers-modal__overlay');
    const dialog = qs(modal, '.teachers-modal__dialog');
    const modalForm = qs(modal, 'form');
    const modalTitle = qs(modal, '#teacher-modal-title');
    const fullNameInput = qs(modal, '#teacher_full_name');
    const emailInput = qs(modal, '#teacher_email');
    const passwordInput = qs(modal, '#teacher_password');
    const passwordField = qs(modal, '[data-password-field]');
    const formTypeInput = modalForm ? qs(modalForm, 'input[name="form_type"]') : null;
    const teacherIdInput = modalForm ? qs(modalForm, 'input[name="teacher_id"]') : null;
    const submitButton = modalForm ? qs(modalForm, 'button[type="submit"]') : null;
    const focusableSelectors = 'input, button, [href], [tabindex]:not([tabindex="-1"])';

    let lastFocusedElement = null;

    const setModalMode = (mode, data = {}) => {
        const normalizedMode = mode === 'update' ? 'update' : 'create';
        modal.dataset.mode = normalizedMode;

        if ('teacherId' in data && data.teacherId) {
            modal.dataset.teacherId = data.teacherId;
        } else {
            delete modal.dataset.teacherId;
        }

        if (formTypeInput) {
            formTypeInput.value = normalizedMode;
        }
        if (teacherIdInput && 'teacherId' in data) {
            teacherIdInput.value = data.teacherId || '';
        }
        if (fullNameInput && 'fullName' in data) {
            fullNameInput.value = data.fullName || '';
        }
        if (emailInput && 'email' in data) {
            emailInput.value = data.email || '';
        }

        if (normalizedMode === 'update') {
            if (modalTitle) {
                modalTitle.textContent = 'Редактирование учителя';
            }
            if (passwordField) {
                passwordField.hidden = true;
            }
            if (passwordInput) {
                passwordInput.required = false;
                passwordInput.value = '';
            }
            if (submitButton) {
                submitButton.textContent = 'Сохранить изменения';
            }
        } else {
            if (modalTitle) {
                modalTitle.textContent = 'Добавление учителя';
            }
            if (passwordField) {
                passwordField.hidden = false;
            }
            if (passwordInput) {
                passwordInput.required = true;
                passwordInput.value = '';
            }
            if (submitButton) {
                submitButton.textContent = 'Сохранить';
            }
        }
    };

    const openModal = (mode = modal.dataset.mode || 'create', data = {}) => {
        lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        setModalMode(mode, data);
        modal.setAttribute('data-open', 'true');
        document.body.classList.add('no-scroll');

        const firstInput = fullNameInput || qs(modal, 'input');
        window.setTimeout(() => {
            if (firstInput) {
                firstInput.focus();
            }
        }, 10);
    };

    const closeModal = () => {
        modal.removeAttribute('data-open');
        document.body.classList.remove('no-scroll');

        const focusTarget = lastFocusedElement || openButton;
        if (focusTarget && typeof focusTarget.focus === 'function') {
            focusTarget.focus();
        }
    };

    if (openButton && !openButton.dataset.modalBound) {
        openButton.addEventListener('click', () => {
            openModal('create', { teacherId: '', fullName: '', email: '' });
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
        const teacherId = modal.dataset.teacherId || '';
        openModal(defaultMode, { teacherId });
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

export { setupTeachersModal };
