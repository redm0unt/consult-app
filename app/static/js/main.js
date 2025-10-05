import { setupAccountMenu } from './components/account-menu.js';
import { setupAlerts } from './components/alerts.js';
import { setupCopyButtons } from './components/copy-buttons.js';
import { setupSearchForms } from './components/search.js';

function init() {
    setupAccountMenu();
    setupAlerts();
    setupCopyButtons();
    setupSearchForms();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
    init();
}
