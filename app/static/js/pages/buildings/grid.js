import { qs } from '../../utils/dom.js';
import { closeAllDropdowns } from '../../components/dropdowns.js';

function setupBuildingsGrid({ root = document, modalManager = null } = {}) {
    const buildingsGrid = qs(root, '.buildings-grid');
    if (!buildingsGrid) {
        return;
    }

    const deleteForm = qs(root, '[data-buildings-delete-form]');

    buildingsGrid.addEventListener('click', (event) => {
        const actionButton = event.target.closest('[data-action]');
        if (!actionButton) {
            return;
        }

        event.preventDefault();
        const action = actionButton.dataset.action;
        closeAllDropdowns();

        if (action === 'edit' && modalManager) {
            const buildingId = actionButton.dataset.buildingId || '';
            const name = actionButton.dataset.buildingName || '';
            const address = actionButton.dataset.buildingAddress || '';
            modalManager.open('update', { buildingId, name, address });
            return;
        }

        if (action === 'delete') {
            if (!deleteForm) {
                return;
            }

            const buildingId = actionButton.dataset.buildingId || '';
            const buildingName = actionButton.dataset.buildingName || '';
            const confirmationMessage = buildingName
                ? `Удалить здание «${buildingName}»?`
                : 'Удалить выбранное здание?';

            if (!window.confirm(confirmationMessage)) {
                return;
            }

            const formTypeField = qs(deleteForm, 'input[name="form_type"]');
            const buildingIdField = qs(deleteForm, 'input[name="building_id"]');

            if (formTypeField) {
                formTypeField.value = 'delete';
            }
            if (buildingIdField) {
                buildingIdField.value = buildingId;
            }

            deleteForm.submit();
        }
    });
}

export { setupBuildingsGrid };
