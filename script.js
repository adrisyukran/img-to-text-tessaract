// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const clearBtn = document.getElementById('clearBtn');
const statusSection = document.getElementById('statusSection');
const statusText = document.getElementById('statusText');
const outputSection = document.getElementById('outputSection');
const outputText = document.getElementById('outputText');
const copyBtn = document.getElementById('copyBtn');
const enhanceBtn = document.getElementById('enhanceBtn');
const undoBtn = document.getElementById('undoBtn');
const summariseBtn = document.getElementById('summariseBtn');

// Summary Section Elements
const summarySection = document.getElementById('summarySection');
const summaryHeader = document.getElementById('summaryHeader');
const summaryContent = document.getElementById('summaryContent');
const summaryText = document.getElementById('summaryText');
const copySummaryBtn = document.getElementById('copySummaryBtn');
const toggleSummaryBtn = document.getElementById('toggleSummaryBtn');

// Token Usage Elements
const tokenUsage = document.getElementById('tokenUsage');
const inputTokensEl = document.getElementById('inputTokens');
const outputTokensEl = document.getElementById('outputTokens');
const totalTokensEl = document.getElementById('totalTokens');
const tokenCostEl = document.getElementById('tokenCost');

// Word Count Elements
const wordCountEl = document.getElementById('wordCountEl');
const charCountEl = document.getElementById('charCount');
const wordCountNumEl = document.getElementById('wordCountNum');

// Toast Container
const toastContainer = document.getElementById('toastContainer');

// Settings Modal Elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const saveApiKeyBtn = document.getElementById('saveApiKeyBtn');
const apiKeyInput = document.getElementById('apiKeyInput');
const modelGemini = document.getElementById('modelGemini');
const modelOpenAI = document.getElementById('modelOpenAI');
const geminiKeyGroup = document.getElementById('geminiKeyGroup');
const openaiConfigGroup = document.getElementById('openaiConfigGroup');
const requestsRemaining = document.getElementById('requestsRemaining');
const resetTimeEl = document.getElementById('resetTime');
const statusDot = document.getElementById('statusDot');
const statusMessage = document.getElementById('statusMessage');

// State
let currentImage = null;
let isTestingConnection = false;
let originalOcrText = null;
let isEnhancing = false;
let isTextEnhanced = false;
let isSummarising = false;
let hasSummary = false;
let currentSummary = null;

// Token usage tracking (cumulative for session)
let totalUsage = {
    inputTokens: 0,
    outputTokens: 0,
    totalTokens: 0,
    totalCost: 0
};

// Initialize spinners for buttons
function initButtonSpinners() {
    if (enhanceBtn) {
        // Remove existing spinner if any
        const existingSpinner = enhanceBtn.querySelector('.btn-spinner');
        if (existingSpinner) existingSpinner.remove();
        
        // Create new spinner
        const spinner = document.createElement('div');
        spinner.className = 'btn-spinner';
        spinner.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; display: none;';
        enhanceBtn.appendChild(spinner);
    }
    if (summariseBtn) {
        // Remove existing spinner if any
        const existingSpinner = summariseBtn.querySelector('.btn-spinner');
        if (existingSpinner) existingSpinner.remove();
        
        // Create new spinner
        const spinner = document.createElement('div');
        spinner.className = 'btn-spinner';
        spinner.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite; display: none;';
        summariseBtn.appendChild(spinner);
    }
}

// Initialize event listeners
function init() {
    // Initialize button spinners
    initButtonSpinners();
    
    // Check if all required elements exist
    if (!uploadArea || !fileInput || !settingsBtn || !settingsModal) {
        return;
    }

    // Click to select file
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Paste from clipboard
    document.addEventListener('paste', handlePaste);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', resetApp);
    }
    
    // Copy button
    if (copyBtn) {
        copyBtn.addEventListener('click', copyToClipboard);
    }

    // AI buttons
    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', enhanceText);
    }
    if (undoBtn) {
        undoBtn.addEventListener('click', undoEnhance);
    }
    if (summariseBtn) {
        summariseBtn.addEventListener('click', summariseText);
    }
    
    // Summary section
    if (toggleSummaryBtn) {
        toggleSummaryBtn.addEventListener('click', toggleSummary);
    }
    if (summaryHeader && copySummaryBtn) {
        summaryHeader.addEventListener('click', (e) => {
            if (e.target !== copySummaryBtn && !copySummaryBtn.contains(e.target)) {
                toggleSummary();
            }
        });
    }
    if (copySummaryBtn) {
        copySummaryBtn.addEventListener('click', copySummary);
    }

    // Settings modal
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettingsModal);
    }
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeSettingsModal);
    }
    if (cancelModalBtn) {
        cancelModalBtn.addEventListener('click', closeSettingsModal);
    }
    if (saveApiKeyBtn) {
        saveApiKeyBtn.addEventListener('click', saveApiKey);
    }
    
    // Model selection
    if (modelGemini) {
        modelGemini.addEventListener('change', handleModelChange);
    }
    if (modelOpenAI) {
        modelOpenAI.addEventListener('change', handleModelChange);
    }
    
    // Close modal on overlay click
    if (settingsModal) {
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                closeSettingsModal();
            }
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close modal
        if (e.key === 'Escape' && settingsModal && settingsModal.classList.contains('active')) {
            closeSettingsModal();
            return;
        }
        
        // Only handle shortcuts when output is visible and modal is not open
        if (!outputSection || outputSection.style.display === 'none' || (settingsModal && settingsModal.classList.contains('active'))) {
            return;
        }
        
        // Ctrl+E for Enhance
        if (e.ctrlKey && e.key === 'e' && enhanceBtn && !enhanceBtn.disabled) {
            e.preventDefault();
            enhanceText();
        }
        
        // Ctrl+Shift+S for Summarise
        if (e.ctrlKey && e.shiftKey && e.key === 'S' && summariseBtn && !summariseBtn.disabled) {
            e.preventDefault();
            summariseText();
        }
        
        // Ctrl+Shift+C for Copy
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            copyToClipboard();
        }
    });

    // Load initial API key status
    updateApiKeyStatus();
    
    // Update button titles with keyboard shortcuts
    if (enhanceBtn) {
        enhanceBtn.title = 'Enhance text with AI (Ctrl+E)';
    }
    if (summariseBtn) {
        summariseBtn.title = 'Summarise text with AI (Ctrl+Shift+S)';
    }
    if (copyBtn) {
        copyBtn.title = 'Copy to clipboard (Ctrl+Shift+C)';
    }
    
    // Start rate limit countdown refresh
    setInterval(() => {
        if (settingsModal && settingsModal.classList.contains('active')) {
            updateRateLimitDisplay();
        }
    }, 1000);
}

// Handle file selection from input
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
        processImage(file);
    } else {
        showError('Please select a valid image file');
    }
}

// Handle paste from clipboard
function handlePaste(event) {
    const items = event.clipboardData.items;
    
    for (let item of items) {
        if (item.type.startsWith('image/')) {
            event.preventDefault();
            const file = item.getAsFile();
            processImage(file);
            break;
        }
    }
}

// Handle drag over
function handleDragOver(event) {
    event.preventDefault();
    if (uploadArea) {
        uploadArea.classList.add('dragover');
    }
}

// Handle drag leave
function handleDragLeave(event) {
    event.preventDefault();
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
    }
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    if (uploadArea) {
        uploadArea.classList.remove('dragover');
    }
    
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        processImage(file);
    } else {
        showError('Please drop a valid image file');
    }
}

// Process the image
function processImage(file) {
    currentImage = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        if (imagePreview) {
            imagePreview.src = e.target.result;
        }
        if (previewContainer) {
            previewContainer.style.display = 'block';
        }
        if (uploadArea) {
            uploadArea.style.display = 'none';
        }
        
        // Start OCR
        performOCR(e.target.result);
    };
    reader.readAsDataURL(file);
}

// Perform OCR using Tesseract.js
async function performOCR(imageData) {
    // Show status
    if (statusSection) {
        statusSection.style.display = 'block';
    }
    if (outputSection) {
        outputSection.style.display = 'none';
    }
    if (statusText) {
        statusText.textContent = 'Initializing OCR...';
    }
    
    try {
        // Check if Tesseract is loaded
        if (typeof Tesseract === 'undefined') {
            throw new Error('Tesseract.js is not loaded');
        }
        
        // Create Tesseract worker
        const worker = await Tesseract.createWorker('eng', 1, {
            logger: (m) => {
                // Update status based on progress
                if (statusText) {
                    if (m.status === 'loading tesseract core') {
                        statusText.textContent = 'Loading OCR engine...';
                    } else if (m.status === 'initializing tesseract') {
                        statusText.textContent = 'Initializing...';
                    } else if (m.status === 'loading language traineddata') {
                        statusText.textContent = 'Loading language data...';
                    } else if (m.status === 'recognizing text') {
                        const progress = Math.round(m.progress * 100);
                        statusText.textContent = `Processing image... ${progress}%`;
                    }
                }
            }
        });
        
        // Perform OCR
        const { data: { text } } = await worker.recognize(imageData);
        
        // Terminate worker
        await worker.terminate();
        
        // Show results
        displayResults(text);
        
    } catch (error) {
        console.error('OCR Error:', error);
        showError('Failed to process image. Please try again. Error: ' + error.message);
    }
}

// Display OCR results
function displayResults(text) {
    if (statusSection) {
        statusSection.style.display = 'none';
    }
    if (outputSection) {
        outputSection.style.display = 'block';
    }
    
    // Reset AI-related state FIRST
    isTextEnhanced = false;
    hasSummary = false;
    currentSummary = null;
    originalOcrText = null;
    
    if (outputSection) {
        outputSection.classList.remove('enhanced');
    }
    if (undoBtn) {
        undoBtn.style.display = 'none';
    }
    if (tokenUsage) {
        tokenUsage.style.display = 'none';
    }
    if (summarySection) {
        summarySection.style.display = 'none';
    }
    if (summaryText) {
        summaryText.innerHTML = '';
    }
    
    // Reset cumulative usage
    totalUsage = { inputTokens: 0, outputTokens: 0, totalTokens: 0, totalCost: 0 };
    
    // Set text values FIRST
    if (outputText) {
        if (text && text.trim()) {
            outputText.value = text;
            originalOcrText = text;
        } else {
            outputText.value = 'No text detected in the image.';
            originalOcrText = null;
        }
    }
    
    // Update word count
    updateWordCount();
    
    // Update button states AFTER text is set
    updateEnhanceButtonState();
    updateSummariseButtonState();
}

// Copy text to clipboard
async function copyToClipboard() {
    if (!outputText) return;
    const text = outputText.value;
    
    if (!text) {
        return;
    }
    
    try {
        await navigator.clipboard.writeText(text);
        
        // Show feedback
        if (copyBtn) {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Copied!
            `;
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        }
        
    } catch (error) {
        console.error('Copy Error:', error);
        showError('Failed to copy text');
    }
}

// Reset the application (FULL RESET - clears all states)
function resetApp() {
    currentImage = null;
    if (fileInput) {
        fileInput.value = '';
    }
    if (imagePreview) {
        imagePreview.src = '';
    }
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
    if (statusSection) {
        statusSection.style.display = 'none';
    }
    if (outputSection) {
        outputSection.style.display = 'none';
    }
    if (uploadArea) {
        uploadArea.style.display = 'block';
    }
    if (outputText) {
        outputText.value = '';
    }
    
    // COMPLETE RESET of all AI states
    originalOcrText = null;
    isTextEnhanced = false;
    isEnhancing = false;
    isSummarising = false;
    hasSummary = false;
    currentSummary = null;
    
    if (outputSection) {
        outputSection.classList.remove('enhanced');
    }
    if (undoBtn) {
        undoBtn.style.display = 'none';
    }
    if (tokenUsage) {
        tokenUsage.style.display = 'none';
    }
    if (summarySection) {
        summarySection.style.display = 'none';
    }
    if (summaryText) {
        summaryText.innerHTML = '';
    }
    
    // Reset cumulative usage
    totalUsage = { inputTokens: 0, outputTokens: 0, totalTokens: 0, totalCost: 0 };
    
    // Reset button texts and states
    resetButtonStates();
    
    console.log('App fully reset - all states cleared');
}

// Reset button texts and spinner states
function resetButtonStates() {
    // Reset enhance button
    resetEnhanceButton();
    
    // Reset summarise button
    resetSummariseButton();
    
    // Reset word count
    if (charCountEl) {
        charCountEl.textContent = '0';
    }
    if (wordCountNumEl) {
        wordCountNumEl.textContent = '0';
    }
}

// Show error message
function showError(message) {
    if (statusSection) {
        statusSection.style.display = 'block';
    }
    if (statusText) {
        statusText.textContent = message;
        statusText.style.color = '#ff4757';
    }
    
    setTimeout(() => {
        if (statusSection) {
            statusSection.style.display = 'none';
        }
        if (statusText) {
            statusText.style.color = '#667fea';
        }
    }, 3000);
    
    // Also show as toast for better visibility
    showToast('Error', message, 'error');
}

// Toast Notification System
function showToast(title, message, type = 'info', duration = 4000) {
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconSvg = type === 'success' 
        ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
        : type === 'error'
        ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
        : '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
    
    toast.innerHTML = `
        ${iconSvg}
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Auto remove
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            toast.remove();
        }, 400);
    }, duration);
}

// Word Count Functions
function updateWordCount() {
    if (!outputText || !charCountEl || !wordCountNumEl) return;
    
    const text = outputText.value || '';
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    charCountEl.textContent = charCount.toLocaleString();
    wordCountNumEl.textContent = wordCount.toLocaleString();
}

// Settings Modal Functions
function openSettingsModal() {
    if (!settingsModal) return;
    
    // Load current settings
    const currentGeminiKey = window.AIService ? window.AIService.getApiKey() : '';
    
    // Set Gemini key
    if (apiKeyInput) {
        apiKeyInput.value = currentGeminiKey || '';
    }
    
    // Load selected model (default to Gemini)
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    if (modelOpenAI && selectedModel === 'openai') {
        modelOpenAI.checked = true;
        if (geminiKeyGroup) {
            geminiKeyGroup.style.display = 'none';
        }
        if (openaiConfigGroup) {
            openaiConfigGroup.style.display = 'block';
        }
    } else if (modelGemini) {
        modelGemini.checked = true;
        if (geminiKeyGroup) {
            geminiKeyGroup.style.display = 'block';
        }
        if (openaiConfigGroup) {
            openaiConfigGroup.style.display = 'none';
        }
    }
    
    // Update rate limit display
    updateRateLimitDisplay();
    
    // Update API status
    updateApiKeyStatus();
    
    // Show modal
    settingsModal.classList.add('active');
    
    // Focus on input
    if (apiKeyInput) {
        setTimeout(() => apiKeyInput.focus(), 100);
    }
    
    console.log('Settings modal opened');
}

// Model selection change handler
function handleModelChange() {
    const isOpenAI = modelOpenAI && modelOpenAI.checked;
    
    if (isOpenAI) {
        if (geminiKeyGroup) {
            geminiKeyGroup.style.display = 'none';
        }
        if (openaiConfigGroup) {
            openaiConfigGroup.style.display = 'block';
        }
        localStorage.setItem('selected_ai_model', 'openai');
    } else {
        if (geminiKeyGroup) {
            geminiKeyGroup.style.display = 'block';
        }
        if (openaiConfigGroup) {
            openaiConfigGroup.style.display = 'none';
        }
        localStorage.setItem('selected_ai_model', 'gemini');
    }
    
    updateApiKeyStatus();
    updateRateLimitDisplay();
}

function closeSettingsModal() {
    if (settingsModal) {
        settingsModal.classList.remove('active');
    }
    if (apiKeyInput) {
        apiKeyInput.value = '';
    }
}

async function saveApiKey() {
    console.log('Saving API key...');
    
    const isOpenAI = modelOpenAI && modelOpenAI.checked;
    const geminiKey = apiKeyInput ? apiKeyInput.value.trim() : '';
    
    if (!isOpenAI) {
        // Save Gemini API key
        if (!geminiKey) {
            if (window.AIService && window.AIService.clearApiKey) {
                window.AIService.clearApiKey();
            }
            showToast('API Key Cleared', 'Your Gemini API key has been removed', 'info');
        } else {
            if (window.AIService && window.AIService.setApiKey) {
                window.AIService.setApiKey(geminiKey);
            }
            showToast('API Key Saved', 'Your Gemini API key has been saved successfully!', 'success');
        }
    } else {
        // For OpenAI-compatible, show info
        showToast('Configuration Saved', 'Using pre-built AI model (rate limits apply)', 'info');
    }
    
    // Update status displays
    updateApiKeyStatus();
    updateRateLimitDisplay();
    
    // Update button states after saving API key
    updateEnhanceButtonState();
    updateSummariseButtonState();
    
    // Close modal after a short delay to show the toast
    setTimeout(() => {
        closeSettingsModal();
    }, 1500);
}

function updateApiKeyStatus() {
    if (!statusDot || !statusMessage) return;
    
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let isConfigured = false;
    
    if (selectedModel === 'openai') {
        if (window.AIService && window.AIService.isOpenAIConfigured) {
            isConfigured = window.AIService.isOpenAIConfigured();
        }
        if (isConfigured) {
            statusDot.className = 'status-dot configured';
            statusMessage.textContent = 'OpenAI-compatible API configured';
        } else {
            statusDot.className = 'status-dot';
            statusMessage.textContent = 'No OpenAI-compatible API key configured';
        }
    } else {
        if (window.AIService && window.AIService.isApiKeyConfigured) {
            isConfigured = window.AIService.isApiKeyConfigured();
        }
        if (isConfigured) {
            statusDot.className = 'status-dot configured';
            statusMessage.textContent = 'Gemini API key configured';
        } else {
            statusDot.className = 'status-dot';
            statusMessage.textContent = 'No Gemini API key configured';
        }
    }
    
    console.log('API key status updated:', isConfigured ? 'configured' : 'not configured');
}

function updateRateLimitDisplay() {
    if (!modelOpenAI || !modelOpenAI.checked) {
        // Still update display if not configured
        if (requestsRemaining) {
            requestsRemaining.textContent = 'Not configured';
            requestsRemaining.classList.remove('text-primary');
            requestsRemaining.classList.add('text-gray-400');
        }
        if (resetTimeEl) {
            resetTimeEl.textContent = '--';
        }
        return;
    }
    
    if (window.AIService && window.AIService.checkRateLimit) {
        const rateLimit = window.AIService.checkRateLimit();
        
        if (requestsRemaining) {
            // Color code based on remaining requests
            const remaining = rateLimit.remaining;
            const maxRequests = 14;
            const percentage = (remaining / maxRequests) * 100;
            
            requestsRemaining.textContent = `${remaining}/${maxRequests}`;
            
            // Apply color based on remaining
            requestsRemaining.classList.remove('text-gray-400', 'text-primary', 'text-amber-500', 'text-red-500');
            if (remaining === 0) {
                requestsRemaining.classList.add('text-red-500');
            } else if (percentage <= 25) {
                requestsRemaining.classList.add('text-amber-500');
            } else {
                requestsRemaining.classList.add('text-primary');
            }
        }
        
        if (resetTimeEl) {
            // Calculate time until reset with countdown
            const now = new Date();
            const resetDate = rateLimit.resetTime;
            const diffMs = resetDate - now;
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            const diffSeconds = Math.floor((diffMs % (1000 * 60)) / 1000);
            
            if (diffMs <= 0) {
                resetTimeEl.textContent = 'Resetting soon...';
            } else if (diffHours > 0) {
                resetTimeEl.textContent = `${diffHours}h ${diffMinutes}m`;
            } else if (diffMinutes > 0) {
                resetTimeEl.textContent = `${diffMinutes}m ${diffSeconds}s`;
            } else {
                resetTimeEl.textContent = `${diffSeconds}s`;
            }
        }
    } else {
        if (requestsRemaining) {
            requestsRemaining.textContent = 'Loading...';
        }
    }
}

// AI Enhancement Functions
function updateEnhanceButtonState() {
    if (!enhanceBtn || !outputText) return;
    
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        if (window.AIService && window.AIService.isOpenAIConfigured) {
            hasApiKey = window.AIService.isOpenAIConfigured();
        }
    } else {
        if (window.AIService && window.AIService.isApiKeyConfigured) {
            hasApiKey = window.AIService.isApiKeyConfigured();
        }
    }
    
    // Enable button if text exists and API key is configured
    enhanceBtn.disabled = !hasText || !hasApiKey || isEnhancing || isTextEnhanced;
    
    if (!hasApiKey) {
        enhanceBtn.title = `Please configure your ${selectedModel === 'openai' ? 'OpenAI-compatible' : 'Gemini'} API key in Settings first`;
    } else if (isTextEnhanced) {
        enhanceBtn.title = 'Text already enhanced';
    } else {
        enhanceBtn.title = 'Enhance text with AI';
    }
}

function updateSummariseButtonState() {
    if (!summariseBtn || !outputText) return;
    
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        if (window.AIService && window.AIService.isOpenAIConfigured) {
            hasApiKey = window.AIService.isOpenAIConfigured();
        }
    } else {
        if (window.AIService && window.AIService.isApiKeyConfigured) {
            hasApiKey = window.AIService.isApiKeyConfigured();
        }
    }
    
    // Enable button if text exists and API key is configured
    summariseBtn.disabled = !hasText || !hasApiKey || isSummarising || hasSummary;
    
    if (!hasApiKey) {
        summariseBtn.title = `Please configure your ${selectedModel === 'openai' ? 'OpenAI-compatible' : 'Gemini'} API key in Settings first`;
    } else if (hasSummary) {
        summariseBtn.title = 'Text already summarised';
    } else {
        summariseBtn.title = 'Summarise text with AI';
    }
}

async function enhanceText() {
    if (isEnhancing || !originalOcrText) {
        console.log('Enhance skipped: isEnhancing=' + isEnhancing + ', originalOcrText=' + originalOcrText);
        return;
    }
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        if (window.AIService && window.AIService.isOpenAIConfigured) {
            hasApiKey = window.AIService.isOpenAIConfigured();
        }
    } else {
        if (window.AIService && window.AIService.isApiKeyConfigured) {
            hasApiKey = window.AIService.isApiKeyConfigured();
        }
    }
    
    if (!hasApiKey) {
        showToast('API Key Required', `Please configure your ${selectedModel === 'openai' ? 'OpenAI-compatible' : 'Gemini'} API key in Settings first`, 'info');
        openSettingsModal();
        return;
    }
    
    // Check for minimum text length
    if (!originalOcrText || originalOcrText.trim().length < 10) {
        showToast('Text Too Short', 'Need at least 10 characters to enhance', 'info');
        return;
    }
    
    console.log('Starting enhancement...');
    isEnhancing = true;
    
    // Show loading state
    console.log('[Enhance] Setting loading state');
    if (enhanceBtn) {
        enhanceBtn.classList.add('loading');
        enhanceBtn.disabled = true;
        const btnText = enhanceBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.classList.add('hidden');
            btnText.style.display = 'none';
        }
        const btnLoading = enhanceBtn.querySelector('.btn-loading');
        if (btnLoading) {
            btnLoading.classList.remove('hidden');
            btnLoading.classList.add('flex');
            btnLoading.style.display = 'flex';
        }
        console.log('[Enhance] Loading state set, button HTML:', enhanceBtn.innerHTML.substring(0, 200));
    }
    
    try {
        let result;
        
        // Use appropriate API based on selected model
        console.log('[Enhance] Calling AI service for model:', selectedModel);
        if (selectedModel === 'openai') {
            if (window.AIService && window.AIService.cleanupTextOpenAI) {
                console.log('[Enhance] Awaiting cleanupTextOpenAI...');
                result = await window.AIService.cleanupTextOpenAI(originalOcrText);
                console.log('[Enhance] cleanupTextOpenAI returned:', result ? { type: typeof result, hasText: !!result.text, hasUsage: !!result.usage } : 'null');
            } else {
                throw new Error('OpenAI-compatible service not available');
            }
        } else {
            if (window.AIService && window.AIService.cleanupText) {
                console.log('[Enhance] Awaiting cleanupText (Gemini)...');
                result = await window.AIService.cleanupText(originalOcrText);
                console.log('[Enhance] cleanupText returned:', result ? { type: typeof result, hasText: !!result.text, hasUsage: !!result.usage } : 'null');
            } else {
                throw new Error('Gemini service not available');
            }
        }
        
        console.log('[Enhance] About to process result');
        
        // Update text
        if (outputText) {
            outputText.value = result.text;
        }
        isTextEnhanced = true;
        
        // Show enhanced indicator
        if (outputSection) {
            outputSection.classList.add('enhanced');
        }
        
        // Show undo button
        if (undoBtn) {
            undoBtn.style.display = 'flex';
        }
        
        // Update token usage display (cumulative)
        console.log('[Enhance] Result received:', { textLength: result.text?.length, usage: result.usage });
        if (result.usage) {
            addToTokenUsage(result.usage);
        } else {
            console.log('[Enhance] No usage data in result');
        }
        
        // Update word count
        updateWordCount();
        
        // Show success feedback - reset button to show "Enhanced ✓"
        console.log('[Enhance] Success - resetting button state');
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.classList.remove('loading');
            
            const btnText = enhanceBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.classList.remove('hidden');
                btnText.style.display = 'flex';
                btnText.innerHTML = '<svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>Enhanced ✓';
            }
            
            const btnLoading = enhanceBtn.querySelector('.btn-loading');
            if (btnLoading) {
                btnLoading.classList.add('hidden');
                btnLoading.classList.remove('flex');
                btnLoading.style.display = 'none';
            }
        }
        showToast('Text Enhanced', 'OCR errors have been cleaned up', 'success');
        
        console.log('[Enhance] Button reset to completed state');
        
    } catch (error) {
        console.error('[Enhance] Error:', error.message);
        showToast('Enhancement Failed', error.message || 'Failed to enhance text', 'error');
        // Reset button on error
        resetEnhanceButton();
    } finally {
        console.log('[Enhance] Finally block executed');
        isEnhancing = false;
        if (enhanceBtn) {
            enhanceBtn.classList.remove('loading');
        }
        updateEnhanceButtonState();
    }
}

// Reset enhance button state
function resetEnhanceButton() {
    console.log('[Enhance] resetEnhanceButton called');
    if (!enhanceBtn) {
        console.log('[Enhance] enhanceBtn not found');
        return;
    }
    enhanceBtn.disabled = false;
    enhanceBtn.classList.remove('loading');
    
    const btnText = enhanceBtn.querySelector('.btn-text');
    if (btnText) {
        btnText.classList.remove('hidden');
        btnText.style.display = 'flex';
        btnText.innerHTML = '<svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>Enhance';
    }
    
    const btnLoading = enhanceBtn.querySelector('.btn-loading');
    if (btnLoading) {
        btnLoading.classList.add('hidden');
        btnLoading.classList.remove('flex');
        btnLoading.style.display = 'none';
    }
    
    console.log('[Enhance] Button reset complete');
}

// Reset summarise button state
function resetSummariseButton() {
    console.log('[Summarise] resetSummariseButton called');
    if (!summariseBtn) {
        console.log('[Summarise] summariseBtn not found');
        return;
    }
    summariseBtn.disabled = false;
    summariseBtn.classList.remove('loading');
    
    const btnText = summariseBtn.querySelector('.btn-text');
    if (btnText) {
        btnText.classList.remove('hidden');
        btnText.style.display = 'flex';
        btnText.innerHTML = '<svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>Summarise';
    }
    
    const btnLoading = summariseBtn.querySelector('.btn-loading');
    if (btnLoading) {
        btnLoading.classList.add('hidden');
        btnLoading.classList.remove('flex');
        btnLoading.style.display = 'none';
    }
    
    console.log('[Summarise] Button reset complete');
}

function undoEnhance() {
    if (!originalOcrText) return;
    
    if (outputText) {
        outputText.value = originalOcrText;
    }
    isTextEnhanced = false;
    
    if (outputSection) {
        outputSection.classList.remove('enhanced');
    }
    if (undoBtn) {
        undoBtn.style.display = 'none';
    }
    
    // Update word count
    updateWordCount();
    
    // Reset enhance button
    if (enhanceBtn) {
        const btnText = enhanceBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = 'Enhance';
        }
    }
    updateEnhanceButtonState();
    
    showToast('Reverted', 'Text restored to original OCR output', 'info');
}

// Summarisation Functions
async function summariseText() {
    if (isSummarising) {
        console.log('Summarise skipped: already summarising');
        return;
    }
    
    if (!outputText) return;
    const textToSummarise = outputText.value.trim();
    if (!textToSummarise || textToSummarise === 'No text detected in the image.') {
        console.log('Summarise skipped: no text');
        return;
    }
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        if (window.AIService && window.AIService.isOpenAIConfigured) {
            hasApiKey = window.AIService.isOpenAIConfigured();
        }
    } else {
        if (window.AIService && window.AIService.isApiKeyConfigured) {
            hasApiKey = window.AIService.isApiKeyConfigured();
        }
    }
    
    if (!hasApiKey) {
        showToast('API Key Required', `Please configure your ${selectedModel === 'openai' ? 'OpenAI-compatible' : 'Gemini'} API key in Settings first`, 'info');
        openSettingsModal();
        return;
    }
    
    // Check for minimum text length
    if (textToSummarise.length < 50) {
        showToast('Text Too Short', 'Need at least 50 characters to summarise effectively', 'info');
        return;
    }
    
    console.log('Starting summarisation...');
    isSummarising = true;
    
    // Show loading state
    console.log('[Summarise] Setting loading state');
    if (summariseBtn) {
        summariseBtn.classList.add('loading');
        summariseBtn.disabled = true;
        const btnText = summariseBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.classList.add('hidden');
            btnText.style.display = 'none';
        }
        const btnLoading = summariseBtn.querySelector('.btn-loading');
        if (btnLoading) {
            btnLoading.classList.remove('hidden');
            btnLoading.classList.add('flex');
            btnLoading.style.display = 'flex';
        }
        console.log('[Summarise] Loading state set, button HTML:', summariseBtn.innerHTML.substring(0, 200));
    }
    
    // Show summary section in loading state
    if (summarySection) {
        summarySection.style.display = 'block';
        summarySection.classList.add('loading');
        summarySection.classList.remove('collapsed');
    }
    if (summaryText) {
        summaryText.innerHTML = '<p>Generating summary...</p>';
    }
    
    try {
        let result;
        
        // Use appropriate API based on selected model
        if (selectedModel === 'openai') {
            if (window.AIService && window.AIService.summariseTextOpenAI) {
                result = await window.AIService.summariseTextOpenAI(textToSummarise);
            } else {
                throw new Error('OpenAI-compatible service not available');
            }
        } else {
            if (window.AIService && window.AIService.summariseText) {
                result = await window.AIService.summariseText(textToSummarise);
            } else {
                throw new Error('Gemini service not available');
            }
        }
        
        // Store and display summary
        currentSummary = result.text;
        hasSummary = true;
        
        // Format and display summary with markdown-like rendering
        if (summaryText) {
            summaryText.innerHTML = formatSummary(result.text);
        }
        
        // Update token usage display (cumulative)
        console.log('[Summarise] Result received:', { textLength: result.text?.length, usage: result.usage });
        if (result.usage) {
            addToTokenUsage(result.usage);
        } else {
            console.log('[Summarise] No usage data in result');
        }
        
        // Show success feedback - reset button to show "Summarised ✓"
        console.log('[Summarise] Success - resetting button state');
        if (summariseBtn) {
            summariseBtn.disabled = false;
            summariseBtn.classList.remove('loading');
            
            const btnText = summariseBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.classList.remove('hidden');
                btnText.style.display = 'flex';
                btnText.innerHTML = '<svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>Summarised ✓';
            }
            
            const btnLoading = summariseBtn.querySelector('.btn-loading');
            if (btnLoading) {
                btnLoading.classList.add('hidden');
                btnLoading.classList.remove('flex');
                btnLoading.style.display = 'none';
            }
        }
        showToast('Summary Generated', 'Text has been summarised successfully', 'success');
        
        console.log('[Summarise] Button reset to completed state');
        
    } catch (error) {
        console.error('[Summarise] Error:', error.message);
        showToast('Summarisation Failed', error.message || 'Failed to summarise text', 'error');
        // Reset button on error
        resetSummariseButton();
        if (summarySection) {
            summarySection.style.display = 'none';
        }
        hasSummary = false;
    } finally {
        console.log('[Summarise] Finally block executed');
        isSummarising = false;
        if (summariseBtn) {
            summariseBtn.classList.remove('loading');
        }
        if (summarySection) {
            summarySection.classList.remove('loading');
        }
        updateSummariseButtonState();
    }
}

function formatSummary(text) {
    if (!text) return '';
    
    // Convert markdown-like formatting to HTML
    let formatted = text
        // Bold text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Bullet points
        .replace(/^[•\-\*]\s+(.+)$/gm, '<li>$1</li>')
        // Line breaks to paragraphs
        .split('\n\n')
        .map(p => p.trim())
        .filter(p => p)
        .map(p => {
            if (p.includes('<li>')) {
                return '<ul>' + p + '</ul>';
            }
            return '<p>' + p + '</p>';
        })
        .join('');
    
    return formatted;
}

function toggleSummary() {
    if (summarySection) {
        summarySection.classList.toggle('collapsed');
    }
}

async function copySummary() {
    if (!currentSummary) return;
    
    try {
        await navigator.clipboard.writeText(currentSummary);
        
        // Show feedback
        if (copySummaryBtn) {
            const originalHTML = copySummaryBtn.innerHTML;
            copySummaryBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            `;
            
            setTimeout(() => {
                copySummaryBtn.innerHTML = originalHTML;
            }, 2000);
        }
        
        showToast('Copied', 'Summary copied to clipboard', 'success', 2000);
        
    } catch (error) {
        console.error('Copy Summary Error:', error);
        showToast('Copy Failed', 'Failed to copy summary', 'error');
    }
}

// Token usage tracking (cumulative)
function addToTokenUsage(usage) {
    console.log('[Token Usage] addToTokenUsage called with:', usage);
    
    if (!usage) {
        console.log('[Token Usage] No usage data provided');
        return;
    }
    
    totalUsage.inputTokens += usage.inputTokens || 0;
    totalUsage.outputTokens += usage.outputTokens || 0;
    totalUsage.totalTokens += usage.totalTokens || 0;
    totalUsage.totalCost += (usage.cost && usage.cost.totalCost) ? usage.cost.totalCost : 0;
    
    console.log('[Token Usage] Updated totals:', totalUsage);
    
    updateTokenUsageDisplay();
}

function updateTokenUsageDisplay() {
    console.log('[Token Usage] updateTokenUsageDisplay called');
    console.log('[Token Usage] Elements found:', {
        tokenUsage: !!tokenUsage,
        inputTokensEl: !!inputTokensEl,
        outputTokensEl: !!outputTokensEl,
        totalTokensEl: !!totalTokensEl,
        tokenCostEl: !!tokenCostEl
    });
    console.log('[Token Usage] Current totals:', totalUsage);
    
    if (!tokenUsage || !inputTokensEl || !outputTokensEl || !totalTokensEl || !tokenCostEl) {
        console.error('[Token Usage] Missing DOM elements');
        return;
    }
    
    tokenUsage.style.display = 'block';
    console.log('[Token Usage] Set tokenUsage display to block');
    
    if (window.AIService && window.AIService.formatTokenCount) {
        const formattedInput = window.AIService.formatTokenCount(totalUsage.inputTokens);
        const formattedOutput = window.AIService.formatTokenCount(totalUsage.outputTokens);
        const formattedTotal = window.AIService.formatTokenCount(totalUsage.totalTokens);
        
        console.log('[Token Usage] Formatted values:', { formattedInput, formattedOutput, formattedTotal });
        
        inputTokensEl.textContent = formattedInput;
        outputTokensEl.textContent = formattedOutput;
        totalTokensEl.textContent = formattedTotal;
    } else {
        console.log('[Token Usage] Using default formatting');
        inputTokensEl.textContent = totalUsage.inputTokens.toString();
        outputTokensEl.textContent = totalUsage.outputTokens.toString();
        totalTokensEl.textContent = totalUsage.totalTokens.toString();
    }
    
    // Format cumulative cost
    const costFormatted = totalUsage.totalCost < 0.0001
        ? 'Free (< $0.0001)'
        : `$${totalUsage.totalCost.toFixed(6)}`;
    tokenCostEl.textContent = costFormatted;
    console.log('[Token Usage] Set cost to:', costFormatted);
    
    // Verify DOM was updated
    console.log('[Token Usage] DOM verification:', {
        inputValue: inputTokensEl.textContent,
        outputValue: outputTokensEl.textContent,
        totalValue: totalTokensEl.textContent,
        costValue: tokenCostEl.textContent
    });
}

// Initialize the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}