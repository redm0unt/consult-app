import { setupDropdowns } from '../../components/dropdowns.js';
import { setupEventsModal } from './modal.js';
import { setupEventsGrid } from './grid.js';
import { setupEventsDetails } from './details.js';

function initEventsPage(root = document) {
    const modalManager = setupEventsModal(root);
    setupEventsDetails(root);
    setupDropdowns(root);
    setupEventsGrid({ root, modalManager });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initEventsPage(), { once: true });
} else {
    initEventsPage();
}

export { initEventsPage };
