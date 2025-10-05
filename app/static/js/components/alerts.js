import {
    SELECTORS,
    DATASET_FLAGS,
    qs,
    qsa,
    matches,
    setDataFlag,
    getDataFlag,
} from '../utils/dom.js';

const ALERT_CLASSES = {
    hidden: 'is-hidden',
};

const ALERT_TIMEOUT = 10000;
const ALERT_REMOVE_DELAY = 300;

let cachedCloseButtonBackground = '';

function closeAlert(alert) {
    if (!alert || getDataFlag(alert, DATASET_FLAGS.dismissed) === 'true') {
        return;
    }

    setDataFlag(alert, DATASET_FLAGS.dismissed, true);
    alert.classList.add(ALERT_CLASSES.hidden);

    setTimeout(() => {
        alert.remove();
    }, ALERT_REMOVE_DELAY);
}

function configureAlert(alert) {
    const closeButton =
        qs(alert, SELECTORS.closeButton) || qs(alert, SELECTORS.closeAlertButton);

    if (closeButton) {
        closeButton.addEventListener('click', () => closeAlert(alert), {
            once: true,
        });
    }

    setTimeout(() => closeAlert(alert), ALERT_TIMEOUT);
}

function setupAlerts(root = document) {
    const container = qs(root, SELECTORS.alertContainer);
    if (!container) {
        return;
    }

    const alerts = qsa(container, SELECTORS.alert);
    alerts.forEach(configureAlert);

    if (!cachedCloseButtonBackground && container.dataset.alertCloseIcon) {
        cachedCloseButtonBackground = `url('${container.dataset.alertCloseIcon}')`;
    }

    if (!cachedCloseButtonBackground) {
        const sampleButton =
            qs(container, SELECTORS.closeButton) || qs(container, SELECTORS.closeAlertButton);
        if (sampleButton) {
            cachedCloseButtonBackground = sampleButton.style.backgroundImage || '';
        }
    }

    container.addEventListener('click', (event) => {
        const target = event.target;
        if (matches(target, SELECTORS.closeButton) || matches(target, SELECTORS.closeAlertButton)) {
            const alert = target.closest(SELECTORS.alert);
            closeAlert(alert);
        }
    });
}

function createAlert({ message, type = 'info', details = null }, root = document) {
    const container = qs(root, SELECTORS.alertContainer);
    if (!container) {
        if (Array.isArray(details) && details.length) {
            window.alert([message, ...details].join('\n'));
        } else {
            window.alert(message);
        }
        return null;
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible`;
    alert.setAttribute('role', 'alert');

    const messageWrapper = document.createElement('div');
    messageWrapper.textContent = message;
    alert.appendChild(messageWrapper);

    if (Array.isArray(details) && details.length) {
        const list = document.createElement('ul');
        list.className = 'alert__details';
        details.forEach((detail) => {
            const item = document.createElement('li');
            item.textContent = detail;
            list.appendChild(item);
        });
        alert.appendChild(list);
    }

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'btn-close close-alert-btn';
    closeButton.setAttribute('aria-label', 'Закрыть уведомление');

    if (cachedCloseButtonBackground) {
        closeButton.style.backgroundImage = cachedCloseButtonBackground;
    }

    alert.appendChild(closeButton);
    container.appendChild(alert);

    configureAlert(alert);
    return alert;
}

export { setupAlerts, createAlert };
