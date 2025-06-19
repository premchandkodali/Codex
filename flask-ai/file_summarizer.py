import os
import time
from fpdf import FPDF
from dotenv import load_dotenv
from github_parser import GitHubParser
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment or .env file.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def gemini_flash_summarize(text, file_path):
    prompt = (
        f"You are a helpful AI code assistant. Summarize the following file for a developer. "
        f"Explain what the file does, its main features, and any important implementation details. "
        f"File: {file_path}\n\n"
        f"--- FILE CONTENT START ---\n"
        f"{text[:12000]}\n"
        f"--- FILE CONTENT END ---"
    )
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            summary = response.text.strip()
            return summary
        except Exception as e:
            err_msg = str(e)
            if '429' in err_msg or "quota" in err_msg.lower() or "rate limit" in err_msg.lower():
                wait_time = 60  # Wait 60 seconds between retries
                print(f"Rate limit hit while summarizing {file_path}, waiting {wait_time} seconds before retrying... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            print(f"Error summarizing {file_path}: {e}")
            return text[:300]
    print(f"Failed to summarize {file_path} after {max_retries} attempts due to rate limits.")
    return text[:300]

def summarize_repo_as_string(repo_url):
    parser = GitHubParser(repo_url)
    repo_data = parser.get_repo_data()
    files = repo_data['files']

    # Filter files to only important types
    allowed_exts = ('.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.md')
    filtered_files = {
        path: info for path, info in files.items()
        if path.endswith(allowed_exts)
    }

    summaries = []
    total = len(filtered_files)

    for i, (file_path, info) in enumerate(filtered_files.items(), 1):
        content = info.get('content', '')
        if not content.strip():
            continue

        print(f"[{i}/{total}] Summarizing: {file_path} ...")
        summary = None

        # Retry if rate limit hit
        for attempt in range(2):
            try:
                summary = gemini_flash_summarize(content, file_path)
                break
            except Exception as e:
                if "rate limit" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
                    wait = 60 * (attempt + 1)
                    print(f"Rate limit hit. Retrying in {wait} sec... (Attempt {attempt+1}/2)")
                    time.sleep(wait)
                else:
                    print(f"Error: {e}")
                    break

        if summary:
            summaries.append(f"## {file_path}\n\n{summary}\n\n---\n")
        else:
            print(f"Skipped {file_path} due to repeated errors.")

        time.sleep(5)  # Be gentle to avoid quota exhaustion

    output = "# File-to-File Summaries \n\n" + "\n".join(summaries)
    return output

# The create_pdf_from_summary function from your provided code remains unchanged.

def create_pdf_from_summary(summary_content, out_name="File-to-File Summaries.pdf"):
    from fpdf import FPDF
    import re
    from datetime import datetime

    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_margins(20, 25, 20)  # Better margins
            
        def header(self):
            # Skip header on first page for cleaner look
            if self.page_no() == 1:
                return
            
            # Subtle header with line
            self.set_draw_color(150, 150, 150)
            self.set_line_width(0.3)
            self.line(20, 20, 190, 20)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, 'File-to-File Summaries', 0, 0, 'L')
            self.cell(0, 8, f'Page {self.page_no()}', 0, 1, 'R')
            self.ln(3)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f'Generated on {datetime.now().strftime("%B %d, %Y")}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Track if we're in the first section for title page styling
    first_title = True
    
    for line in summary_content.split('\n'):
        # Clean line but preserve some formatting indicators
        original_line = line.strip()
        cleaned_line = re.sub(r'[#$%*_]+', '', line.strip())
        
        if not cleaned_line:
            pdf.ln(2)
            continue

        # Main title - make it look like a document title
        if original_line.startswith('# '):
            if first_title:
                pdf.ln(20)  # Extra space at top
                pdf.set_font("Arial", 'B', 24)
                pdf.set_text_color(40, 40, 40)
                pdf.cell(0, 15, cleaned_line.replace('#', '').strip(), ln=True, align='C')
                pdf.ln(8)
                
                # Add a decorative line under main title
                pdf.set_draw_color(100, 100, 100)
                pdf.set_line_width(1)
                y = pdf.get_y()
                pdf.line(60, y, 150, y)
                pdf.ln(15)
                first_title = False
            else:
                pdf.set_font("Arial", 'B', 18)
                pdf.set_text_color(60, 60, 60)
                pdf.cell(0, 12, cleaned_line.replace('#', '').strip(), ln=True, align='L')
                pdf.ln(6)
                
        # Section headers - make them stand out more
        elif original_line.startswith('## '):
            # Add background rectangle for file names
            file_name = cleaned_line.replace('##', '').strip()
            
            # Check if we need a new page for better layout
            if pdf.get_y() > 250:
                pdf.add_page()
            
            pdf.ln(8)  # Space before section
            
            # Background rectangle
            pdf.set_fill_color(248, 248, 248)
            pdf.set_draw_color(200, 200, 200)
            current_y = pdf.get_y()
            pdf.rect(15, current_y, 180, 10, 'FD')
            
            # File name text
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(50, 50, 50)
            pdf.set_xy(18, current_y + 2)
            pdf.cell(0, 6, file_name, 0, 1, 'L')
            pdf.ln(4)
            
        # Divider - make it more subtle
        elif original_line.startswith('---'):
            pdf.ln(4)
            y = pdf.get_y()
            pdf.set_draw_color(220, 220, 220)
            pdf.set_line_width(0.5)
            pdf.line(20, y, 190, y)
            pdf.ln(6)
            
        # Normal text - improve formatting with special section handling
        else:
            if cleaned_line:
                # Clean up markdown-style formatting but preserve some structure
                cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_line)  # Bold
                cleaned_line = re.sub(r'\*(.*?)\*', r'\1', cleaned_line)      # Italic
                cleaned_line = re.sub(r'`(.*?)`', r'\1', cleaned_line)        # Code
                
                # Check for special sections (Main Features, Implementation Details, etc.)
                if any(keyword in cleaned_line for keyword in ['Main Features:', 'Implementation Details:', 'Key Features:', 'Features:', 'Details:', 'Overview:', 'Summary:']):
                    pdf.ln(3)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.set_text_color(40, 40, 40)
                    pdf.cell(0, 8, cleaned_line, 0, 1, 'L')
                    pdf.ln(2)
                    
                # Handle bullet points and lists
                elif cleaned_line.startswith('- ') or cleaned_line.startswith('• '):
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(70, 70, 70)
                    # Add bullet symbol and indent
                    bullet_text = '• ' + cleaned_line[2:].strip()
                    pdf.set_x(25)  # Indent bullet points
                    pdf.multi_cell(0, 6, bullet_text, 0, 'L')
                    pdf.ln(1)
                    
                elif re.match(r'^\d+\.', cleaned_line):
                    # Numbered lists
                    pdf.set_font("Arial", '', 10)
                    pdf.set_text_color(70, 70, 70)
                    pdf.set_x(25)  # Indent numbered lists
                    pdf.multi_cell(0, 6, cleaned_line, 0, 'L')
                    pdf.ln(1)
                    
                # Handle lines that look like sub-headings (contain colons)
                elif ':' in cleaned_line and len(cleaned_line) < 100:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_text_color(50, 50, 50)
                    pdf.multi_cell(0, 6, cleaned_line, 0, 'L')
                    pdf.ln(2)
                    
                else:
                    # Regular paragraphs with justification
                    pdf.set_font("Arial", '', 11)
                    pdf.set_text_color(60, 60, 60)
                    try:
                        pdf.multi_cell(0, 6, cleaned_line, 0, 'J')
                    except TypeError:
                        pdf.multi_cell(0, 6, cleaned_line, 0, 'L')
                    pdf.ln(2)

    pdf.output(out_name)
    print(f"Enhanced PDF created: {out_name}")
    print(f"Total pages: {pdf.page_no()}")