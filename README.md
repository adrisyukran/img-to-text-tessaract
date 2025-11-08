# 📷 Image to Text Converter

A simple, browser-based OCR (Optical Character Recognition) application powered by Tesseract.js. Extract text from images with ease!

## ✨ Features

- **Multiple Input Methods**:
  - Click to select image files
  - Paste images directly from clipboard (perfect for Snipping Tool!)
  - Drag and drop images
  
- **User-Friendly Interface**:
  - Clean, modern design
  - Real-time progress updates during OCR processing
  - Image preview before processing
  
- **Convenient Output**:
  - Extracted text displayed in an editable text area
  - One-click copy to clipboard
  - Clear and reset functionality

- **No Installation Required**:
  - Runs entirely in the browser
  - No server needed
  - Works offline after initial load

## 🚀 Quick Start

### Option 1: Direct File Access
1. Download or clone this repository
2. Open `index.html` in your web browser
3. Start converting images to text!

### Option 2: Local Server (Recommended)
If you have Python installed:
```bash
# Python 3
python -m http.server 8000
```

Then visit `http://localhost:8000` in your browser.

Or with Node.js:
```bash
# Using npx (no installation required)
npx http-server
```

## 📖 How to Use

### Method 1: Select a File
1. Click on the upload area
2. Choose an image file from your computer
3. Wait for the OCR to process
4. Copy the extracted text

### Method 2: Paste from Clipboard
1. Take a screenshot using Windows Snipping Tool (Win + Shift + S)
2. Click anywhere on the page
3. Press `Ctrl + V` to paste
4. The OCR will automatically process the image

### Method 3: Drag and Drop
1. Drag an image file from your file explorer
2. Drop it onto the upload area
3. Wait for processing
4. View and copy the results

## 🖼️ Supported Image Formats

- PNG
- JPEG/JPG
- BMP
- GIF
- WEBP

## 🛠️ Technologies Used

- **HTML5** - Structure and semantic markup
- **CSS3** - Responsive styling with modern design
- **JavaScript** - Application logic and event handling
- **Tesseract.js v5** - OCR engine (WebAssembly-based)

## 📝 Technical Details

### Browser Requirements
- Modern browser with ES6+ support
- Clipboard API support for paste functionality
- File API support for file selection

### Performance Notes
- First-time OCR may take longer as it downloads the Tesseract.js library
- Processing time depends on image size and complexity
- Typical processing: 3-10 seconds for standard screenshots

### Privacy
- All processing happens locally in your browser
- No images or text are sent to any server
- Completely offline-capable after initial load

## 🔧 Customization

### Changing OCR Language
Edit `script.js` line 115 to use a different language:
```javascript
const worker = await Tesseract.createWorker('eng', 1, {
```

Available languages include: `eng`, `spa`, `fra`, `deu`, `chi_sim`, `chi_tra`, etc.
See [Tesseract.js language data](https://github.com/naptha/tessdata) for full list.

### Styling
Modify `style.css` to customize:
- Color scheme (currently purple gradient)
- Layout dimensions
- Font styles
- Animations

## 🐛 Troubleshooting

**Issue**: Paste not working
- **Solution**: Ensure you've granted clipboard permissions to the browser

**Issue**: OCR takes too long
- **Solution**: Try using smaller images or compress the image first

**Issue**: Poor text recognition
- **Solution**: Use high-contrast, clear images with readable fonts

**Issue**: "Failed to process image" error
- **Solution**: Check internet connection for first-time use, or try refreshing the page

## 📄 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests!

## 📬 Support

For issues or questions, please open an issue on GitHub.

---

**Made with ❤️ using Tesseract OCR**
