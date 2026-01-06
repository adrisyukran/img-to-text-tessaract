/**
 * Environment Variable Loader for Browser
 * This script loads environment variables from a .env file and makes them available to the browser
 */

(function() {
    // Function to parse .env file content
    function parseEnvContent(content) {
        const envVars = {};
        const lines = content.split('\n');
        
        for (let line of lines) {
            line = line.trim();
            // Skip empty lines and comments
            if (!line || line.startsWith('#')) continue;
            
            // Handle both formats: KEY=VALUE and KEY = VALUE
            const match = line.match(/^([^=]+)=(.*)$/);
            if (match) {
                const key = match[1].trim();
                let value = match[2].trim();
                
                // Remove quotes if present
                if ((value.startsWith('"') && value.endsWith('"')) || 
                    (value.startsWith("'") && value.endsWith("'"))) {
                    value = value.substring(1, value.length - 1);
                }
                
                envVars[key] = value;
            }
        }
        
        return envVars;
    }
    
    // Function to load .env file
    function loadEnvFile() {
        // In a real implementation, we would need to fetch the .env file
        // But for security reasons, browsers don't allow direct file access
        // So we'll provide a manual way to set these variables
        
        console.log('Environment variables should be set on the server or injected before loading this app.');
        console.log('For development, you can manually set window.OPENAI_COMPATIBLE_API_KEY etc.');
    }
    
    // Try to load environment variables
    try {
        loadEnvFile();
    } catch (error) {
        console.warn('Could not load .env file:', error);
    }
})();
