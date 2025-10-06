import { setupEventsDetails } from '../events/details.js';

function initTeacherEvents(root = document) {
    setupEventsDetails(root);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initTeacherEvents(), { once: true });
} else {
    initTeacherEvents();
}

export { initTeacherEvents };
