import { SELECTORS, qs, qsa } from '../utils/dom.js';

const DROPDOWN_ATTRIBUTE = 'data-open';
let bound = false;
const trackedDropdowns = new Set();

function isOpen(dropdown) {
    return dropdown.hasAttribute(DROPDOWN_ATTRIBUTE);
}

function setExpanded(dropdown, expanded) {
    const toggle = qs(dropdown, SELECTORS.dropdownToggle);
    if (toggle) {
        toggle.setAttribute('aria-expanded', String(expanded));
    }
}

function openDropdown(dropdown) {
    dropdown.setAttribute(DROPDOWN_ATTRIBUTE, 'true');
    setExpanded(dropdown, true);
}

function closeDropdown(dropdown) {
    dropdown.removeAttribute(DROPDOWN_ATTRIBUTE);
    setExpanded(dropdown, false);
}

function closeAllDropdowns(except = null) {
    trackedDropdowns.forEach((dropdown) => {
        if (dropdown === except) {
            return;
        }
        closeDropdown(dropdown);
    });
}

function bindGlobalListeners() {
    if (bound) {
        return;
    }

    document.addEventListener('click', () => {
        closeAllDropdowns();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeAllDropdowns();
        }
    });

    bound = true;
}

function registerDropdown(dropdown) {
    const toggle = qs(dropdown, SELECTORS.dropdownToggle);
    if (!toggle) {
        return;
    }

    if (!dropdown.dataset.dropdownBound) {
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const currentlyOpen = isOpen(dropdown);
            if (currentlyOpen) {
                closeDropdown(dropdown);
            } else {
                closeAllDropdowns(dropdown);
                openDropdown(dropdown);
            }
        });

        dropdown.dataset.dropdownBound = 'true';
    }

    trackedDropdowns.add(dropdown);
}

function setupDropdowns(root = document) {
    const dropdowns = qsa(root, SELECTORS.dropdown);
    if (!dropdowns.length) {
        return;
    }

    dropdowns.forEach(registerDropdown);
    bindGlobalListeners();
}

export { setupDropdowns, closeAllDropdowns };
