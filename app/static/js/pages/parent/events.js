const forms = document.querySelectorAll('[data-slot-form]');
const modalTemplate = document.getElementById('parent-slot-modal-template');

let modalRoot = null;
let modalConfirmButton = null;
let modalCancelButton = null;
let modalCloseElements = [];
let modalTeacher = null;
let modalTime = null;
let modalAction = null;
let modalTitle = null;
let activeForm = null;
let activeButton = null;

const ACTION_LABELS = {
    book: 'Записаться',
    cancel: 'Отменить запись',
};

const ACTION_DESCRIPTIONS = {
    book: 'Вы собираетесь записаться на консультацию.',
    cancel: 'Вы собираетесь отменить свою запись.',
};

function ensureModal() {
    if (!modalTemplate) {
        return null;
    }

    if (!modalRoot) {
        const fragment = modalTemplate.content.cloneNode(true);
        modalRoot = fragment.querySelector('[data-slot-modal]');
    modalConfirmButton = fragment.querySelector('[data-slot-modal-confirm]');
    modalCancelButton = fragment.querySelector('[data-slot-modal-cancel]');
        modalCloseElements = Array.from(fragment.querySelectorAll('[data-slot-modal-close]'));
        modalTeacher = fragment.querySelector('[data-slot-modal-teacher]');
        modalTime = fragment.querySelector('[data-slot-modal-time]');
        modalAction = fragment.querySelector('[data-slot-modal-action]');
    modalTitle = fragment.querySelector('[data-slot-modal-title]');

        document.body.appendChild(fragment);

        modalConfirmButton?.addEventListener('click', () => {
            if (!activeForm) {
                closeModal();
                return;
            }

            submitActiveForm();
        });

        const closeHandler = () => {
            closeModal();
        };

        modalCancelButton?.addEventListener('click', closeHandler);
        modalCloseElements.forEach((el) => el.addEventListener('click', closeHandler));

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && !modalRoot?.hidden) {
                event.preventDefault();
                closeModal();
            }
        });
    }

    return modalRoot;
}

function openModal(form) {
    const modal = ensureModal();
    if (!modal) {
        submitFormImmediately(form);
        return;
    }

    const button = form.querySelector('[data-slot-button]');
    activeForm = form;
    activeButton = button;

    const actionValue = form.querySelector('input[name="action"]')?.value || 'book';
    const state = (form.dataset.slotState || 'available');
    const label = ACTION_LABELS[actionValue] || ACTION_LABELS.book;
    const description = ACTION_DESCRIPTIONS[actionValue] || ACTION_DESCRIPTIONS.book;

    if (modalTitle) {
        modalTitle.textContent = actionValue === 'cancel' ? 'Отмена записи' : 'Подтверждение записи';
    }

    if (modalTeacher) {
        modalTeacher.textContent = form.dataset.slotTeacher || '—';
    }
    if (modalTime) {
        modalTime.textContent = form.dataset.slotLabel || '—';
    }
    if (modalAction) {
        modalAction.textContent = `${label}. ${description}`;
    }

    if (modalConfirmButton) {
        modalConfirmButton.textContent = label;
        modalConfirmButton.dataset.action = actionValue;
    }

    modal.hidden = false;
    modal.dataset.state = state;

    requestAnimationFrame(() => {
        modalConfirmButton?.focus();
    });
}

function closeModal() {
    if (!modalRoot || modalRoot.hidden) {
        return;
    }

    modalRoot.hidden = true;
    const buttonToFocus = activeButton;
    activeForm = null;
    activeButton = null;

    if (buttonToFocus && typeof buttonToFocus.focus === 'function') {
        buttonToFocus.focus();
    }
}

function submitActiveForm() {
    if (!activeForm) {
        closeModal();
        return;
    }

    const button = activeButton;
    if (button) {
        button.disabled = true;
        button.classList.add('parent-slot--pending');
    }

    activeForm.dataset.skipConfirm = 'true';
    const hasRequestSubmit = typeof activeForm.requestSubmit === 'function';
    if (hasRequestSubmit) {
        activeForm.requestSubmit();
    } else {
        activeForm.submit();
    }
    closeModal();
}

function submitFormImmediately(form) {
    const button = form.querySelector('[data-slot-button]');
    if (button) {
        button.disabled = true;
        button.classList.add('parent-slot--pending');
    }

    form.dataset.skipConfirm = 'true';
    if (typeof form.requestSubmit === 'function') {
        form.requestSubmit();
    } else {
        form.submit();
    }
}

forms.forEach((form) => {
    const button = form.querySelector('[data-slot-button]');
    if (!button) {
        return;
    }

    const state = form.dataset.slotState;

    if (button.disabled || state === 'taken' || state === 'closed') {
        return;
    }

    form.addEventListener('submit', (event) => {
        if (form.dataset.skipConfirm === 'true') {
            delete form.dataset.skipConfirm;
            return;
        }

        event.preventDefault();
        openModal(form);
    });
});
