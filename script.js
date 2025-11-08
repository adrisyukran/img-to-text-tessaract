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

// State
let currentImage = null;

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
    
    if (text.trim()) {
        outputText.value = text;
    } else {
        outputText.value = 'No text detected in the image.';
    }
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

// Initialize the app
init();
