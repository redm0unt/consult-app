import { qs } from '../../utils/dom.js';
import { closeAllDropdowns } from '../../components/dropdowns.js';

function setupEventsGrid({ root = document, modalManager = null } = {}) {
    const eventsGrid = qs(root, '.events-grid');
    if (!eventsGrid) {
        return;
    }

    const deleteForm = qs(root, '[data-events-delete-form]');

    eventsGrid.addEventListener('click', (event) => {
        const actionButton = event.target.closest('[data-action]');
        if (!actionButton) {
            return;
        }

        event.preventDefault();
        const action = actionButton.dataset.action;
        closeAllDropdowns();

        if (action === 'edit' && modalManager) {
            const eventId = actionButton.dataset.eventId || '';
            const start = actionButton.dataset.eventStart || '';
            const end = actionButton.dataset.eventEnd || '';
            const name = actionButton.dataset.eventName || '';
            const consultations = actionButton.dataset.eventConsultations || '0';
            const consultationDuration = actionButton.dataset.eventConsultationDuration || '';
            const durationMinutes = actionButton.dataset.eventDurationMinutes || '';
            const teachersRaw = actionButton.dataset.eventTeachers || '';
            const teacherIds = teachersRaw
                ? teachersRaw.split(',').map((value) => value.trim()).filter(Boolean)
                : [];
            modalManager.open('update', {
                eventId,
                name,
                consultations,
                consultationDuration,
                durationMinutes,
                start,
                end,
                teacherIds,
                step: 'basic',
            });
            return;
        }

        if (action === 'delete') {
            if (!deleteForm) {
                return;
            }

            const eventId = actionButton.dataset.eventId || '';
            const eventPeriod = actionButton.dataset.eventPeriod || '';
            const eventName = actionButton.dataset.eventName || '';
            let confirmationMessage = 'Удалить выбранное мероприятие?';

            if (eventName && eventPeriod) {
                confirmationMessage = `Удалить мероприятие «${eventName}» (${eventPeriod})?`;
            } else if (eventName) {
                confirmationMessage = `Удалить мероприятие «${eventName}»?`;
            } else if (eventPeriod) {
                confirmationMessage = `Удалить мероприятие (${eventPeriod})?`;
            }

            if (!window.confirm(confirmationMessage)) {
                return;
            }

            const formTypeField = qs(deleteForm, 'input[name="form_type"]');
            const eventIdField = qs(deleteForm, 'input[name="event_id"]');

            if (formTypeField) {
                formTypeField.value = 'delete';
            }
            if (eventIdField) {
                eventIdField.value = eventId;
            }

            deleteForm.submit();
        }
    });
}

export { setupEventsGrid };
