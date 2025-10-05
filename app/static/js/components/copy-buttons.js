import { SELECTORS, qsa } from '../utils/dom.js';

const STATE_CLASSES = {
    copied: 'is-copied',
};

const COPY_SUCCESS_LABEL = 'Скопировано';
const COPY_RESET_TIMEOUT = 2000;

async function writeToClipboard(text) {
    if (!text) {
        return false;
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

        return true;
    } catch (error) {
        console.error('Не удалось скопировать текст', error);
        return false;
    }
}

function setupCopyButtons(root = document) {
    const buttons = qsa(root, SELECTORS.copyButton);
    if (!buttons.length) {
        return;
    }

    buttons.forEach((button) => {
        const defaultLabel = button.getAttribute('aria-label') ?? '';

        button.addEventListener('click', async () => {
            const text = button.dataset.copyText;
            const copied = await writeToClipboard(text);

            if (!copied) {
                return;
            }

            button.classList.add(STATE_CLASSES.copied);
            button.setAttribute('aria-label', COPY_SUCCESS_LABEL);

            setTimeout(() => {
                button.classList.remove(STATE_CLASSES.copied);
                button.setAttribute('aria-label', defaultLabel);
            }, COPY_RESET_TIMEOUT);
        });
    });
}

export { setupCopyButtons };
