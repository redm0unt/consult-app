import {
    SELECTORS,
    qs,
    toggleClass,
    setAriaExpanded,
    matches,
} from '../utils/dom.js';

const STATE_CLASSES = {
    open: 'is-open',
};

function openMenu(toggle, menu) {
    toggleClass(toggle, STATE_CLASSES.open, true);
    toggleClass(menu, STATE_CLASSES.open, true);
    setAriaExpanded(toggle, true);
}

function closeMenu(toggle, menu) {
    toggleClass(toggle, STATE_CLASSES.open, false);
    toggleClass(menu, STATE_CLASSES.open, false);
    setAriaExpanded(toggle, false);
}

function setupAccountMenu(root = document) {
    const toggle = qs(root, SELECTORS.accountMenuToggle);
    const menu = qs(root, SELECTORS.accountMenu);

    if (!toggle || !menu) {
        return;
    }

    const isOpen = () => toggle.classList.contains(STATE_CLASSES.open);

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        if (isOpen()) {
            closeMenu(toggle, menu);
        } else {
            openMenu(toggle, menu);
        }
    });

    menu.addEventListener('click', (event) => event.stopPropagation());

    document.addEventListener('click', () => {
        if (isOpen()) {
            closeMenu(toggle, menu);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && isOpen()) {
            closeMenu(toggle, menu);
            toggle.focus();
        }
    });

    document.addEventListener('focusin', (event) => {
        if (!isOpen()) {
            return;
        }

        const target = event.target;
        if (!matches(target, SELECTORS.accountMenu) && target !== toggle && !menu.contains(target)) {
            closeMenu(toggle, menu);
        }
    });
}

export { setupAccountMenu };
