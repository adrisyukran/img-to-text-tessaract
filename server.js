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
const PORT = process.env.PORT || 3001;

// Serve static files (but not index.html)
app.use(express.static('.', {
    index: false  // Don't serve index.html through static middleware
}));

// Serve the main page with environment variables injected
app.get('/', (req, res) => {
    // Read the index.html file
    const indexPath = path.join(__dirname, 'index.html');
    let htmlContent = fs.readFileSync(indexPath, 'utf8');
    
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
    
    // Inject the environment variables script before the closing head tag
    const originalHeadClosed = (htmlContent.match(/<\/head>/g) || []).length;
    htmlContent = htmlContent.replace('</head>', `${envScript}\n</head>`);
    const newHeadClosed = (htmlContent.match(/<\/head>/g) || []).length;
    
    // Debug: log what we're sending
    console.log(`HTML replacement: ${originalHeadClosed} </head> tags before, ${newHeadClosed} after`);
    console.log('Sending HTML with injected env vars');
    
    res.send(htmlContent);
});

// Handle favicon request
app.get('/favicon.ico', (req, res) => {
    res.status(204).end();
});

// Serve index.html for any other routes (SPA support) with environment variables injected
app.get('*', (req, res) => {
    // For static assets, serve them normally
    if (req.path.endsWith('.js') || req.path.endsWith('.css') || req.path.endsWith('.ico') || req.path.endsWith('.png') || req.path.endsWith('.jpg') || req.path.endsWith('.jpeg') || req.path.endsWith('.gif')) {
        const filePath = path.join(__dirname, req.path);
        fs.access(filePath, fs.constants.F_OK, (err) => {
            if (err) {
                res.status(404).send('File not found');
            } else {
                res.sendFile(filePath);
            }
        });
    } else {
        // For HTML pages, inject environment variables
        const indexPath = path.join(__dirname, 'index.html');
        let htmlContent = fs.readFileSync(indexPath, 'utf8');
        
        // Create script tag with environment variables
        const envScript = `
        <script>
            // Inject environment variables
            window.OPENAI_COMPATIBLE_API_KEY = ${process.env.OPENAI_COMPATIBLE_API_KEY ? JSON.stringify(process.env.OPENAI_COMPATIBLE_API_KEY) : 'null'};
            window.OPENAI_COMPATIBLE_BASE_URL = ${process.env.OPENAI_COMPATIBLE_BASE_URL ? JSON.stringify(process.env.OPENAI_COMPATIBLE_BASE_URL) : 'null'};
            window.OPENAI_COMPATIBLE_MODEL = ${process.env.OPENAI_COMPATIBLE_MODEL ? JSON.stringify(process.env.OPENAI_COMPATIBLE_MODEL) : 'null'};
            console.log('Environment variables injected for route:', req.path, {
                hasApiKey: !!window.OPENAI_COMPATIBLE_API_KEY,
                apiKeyLength: window.OPENAI_COMPATIBLE_API_KEY ? window.OPENAI_COMPATIBLE_API_KEY.length : 0,
                baseUrl: window.OPENAI_COMPATIBLE_BASE_URL,
                model: window.OPENAI_COMPATIBLE_MODEL
            });
        </script>`;
        
        // Inject the environment variables script before the closing head tag
        htmlContent = htmlContent.replace('</head>', `${envScript}\n</head>`);
        
        res.send(htmlContent);
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log('Environment variables for OpenAI-compatible API:');
    console.log('OPENAI_COMPATIBLE_API_KEY:', process.env.OPENAI_COMPATIBLE_API_KEY ? '[SET]' : '[NOT SET]');
    console.log('OPENAI_COMPATIBLE_BASE_URL:', process.env.OPENAI_COMPATIBLE_BASE_URL || '[USING DEFAULT]');
    console.log('OPENAI_COMPATIBLE_MODEL:', process.env.OPENAI_COMPATIBLE_MODEL || '[USING DEFAULT]');
});

module.exports = app;
