/**
 * Configuration for OpenAI-compatible API
 * This file contains default configuration that can be overridden
 */

// Default configuration - can be overridden by environment or build process
const DEFAULT_CONFIG = {
    openaiCompatible: {
        apiKey: null, // Will be set via environment variables
        baseUrl: 'https://nano-gpt.com/api/v1',
        model: 'openai/gpt-oss-120b',
        rateLimit: {
            maxRequests: 20,  // Increased to 20 requests per 24 hours
            windowHours: 24
        },
        // Pricing per 1M tokens 
        pricing: {
            input: 0.05,
            output: 0.25
        }
    },
    storageKeys: {
        openaiApiKey: 'openai_compatible_api_key',
        openaiBaseUrl: 'openai_compatible_base_url',
        openaiModel: 'openai_compatible_model',
        openaiRequests: 'openai_compatible_requests'
    }
};

// Check for environment variables in different contexts
function loadEnvironmentVariables() {
    // Node.js environment
    if (typeof process !== 'undefined' && process.env) {
        if (process.env.OPENAI_COMPATIBLE_API_KEY) {
            DEFAULT_CONFIG.openaiCompatible.apiKey = process.env.OPENAI_COMPATIBLE_API_KEY;
        }
        if (process.env.OPENAI_COMPATIBLE_BASE_URL) {
            DEFAULT_CONFIG.openaiCompatible.baseUrl = process.env.OPENAI_COMPATIBLE_BASE_URL;
        }
        if (process.env.OPENAI_COMPATIBLE_MODEL) {
            DEFAULT_CONFIG.openaiCompatible.model = process.env.OPENAI_COMPATIBLE_MODEL;
        }
        return;
    }
    
    // Browser environment - check for global environment variables that might be injected
    if (typeof window !== 'undefined') {
        // Check if environment variables were injected as window properties
        if (window.OPENAI_COMPATIBLE_API_KEY) {
            DEFAULT_CONFIG.openaiCompatible.apiKey = window.OPENAI_COMPATIBLE_API_KEY;
        }
        if (window.OPENAI_COMPATIBLE_BASE_URL) {
            DEFAULT_CONFIG.openaiCompatible.baseUrl = window.OPENAI_COMPATIBLE_BASE_URL;
        }
        if (window.OPENAI_COMPATIBLE_MODEL) {
            DEFAULT_CONFIG.openaiCompatible.model = window.OPENAI_COMPATIBLE_MODEL;
        }
    }
}

// Load environment variables
loadEnvironmentVariables();

// Export configuration
window.APP_CONFIG = DEFAULT_CONFIG;
