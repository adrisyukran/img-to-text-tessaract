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
const wordCountEl = document.getElementById('wordCount');
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
const resetTime = document.getElementById('resetTime');
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

// Initialize event listeners
function init() {
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
    clearBtn.addEventListener('click', resetApp);
    
    // Copy button
    copyBtn.addEventListener('click', copyToClipboard);

    // AI buttons
    enhanceBtn.addEventListener('click', enhanceText);
    undoBtn.addEventListener('click', undoEnhance);
    summariseBtn.addEventListener('click', summariseText);
    
    // Summary section
    toggleSummaryBtn.addEventListener('click', toggleSummary);
    summaryHeader.addEventListener('click', (e) => {
        if (e.target !== copySummaryBtn && !copySummaryBtn.contains(e.target)) {
            toggleSummary();
        }
    });
    copySummaryBtn.addEventListener('click', copySummary);

    // Settings modal
    settingsBtn.addEventListener('click', openSettingsModal);
    closeModalBtn.addEventListener('click', closeSettingsModal);
    cancelModalBtn.addEventListener('click', closeSettingsModal);
    saveApiKeyBtn.addEventListener('click', saveApiKey);
    
    // Model selection
    modelGemini.addEventListener('change', handleModelChange);
    modelOpenAI.addEventListener('change', handleModelChange);
    
    // Close modal on overlay click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeSettingsModal();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close modal
        if (e.key === 'Escape' && settingsModal.classList.contains('active')) {
            closeSettingsModal();
            return;
        }
        
        // Only handle shortcuts when output is visible and modal is not open
        if (outputSection.style.display === 'none' || settingsModal.classList.contains('active')) {
            return;
        }
        
        // Ctrl+E for Enhance
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            if (!enhanceBtn.disabled) {
                enhanceText();
            }
        }
        
        // Ctrl+Shift+S for Summarise
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            if (!summariseBtn.disabled) {
                summariseText();
            }
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
    enhanceBtn.title = 'Enhance text with AI (Ctrl+E)';
    summariseBtn.title = 'Summarise text with AI (Ctrl+Shift+S)';
    copyBtn.title = 'Copy to clipboard (Ctrl+Shift+C)';
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
    uploadArea.classList.add('dragover');
}

// Handle drag leave
function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
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
        imagePreview.src = e.target.result;
        previewContainer.style.display = 'block';
        uploadArea.style.display = 'none';
        
        // Start OCR
        performOCR(e.target.result);
    };
    reader.readAsDataURL(file);
}

// Perform OCR using Tesseract.js
async function performOCR(imageData) {
    // Show status
    statusSection.style.display = 'block';
    outputSection.style.display = 'none';
    statusText.textContent = 'Initializing OCR...';
    
    try {
        // Create Tesseract worker
        const worker = await Tesseract.createWorker('eng', 1, {
            logger: (m) => {
                // Update status based on progress
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
        });
        
        // Perform OCR
        const { data: { text } } = await worker.recognize(imageData);
        
        // Terminate worker
        await worker.terminate();
        
        // Show results
        displayResults(text);
        
    } catch (error) {
        console.error('OCR Error:', error);
        showError('Failed to process image. Please try again.');
    }
}

// Display OCR results
function displayResults(text) {
    statusSection.style.display = 'none';
    outputSection.style.display = 'block';
    
    // Reset AI-related state
    isTextEnhanced = false;
    outputSection.classList.remove('enhanced');
    undoBtn.style.display = 'none';
    tokenUsage.style.display = 'none';
    
    // Reset summary state
    hasSummary = false;
    currentSummary = null;
    summarySection.style.display = 'none';
    summaryText.innerHTML = '';
    
    // Reset cumulative usage
    totalUsage = { inputTokens: 0, outputTokens: 0, totalTokens: 0, totalCost: 0 };
    
    // Set text values FIRST
    if (text.trim()) {
        outputText.value = text;
        originalOcrText = text;
    } else {
        outputText.value = 'No text detected in the image.';
        originalOcrText = null;
    }
    
    // Update word count
    updateWordCount();
    
    // Update button states AFTER text is set
    updateEnhanceButtonState();
    updateSummariseButtonState();
}

// Copy text to clipboard
async function copyToClipboard() {
    const text = outputText.value;
    
    if (!text) {
        return;
    }
    
    try {
        await navigator.clipboard.writeText(text);
        
        // Show feedback
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
        
    } catch (error) {
        console.error('Copy Error:', error);
        showError('Failed to copy text');
    }
}

// Reset the application
function resetApp() {
    currentImage = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    statusSection.style.display = 'none';
    outputSection.style.display = 'none';
    uploadArea.style.display = 'block';
    outputText.value = '';
    
    // Reset AI state
    originalOcrText = null;
    isTextEnhanced = false;
    isEnhancing = false;
    isSummarising = false;
    hasSummary = false;
    currentSummary = null;
    outputSection.classList.remove('enhanced');
    undoBtn.style.display = 'none';
    tokenUsage.style.display = 'none';
    summarySection.style.display = 'none';
    summaryText.innerHTML = '';
    
    // Reset cumulative usage
    totalUsage = { inputTokens: 0, outputTokens: 0, totalTokens: 0, totalCost: 0 };
}

// Show error message
function showError(message) {
    statusSection.style.display = 'block';
    statusText.textContent = message;
    statusText.style.color = '#ff4757';
    
    setTimeout(() => {
        statusSection.style.display = 'none';
        statusText.style.color = '#667eea';
    }, 3000);
    
    // Also show as toast for better visibility
    showToast('Error', message, 'error');
}

// Toast Notification System
function showToast(title, message, type = 'info', duration = 4000) {
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
    const text = outputText.value || '';
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    
    charCountEl.textContent = charCount.toLocaleString();
    wordCountNumEl.textContent = wordCount.toLocaleString();
}

// Settings Modal Functions
function openSettingsModal() {
    // Load current settings
    const currentGeminiKey = window.AIService.getApiKey();
    
    // Set Gemini key
    apiKeyInput.value = currentGeminiKey || '';
    
    // Load selected model (default to Gemini)
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    if (selectedModel === 'openai') {
        modelOpenAI.checked = true;
        geminiKeyGroup.style.display = 'none';
        openaiConfigGroup.style.display = 'block';
    } else {
        modelGemini.checked = true;
        geminiKeyGroup.style.display = 'block';
        openaiConfigGroup.style.display = 'none';
    }
    
    // Update rate limit display
    updateRateLimitDisplay();
    
    settingsModal.classList.add('active');
    apiKeyInput.focus();
}

// Model selection change handler
function handleModelChange() {
    if (modelOpenAI.checked) {
        geminiKeyGroup.style.display = 'none';
        openaiConfigGroup.style.display = 'block';
        localStorage.setItem('selected_ai_model', 'openai');
    } else {
        geminiKeyGroup.style.display = 'block';
        openaiConfigGroup.style.display = 'none';
        localStorage.setItem('selected_ai_model', 'gemini');
    }
}

function closeSettingsModal() {
    settingsModal.classList.remove('active');
    apiKeyInput.value = '';
}

async function saveApiKey() {
    // Save only Gemini API key (OpenAI-compatible is configured via environment variables only)
    if (!modelOpenAI.checked) {
        const geminiKey = apiKeyInput.value.trim();
        
        if (!geminiKey) {
            window.AIService.clearApiKey();
        } else {
            window.AIService.setApiKey(geminiKey);
        }
    }
    
    updateApiKeyStatus();
    updateRateLimitDisplay();
    closeSettingsModal();
}

async function testApiConnection() {
    if (isTestingConnection) return;
    
    isTestingConnection = true;
    statusDot.className = 'status-dot testing';
    statusMessage.textContent = 'Testing connection...';
    saveApiKeyBtn.disabled = true;

    try {
        let success = false;
        
        if (modelOpenAI.checked) {
            // Test OpenAI-compatible API
            if (window.AIService.isOpenAIConfigured()) {
                await window.AIService.testOpenAIConnection();
                success = true;
                statusDot.className = 'status-dot configured';
                statusMessage.textContent = 'OpenAI-compatible API key valid ✓';
            } else {
                throw new Error('OpenAI-compatible API key not configured');
            }
        } else {
            // Test Gemini API
            if (window.AIService.isApiKeyConfigured()) {
                await window.AIService.testConnection();
                success = true;
                statusDot.className = 'status-dot configured';
                statusMessage.textContent = 'Gemini API key valid ✓';
            } else {
                throw new Error('Gemini API key not configured');
            }
        }
        
        if (success) {
            // Close modal after successful test
            setTimeout(() => {
                closeSettingsModal();
            }, 1000);
        }
    } catch (error) {
        statusDot.className = 'status-dot error';
        statusMessage.textContent = error.message || 'Connection failed';
    } finally {
        isTestingConnection = false;
        saveApiKeyBtn.disabled = false;
    }
}

function updateApiKeyStatus() {
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    
    if (selectedModel === 'openai') {
        if (window.AIService.isOpenAIConfigured()) {
            statusDot.className = 'status-dot configured';
            statusMessage.textContent = 'OpenAI-compatible API configured';
        } else {
            statusDot.className = 'status-dot';
            statusMessage.textContent = 'No OpenAI-compatible API key configured';
        }
    } else {
        if (window.AIService.isApiKeyConfigured()) {
            statusDot.className = 'status-dot configured';
            statusMessage.textContent = 'Gemini API key configured';
        } else {
            statusDot.className = 'status-dot';
            statusMessage.textContent = 'No Gemini API key configured';
        }
    }
}

function updateRateLimitDisplay() {
    if (modelOpenAI.checked) {
        const rateLimit = window.AIService.checkRateLimit();
        requestsRemaining.textContent = `${rateLimit.remaining}/${window.APP_CONFIG.openaiCompatible.rateLimit.maxRequests}`;
        
        // Calculate time until reset
        const now = new Date();
        const resetDate = rateLimit.resetTime;
        const diffMs = resetDate - now;
        const diffHours = Math.ceil(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.ceil(diffMs / (1000 * 60));
        
        if (diffHours > 0) {
            resetTime.textContent = `${diffHours} hour${diffHours > 1 ? 's' : ''}`;
        } else if (diffMinutes > 0) {
            resetTime.textContent = `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`;
        } else {
            resetTime.textContent = 'soon';
        }
    }
}

// AI Enhancement Functions
function updateEnhanceButtonState() {
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        hasApiKey = window.AIService.isOpenAIConfigured();
    } else {
        hasApiKey = window.AIService.isApiKeyConfigured();
    }
    
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
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        hasApiKey = window.AIService.isOpenAIConfigured();
    } else {
        hasApiKey = window.AIService.isApiKeyConfigured();
    }
    
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
    if (isEnhancing || !originalOcrText) return;
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        hasApiKey = window.AIService.isOpenAIConfigured();
    } else {
        hasApiKey = window.AIService.isApiKeyConfigured();
    }
    
    if (!hasApiKey) {
        showToast('API Key Required', `Please configure your ${selectedModel === 'openai' ? 'OpenAI-compatible' : 'Gemini'} API key in Settings first`, 'info');
        openSettingsModal();
        return;
    }
    
    // Check for minimum text length
    if (originalOcrText.trim().length < 10) {
        showToast('Text Too Short', 'Need at least 10 characters to enhance', 'info');
        return;
    }
    
    isEnhancing = true;
    enhanceBtn.classList.add('loading');
    enhanceBtn.querySelector('.btn-text').textContent = 'Enhancing';
    enhanceBtn.disabled = true;
    
    try {
        let result;
        
        // Use appropriate API based on selected model
        if (selectedModel === 'openai') {
            result = await window.AIService.cleanupTextOpenAI(originalOcrText);
        } else {
            result = await window.AIService.cleanupText(originalOcrText);
        }
        
        // Update text
        outputText.value = result.text;
        isTextEnhanced = true;
        
        // Show enhanced indicator
        outputSection.classList.add('enhanced');
        
        // Show undo button
        undoBtn.style.display = 'flex';
        
        // Update token usage display (cumulative)
        addToTokenUsage(result.usage);
        
        // Update word count
        updateWordCount();
        
        // Show success feedback
        enhanceBtn.querySelector('.btn-text').textContent = 'Enhanced ✓';
        showToast('Text Enhanced', 'OCR errors have been cleaned up', 'success');
        
    } catch (error) {
        console.error('Enhance Error:', error);
        showToast('Enhancement Failed', error.message || 'Failed to enhance text', 'error');
        enhanceBtn.querySelector('.btn-text').textContent = 'Enhance';
    } finally {
        isEnhancing = false;
        enhanceBtn.classList.remove('loading');
        updateEnhanceButtonState();
    }
}

function undoEnhance() {
    if (!originalOcrText) return;
    
    outputText.value = originalOcrText;
    isTextEnhanced = false;
    outputSection.classList.remove('enhanced');
    undoBtn.style.display = 'none';
    
    // Update word count
    updateWordCount();
    
    // Reset enhance button
    enhanceBtn.querySelector('.btn-text').textContent = 'Enhance';
    updateEnhanceButtonState();
    
    showToast('Reverted', 'Text restored to original OCR output', 'info');
}

// Summarisation Functions
async function summariseText() {
    if (isSummarising) return;
    
    const textToSummarise = outputText.value.trim();
    if (!textToSummarise || textToSummarise === 'No text detected in the image.') return;
    
    // Check for API key based on selected model
    const selectedModel = localStorage.getItem('selected_ai_model') || 'gemini';
    let hasApiKey = false;
    
    if (selectedModel === 'openai') {
        hasApiKey = window.AIService.isOpenAIConfigured();
    } else {
        hasApiKey = window.AIService.isApiKeyConfigured();
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
    
    isSummarising = true;
    summariseBtn.classList.add('loading');
    summariseBtn.querySelector('.btn-text').textContent = 'Summarising';
    summariseBtn.disabled = true;
    
    // Show summary section in loading state
    summarySection.style.display = 'block';
    summarySection.classList.add('loading');
    summarySection.classList.remove('collapsed');
    summaryText.innerHTML = '<p>Generating summary...</p>';
    
    try {
        let result;
        
        // Use appropriate API based on selected model
        if (selectedModel === 'openai') {
            result = await window.AIService.summariseTextOpenAI(textToSummarise);
        } else {
            result = await window.AIService.summariseText(textToSummarise);
        }
        
        // Store and display summary
        currentSummary = result.text;
        hasSummary = true;
        
        // Format and display summary with markdown-like rendering
        summaryText.innerHTML = formatSummary(result.text);
        
        // Update token usage display (cumulative)
        addToTokenUsage(result.usage);
        
        // Show success feedback
        summariseBtn.querySelector('.btn-text').textContent = 'Summarised ✓';
        showToast('Summary Generated', 'Text has been summarised successfully', 'success');
        
    } catch (error) {
        console.error('Summarise Error:', error);
        showToast('Summarisation Failed', error.message || 'Failed to summarise text', 'error');
        summariseBtn.querySelector('.btn-text').textContent = 'Summarise';
        summarySection.style.display = 'none';
        hasSummary = false;
    } finally {
        isSummarising = false;
        summariseBtn.classList.remove('loading');
        summarySection.classList.remove('loading');
        updateSummariseButtonState();
    }
}

function formatSummary(text) {
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
    summarySection.classList.toggle('collapsed');
}

async function copySummary() {
    if (!currentSummary) return;
    
    try {
        await navigator.clipboard.writeText(currentSummary);
        
        // Show feedback
        const originalHTML = copySummaryBtn.innerHTML;
        copySummaryBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        `;
        
        setTimeout(() => {
            copySummaryBtn.innerHTML = originalHTML;
        }, 2000);
        
        showToast('Copied', 'Summary copied to clipboard', 'success', 2000);
        
    } catch (error) {
        console.error('Copy Summary Error:', error);
        showToast('Copy Failed', 'Failed to copy summary', 'error');
    }
}

// Token usage tracking (cumulative)
function addToTokenUsage(usage) {
    if (!usage) return;
    
    totalUsage.inputTokens += usage.inputTokens;
    totalUsage.outputTokens += usage.outputTokens;
    totalUsage.totalTokens += usage.totalTokens;
    totalUsage.totalCost += usage.cost.totalCost;
    
    updateTokenUsageDisplay();
}

function updateTokenUsageDisplay() {
    tokenUsage.style.display = 'block';
    
    inputTokensEl.textContent = window.AIService.formatTokenCount(totalUsage.inputTokens);
    outputTokensEl.textContent = window.AIService.formatTokenCount(totalUsage.outputTokens);
    totalTokensEl.textContent = window.AIService.formatTokenCount(totalUsage.totalTokens);
    
    // Format cumulative cost
    const costFormatted = totalUsage.totalCost < 0.0001 
        ? 'Free (< $0.0001)' 
        : `$${totalUsage.totalCost.toFixed(6)}`;
    tokenCostEl.textContent = costFormatted;
}

// Initialize the app
init();
