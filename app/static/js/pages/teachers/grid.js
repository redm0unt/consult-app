import { qs } from '../../utils/dom.js';
import { closeAllDropdowns } from '../../components/dropdowns.js';

function setupTeacherGrid({ root = document, modalManager = null } = {}) {
    const teacherGrid = qs(root, '.teachers-grid');
    if (!teacherGrid) {
        return;
    }

    const deleteForm = qs(root, '[data-teachers-delete-form]');

    teacherGrid.addEventListener('click', (event) => {
        const actionButton = event.target.closest('[data-action]');
        if (!actionButton) {
            return;
        }

        event.preventDefault();
        const action = actionButton.dataset.action;
        closeAllDropdowns();

        if (action === 'edit' && modalManager) {
            const teacherId = actionButton.dataset.teacherId || '';
            const fullName = actionButton.dataset.teacherFullName || '';
            const email = actionButton.dataset.teacherEmail || '';
            modalManager.open('update', { teacherId, fullName, email });
            return;
        }

        if (action === 'delete') {
            if (!deleteForm) {
                return;
            }

            const teacherId = actionButton.dataset.teacherId || '';
            const teacherName = actionButton.dataset.teacherName || '';
            const confirmationMessage = teacherName
                ? `Удалить учителя «${teacherName}»?`
                : 'Удалить выбранного учителя?';

            if (!window.confirm(confirmationMessage)) {
                return;
            }

            const formTypeField = qs(deleteForm, 'input[name="form_type"]');
            const teacherIdField = qs(deleteForm, 'input[name="teacher_id"]');

            if (formTypeField) {
                formTypeField.value = 'delete';
            }
            if (teacherIdField) {
                teacherIdField.value = teacherId;
            }

            deleteForm.submit();
        }
    });
}

export { setupTeacherGrid };
