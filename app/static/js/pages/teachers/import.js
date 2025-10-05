import { qs } from '../../utils/dom.js';
import { createAlert } from '../../components/alerts.js';

const LOADING_MARKUP = '<span class="button__icon" aria-hidden="true">⏳</span><span>Загрузка…</span>';

function buildTeachersDetailsList(teachers) {
    if (!Array.isArray(teachers) || !teachers.length) {
        return null;
    }

    return teachers.map((teacher) => {
        const name = teacher.full_name || '—';
        const email = teacher.email || '—';
        const password = teacher.password || '—';
        return `${name} — ${email} — пароль: ${password}`;
    });
}

function handleImportResponse(data) {
    if (!data) {
        createAlert({ message: 'Не удалось обработать ответ сервера', type: 'danger' });
        return;
    }

    if (!data.success) {
        const message = data.message || 'Не удалось загрузить учителей';
        const details = Array.isArray(data.errors) ? data.errors : null;
        createAlert({ message, type: 'danger', details });
        return;
    }

    if (Array.isArray(data.errors) && data.errors.length) {
        createAlert({
            message: 'Некоторые строки были пропущены при импорте:',
            type: 'warning',
            details: data.errors,
        });
    }

    const details = buildTeachersDetailsList(data.teachers);
    createAlert({
        message: data.message || 'Учителя успешно загружены',
        type: 'success',
        details,
    });

    window.setTimeout(() => {
        window.location.reload();
    }, 1200);
}

function setupTeacherImport(root = document) {
    const importForm = qs(root, '[data-teachers-import]');
    if (!importForm) {
        return;
    }

    const importInput = qs(importForm, '[data-teachers-import-input]');
    const importTrigger = qs(importForm, '[data-teachers-import-trigger]');

    if (!importInput || !importTrigger) {
        return;
    }

    let isUploading = false;
    const originalTriggerHtml = importTrigger.innerHTML;

    const resetImportState = () => {
        importTrigger.disabled = false;
        importTrigger.classList.remove('is-loading');
        importTrigger.innerHTML = originalTriggerHtml;
        isUploading = false;
    };

    importTrigger.addEventListener('click', (event) => {
        event.preventDefault();
        if (isUploading) {
            return;
        }
        importInput.click();
    });

    importInput.addEventListener('change', async () => {
        if (!importInput.files || !importInput.files.length || isUploading) {
            return;
        }

        const file = importInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        isUploading = true;
        importTrigger.disabled = true;
        importTrigger.classList.add('is-loading');
        importTrigger.innerHTML = LOADING_MARKUP;

        try {
            const response = await fetch(importForm.action, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json().catch(() => null);
            if (!response.ok) {
                const composed = data && (data.message || (Array.isArray(data.errors) && data.errors.length))
                    ? { success: false, ...data }
                    : { success: false, message: 'Произошла ошибка при загрузке файла. Попробуйте позже' };
                handleImportResponse(composed);
                return;
            }

            handleImportResponse(data);
        } catch (error) {
            console.error('Failed to upload teachers file', error);
            createAlert({
                message: 'Произошла ошибка при загрузке файла. Попробуйте позже',
                type: 'danger',
            });
        } finally {
            importInput.value = '';
            resetImportState();
        }
    });
}

export { setupTeacherImport };
