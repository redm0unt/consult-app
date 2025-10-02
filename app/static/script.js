// Sidebar account actions popup menu
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.querySelector('.sidebar-account-actions');
    const menu = document.querySelector('.sidebar-popup-menu');

    if (toggle && menu) {
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
    }

    const alerts = document.querySelectorAll('.alerts-area .alert');
    alerts.forEach((alert) => {
        const hideAlert = () => {
            if (alert.dataset.dismissed === 'true') {
                return;
            }
            alert.dataset.dismissed = 'true';
            alert.classList.add('is-hidden');
            window.setTimeout(() => {
                alert.remove();
            }, 300);
        };

        const closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', hideAlert, { once: true });
        }

        window.setTimeout(hideAlert, 10000);
    });
});