/**
 * AI Service Module - Multi-AI Integration
 * Handles all AI-related API calls and configuration for both Gemini and OpenAI-compatible endpoints
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
    storageKey: 'gemini_api_key',
    // Gemini 2.5 Flash pricing (per 1M tokens) - as of 2024
    // Free tier: 1,500 requests/day, so effectively $0 for most personal use
    pricing: {
        input: 0.075,   // $0.075 per 1M input tokens
        output: 0.30    // $0.30 per 1M output tokens
    }
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
 * Calculate estimated cost based on token usage
 * @param {number} inputTokens - Number of input tokens
 * @param {number} outputTokens - Number of output tokens
 * @returns {object} Cost breakdown
 */
function calculateCost(inputTokens, outputTokens) {
    const inputCost = (inputTokens / 1000000) * AI_CONFIG.pricing.input;
    const outputCost = (outputTokens / 1000000) * AI_CONFIG.pricing.output;
    const totalCost = inputCost + outputCost;
    
    return {
        inputCost,
        outputCost,
        totalCost,
        // Format for display
        formatted: totalCost < 0.0001 ? 'Free (< $0.0001)' : `$${totalCost.toFixed(6)}`
    };
}

/**
 * Call the Gemini API with a prompt and text content
 * @param {string} systemPrompt - The system instruction
 * @param {string} userContent - The user's text content
 * @param {number} maxTokens - Maximum tokens for response
 * @returns {Promise<object>} Object with text and usage metadata
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
                const responseText = parts[0].text;
                
                // Extract token usage from response metadata
                const usageMetadata = data.usageMetadata || {};
                const inputTokens = usageMetadata.promptTokenCount || 0;
                const outputTokens = usageMetadata.candidatesTokenCount || 0;
                const totalTokens = usageMetadata.totalTokenCount || (inputTokens + outputTokens);
                
                // Calculate cost
                const cost = calculateCost(inputTokens, outputTokens);
                
                return {
                    text: responseText,
                    usage: {
                        inputTokens,
                        outputTokens,
                        totalTokens,
                        cost
                    }
                };
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
 * @returns {Promise<object>} Object with cleaned text and usage metadata
 */
async function cleanupText(text) {
    return callGemini(PROMPTS.cleanup, text, AI_CONFIG.maxTokens.cleanup);
}

/**
 * Summarise text using AI
 * @param {string} text - The text to summarise
 * @returns {Promise<object>} Object with summary and usage metadata
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
        return result.text.toLowerCase().includes('connected');
    } catch (error) {
        throw error;
    }
}

/**
 * Format token count for display
 * @param {number} tokens - Token count
 * @returns {string} Formatted string
 */
function formatTokenCount(tokens) {
    if (tokens >= 1000) {
        return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
}

// OpenAI-Compatible API Integration with Rate Limiting
const OPENAI_CONFIG = window.APP_CONFIG.openaiCompatible;
const STORAGE_KEYS = window.APP_CONFIG.storageKeys;

/**
 * Get OpenAI-compatible API configuration
 * @returns {object} Configuration with apiKey, baseUrl, and model
 */
function getOpenAIConfig() {
    // Priority: localStorage > environment variables > defaults
    return {
        apiKey: localStorage.getItem(STORAGE_KEYS.openaiApiKey) || OPENAI_CONFIG.apiKey,
        baseUrl: localStorage.getItem(STORAGE_KEYS.openaiBaseUrl) || OPENAI_CONFIG.baseUrl,
        model: localStorage.getItem(STORAGE_KEYS.openaiModel) || OPENAI_CONFIG.model
    };
}

/**
 * Save OpenAI-compatible API configuration
 * @param {string} apiKey - API key
 * @param {string} baseUrl - Base URL (optional)
 * @param {string} model - Model name (optional)
 */
function setOpenAIConfig(apiKey, baseUrl = null, model = null) {
    if (apiKey && apiKey.trim()) {
        localStorage.setItem(STORAGE_KEYS.openaiApiKey, apiKey.trim());
    } else {
        localStorage.removeItem(STORAGE_KEYS.openaiApiKey);
    }
    
    if (baseUrl !== null) {
        if (baseUrl.trim()) {
            localStorage.setItem(STORAGE_KEYS.openaiBaseUrl, baseUrl.trim());
        } else {
            localStorage.removeItem(STORAGE_KEYS.openaiBaseUrl);
        }
    }
    
    if (model !== null) {
        if (model.trim()) {
            localStorage.setItem(STORAGE_KEYS.openaiModel, model.trim());
        } else {
            localStorage.removeItem(STORAGE_KEYS.openaiModel);
        }
    }
}

/**
 * Check if OpenAI-compatible API is configured
 * @returns {boolean} True if API key exists
 */
function isOpenAIConfigured() {
    // Check localStorage first (user-provided key)
    const config = getOpenAIConfig();
    const hasLocalKey = config.apiKey !== null && config.apiKey.trim().length > 0;
    
    // Also check window.OPENAI_COMPATIBLE_API_KEY (from server/env injection)
    const hasEnvKey = window.OPENAI_COMPATIBLE_API_KEY && window.OPENAI_COMPATIBLE_API_KEY.trim().length > 0;
    
    return hasLocalKey || hasEnvKey;
}

/**
 * Clear OpenAI-compatible API configuration
 */
function clearOpenAIConfig() {
    localStorage.removeItem(STORAGE_KEYS.openaiApiKey);
    localStorage.removeItem(STORAGE_KEYS.openaiBaseUrl);
    localStorage.removeItem(STORAGE_KEYS.openaiModel);
}

/**
 * Get request history for rate limiting
 * @returns {Array} Array of timestamp numbers
 */
function getRequestHistory() {
    const history = localStorage.getItem(STORAGE_KEYS.openaiRequests);
    if (!history) return [];
    try {
        return JSON.parse(history);
    } catch (e) {
        return [];
    }
}

/**
 * Save request history for rate limiting
 * @param {Array} history - Array of timestamp numbers
 */
function saveRequestHistory(history) {
    localStorage.setItem(STORAGE_KEYS.openaiRequests, JSON.stringify(history));
}

/**
 * Check if rate limit has been exceeded
 * @returns {object} Object with {exceeded: boolean, remaining: number, resetTime: Date}
 */
function checkRateLimit() {
    const history = getRequestHistory();
    const now = Date.now();
    const windowMs = OPENAI_CONFIG.rateLimit.windowHours * 60 * 60 * 1000; // Convert hours to milliseconds
    const windowStart = now - windowMs;
    
    // Filter out requests older than the window
    const recentRequests = history.filter(timestamp => timestamp > windowStart);
    
    const remaining = Math.max(0, OPENAI_CONFIG.rateLimit.maxRequests - recentRequests.length);
    const exceeded = remaining <= 0;
    
    // Calculate when the oldest request will expire
    let resetTime = new Date(now + windowMs);
    if (recentRequests.length > 0) {
        const oldestRequest = Math.min(...recentRequests);
        resetTime = new Date(oldestRequest + windowMs);
    }
    
    return {
        exceeded,
        remaining,
        resetTime,
        used: recentRequests.length
    };
}

/**
 * Record a request for rate limiting
 */
function recordRequest() {
    const history = getRequestHistory();
    const now = Date.now();
    const windowMs = OPENAI_CONFIG.rateLimit.windowHours * 60 * 60 * 1000;
    const windowStart = now - windowMs;
    
    // Filter out old requests and add the new one
    const recentRequests = history.filter(timestamp => timestamp > windowStart);
    recentRequests.push(now);
    
    saveRequestHistory(recentRequests);
}

/**
 * Call the OpenAI-compatible API with a prompt and text content
 * @param {string} systemPrompt - The system instruction
 * @param {string} userContent - The user's text content
 * @param {number} maxTokens - Maximum tokens for response
 * @returns {Promise<object>} Object with text and usage metadata
 * @throws {Error} If API call fails or rate limit exceeded
 */
async function callOpenAICompatible(systemPrompt, userContent, maxTokens = 2048) {
    const config = getOpenAIConfig();
    
    if (!config.apiKey) {
        throw new Error('OpenAI-compatible API key not configured.');
    }

    if (!userContent || userContent.trim().length === 0) {
        throw new Error('No text content provided.');
    }

    // Check rate limit
    const rateLimit = checkRateLimit();
    if (rateLimit.exceeded) {
        const resetTime = rateLimit.resetTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        throw new Error(`Rate limit exceeded. Please try again after ${resetTime}. (${OPENAI_CONFIG.rateLimit.maxRequests} requests per ${OPENAI_CONFIG.rateLimit.windowHours} hours)`);
    }

    const url = `${config.baseUrl}/chat/completions`;
    
    // Prepare messages for chat completion
    const messages = [
        { role: "system", content: systemPrompt },
        { role: "user", content: userContent }
    ];
    
    const requestBody = {
        model: config.model,
        messages: messages,
        max_tokens: maxTokens,
        temperature: 0.3
    };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${config.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            
            if (response.status === 400) {
                throw new Error('Invalid request. Please check your API configuration.');
            } else if (response.status === 401 || response.status === 403) {
                throw new Error('Invalid API key. Please check your OpenAI-compatible API key.');
            } else if (response.status === 429) {
                // Record the request even if it failed due to rate limiting
                recordRequest();
                throw new Error('Rate limit exceeded by the API. Please try again later.');
            } else if (response.status >= 500) {
                throw new Error('OpenAI-compatible API server error. Please try again later.');
            } else {
                throw new Error(errorData.error?.message || `API error: ${response.status}`);
            }
        }

        const data = await response.json();
        
        // Record successful request for rate limiting
        recordRequest();

        // Extract text from OpenAI-compatible response
        if (data.choices && data.choices[0] && data.choices[0].message) {
            const responseText = data.choices[0].message.content;
            
            // Extract token usage from response
            const usage = data.usage || {};
            const inputTokens = usage.prompt_tokens || 0;
            const outputTokens = usage.completion_tokens || 0;
            const totalTokens = usage.total_tokens || (inputTokens + outputTokens);
            
            // Calculate cost using the new pricing configuration
            const cost = calculateOpenAICost(inputTokens, outputTokens);
            
            return {
                text: responseText,
                usage: {
                    inputTokens,
                    outputTokens,
                    totalTokens,
                    cost
                }
            };
        }

        throw new Error('Unexpected API response format.');

    } catch (error) {
        // Re-throw if it's already our custom error
        if (error.message.includes('API key') || 
            error.message.includes('Rate limit') || 
            error.message.includes('server error') ||
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
 * Calculate estimated cost for OpenAI-compatible API based on token usage
 * @param {number} inputTokens - Number of input tokens
 * @param {number} outputTokens - Number of output tokens
 * @returns {object} Cost breakdown
 */
function calculateOpenAICost(inputTokens, outputTokens) {
    const OPENAI_CONFIG = window.APP_CONFIG.openaiCompatible;
    const inputCost = (inputTokens / 1000000) * OPENAI_CONFIG.pricing.input;
    const outputCost = (outputTokens / 1000000) * OPENAI_CONFIG.pricing.output;
    const totalCost = inputCost + outputCost;
    
    return {
        inputCost,
        outputCost,
        totalCost,
        // Format for display
        formatted: totalCost < 0.0001 ? 'Free (< $0.0001)' : `$${totalCost.toFixed(6)}`
    };
}

/**
 * Clean up OCR text using OpenAI-compatible API
 * @param {string} text - The OCR text to clean
 * @returns {Promise<object>} Object with cleaned text and usage metadata
 */
async function cleanupTextOpenAI(text) {
    return callOpenAICompatible(PROMPTS.cleanup, text, 2048);
}

/**
 * Summarise text using OpenAI-compatible API
 * @param {string} text - The text to summarise
 * @returns {Promise<object>} Object with summary and usage metadata
 */
async function summariseTextOpenAI(text) {
    return callOpenAICompatible(PROMPTS.summarise, text, 1024);
}

/**
 * Test the OpenAI-compatible API connection
 * @returns {Promise<boolean>} True if connection successful
 */
async function testOpenAIConnection() {
    try {
        // Check rate limit first
        const rateLimit = checkRateLimit();
        if (rateLimit.exceeded) {
            const resetTime = rateLimit.resetTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            throw new Error(`Rate limit exceeded. Please try again after ${resetTime}.`);
        }
        
        const result = await callOpenAICompatible('Respond with only the word "connected"', 'Test', 50);
        return result.text.toLowerCase().includes('connected');
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
    calculateCost,
    formatTokenCount,
    PROMPTS,
    CONFIG: AI_CONFIG,
    
    // OpenAI-compatible API functions
    getOpenAIConfig,
    setOpenAIConfig,
    isOpenAIConfigured,
    clearOpenAIConfig,
    callOpenAICompatible,
    cleanupTextOpenAI,
    summariseTextOpenAI,
    testOpenAIConnection,
    checkRateLimit
};
