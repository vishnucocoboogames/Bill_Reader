document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reconciliation-form');
    const runBtn = document.getElementById('run-btn');
    const btnText = form.querySelector('.btn-text');
    const loader = form.querySelector('.loader');

    const statusCard = document.getElementById('status-card');
    const resultCard = document.getElementById('result-card');
    const errorCard = document.getElementById('error-card');

    const reportPathText = document.getElementById('report-path');
    const errorMessageText = document.getElementById('error-message');

    document.getElementById('reset-btn').addEventListener('click', resetView);
    document.getElementById('retry-btn').addEventListener('click', resetView);

    // Folder selection logic (native Browse via AppleScript/PowerShell)
    document.querySelectorAll('.browse-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.getAttribute('data-target');
            const originalText = btn.textContent;
            btn.textContent = '...';
            btn.disabled = true;

            try {
                const response = await fetch('/api/select-folder');
                const data = await response.json();

                if (data.path) {
                    document.getElementById(targetId).value = data.path;
                } else if (data.error && !data.error.includes("cancelled")) {
                    alert('Error selecting folder: ' + data.error);
                }
            } catch (err) {
                console.error("Failed to call native folder picker.", err);
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const payload = {
            previous_month_dir: document.getElementById('prev_month_dir').value.trim(),
            current_month_dir: document.getElementById('curr_month_dir').value.trim(),
            checked_dir: document.getElementById('checked_dir').value.trim(),
            manual_review_dir: document.getElementById('manual_review_dir').value.trim()
        };

        // UI transitions
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        runBtn.disabled = true;

        form.style.opacity = '0.5';
        form.style.pointerEvents = 'none';

        errorCard.classList.add('hidden');
        resultCard.classList.add('hidden');
        statusCard.classList.remove('hidden');

        try {
            const response = await fetch('/process-bills', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to start processing');
            }

            const data = await response.json();
            pollStatus(data.job_id);

        } catch (error) {
            showError(error.message);
        }
    });

    async function pollStatus(jobId) {
        try {
            const res = await fetch(`/status/${jobId}`);
            const data = await res.json();

            // Update progress bar
            if (data.processed !== undefined && data.total !== undefined) {
                const fill = document.getElementById('progress-bar-fill');
                const text = document.getElementById('progress-text');

                if (fill && text) {
                    fill.classList.remove('indeterminate');
                    const percentage = data.total > 0 ? (data.processed / data.total) * 100 : 0;

                    fill.style.width = `${percentage}%`;
                    fill.style.animation = 'none';
                    fill.style.transform = 'none';

                    text.textContent = `${data.processed} / ${data.total} files processed`;
                }
            }

            if (data.status === 'COMPLETED') {
                showSuccess(data.report);
            } else if (data.status === 'FAILED') {
                showError(data.error || 'The job failed unexpectedly.');
            } else {
                setTimeout(() => pollStatus(jobId), 1000);
            }
        } catch (error) {
            showError('Error checking job status: ' + error.message);
        }
    }

    function showSuccess(reportPath) {
        statusCard.classList.add('hidden');
        resultCard.classList.remove('hidden');
        reportPathText.textContent = reportPath;
        resetFormUI();
    }

    function showError(msg) {
        statusCard.classList.add('hidden');
        errorCard.classList.remove('hidden');
        errorMessageText.textContent = msg;
        resetFormUI();
    }

    function resetFormUI() {
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
        runBtn.disabled = false;
        form.style.opacity = '1';
        form.style.pointerEvents = 'auto';

        // Reset progress bar
        const fill = document.getElementById('progress-bar-fill');
        const text = document.getElementById('progress-text');
        if (fill && text) {
            fill.classList.add('indeterminate');
            fill.style.width = '50%';
            fill.style.animation = '';
            fill.style.transform = '';
            text.textContent = '';
        }
    }

    function resetView() {
        resultCard.classList.add('hidden');
        errorCard.classList.add('hidden');
    }
});
