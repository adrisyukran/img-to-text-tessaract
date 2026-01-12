/**
 * Server for Image to Text Converter with Environment Variable Injection
 * This server serves the application with environment variables properly injected
 */

// Load environment variables from .env file
require('dotenv').config();

// Debug logging
console.log('=== Environment Variables Debug ===');
console.log('Process env keys:', Object.keys(process.env));
console.log('OPENAI_COMPATIBLE_API_KEY:', process.env.OPENAI_COMPATIBLE_API_KEY);
console.log('OPENAI_COMPATIBLE_BASE_URL:', process.env.OPENAI_COMPATIBLE_BASE_URL);
console.log('OPENAI_COMPATIBLE_MODEL:', process.env.OPENAI_COMPATIBLE_MODEL);

const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3005;

// Helper function to inject environment variables into HTML
function injectEnvVars(htmlContent) {
    // Create script tag with environment variables
    const envScript = `
    <script>
        // Inject environment variables
        window.OPENAI_COMPATIBLE_API_KEY = ${process.env.OPENAI_COMPATIBLE_API_KEY ? JSON.stringify(process.env.OPENAI_COMPATIBLE_API_KEY) : 'null'};
        window.OPENAI_COMPATIBLE_BASE_URL = ${process.env.OPENAI_COMPATIBLE_BASE_URL ? JSON.stringify(process.env.OPENAI_COMPATIBLE_BASE_URL) : 'null'};
        window.OPENAI_COMPATIBLE_MODEL = ${process.env.OPENAI_COMPATIBLE_MODEL ? JSON.stringify(process.env.OPENAI_COMPATIBLE_MODEL) : 'null'};
        console.log('Environment variables injected:', {
            hasApiKey: !!window.OPENAI_COMPATIBLE_API_KEY,
            apiKeyLength: window.OPENAI_COMPATIBLE_API_KEY ? window.OPENAI_COMPATIBLE_API_KEY.length : 0,
            baseUrl: window.OPENAI_COMPATIBLE_BASE_URL,
            model: window.OPENAI_COMPATIBLE_MODEL
        });
    </script>`;
    
    // Try to inject before </head> first (for pages with head section)
    if (htmlContent.includes('</head>')) {
        htmlContent = htmlContent.replace('</head>', `${envScript}\n</head>`);
    } else {
        // For pages without head (like landing.html), inject at start of <body>
        htmlContent = htmlContent.replace('<body', `${envScript}\n<body`);
    }
    
    return htmlContent;
}

// Serve the landing page with environment variables injected (MUST come before static middleware)
app.get('/landing.html', (req, res) => {
    const landingPath = path.join(__dirname, 'landing.html');
    let htmlContent = fs.readFileSync(landingPath, 'utf8');
    htmlContent = injectEnvVars(htmlContent);
    res.send(htmlContent);
});

// Serve the main page with environment variables injected (MUST come before static middleware)
app.get('/', (req, res) => {
    const indexPath = path.join(__dirname, 'index.html');
    let htmlContent = fs.readFileSync(indexPath, 'utf8');
    htmlContent = injectEnvVars(htmlContent);
    res.send(htmlContent);
});

// Serve static files (CSS, JS, images, etc.)
app.use(express.static('.', {
    setHeaders: (res, path) => {
        // Don't cache HTML files - they need to go through our injection
        if (path.endsWith('.html')) {
            res.setHeader('Cache-Control', 'no-cache');
        }
    }
}));

// Handle favicon request
app.get('/favicon.ico', (req, res) => {
    res.status(204).end();
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT} (listening on all interfaces)`);
    console.log('Environment variables for OpenAI-compatible API:');
    console.log('OPENAI_COMPATIBLE_API_KEY:', process.env.OPENAI_COMPATIBLE_API_KEY ? '[SET]' : '[NOT SET]');
    console.log('OPENAI_COMPATIBLE_BASE_URL:', process.env.OPENAI_COMPATIBLE_BASE_URL || '[USING DEFAULT]');
    console.log('OPENAI_COMPATIBLE_MODEL:', process.env.OPENAI_COMPATIBLE_MODEL || '[USING DEFAULT]');
});

module.exports = app;        // For HTML pages, inject environment variables
