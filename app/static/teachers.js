document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.teachers-search__input');
    const clearButton = document.querySelector('[data-search-clear]');

    const toggleClearVisibility = () => {
        if (!clearButton) {
            return;
        }
        const hasValue = Boolean(searchInput && searchInput.value.trim());
        clearButton.hidden = !hasValue;
    };

    if (searchInput) {
        searchInput.addEventListener('input', toggleClearVisibility);
    }

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            if (!searchInput) {
                return;
            }
            searchInput.value = '';
            toggleClearVisibility();
            searchInput.focus();
            const form = searchInput.closest('form');
            if (form) {
                form.submit();
            }
        });
    }

    toggleClearVisibility();

    const dropdowns = Array.from(document.querySelectorAll('[data-dropdown]'));

    const closeAllDropdowns = (except = null) => {
        dropdowns.forEach((dropdown) => {
            if (dropdown === except) {
                return;
            }
            dropdown.removeAttribute('data-open');
            const toggle = dropdown.querySelector('[data-dropdown-toggle]');
            if (toggle) {
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    };

    dropdowns.forEach((dropdown) => {
        const toggle = dropdown.querySelector('[data-dropdown-toggle]');
        if (!toggle) {
            return;
        }

        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const isOpen = dropdown.hasAttribute('data-open');
            closeAllDropdowns(isOpen ? null : dropdown);
            if (!isOpen) {
                dropdown.setAttribute('data-open', 'true');
                toggle.setAttribute('aria-expanded', 'true');
            } else {
                dropdown.removeAttribute('data-open');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    });

    document.addEventListener('click', () => {
        closeAllDropdowns();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeAllDropdowns();
        }
    });

    const modal = document.querySelector('[data-teachers-modal]');
    const alertsArea = document.querySelector('.alerts-area');
    let closeButtonBackground = '';
    if (alertsArea) {
        const sampleCloseButton = alertsArea.querySelector('.btn-close');
        if (sampleCloseButton) {
            closeButtonBackground = sampleCloseButton.style.backgroundImage || '';
        }
    }

    const showAlert = (message, type = 'info', details = null) => {
        if (!alertsArea) {
            if (Array.isArray(details) && details.length) {
                window.alert([message, ...details].join('\n'));
            } else {
                window.alert(message);
            }
            return;
        }

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.setAttribute('role', 'alert');

        const messageWrapper = document.createElement('div');
        messageWrapper.textContent = message;
        alert.appendChild(messageWrapper);

        if (Array.isArray(details) && details.length) {
            const list = document.createElement('ul');
            list.className = 'mt-2 mb-0';
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
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        if (closeButtonBackground) {
            closeButton.style.backgroundImage = closeButtonBackground;
        }

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

        closeButton.addEventListener('click', hideAlert, { once: true });
        alert.appendChild(closeButton);
        alertsArea.appendChild(alert);

        window.setTimeout(hideAlert, 10000);
    };

    if (modal) {
        const openButton = document.querySelector('[data-teachers-add]');
        const closeButtons = modal.querySelectorAll('[data-teachers-close]');
        const overlay = modal.querySelector('.teachers-modal__overlay');
        const dialog = modal.querySelector('.teachers-modal__dialog');
        const modalForm = modal.querySelector('form');
        const modalTitle = modal.querySelector('#teacher-modal-title');
        const fullNameInput = modal.querySelector('#teacher_full_name');
        const emailInput = modal.querySelector('#teacher_email');
        const passwordInput = modal.querySelector('#teacher_password');
        const passwordField = modal.querySelector('[data-password-field]');
        const formTypeInput = modalForm ? modalForm.querySelector('input[name="form_type"]') : null;
        const teacherIdInput = modalForm ? modalForm.querySelector('input[name="teacher_id"]') : null;
        const submitButton = modalForm ? modalForm.querySelector('button[type="submit"]') : null;
        const focusableSelectors = 'input, button, [href], [tabindex]:not([tabindex="-1"])';

        const setModalMode = (mode, data = {}) => {
            const normalizedMode = mode === 'update' ? 'update' : 'create';
            modal.dataset.mode = normalizedMode;
            if ('teacherId' in data && data.teacherId) {
                modal.dataset.teacherId = data.teacherId;
            } else {
                delete modal.dataset.teacherId;
            }

            if (formTypeInput) {
                formTypeInput.value = normalizedMode;
            }
            if (teacherIdInput && 'teacherId' in data) {
                teacherIdInput.value = data.teacherId || '';
            }
            if (fullNameInput && 'fullName' in data) {
                fullNameInput.value = data.fullName || '';
            }
            if (emailInput && 'email' in data) {
                emailInput.value = data.email || '';
            }

            if (normalizedMode === 'update') {
                if (modalTitle) {
                    modalTitle.textContent = 'Редактирование учителя';
                }
                if (passwordField) {
                    passwordField.hidden = true;
                }
                if (passwordInput) {
                    passwordInput.required = false;
                    passwordInput.value = '';
                }
                if (submitButton) {
                    submitButton.textContent = 'Сохранить изменения';
                }
            } else {
                if (modalTitle) {
                    modalTitle.textContent = 'Добавление учителя';
                }
                if (passwordField) {
                    passwordField.hidden = false;
                }
                if (passwordInput) {
                    passwordInput.required = true;
                    passwordInput.value = '';
                }
                if (submitButton) {
                    submitButton.textContent = 'Сохранить';
                }
            }
        };

        const openModal = (mode = modal.dataset.mode || 'create', data = {}) => {
            setModalMode(mode, data);
            modal.setAttribute('data-open', 'true');
            const firstInput = fullNameInput || modal.querySelector('input');
            window.setTimeout(() => {
                if (firstInput) {
                    firstInput.focus();
                }
            }, 10);
            document.body.classList.add('no-scroll');
        };

        const closeModal = () => {
            modal.removeAttribute('data-open');
            document.body.classList.remove('no-scroll');
            if (openButton) {
                openButton.focus();
            }
        };

        if (openButton) {
            openButton.addEventListener('click', () => {
                openModal('create', { teacherId: '', fullName: '', email: '' });
            });
        }

        closeButtons.forEach((button) => {
            button.addEventListener('click', closeModal);
        });

        if (overlay) {
            overlay.addEventListener('click', closeModal);
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.hasAttribute('data-open')) {
                closeModal();
            }
        });

        if (modal.hasAttribute('data-open')) {
            const defaultMode = modal.dataset.mode || 'create';
            const teacherId = modal.dataset.teacherId || '';
            openModal(defaultMode, { teacherId });
        }

        modal.addEventListener('keydown', (event) => {
            if (event.key !== 'Tab' || !modal.hasAttribute('data-open')) {
                return;
            }

            const focusableElements = Array.from(dialog.querySelectorAll(focusableSelectors)).filter((element) => !element.hasAttribute('disabled') && element.offsetParent !== null);
            if (!focusableElements.length) {
                return;
            }

            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (event.shiftKey && document.activeElement === firstElement) {
                event.preventDefault();
                lastElement.focus();
            } else if (!event.shiftKey && document.activeElement === lastElement) {
                event.preventDefault();
                firstElement.focus();
            }
        });

        const teacherGrid = document.querySelector('.teachers-grid');
        const deleteForm = document.querySelector('[data-teachers-delete-form]');

        if (teacherGrid) {
            teacherGrid.addEventListener('click', (event) => {
                const actionButton = event.target.closest('[data-action]');
                if (!actionButton) {
                    return;
                }

                event.preventDefault();
                const action = actionButton.dataset.action;

                if (action === 'edit') {
                    closeAllDropdowns();
                    const teacherId = actionButton.dataset.teacherId || '';
                    const fullName = actionButton.dataset.teacherFullName || '';
                    const email = actionButton.dataset.teacherEmail || '';
                    openModal('update', { teacherId, fullName, email });
                } else if (action === 'delete') {
                    closeAllDropdowns();
                    if (!deleteForm) {
                        return;
                    }
                    const teacherId = actionButton.dataset.teacherId || '';
                    const teacherName = actionButton.dataset.teacherName || '';
                    const confirmationMessage = teacherName
                        ? `Удалить учителя «${teacherName}»?`
                        : 'Удалить выбранного учителя?';
                    const confirmed = window.confirm(confirmationMessage);
                    if (!confirmed) {
                        return;
                    }

                    const formTypeField = deleteForm.querySelector('input[name="form_type"]');
                    const teacherIdField = deleteForm.querySelector('input[name="teacher_id"]');
                    if (formTypeField) {
                        formTypeField.value = 'delete';
                    }
                    if (teacherIdField) {
                        teacherIdField.value = teacherId;
                    }
                    deleteForm.submit();
                }
            });
        }
    }

    const importForm = document.querySelector('[data-teachers-import]');
    if (importForm) {
        const importInput = importForm.querySelector('[data-teachers-import-input]');
        const importTrigger = importForm.querySelector('[data-teachers-import-trigger]');
        let isUploading = false;
        const originalTriggerHtml = importTrigger ? importTrigger.innerHTML : '';

        const resetImportState = () => {
            if (importTrigger) {
                importTrigger.disabled = false;
                importTrigger.classList.remove('is-loading');
                importTrigger.innerHTML = originalTriggerHtml;
            }
            isUploading = false;
        };

        const handleImportResponse = (data) => {
            if (!data) {
                showAlert('Не удалось обработать ответ сервера.', 'danger');
                return;
            }

            if (!data.success) {
                const message = data.message || 'Не удалось загрузить учителей.';
                if (Array.isArray(data.errors) && data.errors.length) {
                    showAlert([message, data.errors.join('\n')].join('\n'), 'danger');
                } else {
                    showAlert(message, 'danger');
                }
                return;
            }

            if (Array.isArray(data.errors) && data.errors.length) {
                showAlert('Некоторые строки были пропущены при импорте:', 'warning', data.errors);
            }

            let details = null;
            if (Array.isArray(data.teachers) && data.teachers.length) {
                details = data.teachers.map((teacher) => {
                    const name = teacher.full_name || '—';
                    const email = teacher.email || '—';
                    const password = teacher.password || '—';
                    return `${name} — ${email} — пароль: ${password}`;
                });
            }

            showAlert(data.message || 'Учителя успешно загружены.', 'success', details);

            window.setTimeout(() => {
                window.location.reload();
            }, 1200);
        };

        if (importTrigger && importInput) {
            importTrigger.addEventListener('click', (event) => {
                event.preventDefault();
                if (isUploading) {
                    return;
                }
                importInput.click();
            });

            importInput.addEventListener('change', async () => {
                if (!importInput.files || !importInput.files.length || !importTrigger) {
                    return;
                }

                const file = importInput.files[0];
                const formData = new FormData();
                formData.append('file', file);

                isUploading = true;
                importTrigger.disabled = true;
                importTrigger.classList.add('is-loading');
                importTrigger.innerHTML = '<span class="button__icon" aria-hidden="true">⏳</span><span>Загрузка…</span>';

                try {
                    const response = await fetch(importForm.action, {
                        method: 'POST',
                        body: formData,
                    });

                    const data = await response.json().catch(() => null);
                    if (!response.ok) {
                        if (data && (data.message || (Array.isArray(data.errors) && data.errors.length))) {
                            handleImportResponse({ success: false, ...data });
                        } else {
                            showAlert('Произошла ошибка при загрузке файла. Попробуйте позже.', 'danger');
                        }
                        return;
                    }

                    handleImportResponse(data);
                } catch (error) {
                    console.error('Failed to upload teachers file', error);
                    showAlert('Произошла ошибка при загрузке файла. Попробуйте позже.', 'danger');
                } finally {
                    importInput.value = '';
                    resetImportState();
                }
            });
        }
    }
});
