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

    const copyButtons = document.querySelectorAll('[data-copy-text]');
    copyButtons.forEach((button) => {
        const originalTitle = button.getAttribute('aria-label') || '';

        button.addEventListener('click', async () => {
            const text = button.dataset.copyText;
            if (!text) {
                return;
            }

            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(text);
                } else {
                    const tempInput = document.createElement('input');
                    tempInput.value = text;
                    document.body.appendChild(tempInput);
                    tempInput.select();
                    document.execCommand('copy');
                    document.body.removeChild(tempInput);
                }

                button.classList.add('is-copied');
                button.setAttribute('aria-label', 'Скопировано');
                window.setTimeout(() => {
                    button.classList.remove('is-copied');
                    button.setAttribute('aria-label', originalTitle);
                }, 2000);
            } catch (error) {
                console.error('Не удалось скопировать ссылку', error);
            }
        });
    });
});