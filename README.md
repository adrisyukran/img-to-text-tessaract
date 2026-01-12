# 📷 Image to Text Converter

A powerful, browser-based OCR (Optical Character Recognition) application powered by Tesseract.js and enhanced with **Google Gemini AI**. Extract text from images, clean up OCR errors, and generate summaries — all running locally in your browser!

## ✨ Features

### 🔍 OCR Extraction
- **Multiple Input Methods**:
  - Click to select image files
  - Paste images directly from clipboard (perfect for Snipping Tool!)
  - Drag and drop images
  
- **User-Friendly Interface**:
  - Clean, modern design
  - Real-time progress updates during OCR processing
  - Image preview before processing
  - Word and character count display

### 🤖 AI-Powered Enhancement (NEW!)
- **Text Cleanup**: Fix OCR errors, punctuation, and formatting using Gemini AI
- **Smart Summarisation**: Generate concise summaries with TL;DR and bullet points
- **Token Usage Tracking**: Monitor your API usage with real-time token counts and cost estimates
- **Cumulative Tracking**: See total tokens used across multiple AI operations

### ⌨️ Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl + V` | Paste image from clipboard |
| `Ctrl + E` | Enhance text with AI |
| `Ctrl + Shift + S` | Summarise text |
| `Ctrl + Shift + C` | Copy extracted text |
| `Escape` | Close settings modal |

### 🔒 Privacy-First
- All OCR processing happens locally in your browser
- AI features use your own API key (never stored on any server)
- No images or text are sent anywhere except to Google's Gemini API (when you use AI features)
- Works offline for basic OCR after initial load

<!-- 

## 🚀 Quick Start

### Step 1: Open the App
**Option A: Direct File Access**
1. Download or clone this repository
2. Open `index.html` in your web browser

**Option B: Local Server (Recommended)**
```bash
# Python 3
python -m http.server 8000

# Or with Node.js
npx http-server
```
Then visit `http://localhost:8000`

### Step 2: Set Up AI Features (Optional but Recommended)
1. Click the ⚙️ **Settings** button in the top-right corner
2. Get your free API key from [Google AI Studio](https://aistudio.google.com/apikey)
3. Paste your API key and click **Save**
4. The status indicator will turn green when connected ✓

### Step 3: Start Converting!
1. Upload, paste, or drag an image
2. Wait for OCR to extract the text
3. Click **✨ Enhance** to clean up OCR errors
4. Click **📝 Summarise** to get a quick summary
5. Copy the results!
-->
## 📖 How to Use

### Basic OCR
1. **Select/Paste/Drop** an image
2. Wait for Tesseract.js to process (3-10 seconds typically)
3. View extracted text in the output area
4. Click **Copy** to copy to clipboard

### AI Enhancement
1. After OCR completes, click **✨ Enhance**
2. Gemini AI will fix:
   - OCR misreads (e.g., 'rn' → 'm', '0' → 'O')
   - Punctuation and spacing issues
   - Obvious spelling mistakes
3. Click **↩️ Undo** to revert to original if needed

### Summarisation
1. Click **📝 Summarise** to generate a summary
2. View the collapsible summary section with:
   - **TL;DR**: One-sentence summary
   - **Key Points**: Bullet points of main information
3. Click the summary header to expand/collapse
4. Use the copy button to copy the summary

### Token Usage
The AI Usage panel shows:
- **Input**: Tokens sent to the AI
- **Output**: Tokens received from the AI
- **Total**: Cumulative tokens for all operations
- **Cost**: Estimated cost (usually "Free" for light usage)

## 🖼️ Supported Image Formats

- PNG
- JPEG/JPG
- BMP
- GIF
- WEBP

## 🛠️ Technologies Used

- **HTML5** - Structure and semantic markup
- **CSS3** - Responsive styling with modern design
- **JavaScript (ES6+)** - Application logic and event handling
- **Tesseract.js v5** - OCR engine (WebAssembly-based)
- **Google Gemini 2.5 Flash** - AI text enhancement and summarisation

## 📝 Technical Details

### Browser Requirements
- Modern browser with ES6+ support
- Clipboard API support for paste functionality
- File API support for file selection

### Performance Notes
- First-time OCR may take longer as it downloads the Tesseract.js library (~2MB)
- Typical OCR processing: 3-10 seconds for standard screenshots
- AI features typically respond in 1-3 seconds

### API Usage (Gemini 2.5 Flash)
- **Free Tier**: 1,500 requests/day, 15 requests/minute
- **Typical Usage**: ~200-500 tokens per enhance, ~150-300 tokens per summarise
- **Cost**: Effectively free for personal use (< $0.0001 per operation)

### Privacy & Security
- API key stored in browser's localStorage (never leaves your device)
- OCR runs entirely client-side
- AI requests go directly from your browser to Google's API
- No intermediary servers or data collection

<!--
## 🔧 Customization

### Changing OCR Language
Edit `script.js` to use a different language:
```javascript
const worker = await Tesseract.createWorker('eng', 1, {
```

Available languages: `eng`, `spa`, `fra`, `deu`, `chi_sim`, `chi_tra`, `jpn`, `kor`, etc.
See [Tesseract.js language data](https://github.com/naptha/tessdata) for full list.

### Styling
Modify `style.css` to customize:
- Color scheme (currently purple gradient)
- Layout dimensions
- Font styles
- Animations

### AI Prompts
Edit `ai-service.js` to modify the AI behavior:
- `PROMPTS.cleanup` - Controls how text enhancement works
- `PROMPTS.summarise` - Controls summary format and style

## 🐛 Troubleshooting

**Issue**: Paste not working
- **Solution**: Ensure you've granted clipboard permissions to the browser

**Issue**: OCR takes too long
- **Solution**: Try using smaller images or compress the image first

**Issue**: Poor text recognition
- **Solution**: Use high-contrast, clear images with readable fonts

**Issue**: AI features not working
- **Solution**: Check that your API key is valid in Settings. The status should show green.

**Issue**: "Rate limit exceeded" error
- **Solution**: Wait a moment and try again. Free tier allows 15 requests/minute.

**Issue**: "API key invalid" error
- **Solution**: Get a new API key from [Google AI Studio](https://aistudio.google.com/apikey)

-->
## 📁 Project Structure

```
img-to-text-tessaract/
├── index.html          # Main HTML file
├── script.js           # Application logic, event handling
├── style.css           # Styling and animations
├── ai-service.js       # Gemini API integration
├── README.md           # This file

```

## 🔮 Future Enhancements

Planned features for future development:
- Entity extraction (names, dates, emails, phone numbers)
- Document Q&A (ask questions about extracted text)
- Multi-provider AI support (OpenAI, Ollama)
- Document history and search
- Export to PDF/Word

<!--
## 📄 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests!

## 📬 Support

For issues or questions, please open an issue on GitHub.

## 🔧 Environment Variables for OpenAI-Compatible API

The application now supports OpenAI-compatible APIs with rate limiting. You can configure the API key and settings through environment variables for better security:

### Environment Variables
- `OPENAI_COMPATIBLE_API_KEY` - Your OpenAI-compatible API key
- `OPENAI_COMPATIBLE_BASE_URL` - Base URL for the API (default: https://nano-gpt.com/api/v1)
- `OPENAI_COMPATIBLE_MODEL` - Model name (default: chatgpt-4o-latest)

### Setting Environment Variables

#### Development (.env file)
Create a `.env` file in your project root:
```bash
OPENAI_COMPATIBLE_API_KEY=your-api-key-here
OPENAI_COMPATIBLE_BASE_URL=https://nano-gpt.com/api/v1
OPENAI_COMPATIBLE_MODEL=chatgpt-4o-latest
```

#### Running the Application
Since this is a browser-based application that needs to access environment variables, you need to run it through the provided server:

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the server**:
   ```bash
   npm start
   ```

3. **Visit the application**:
   Open your browser and go to `http://localhost:3000`

The server will automatically inject the environment variables from your `.env` file into the browser application.

#### Production Deployments
For production deployments, set environment variables according to your platform:
- **Heroku**: Config Vars
- **Vercel**: Environment Variables
- **Docker**: `-e` flag or docker-compose environment
- **Cloud Platforms**: Platform-specific environment variable settings

### Benefits
- API keys are not exposed in the frontend
- Centralized configuration management
- Easy deployment across different environments
- Rate limiting (3 requests per 24 hours) for the pre-built model

---

**Made with ❤️ using Tesseract OCR & Google Gemini AI**
-->