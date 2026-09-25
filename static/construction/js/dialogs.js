(function () {
    const backdrop = document.getElementById('dialogBackdrop');
    const title = document.getElementById('dialogTitle');
    const detail = document.getElementById('dialogDetail');
    const eyebrow = document.getElementById('dialogEyebrow');
    const icon = document.getElementById('dialogIcon');
    const confirmButton = document.getElementById('dialogConfirmButton');
    const toastStack = document.getElementById('toastStack');

    if (!backdrop || !confirmButton) return;

    let pendingAction = null;
    let lastFocused = null;

    const presets = {
        logout: {
            title: 'Sign out of ConstructPro?',
            detail: 'You will return to the login page. Save any form changes before signing out.',
            action: 'Sign out',
            icon: '->',
        },
        discard: {
            title: 'Discard this form?',
            detail: 'Any information entered on this page will be lost if you leave now.',
            action: 'Discard',
            icon: '!',
        },
    };

    function optionsFrom(element, fallback) {
        const preset = presets[element.dataset.dialogPreset] || {};
        return {
            title: element.dataset.dialogConfirm || preset.title || fallback.title,
            detail: element.dataset.dialogDetail || preset.detail || fallback.detail,
            action: element.dataset.dialogAction || preset.action || fallback.action,
            icon: element.dataset.dialogIcon || preset.icon || fallback.icon,
        };
    }

    function openDialog(options) {
        lastFocused = document.activeElement;
        title.textContent = options.title || 'Are you sure?';
        detail.textContent = options.detail || 'Please confirm before continuing.';
        eyebrow.textContent = options.eyebrow || 'Confirm Action';
        icon.textContent = options.icon || '!';
        confirmButton.textContent = options.action || 'Continue';
        pendingAction = options.onConfirm;
        backdrop.hidden = false;
        document.body.classList.add('dialog-open');
        confirmButton.focus();
    }

    function closeDialog() {
        backdrop.hidden = true;
        document.body.classList.remove('dialog-open');
        pendingAction = null;
        if (lastFocused && typeof lastFocused.focus === 'function') {
            lastFocused.focus();
        }
    }

    function toast(message, type) {
        if (!toastStack || !message) return;
        const item = document.createElement('div');
        item.className = `toast toast-${type || 'info'}`;
        item.innerHTML = `<strong>${type === 'error' ? 'Needs attention' : type === 'success' ? 'Success' : 'Update'}</strong><span></span><button type="button" aria-label="Dismiss">x</button>`;
        item.querySelector('span').textContent = message;
        item.querySelector('button').addEventListener('click', () => item.remove());
        toastStack.appendChild(item);
        window.setTimeout(() => {
            item.classList.add('toast-leaving');
            window.setTimeout(() => item.remove(), 220);
        }, 5200);
    }

    document.querySelectorAll('[data-popup-message]').forEach((node) => {
        toast(node.dataset.popupMessage, node.dataset.popupType || 'info');
    });

    document.querySelectorAll('form[data-dialog-confirm], form[data-dialog-preset]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (form.dataset.dialogApproved === 'true') {
                delete form.dataset.dialogApproved;
                return;
            }
            event.preventDefault();
            const options = optionsFrom(form, {
                title: 'Submit this form?',
                detail: 'Please confirm before continuing.',
                action: 'Continue',
                icon: '!',
            });
            openDialog({
                title: options.title,
                detail: options.detail,
                action: options.action,
                icon: options.icon,
                onConfirm: () => {
                    form.dataset.dialogApproved = 'true';
                    form.submit();
                },
            });
        });
    });

    document.querySelectorAll('[data-dialog-link]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const options = optionsFrom(link, {
                title: 'Leave this page?',
                detail: 'Please confirm before continuing.',
                action: 'Continue',
                icon: '!',
            });
            openDialog({
                title: options.title,
                detail: options.detail,
                action: options.action,
                icon: options.icon,
                onConfirm: () => {
                    window.location.href = link.href;
                },
            });
        });
    });

    confirmButton.addEventListener('click', () => {
        const action = pendingAction;
        closeDialog();
        if (typeof action === 'function') action();
    });

    backdrop.querySelectorAll('[data-dialog-cancel]').forEach((button) => {
        button.addEventListener('click', closeDialog);
    });

    backdrop.addEventListener('click', (event) => {
        if (event.target === backdrop) closeDialog();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !backdrop.hidden) closeDialog();
    });

    window.ConstructProDialog = {
        confirm: openDialog,
        toast,
    };
})();
