// Sidebar account actions popup menu
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.querySelector('.sidebar-account-actions');
    const menu = document.querySelector('.sidebar-popup-menu');

    if (!toggle || !menu) {
        return;
    }

    const openMenu = () => {
        toggle.classList.add('is-open');
        menu.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
    };

    const closeMenu = () => {
        toggle.classList.remove('is-open');
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
    };

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        if (toggle.classList.contains('is-open')) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    menu.addEventListener('click', (event) => {
        event.stopPropagation();
    });

    document.addEventListener('click', () => {
        if (toggle.classList.contains('is-open')) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && toggle.classList.contains('is-open')) {
            closeMenu();
            toggle.focus();
        }
    });
});