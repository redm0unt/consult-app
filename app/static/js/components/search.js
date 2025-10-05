import { qs, qsa } from '../utils/dom.js';

function findSearchInput(start) {
    return (
        qs(start, 'input[type="search"]') || qs(start, '.search__input') || qs(start, 'input[name="q"]')
    );
}

function setupSearchForms(root = document) {
    const clearButtons = qsa(root, '[data-search-clear]');
    if (!clearButtons.length) {
        return;
    }

    clearButtons.forEach((button) => {
        const form = button.closest('form');
        const searchInput = form ? findSearchInput(form) : null;

        const toggleClearVisibility = () => {
            if (!button) {
                return;
            }
            const hasValue = Boolean(searchInput && searchInput.value.trim());
            button.hidden = !hasValue;
        };

        toggleClearVisibility();

        if (searchInput && !searchInput.dataset.searchEnhancementBound) {
            searchInput.addEventListener('input', toggleClearVisibility);
            searchInput.dataset.searchEnhancementBound = 'true';
        }

        if (!button.dataset.searchEnhancementBound) {
            button.addEventListener('click', () => {
                if (!searchInput) {
                    return;
                }
                searchInput.value = '';
                toggleClearVisibility();
                searchInput.focus();
                if (form) {
                    form.submit();
                }
            });
            button.dataset.searchEnhancementBound = 'true';
        }
    });
}

export { setupSearchForms };
