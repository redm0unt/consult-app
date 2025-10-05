import { setupDropdowns } from '../../components/dropdowns.js';
import { setupTeachersModal } from './modal.js';
import { setupTeacherGrid } from './grid.js';
import { setupTeacherImport } from './import.js';

function initTeachersPage(root = document) {
    const modalManager = setupTeachersModal(root);
    setupDropdowns(root);
    setupTeacherGrid({ root, modalManager });
    setupTeacherImport(root);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initTeachersPage(), { once: true });
} else {
    initTeachersPage();
}

export { initTeachersPage };
