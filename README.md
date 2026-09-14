# 📄 ResumeStudio

> **AI-Powered ATS-Optimized Resume Generator**  
> Transform your resume to match any job description with intelligent keyword optimization and professional LaTeX formatting.

<div align="center">
<img width="659" height="298" alt="image" src="https://github.com/user-attachments/assets/bd5d25d8-4c76-425c-8631-f2b8266288cf" />

<img width="644" height="491" alt="image" src="https://github.com/user-attachments/assets/d6cde67a-c29a-4101-9d1c-e4656d95d30f" />


</div>

---

## 🌟 Overview

**ResumeStudio** is a cutting-edge web application that leverages AI to automatically optimize your resume for any job posting. Simply paste a job description, and the system intelligently rewrites your resume with relevant keywords, skills, and experience highlights to maximize your ATS (Applicant Tracking System) score.

### ✨ Why ResumeStudio?

- **🎯 ATS-Optimized**: Automatically incorporates job-specific keywords
- **🤖 AI-Powered**: Uses advanced language models for intelligent content generation
- **⚡ Instant PDF**: Generates professional LaTeX-formatted PDFs in seconds
- **🎨 Beautiful UI**: Dark, minimal interface with smooth animations
- **🔒 Privacy-First**: All files auto-delete after 1 hour
- **📱 Responsive**: Works seamlessly on desktop and mobile devices

---

## 🚀 Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Smart Resume Optimization** | AI analyzes job descriptions and tailors your resume content |
| **LaTeX Generation** | Professional typesetting with clean, ATS-friendly formatting |
| **One-Click PDF Export** | Instant PDF generation with download capability |
| **Real-time Preview** | View generated LaTeX code before downloading |
| **Auto-Cleanup** | Files automatically deleted after 1 hour for privacy |
| **Mobile Responsive** | Perfect experience on any device |

### Technical Highlights

- 🔄 **Async Processing**: Non-blocking AI queries with progress indicators
- 🧹 **Smart Cleanup**: Background thread removes old files automatically
- 🎯 **Error Handling**: Robust error management with user-friendly messages
- 📊 **File Metadata**: Tracks creation time and cleanup schedules
- 🔐 **Secure Storage**: Temporary file system with UUID-based naming

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **Git** (for cloning the repository)

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/resumestudio.git
cd resumestudio
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
```
flask
curl_cffi
requests
```

### 4. Create Required Directories

```bash
mkdir generated_resumes
```

---

## ⚙️ Configuration

### 🔑 Step 1: Get Perplexity Cookie

The application uses Perplexity AI for intelligent resume optimization. You need to obtain your cookie:

1. **Open Perplexity.ai** in your browser
2. **Open Developer Tools** (F12 or Right-click → Inspect)
3. **Go to Network Tab**
4. **Refresh the page** and interact with Perplexity
5. **Find any request** to `perplexity.ai`
6. **Copy the Cookie header** from Request Headers

**Example Cookie:**
```
pplx.visitor-id=8839cf87-f6ac-4df0-a96a-d66d29b4e347; session_token=abc123...
```

### 📝 Step 2: Update Cookie in Code

Open the main Python file and locate the `ask_perplexity()` function:

```python
def ask_perplexity(query: str):
    # ...
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Content-Type': 'application/json',
        'Referer': 'https://www.perplexity.ai/',
        'Origin': 'https://www.perplexity.ai',
        'Cookie': 'YOUR_COOKIE_HERE'  # ← Replace this line
    }
```

**Replace** `'YOUR_COOKIE_HERE'` with your actual cookie string.

---

### 📄 Step 3: Replace Your Resume Template

Locate the `optimize_resume()` function and find the LaTeX template section:

```python
@app.route('/optimize', methods=['POST'])
def optimize_resume():
    # ...
    prompt = f"""MY RESUME LATEX CODE:

\\documentclass[10pt,a4paper]{{article}}
# ... YOUR RESUME LATEX CODE HERE ...
\\end{{document}}
```

**How to Replace:**

1. **Export your current resume to LaTeX** (use Overleaf, TeXworks, or any LaTeX editor)
2. **Copy your entire LaTeX code** (from `\documentclass` to `\end{document}`)
3. **Replace the template** in the code with your LaTeX
4. **Escape curly braces**: Change `{` to `{{` and `}` to `}}`

**Example:**
```latex
Before: \textbf{Your Name}
After:  \\textbf{{Your Name}}
```

---

## 🎮 Usage

### Starting the Application

```bash
python app.py
```

You should see:
```
🚀 ResumeStudio starting (dark minimal)…
📁 Generated files stored in: generated_resumes
🗑️ Automatic cleanup enabled (files deleted after 1 hour)
 * Running on http://0.0.0.0:5000
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

### Generating Your Optimized Resume

1. **Paste Job Description**
   - Copy the entire job posting from LinkedIn, Indeed, etc.
   - Paste into the left text area

2. **Click Generate**
   - Wait 1-2 minutes for AI processing
   - Progress indicator shows processing status

3. **Review LaTeX Code**
   - View generated LaTeX in the right panel
   - Click "Copy" to copy the code

4. **Download PDF**
   - Click "Download PDF" when ready
   - PDF is ATS-optimized and ready to submit

5. **Clear & Start Over**
   - Click "Clear" to reset for a new job application

---

## 🏗️ Project Structure

```
resumestudio/
│
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── generated_resumes/        # Temporary PDF storage (auto-created)
│   └── [UUID].pdf           # Generated resume files
│
└── templates/                # (Optional) External templates
```

---

## 🔧 Configuration Options

### Cleanup Interval

Change auto-cleanup time (default: 1 hour):

```python
CLEANUP_INTERVAL = 3600  # seconds (3600 = 1 hour)
```

### Upload Folder

Change PDF storage location:

```python
UPLOAD_FOLDER = 'generated_resumes'
```

### Server Port

Change the port number:

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change 5000 to your port
```

---

## 🎨 Customization

### Modify UI Colors

Edit the CSS variables in `HTML_TEMPLATE`:

```css
:root {
    --bg: #0b0f17;           /* Background */
    --panel: #121826;        /* Panel background */
    --primary: #7c9cff;      /* Primary color */
    --success: #22c55e;      /* Success color */
    --error: #ef4444;        /* Error color */
}
```

### Change Fonts

Modify the font-family in the body style:

```css
body {
    font-family: 'Your Preferred Font', system-ui, -apple-system;
}
```

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"No answer found" error** | Update Perplexity cookie |
| **PDF generation fails** | Check internet connection to texviewer.herokuapp.com |
| **Port already in use** | Change port in `app.run()` or kill existing process |
| **Import errors** | Run `pip install -r requirements.txt` |
| **LaTeX errors** | Verify your template has proper escaping (`{{` and `}}`) |

### Debug Mode

Enable detailed logging:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 📊 Performance Tips

1. **Cookie Expiry**: Update Perplexity cookie if requests fail
2. **Network**: Ensure stable internet for PDF generation
3. **Template Size**: Keep LaTeX template under 2 pages for best results
4. **Job Description**: Paste complete job postings for better optimization

---

## 🔐 Security Considerations

- ⚠️ **Cookie Security**: Never commit cookies to version control
- 🗑️ **Auto-Cleanup**: Files are automatically deleted after 1 hour
- 🔒 **Local Storage**: All processing happens on your server
- 🚫 **No Data Collection**: Zero user tracking or analytics

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---


## 🙏 Acknowledgments

- **Perplexity AI** for intelligent content generation
- **TeXViewer** for LaTeX to PDF conversion
- **Flask** for the web framework
- **curl_cffi** for advanced HTTP requests

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

**Made with ❤️ by Koushik Navuluri**

</div>
"# resume-studio" 
"# resume-studio" 
