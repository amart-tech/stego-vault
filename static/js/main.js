// StegoVault Frontend Controller
// Handles UI state, live capacity calculations, drag-and-drop, and AJAX requests.

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const state = {
        encodeFile: null,
        encodeImageMetrics: null,
        decodeFile: null,
    };

    // --------------------------------------------------------------------------
    // 2. TOAST NOTIFICATION ENGINE
    // --------------------------------------------------------------------------
    const toastContainer = document.getElementById('toast-container');

    function showToast(message, type = 'error', title = null) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const defaultTitles = {
            success: 'Operation Successful',
            error: 'Security Alert / Error',
            warning: 'Capacity Warning',
        };

        const resolvedTitle = title || defaultTitles[type] || 'Notice';

        // SVGs for different toast states
        let iconSvg = '';
        if (type === 'success') {
            iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
        } else if (type === 'warning') {
            iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
        } else {
            iconSvg = `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
        }

        toast.innerHTML = `
            ${iconSvg}
            <div class="toast-content">
                <div class="toast-title">${resolvedTitle}</div>
                <div class="toast-message">${escapeHtml(message)}</div>
            </div>
            <button class="toast-close" aria-label="Close notification">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        `;

        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => dismissToast(toast));

        toastContainer.appendChild(toast);

        // Auto-dismiss after 5 seconds
        const timer = setTimeout(() => {
            dismissToast(toast);
        }, 5000);

        toast._timer = timer;
    }

    function dismissToast(toast) {
        if (!toast || toast._dismissed) return;
        toast._dismissed = true;
        clearTimeout(toast._timer);
        toast.classList.add('toast-closing');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // --------------------------------------------------------------------------
    // 3. TAB NAVIGATION
    // --------------------------------------------------------------------------
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTabId = btn.getAttribute('data-tab');

            tabButtons.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-selected', 'false');
            });
            tabPanels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
            const targetPanel = document.getElementById(targetTabId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });

    // --------------------------------------------------------------------------
    // 4. PASSWORD VISIBILITY TOGGLE
    // --------------------------------------------------------------------------
    const toggleButtons = document.querySelectorAll('.btn-toggle-password');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;

            const eyeOpen = btn.querySelector('.eye-open');
            const eyeClosed = btn.querySelector('.eye-closed');

            if (input.type === 'password') {
                input.type = 'text';
                eyeOpen.classList.add('hidden');
                eyeClosed.classList.remove('hidden');
            } else {
                input.type = 'password';
                eyeOpen.classList.remove('hidden');
                eyeClosed.classList.add('hidden');
            }
        });
    });

    // --------------------------------------------------------------------------
    // 5. IMAGE INGESTION & DRAG-AND-DROP SETUP
    // --------------------------------------------------------------------------

    /**
     * Sets up drag and drop and file input handling for a dropzone.
     */
    function setupDropzone(config) {
        const dropzone = document.getElementById(config.dropzoneId);
        const fileInput = document.getElementById(config.fileInputId);
        const promptEl = document.getElementById(config.promptId);
        const previewContainer = document.getElementById(config.previewContainerId);
        const previewImg = document.getElementById(config.previewImgId);
        const fileNameEl = document.getElementById(config.fileNameId);
        const removeBtn = document.getElementById(config.removeBtnId);

        // Click on dropzone opens native file picker
        dropzone.addEventListener('click', (e) => {
            if (e.target.closest(`#${config.removeBtnId}`) || e.target.closest('.image-preview-container')) {
                return;
            }
            fileInput.click();
        });

        // Drag & Drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                handleFileSelection(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files.length > 0) {
                handleFileSelection(fileInput.files[0]);
            }
        });

        if (removeBtn) {
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                clearImageSelection();
            });
        }

        function handleFileSelection(file) {
            const filename = file.name.toLowerCase();
            const isEncode = config.isEncode || false;

            if (isEncode) {
                const isPngOrJpg = filename.endsWith('.png') || filename.endsWith('.jpg') || filename.endsWith('.jpeg') ||
                                   (file.type && (file.type === 'image/png' || file.type === 'image/jpeg'));
                if (!isPngOrJpg) {
                    showToast(
                        'Invalid file format. Please upload a PNG or JPEG/JPG carrier image.',
                        'error',
                        'Format Rejected'
                    );
                    clearImageSelection();
                    return;
                }
                if (filename.endsWith('.jpg') || filename.endsWith('.jpeg')) {
                    showToast(
                        'JPEG carrier loaded. The resulting stego image will be saved as a lossless PNG to protect hidden bits.',
                        'warning',
                        'JPEG Carrier Loaded'
                    );
                }
            } else {
                // Decode strictly requires PNG
                if (!filename.endsWith('.png') || (file.type && file.type !== 'image/png')) {
                    showToast(
                        'Stego images must be lossless PNG. If this image was saved or converted to JPEG, lossy compression (DCT) has permanently erased the hidden LSB data.',
                        'error',
                        'PNG Required for Decode'
                    );
                    clearImageSelection();
                    return;
                }
            }

            // Create object URL for preview
            const objectUrl = URL.createObjectURL(file);
            const img = new Image();

            img.onload = () => {
                const width = img.naturalWidth;
                const height = img.naturalHeight;
                const totalChannels = width * height * 3;
                const usableBits = Math.max(0, totalChannels - 32);
                const maxPayloadBytes = Math.floor(usableBits / 8);

                // Update UI elements
                previewImg.src = objectUrl;
                fileNameEl.textContent = file.name;
                promptEl.classList.add('hidden');
                previewContainer.classList.remove('hidden');

                if (config.dimsId) {
                    document.getElementById(config.dimsId).textContent = `${width} \u00d7 ${height}`;
                }
                if (config.channelsId) {
                    document.getElementById(config.channelsId).textContent = `${totalChannels.toLocaleString()} bits`;
                }
                if (config.maxBytesId) {
                    document.getElementById(config.maxBytesId).textContent = `${maxPayloadBytes.toLocaleString()} bytes`;
                }

                config.onSuccess({
                    file,
                    width,
                    height,
                    totalChannels,
                    maxPayloadBytes,
                });
            };

            img.onerror = () => {
                showToast('Unable to read selected image file. Please ensure it is a valid image.', 'error');
                clearImageSelection();
            };

            img.src = objectUrl;
        }

        function clearImageSelection() {
            fileInput.value = '';
            previewImg.src = '';
            previewContainer.classList.add('hidden');
            promptEl.classList.remove('hidden');
            config.onClear();
        }
    }

    // Initialize Encode Dropzone
    setupDropzone({
        isEncode: true,
        dropzoneId: 'encode-dropzone',
        fileInputId: 'encode-image-input',
        promptId: 'encode-dropzone-prompt',
        previewContainerId: 'encode-preview-container',
        previewImgId: 'encode-image-preview',
        fileNameId: 'encode-file-name',
        removeBtnId: 'encode-remove-image',
        dimsId: 'encode-img-dims',
        channelsId: 'encode-img-channels',
        maxBytesId: 'encode-img-max-bytes',
        onSuccess: (metrics) => {
            state.encodeFile = metrics.file;
            state.encodeImageMetrics = metrics;
            updateCapacityEstimation();
        },
        onClear: () => {
            state.encodeFile = null;
            state.encodeImageMetrics = null;
            updateCapacityEstimation();
        },
    });

    // Initialize Decode Dropzone
    setupDropzone({
        dropzoneId: 'decode-dropzone',
        fileInputId: 'decode-image-input',
        promptId: 'decode-dropzone-prompt',
        previewContainerId: 'decode-preview-container',
        previewImgId: 'decode-image-preview',
        fileNameId: 'decode-file-name',
        removeBtnId: 'decode-remove-image',
        dimsId: 'decode-img-dims',
        channelsId: 'decode-img-channels',
        onSuccess: (metrics) => {
            state.decodeFile = metrics.file;
        },
        onClear: () => {
            state.decodeFile = null;
        },
    });

    // --------------------------------------------------------------------------
    // 6. LIVE CAPACITY ESTIMATION & TEXTAREA COUNTER
    // --------------------------------------------------------------------------
    const messageInput = document.getElementById('encode-message');
    const messageCounter = document.getElementById('message-counter');
    const capacityProgressBar = document.getElementById('capacity-progress-bar');
    const capacityUsedText = document.getElementById('capacity-used-text');
    const capacityFootnote = document.getElementById('capacity-footnote');

    messageInput.addEventListener('input', () => {
        updateCapacityEstimation();
    });

    /**
     * Calculates the estimated bits required by the message:
     * - 32-bit length header
     * - 16 bytes salt
     * - Fernet ciphertext (AES-128-CBC + PKCS7 padding + HMAC-SHA256, base64 encoded)
     */
    function calculateEstimatedBits(text) {
        if (!text || text.length === 0) return 0;
        const msgBytes = new TextEncoder().encode(text).length;

        // PKCS7 padding rounds up to next multiple of 16 (always adds 1 to 16 bytes)
        const paddedMsgLen = Math.ceil((msgBytes + 1) / 16) * 16;

        // Fernet token structure:
        // Version (1) + Timestamp (8) + IV (16) + Padded Ciphertext (N) + HMAC (32)
        const fernetRawLen = 1 + 8 + 16 + paddedMsgLen + 32;

        // Fernet tokens are URL-safe base64 encoded (4 chars per 3 bytes)
        const fernetB64Len = Math.ceil(fernetRawLen / 3) * 4;

        // Full payload = 16 bytes (salt) + fernet token bytes
        const totalPayloadBytes = 16 + fernetB64Len;

        // Total bits = 32-bit header + (payload bytes * 8)
        return 32 + (totalPayloadBytes * 8);
    }

    function updateCapacityEstimation() {
        const text = messageInput.value;
        const charCount = text.length;
        messageCounter.textContent = `${charCount} char${charCount === 1 ? '' : 's'}`;

        if (!state.encodeImageMetrics) {
            capacityProgressBar.style.width = '0%';
            capacityProgressBar.style.backgroundColor = 'var(--emerald-400)';
            capacityUsedText.textContent = 'Upload PNG to check capacity';
            capacityFootnote.textContent = 'Carrier image not selected.';
            return;
        }

        const availableChannels = state.encodeImageMetrics.totalChannels;
        const requiredBits = calculateEstimatedBits(text);

        if (requiredBits === 0) {
            capacityProgressBar.style.width = '0%';
            capacityProgressBar.style.backgroundColor = 'var(--emerald-400)';
            capacityUsedText.textContent = '0% Used';
            capacityFootnote.textContent = `Carrier capacity: ${state.encodeImageMetrics.maxPayloadBytes.toLocaleString()} bytes.`;
            return;
        }

        const percent = (requiredBits / availableChannels) * 100;
        const clampedWidth = Math.min(100, Math.max(0.5, percent));
        capacityProgressBar.style.width = `${clampedWidth}%`;

        if (percent > 100) {
            capacityProgressBar.style.backgroundColor = 'var(--rose-400)';
            capacityUsedText.style.color = 'var(--rose-400)';
            capacityUsedText.textContent = `${percent.toFixed(1)}% (OVERFLOW)`;
            capacityFootnote.textContent = `Requires ${requiredBits.toLocaleString()} bits, but image only provides ${availableChannels.toLocaleString()} bits. Image is too small!`;
        } else if (percent > 75) {
            capacityProgressBar.style.backgroundColor = 'var(--amber-400)';
            capacityUsedText.style.color = 'var(--amber-400)';
            capacityUsedText.textContent = `${percent.toFixed(2)}% Used`;
            capacityFootnote.textContent = `Using ${requiredBits.toLocaleString()} of ${availableChannels.toLocaleString()} bits.`;
        } else {
            capacityProgressBar.style.backgroundColor = 'var(--emerald-400)';
            capacityUsedText.style.color = 'var(--emerald-400)';
            capacityUsedText.textContent = `${percent.toFixed(2)}% Used`;
            capacityFootnote.textContent = `Using ${requiredBits.toLocaleString()} of ${availableChannels.toLocaleString()} bits (${(availableChannels - requiredBits).toLocaleString()} bits remaining).`;
        }
    }

    // --------------------------------------------------------------------------
    // 7. ENCODE FORM SUBMISSION (AJAX)
    // --------------------------------------------------------------------------
    const encodeForm = document.getElementById('encode-form');
    const btnSubmitEncode = document.getElementById('btn-submit-encode');
    const encodeEmptyState = document.getElementById('encode-empty-state');
    const encodeResultContent = document.getElementById('encode-result-content');
    const encodeStatusBadge = document.getElementById('encode-status-badge');

    // Result elements
    const stegoImagePreview = document.getElementById('stego-image-preview');
    const resSaltSize = document.getElementById('res-salt-size');
    const resCtSize = document.getElementById('res-ct-size');
    const resTotalBits = document.getElementById('res-total-bits');
    const resCapacityPct = document.getElementById('res-capacity-pct');
    const resPsnr = document.getElementById('res-psnr');
    const resMse = document.getElementById('res-mse');
    const btnDownloadStego = document.getElementById('btn-download-stego');
    const btnResetEncode = document.getElementById('btn-reset-encode');

    encodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!state.encodeFile) {
            showToast('Please select or drop a carrier PNG image first.', 'warning');
            return;
        }

        const secretText = messageInput.value.trim();
        if (!secretText) {
            showToast('Secret message cannot be empty.', 'warning');
            messageInput.focus();
            return;
        }

        const passphrase = document.getElementById('encode-passphrase').value.trim();
        if (!passphrase) {
            showToast('Please enter an encryption passphrase.', 'warning');
            document.getElementById('encode-passphrase').focus();
            return;
        }

        // Check if message exceeds image capacity before sending
        if (state.encodeImageMetrics) {
            const reqBits = calculateEstimatedBits(secretText);
            if (reqBits > state.encodeImageMetrics.totalChannels) {
                showToast(
                    `Image too small for this message! Required: ${reqBits} bits, but image only provides ${state.encodeImageMetrics.totalChannels} bits. Choose a larger image.`,
                    'error',
                    'Capacity Exceeded'
                );
                return;
            }
        }

        // Set Loading State
        setButtonLoading(btnSubmitEncode, true, 'Encrypting & Embedding in LSB...');

        const formData = new FormData();
        formData.append('image', state.encodeFile);
        formData.append('message', secretText);
        formData.append('passphrase', passphrase);

        try {
            const response = await fetch('/api/encode', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to encode stego-image.');
            }

            // Populate Result View
            stegoImagePreview.src = data.image_data;
            resSaltSize.textContent = `${data.stats.salt_size_bytes} Bytes (128-bit)`;
            resCtSize.textContent = `${data.stats.ciphertext_size_bytes} Bytes`;
            resTotalBits.textContent = `${data.stats.total_bits_embedded.toLocaleString()} bits (${data.stats.payload_length_bytes + 4} Bytes)`;
            resCapacityPct.textContent = `${data.stats.capacity_used_percent}% of carrier pixels used`;
            if (resPsnr && data.stats.psnr_db !== undefined) {
                resPsnr.textContent = `${data.stats.psnr_db} dB (Imperceptible)`;
            }
            if (resMse && data.stats.mse !== undefined) {
                resMse.textContent = `${data.stats.mse}`;
            }

            // Download Link Setup
            btnDownloadStego.href = data.image_data;
            btnDownloadStego.download = data.filename || 'stego_vault_encoded.png';

            // Show results with smooth transition
            encodeEmptyState.classList.add('hidden');
            encodeResultContent.classList.remove('hidden');
            encodeStatusBadge.textContent = 'Embedded & Ready';
            encodeStatusBadge.className = 'badge badge-emerald';

            showToast('Payload encrypted with AES-128 and concealed in LSB channels!', 'success', 'Concealment Complete');

        } catch (err) {
            showToast(err.message, 'error', 'Encoding Error');
        } finally {
            setButtonLoading(btnSubmitEncode, false);
        }
    });

    if (btnResetEncode) {
        btnResetEncode.addEventListener('click', () => {
            encodeForm.reset();
            const removeBtn = document.getElementById('encode-remove-image');
            if (removeBtn) removeBtn.click();
            encodeEmptyState.classList.remove('hidden');
            encodeResultContent.classList.add('hidden');
            encodeStatusBadge.textContent = 'Awaiting Input';
            encodeStatusBadge.className = 'badge badge-emerald';
            updateCapacityEstimation();
            showToast('Ready for a new encoding session.', 'success', 'Session Reset');
        });
    }

    // --------------------------------------------------------------------------
    // 8. DECODE FORM SUBMISSION (AJAX)
    // --------------------------------------------------------------------------
    const decodeForm = document.getElementById('decode-form');
    const btnSubmitDecode = document.getElementById('btn-submit-decode');
    const decodeEmptyState = document.getElementById('decode-empty-state');
    const decodeResultContent = document.getElementById('decode-result-content');
    const decodeStatusBadge = document.getElementById('decode-status-badge');

    // Decode Result elements
    const decryptedTextOutput = document.getElementById('decrypted-text-output');
    const decPayloadSize = document.getElementById('dec-payload-size');
    const decTotalBits = document.getElementById('dec-total-bits');
    const btnCopyPlaintext = document.getElementById('btn-copy-plaintext');

    decodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!state.decodeFile) {
            showToast('Please upload an encoded steganographic PNG image.', 'warning');
            return;
        }

        const passphrase = document.getElementById('decode-passphrase').value.trim();
        if (!passphrase) {
            showToast('Please provide the decryption passphrase.', 'warning');
            document.getElementById('decode-passphrase').focus();
            return;
        }

        // Set Loading State
        setButtonLoading(btnSubmitDecode, true, 'Extracting Bits & Decrypting...');

        const formData = new FormData();
        formData.append('image', state.decodeFile);
        formData.append('passphrase', passphrase);

        try {
            const response = await fetch('/api/decode', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Failed to extract hidden message.');
            }

            // Display Decrypted Output
            decryptedTextOutput.textContent = data.message;
            decPayloadSize.textContent = `${data.stats.payload_length_bytes} Bytes`;
            decTotalBits.textContent = `${data.stats.total_bits_extracted.toLocaleString()} bits`;

            decodeEmptyState.classList.add('hidden');
            decodeResultContent.classList.remove('hidden');
            decodeStatusBadge.textContent = 'Decrypted Successfully';
            decodeStatusBadge.className = 'badge badge-emerald';

            showToast('Secret payload decrypted and HMAC authenticated!', 'success', 'Extraction Success');

        } catch (err) {
            showToast(err.message, 'error', 'Decryption Failed');
        } finally {
            setButtonLoading(btnSubmitDecode, false);
        }
    });

    const btnResetDecode = document.getElementById('btn-reset-decode');
    if (btnResetDecode) {
        btnResetDecode.addEventListener('click', () => {
            decodeForm.reset();
            const removeBtn = document.getElementById('decode-remove-image');
            if (removeBtn) removeBtn.click();
            decodeEmptyState.classList.remove('hidden');
            decodeResultContent.classList.add('hidden');
            decodeStatusBadge.textContent = 'Awaiting Payload';
            decodeStatusBadge.className = 'badge badge-indigo';
            showToast('Ready for another decode operation.', 'success', 'Session Reset');
        });
    }

    // --------------------------------------------------------------------------
    // 9. COPY-TO-CLIPBOARD WITH VISUAL FEEDBACK
    // --------------------------------------------------------------------------
    if (btnCopyPlaintext) {
        btnCopyPlaintext.addEventListener('click', async () => {
            const textToCopy = decryptedTextOutput.textContent;
            if (!textToCopy) return;

            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(textToCopy);
                } else {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = textToCopy;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }

                // Visual Feedback
                const copyIcon = btnCopyPlaintext.querySelector('.copy-icon');
                const checkIcon = btnCopyPlaintext.querySelector('.check-icon');
                const copyBtnText = document.getElementById('copy-btn-text');

                copyIcon.classList.add('hidden');
                checkIcon.classList.remove('hidden');
                copyBtnText.textContent = 'Copied!';

                setTimeout(() => {
                    copyIcon.classList.remove('hidden');
                    checkIcon.classList.add('hidden');
                    copyBtnText.textContent = 'Copy';
                }, 2000);

                showToast('Extracted message copied to clipboard.', 'success', 'Copied');

            } catch (err) {
                showToast('Unable to copy text to clipboard.', 'error');
            }
        });
    }

    // --------------------------------------------------------------------------
    // 10. HELPER FUNCTIONS
    // --------------------------------------------------------------------------
    function setButtonLoading(button, isLoading, loadingText = '') {
        const btnText = button.querySelector('.btn-text');
        const btnSpinner = button.querySelector('.btn-spinner');

        if (isLoading) {
            button.disabled = true;
            btnText.classList.add('hidden');
            btnSpinner.classList.remove('hidden');
            if (loadingText) {
                const ring = btnSpinner.querySelector('.spinner-ring');
                btnSpinner.innerHTML = '';
                btnSpinner.appendChild(ring);
                btnSpinner.appendChild(document.createTextNode(' ' + loadingText));
            }
        } else {
            button.disabled = false;
            btnText.classList.remove('hidden');
            btnSpinner.classList.add('hidden');
        }
    }

});
