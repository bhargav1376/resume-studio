from flask import Flask, render_template, request, jsonify, send_from_directory, Response
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except Exception as e:
    import requests as curl_requests
    HAS_CURL_CFFI = False
import json
import sys
import re
import os
import uuid
import time
import threading
from datetime import datetime, timedelta
import requests as std_requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Windows stdout/stderr unicode handling
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Vercel serverless / Read-only filesystem fallback to /tmp
if os.environ.get('VERCEL') or not os.access('.', os.W_OK):
    UPLOAD_FOLDER = os.path.join('/tmp', 'generated_resumes')
else:
    UPLOAD_FOLDER = 'generated_resumes'

CLEANUP_INTERVAL = 3600  # seconds

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception:
    pass

# Simple in-memory metadata for generated files
file_metadata = {}

DEFAULT_LATEX_TEMPLATE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{fontawesome}
\usepackage{xcolor}
\usepackage{lmodern}

\hypersetup{
    colorlinks=true,
    linkcolor=black,
    urlcolor=black
}

\pagestyle{empty}
\setlist[itemize]{noitemsep, topsep=0pt, leftmargin=1.5em}

\begin{document}

\begin{center}
    {\Huge \bfseries BHARGAV CHINTHA}\\[4pt]
    \small \faEnvelope\ bhargavchintha123@gmail.com ~|~ \faPhone\ +91 9876543210 ~|~ \faGithub\ github.com/bhargav ~|~ \faLinkedin\ linkedin.com/in/bhargav
\end{center}

\vspace{-8pt}
\section*{Professional Summary}
\hrule \vspace{4pt}
Results-driven Software Engineer with hands-on experience in building scalable web applications, API integrations, and cloud services. Passionate about optimizing resume ATS scores and delivering clean, maintainable code.

\vspace{-4pt}
\section*{Technical Skills}
\hrule \vspace{4pt}
\begin{itemize}
    \item \textbf{Languages:} Python, JavaScript, HTML5, CSS3, SQL
    \item \textbf{Frameworks \& Tools:} Flask, React, Node.js, Git, Docker, Perplexity API
    \item \textbf{Database \& Cloud:} PostgreSQL, MongoDB, AWS, Heroku
\end{itemize}

\vspace{-4pt}
\section*{Experience}
\hrule \vspace{4pt}
\textbf{Software Engineer} \hfill Jan 2024 -- Present\\
\textit{ResumeStudio Labs} \hfill Hyderabad, India
\begin{itemize}
    \item Developed an AI-powered resume optimization platform using Flask, curl-cffi, and LaTeX generation tools.
    \item Implemented automated PDF conversion pipelines and local caching mechanisms.
\end{itemize}

\vspace{-4pt}
\section*{Projects}
\hrule \vspace{4pt}
\textbf{ATS Resume Builder Studio} \hfill 2024
\begin{itemize}
    \item Built a web app supporting custom LaTeX template management, localStorage persistence, and Perplexity AI optimization.
\end{itemize}

\vspace{-4pt}
\section*{Education}
\hrule \vspace{4pt}
\textbf{Bachelor of Technology in Computer Science} \hfill 2020 -- 2024\\
\textit{XYZ Institute of Technology}

\end{document}"""


def cleanup_old_files():
    current_time = datetime.now()
    files_to_remove = []

    for file_id, metadata in list(file_metadata.items()):
        if current_time - metadata['created_at'] > timedelta(seconds=CLEANUP_INTERVAL):
            files_to_remove.append(file_id)

    for file_id in files_to_remove:
        try:
            file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")
            if os.path.exists(file_path):
                os.remove(file_path)
            file_metadata.pop(file_id, None)
            print(f"Cleaned up file: {file_id}")
        except Exception as e:
            print(f"Error cleaning up file {file_id}: {e}")


def start_cleanup_scheduler():
    def cleanup_loop():
        while True:
            time.sleep(300)
            cleanup_old_files()

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()


# ========= AI + PDF Generation ========= #

def ask_perplexity(query: str):
    url = "https://www.perplexity.ai/rest/sse/perplexity_ask"

    payload = {
        "params": {
            "attachments": [],
            "language": "en-US",
            "timezone": "Asia/Kolkata",
            "search_focus": "writing",
            "sources": [],
            "frontend_uuid": "fae808a1-d386-4d43-85ff-cbdede546228",
            "mode": "writing",
            "model_preference": "gemini2flash",
            "query_source": "home",
            "dsl_query": query,
            "version": "2.18"
        },
        "query_str": query
    }

    cookie = os.getenv('PPlxcookie') or os.getenv('PPLXCOOKIE')
    if not cookie:
        return "Error: PPlxcookie environment variable is missing or not set in .env file."

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Content-Type': 'application/json',
        'Referer': 'https://www.perplexity.ai/',
        'Origin': 'https://www.perplexity.ai',
        'Cookie': cookie,
    }

    try:
        post_kwargs = {
            'headers': headers,
            'data': json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            'timeout': 120,
        }
        if HAS_CURL_CFFI:
            post_kwargs['impersonate'] = "chrome110"

        response = curl_requests.post(
            url,
            **post_kwargs
        )
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return f"Error from Perplexity API (HTTP status {response.status_code}). Please check if your cookie in .env has expired."

        final_answer = None

        for line in response.text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            try:
                data = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue

            # Perplexity SSE stream parsing
            if isinstance(data, dict):
                blocks = data.get("blocks", [])
                for block in blocks:
                    if isinstance(block, dict):
                        markdown = block.get("markdown_block")
                        if isinstance(markdown, dict) and markdown.get("answer"):
                            ans = markdown["answer"].strip()
                            if ans:
                                final_answer = ans
                        elif block.get("answer"):
                            final_answer = str(block.get("answer")).strip()
                        elif block.get("text"):
                            final_answer = str(block.get("text")).strip()

                if data.get("answer"):
                    final_answer = str(data.get("answer")).strip()
                elif data.get("text"):
                    final_answer = str(data.get("text")).strip()

        return final_answer or "Warning: No answer found in AI response."

    except Exception as e:
        return f"Error occurred: {str(e)}"


def sanitize_latex(latex: str) -> str:
    if not latex:
        return latex
    s = latex.strip()
    s = re.sub(r'^\s*```[\w-]*\s*$', '', s, flags=re.MULTILINE)
    s = s.replace('```', '')
    end_match = re.search(r'\\end{document}', s, flags=re.IGNORECASE)
    if end_match:
        s = s[:end_match.end()]
    return s.strip()


def extract_latex_code(text: str):
    if not text:
        return None
    m = re.search(r'```(?:latex|tex)\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        return sanitize_latex(m.group(1))
    m2 = re.search(r'```[\w-]*\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m2 and ('\\documentclass' in m2.group(1) or '\\begin{document}' in m2.group(1)):
        return sanitize_latex(m2.group(1))
    start = text.find('\\documentclass')
    if start != -1:
        end_match2 = re.search(r'\\end{document}', text[start:], re.IGNORECASE | re.DOTALL)
        if end_match2:
            end_index = start + end_match2.end()
            return sanitize_latex(text[start:end_index])
        return sanitize_latex(text[start:])
    return None


def convert_latex_to_pdf(latex_code: str):
    unique_id = str(uuid.uuid4())
    local_filename = f"{unique_id}.pdf"
    local_path = os.path.join(UPLOAD_FOLDER, local_filename)

    # 1. Primary: Fast MeTool / LaTeX Online Compiler Engine (Instant PDF Conversion)
    try:
        url = "https://latexonline.cc/compile"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Edg/153.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://metool.online/latex/convert/',
            'Origin': 'https://metool.online'
        }
        res = std_requests.get(url, params={"text": latex_code}, headers=headers, timeout=25)

        if res.status_code == 200 and len(res.content) > 500 and (res.content.startswith(b'%PDF') or 'pdf' in res.headers.get('content-type', '').lower()):
            with open(local_path, 'wb') as f:
                f.write(res.content)

            file_metadata[unique_id] = {
                'created_at': datetime.now(),
                'filename': local_filename,
                'original_url': url,
            }

            return {
                'status': 'success',
                'file_id': unique_id,
                'local_filename': local_filename,
                'download_url': f'/download/{unique_id}',
                'preview_url': f'/preview/{unique_id}',
                'cleanup_time': datetime.now() + timedelta(seconds=CLEANUP_INTERVAL),
            }
    except Exception as e:
        print(f"MeTool Primary LaTeX Compiler Warning: {e}. Switching to secondary fallback...")

    # 2. Secondary Fallback: TexViewer / Herokuapp compiler
    try:
        upload_url = f"https://texviewer.herokuapp.com/upload.php?uid={unique_id}"
        payload = {
            'texts': latex_code,
            'nonstopmode': '1',
            'title': 'Optimized Resume'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
            'Origin': 'https://texviewer.herokuapp.com',
            'Referer': 'https://texviewer.herokuapp.com/'
        }

        response = std_requests.post(upload_url, headers=headers, data=payload, timeout=20)
        if response.status_code == 200:
            status_res = check_pdf_status(unique_id)
            if isinstance(status_res, dict) and status_res.get('status') == 'success':
                return status_res
    except Exception as e:
        print(f"Fallback TeXViewer PDF compilation failed: {e}")

    return "PDF generation failed on all compilers."


def check_pdf_status(unique_id: str, max_attempts=30, delay=0.5):
    check_url = "https://texviewer.herokuapp.com/upload.php?action=checkcomplete"

    payload = {
        'uid': unique_id,
        'resultfile': f'temp/{unique_id}-result.txt'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0',
        'Origin': 'https://texviewer.herokuapp.com',
        'Referer': 'https://texviewer.herokuapp.com/'
    }

    for attempt in range(max_attempts):
        try:
            response = std_requests.post(check_url, headers=headers, data=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()

                if 'error' in result and result['error']:
                    return f"PDF generation error: {result['error']}"

                if 'pdfname' in result:
                    return download_and_save_pdf(result['pdfname'], unique_id)
                elif 'progress' in result:
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        continue
                    else:
                        return f"PDF generation timeout"

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
                continue
            else:
                return f"Error checking PDF status: {str(e)}"

    return "PDF generation timeout"


def download_and_save_pdf(pdf_url: str, unique_id: str):
    try:
        pdf_response = std_requests.get(pdf_url, timeout=30)

        if pdf_response.status_code == 200:
            local_filename = f"{unique_id}.pdf"
            local_path = os.path.join(UPLOAD_FOLDER, local_filename)

            with open(local_path, 'wb') as f:
                f.write(pdf_response.content)

            file_metadata[unique_id] = {
                'created_at': datetime.now(),
                'filename': local_filename,
                'original_url': pdf_url,
            }

            return {
                'status': 'success',
                'file_id': unique_id,
                'local_filename': local_filename,
                'download_url': f'/download/{unique_id}',
                'preview_url': f'/preview/{unique_id}',
                'cleanup_time': datetime.now() + timedelta(seconds=CLEANUP_INTERVAL),
            }
        else:
            return f"Failed to download PDF: HTTP {pdf_response.status_code}"

    except Exception as e:
        return f"Error downloading PDF: {str(e)}"


# ========= Routes ========= #

@app.route('/')
def index():
    return render_template('index.html', active_page='home')


@app.route('/templates')
def templates_page():
    return render_template('templates.html', active_page='templates')


@app.route('/saved')
def saved_page():
    return render_template('saved.html', active_page='saved')


@app.route('/help')
def help_page():
    return render_template('help.html', active_page='help')


SVG_FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#7c9cff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>"""


@app.route('/favicon.ico')
@app.route('/images/favicon.ico')
def favicon():
    return Response(SVG_FAVICON, mimetype='image/svg+xml')


@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404

        filename = file_metadata[file_id]['filename']
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File no longer exists'}), 404

        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/preview/<file_id>')
def preview_file(file_id):
    try:
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404

        filename = file_metadata[file_id]['filename']
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File no longer exists'}), 404

        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/optimize', methods=['POST'])
def optimize_resume():
    try:
        data = request.get_json(force=True, silent=True) or {}
        job_description = data.get('job_description', '').strip()
        custom_latex_template = data.get('latex_template', '').strip()

        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        base_latex = custom_latex_template if custom_latex_template else DEFAULT_LATEX_TEMPLATE

        prompt = f"""MY RESUME LATEX CODE:

{base_latex}

JOB DETAILS: {job_description}

TASK: Revise the provided LaTeX resume code based on the posted job description. Incorporate all relevant ATS keywords to maximize the ATS score and improve shortlisting potential. Rephrase only the Professional Summary, Experience Descriptions, Project Descriptions, and Technologies sections based on the job description with same length as original text. Ensure the final version fits on one page, no text should exceed to next page please. Return only the complete updated LaTeX code — no explanations or additional text."""

        answer = ask_perplexity(prompt)
        latex_code = extract_latex_code(answer)

        # Fallback to base template if AI response returned Warning/Error or no LaTeX block
        if not latex_code or not isinstance(latex_code, str) or len(latex_code) < 50:
            print(f"Notice: AI response didn't contain valid LaTeX ({answer}). Utilizing base template for compilation.")
            latex_code = base_latex

        latex_code = sanitize_latex(latex_code)
        pdf_response = convert_latex_to_pdf(latex_code)

        if isinstance(pdf_response, dict) and pdf_response.get('status') == 'success':
            return jsonify({
                'success': True,
                'latex_code': latex_code,
                'pdf_generated': True,
                'file_id': pdf_response['file_id'],
                'preview_url': pdf_response['preview_url'],
                'download_url': pdf_response['download_url'],
                'cleanup_time': pdf_response['cleanup_time'].isoformat(),
                'message': 'PDF generated successfully!'
            })
        else:
            return jsonify({
                'success': True,
                'latex_code': latex_code,
                'pdf_generated': False,
                'pdf_error': str(pdf_response),
                'message': 'LaTeX code generated, but PDF generation failed'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 ResumeStudio starting (Modular Pages with Templates & LocalStorage)…")
    print("📁 Generated files stored in:", UPLOAD_FOLDER)
    print("🗑️ Automatic cleanup enabled (files deleted after 1 hour)")
    app.run(debug=True, host='0.0.0.0', port=5005)
