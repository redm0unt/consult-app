import { qs, qsa } from '../../utils/dom.js';

function setupBuildingsModal(root = document) {
    const modal = qs(root, '[data-buildings-modal]');
    if (!modal) {
        return null;
    }

    const openButton = qs(root, '[data-buildings-add]');
    const closeButtons = qsa(modal, '[data-buildings-close]');
    const overlay = qs(modal, '.buildings-modal__overlay');
    const dialog = qs(modal, '.buildings-modal__dialog');
    const modalForm = qs(modal, 'form');
    const modalTitle = qs(modal, '#building-modal-title');
    const nameInput = qs(modal, '#building_name');
    const addressInput = qs(modal, '#building_address');
    const formTypeInput = modalForm ? qs(modalForm, 'input[name="form_type"]') : null;
    const buildingIdInput = modalForm ? qs(modalForm, 'input[name="building_id"]') : null;
    const submitButton = modalForm ? qs(modalForm, 'button[type="submit"]') : null;
    const focusableSelectors = 'input, textarea, button, [href], [tabindex]:not([tabindex="-1"])';

    let lastFocusedElement = null;

    const setModalMode = (mode, data = {}) => {
        const normalizedMode = mode === 'update' ? 'update' : 'create';
        modal.dataset.mode = normalizedMode;

        if ('buildingId' in data && data.buildingId) {
            modal.dataset.buildingId = data.buildingId;
        } else {
            delete modal.dataset.buildingId;
        }

        if (formTypeInput) {
            formTypeInput.value = normalizedMode;
        }
        if (buildingIdInput && 'buildingId' in data) {
            buildingIdInput.value = data.buildingId || '';
        }
        if (nameInput && 'name' in data) {
            nameInput.value = data.name || '';
        }
        if (addressInput && 'address' in data) {
            addressInput.value = data.address || '';
        }

        if (normalizedMode === 'update') {
            if (modalTitle) {
                modalTitle.textContent = 'Редактирование здания';
            }
            if (submitButton) {
                submitButton.textContent = 'Сохранить изменения';
            }
        } else {
            if (modalTitle) {
                modalTitle.textContent = 'Добавление здания';
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

        const focusTarget = nameInput || qs(modal, 'input, textarea');
        window.setTimeout(() => {
            if (focusTarget) {
                focusTarget.focus();
                if (focusTarget instanceof HTMLInputElement || focusTarget instanceof HTMLTextAreaElement) {
                    focusTarget.setSelectionRange(focusTarget.value.length, focusTarget.value.length);
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
            openModal('create', { buildingId: '', name: '', address: '' });
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
        const buildingId = modal.dataset.buildingId || '';
        const nameValue = nameInput ? nameInput.value : '';
        const addressValue = addressInput ? addressInput.value : '';
        openModal(defaultMode, { buildingId, name: nameValue, address: addressValue });
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

export { setupBuildingsModal };
