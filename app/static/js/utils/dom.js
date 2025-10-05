const SELECTORS = {
    accountMenuToggle: '.sidebar-account-actions',
    accountMenu: '.sidebar-popup-menu',
    alertContainer: '.alerts-area',
    closeButton: '.btn-close',
    closeAlertButton: '.close-alert-btn',
    alert: '.alert',
    copyButton: '[data-copy-text]',
    dropdown: '[data-dropdown]',
    dropdownToggle: '[data-dropdown-toggle]',
};

const KEYBOARD = {
    ESC: 'Escape',
};

const DATASET_FLAGS = {
    dismissed: 'dismissed',
};

function matches(element, selector) {
    return element instanceof Element && element.matches(selector);
}

function qs(root, selector) {
    if (!root) {
        return null;
    }
    return root.querySelector(selector);
}

function qsa(root, selector) {
    if (!root) {
        return [];
    }
    return Array.from(root.querySelectorAll(selector));
}

function toggleClass(element, className, force) {
    if (!element) {
        return;
    }
    element.classList.toggle(className, force);
}

function setAriaExpanded(element, value) {
    if (!element) {
        return;
    }
    element.setAttribute('aria-expanded', String(Boolean(value)));
}

function addClass(element, className) {
    if (!element) {
        return;
    }
    element.classList.add(className);
}

function removeClass(element, className) {
    if (!element) {
        return;
    }
    element.classList.remove(className);
}

function setDataFlag(element, flag, value) {
    if (!element) {
        return;
    }
    element.dataset[flag] = String(value);
}

function getDataFlag(element, flag) {
    if (!element) {
        return undefined;
    }
    return element.dataset[flag];
}

export {
    SELECTORS,
    KEYBOARD,
    DATASET_FLAGS,
    matches,
    qs,
    qsa,
    toggleClass,
    addClass,
    removeClass,
    setAriaExpanded,
    setDataFlag,
    getDataFlag,
};
