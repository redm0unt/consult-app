import { setupDropdowns } from '../../components/dropdowns.js';
import { setupBuildingsModal } from './modal.js';
import { setupBuildingsGrid } from './grid.js';

function initBuildingsPage(root = document) {
    const modalManager = setupBuildingsModal(root);
    setupDropdowns(root);
    setupBuildingsGrid({ root, modalManager });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initBuildingsPage(), { once: true });
} else {
    initBuildingsPage();
}

export { initBuildingsPage };
