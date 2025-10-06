import { setupDropdowns } from '../../components/dropdowns.js';
import { setupEventsModal } from './modal.js';
import { setupEventsGrid } from './grid.js';

function initEventsPage(root = document) {
    const modalManager = setupEventsModal(root);
    setupDropdowns(root);
    setupEventsGrid({ root, modalManager });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initEventsPage(), { once: true });
} else {
    initEventsPage();
}

export { initEventsPage };
