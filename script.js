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

// Settings Modal Elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const saveApiKeyBtn = document.getElementById('saveApiKeyBtn');
const apiKeyInput = document.getElementById('apiKeyInput');
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
    
    // Close modal on overlay click
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeSettingsModal();
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsModal.classList.contains('active')) {
            closeSettingsModal();
        }
    });

    // Load initial API key status
    updateApiKeyStatus();
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
}

// Settings Modal Functions
function openSettingsModal() {
    const currentKey = window.AIService.getApiKey();
    apiKeyInput.value = currentKey || '';
    updateApiKeyStatus();
    settingsModal.classList.add('active');
    apiKeyInput.focus();
}

function closeSettingsModal() {
    settingsModal.classList.remove('active');
    apiKeyInput.value = '';
}

async function saveApiKey() {
    const key = apiKeyInput.value.trim();
    
    if (!key) {
        window.AIService.clearApiKey();
        updateApiKeyStatus();
        closeSettingsModal();
        return;
    }

    // Save the key first
    window.AIService.setApiKey(key);
    
    // Test the connection
    await testApiConnection();
}

async function testApiConnection() {
    if (isTestingConnection) return;
    
    isTestingConnection = true;
    statusDot.className = 'status-dot testing';
    statusMessage.textContent = 'Testing connection...';
    saveApiKeyBtn.disabled = true;

    try {
        await window.AIService.testConnection();
        statusDot.className = 'status-dot configured';
        statusMessage.textContent = 'API key valid ✓';
        
        // Close modal after successful test
        setTimeout(() => {
            closeSettingsModal();
        }, 1000);
    } catch (error) {
        statusDot.className = 'status-dot error';
        statusMessage.textContent = error.message || 'Connection failed';
    } finally {
        isTestingConnection = false;
        saveApiKeyBtn.disabled = false;
    }
}

function updateApiKeyStatus() {
    if (window.AIService.isApiKeyConfigured()) {
        statusDot.className = 'status-dot configured';
        statusMessage.textContent = 'API key configured';
    } else {
        statusDot.className = 'status-dot';
        statusMessage.textContent = 'No API key configured';
    }
}

// AI Enhancement Functions
function updateEnhanceButtonState() {
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    const hasApiKey = window.AIService.isApiKeyConfigured();
    
    enhanceBtn.disabled = !hasText || !hasApiKey || isEnhancing || isTextEnhanced;
    
    if (!hasApiKey) {
        enhanceBtn.title = 'Please configure your API key in Settings first';
    } else if (isTextEnhanced) {
        enhanceBtn.title = 'Text already enhanced';
    } else {
        enhanceBtn.title = 'Enhance text with AI';
    }
}

function updateSummariseButtonState() {
    const hasText = outputText.value.trim() && outputText.value !== 'No text detected in the image.';
    const hasApiKey = window.AIService.isApiKeyConfigured();
    
    summariseBtn.disabled = !hasText || !hasApiKey || isSummarising || hasSummary;
    
    if (!hasApiKey) {
        summariseBtn.title = 'Please configure your API key in Settings first';
    } else if (hasSummary) {
        summariseBtn.title = 'Text already summarised';
    } else {
        summariseBtn.title = 'Summarise text with AI';
    }
}

async function enhanceText() {
    if (isEnhancing || !originalOcrText) return;
    
    // Check for API key
    if (!window.AIService.isApiKeyConfigured()) {
        showError('Please add your Gemini API key in Settings first');
        openSettingsModal();
        return;
    }
    
    isEnhancing = true;
    enhanceBtn.classList.add('loading');
    enhanceBtn.querySelector('.btn-text').textContent = 'Enhancing';
    enhanceBtn.disabled = true;
    
    try {
        const result = await window.AIService.cleanupText(originalOcrText);
        
        // Update text
        outputText.value = result.text;
        isTextEnhanced = true;
        
        // Show enhanced indicator
        outputSection.classList.add('enhanced');
        
        // Show undo button
        undoBtn.style.display = 'flex';
        
        // Update token usage display (cumulative)
        addToTokenUsage(result.usage);
        
        // Show success feedback
        enhanceBtn.querySelector('.btn-text').textContent = 'Enhanced ✓';
        
    } catch (error) {
        console.error('Enhance Error:', error);
        showError(error.message || 'Failed to enhance text');
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
    
    // Reset enhance button
    enhanceBtn.querySelector('.btn-text').textContent = 'Enhance';
    updateEnhanceButtonState();
}

// Summarisation Functions
async function summariseText() {
    if (isSummarising) return;
    
    const textToSummarise = outputText.value.trim();
    if (!textToSummarise || textToSummarise === 'No text detected in the image.') return;
    
    // Check for API key
    if (!window.AIService.isApiKeyConfigured()) {
        showError('Please add your Gemini API key in Settings first');
        openSettingsModal();
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
        const result = await window.AIService.summariseText(textToSummarise);
        
        // Store and display summary
        currentSummary = result.text;
        hasSummary = true;
        
        // Format and display summary with markdown-like rendering
        summaryText.innerHTML = formatSummary(result.text);
        
        // Update token usage display (cumulative)
        addToTokenUsage(result.usage);
        
        // Show success feedback
        summariseBtn.querySelector('.btn-text').textContent = 'Summarised ✓';
        
    } catch (error) {
        console.error('Summarise Error:', error);
        showError(error.message || 'Failed to summarise text');
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
        
    } catch (error) {
        console.error('Copy Summary Error:', error);
        showError('Failed to copy summary');
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
