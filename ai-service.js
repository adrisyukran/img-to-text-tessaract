/**
 * AI Service Module - Gemini 2.5 Flash Integration
 * Handles all AI-related API calls and configuration
 */

// API Configuration
const AI_CONFIG = {
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
    model: 'gemini-2.5-flash',
    maxTokens: {
        cleanup: 8192,
        summary: 1024
    },
    temperature: 0.3,
    storageKey: 'gemini_api_key'
};

// Prompts
const PROMPTS = {
    cleanup: `You are an OCR text cleanup assistant. Clean up the following text that was extracted from an image using OCR:

1. Fix obvious OCR errors (e.g., 'rn' misread as 'm', '0' as 'O', 'l' as '1')
2. Fix punctuation and spacing issues
3. Correct obvious spelling mistakes caused by OCR
4. Maintain paragraph breaks and structure
5. Preserve the original meaning - do NOT add or remove content
6. Do NOT summarise or paraphrase

Return ONLY the cleaned text with no explanations or commentary.`,

    summarise: `Summarise the following text concisely:

1. Start with a single TL;DR sentence
2. Follow with 3-5 bullet points covering key information
3. Keep total summary under 150 words
4. Highlight any important: dates, names, numbers, or action items
5. Use clear, simple language

Format your response as:
**TL;DR:** [one sentence summary]

**Key Points:**
• [point 1]
• [point 2]
• [point 3]`
};

/**
 * Get the stored API key from localStorage
 * @returns {string|null} The API key or null if not set
 */
function getApiKey() {
    return localStorage.getItem(AI_CONFIG.storageKey);
}

/**
 * Save the API key to localStorage
 * @param {string} key - The API key to store
 */
function setApiKey(key) {
    if (key && key.trim()) {
        localStorage.setItem(AI_CONFIG.storageKey, key.trim());
    } else {
        localStorage.removeItem(AI_CONFIG.storageKey);
    }
}

/**
 * Check if an API key is configured
 * @returns {boolean} True if API key exists
 */
function isApiKeyConfigured() {
    const key = getApiKey();
    return key !== null && key.trim().length > 0;
}

/**
 * Clear the stored API key
 */
function clearApiKey() {
    localStorage.removeItem(AI_CONFIG.storageKey);
}

/**
 * Call the Gemini API with a prompt and text content
 * @param {string} systemPrompt - The system instruction
 * @param {string} userContent - The user's text content
 * @param {number} maxTokens - Maximum tokens for response
 * @returns {Promise<string>} The API response text
 * @throws {Error} If API call fails
 */
async function callGemini(systemPrompt, userContent, maxTokens = AI_CONFIG.maxTokens.cleanup) {
    const apiKey = getApiKey();
    
    if (!apiKey) {
        throw new Error('API key not configured. Please add your Gemini API key in Settings.');
    }

    if (!userContent || userContent.trim().length === 0) {
        throw new Error('No text content provided.');
    }

    const url = `${AI_CONFIG.endpoint}?key=${apiKey}`;
    
    const requestBody = {
        contents: [
            {
                parts: [
                    {
                        text: `${systemPrompt}\n\n---\n\nText to process:\n\n${userContent}`
                    }
                ]
            }
        ],
        generationConfig: {
            temperature: AI_CONFIG.temperature,
            maxOutputTokens: maxTokens
        }
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            
            if (response.status === 400) {
                throw new Error('Invalid request. Please check your API key and try again.');
            } else if (response.status === 401 || response.status === 403) {
                throw new Error('Invalid API key. Please check your Gemini API key in Settings.');
            } else if (response.status === 429) {
                throw new Error('Rate limit exceeded. Please wait a moment and try again.');
            } else if (response.status >= 500) {
                throw new Error('Gemini API server error. Please try again later.');
            } else {
                throw new Error(errorData.error?.message || `API error: ${response.status}`);
            }
        }

        const data = await response.json();

        // Extract text from Gemini response
        if (data.candidates && data.candidates[0] && data.candidates[0].content) {
            const parts = data.candidates[0].content.parts;
            if (parts && parts[0] && parts[0].text) {
                return parts[0].text;
            }
        }

        // Check for blocked content
        if (data.candidates && data.candidates[0] && data.candidates[0].finishReason === 'SAFETY') {
            throw new Error('Content was blocked by safety filters. Please try different text.');
        }

        throw new Error('Unexpected API response format.');

    } catch (error) {
        // Re-throw if it's already our custom error
        if (error.message.includes('API key') || 
            error.message.includes('Rate limit') || 
            error.message.includes('server error') ||
            error.message.includes('safety filters') ||
            error.message.includes('No text content')) {
            throw error;
        }
        
        // Handle network errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Network error. Please check your internet connection.');
        }
        
        throw new Error(`Failed to process: ${error.message}`);
    }
}

/**
 * Clean up OCR text using AI
 * @param {string} text - The OCR text to clean
 * @returns {Promise<string>} The cleaned text
 */
async function cleanupText(text) {
    return callGemini(PROMPTS.cleanup, text, AI_CONFIG.maxTokens.cleanup);
}

/**
 * Summarise text using AI
 * @param {string} text - The text to summarise
 * @returns {Promise<string>} The summary
 */
async function summariseText(text) {
    return callGemini(PROMPTS.summarise, text, AI_CONFIG.maxTokens.summary);
}

/**
 * Test the API connection with a simple request
 * @returns {Promise<boolean>} True if connection successful
 */
async function testConnection() {
    try {
        const result = await callGemini('Respond with only the word "connected"', 'Test', 50);
        return result.toLowerCase().includes('connected');
    } catch (error) {
        throw error;
    }
}

// Export functions for use in other scripts
window.AIService = {
    getApiKey,
    setApiKey,
    isApiKeyConfigured,
    clearApiKey,
    callGemini,
    cleanupText,
    summariseText,
    testConnection,
    PROMPTS,
    CONFIG: AI_CONFIG
};