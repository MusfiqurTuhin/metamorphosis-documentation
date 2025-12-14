import streamlit as st
import io
import json
import base64
import zlib
import requests
import re
from datetime import datetime
from fpdf import FPDF
from docx import Document
from PIL import Image
import os

def add_to_history(st_obj, feature, content, title="Untitled"):
    """Add item to history in session state."""
    if 'history' not in st_obj.session_state:
        st_obj.session_state.history = {}
    
    if feature not in st_obj.session_state.history:
        st_obj.session_state.history[feature] = []
    
    st_obj.session_state.history[feature].insert(0, {
        'title': title,
        'content': content,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Keep only last 10 items
    st_obj.session_state.history[feature] = st_obj.session_state.history[feature][:10]

def save_to_favorites(st_obj, content, feature, title):
    """Save item to favorites in session state."""
    if 'favorites' not in st_obj.session_state:
        st_obj.session_state.favorites = []
        
    st_obj.session_state.favorites.append({
        'feature': feature,
        'title': title,
        'content': content,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })

def extract_context_text(uploaded_file):
    """Extract text from uploaded file (txt, md, pdf, docx)."""
    if not uploaded_file:
        return None
    
    try:
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(".md"):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return None

def create_docx(text):
    """Create a DOCX file from text."""
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def create_pdf(text, image_bytes=None):
    """Create a PDF file from text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add image if provided
    if image_bytes:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=10, w=190)
            pdf.ln(10)
        except:
            pdf.cell(0, 10, "Image Error", ln=True)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # Add text
    # Encode/decode to handle latin-1 limitations of FPDF
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

def sanitize_mermaid_code(raw_text):
    """Extract and sanitize Mermaid code from LLM response."""
    match = re.search(r"```mermaid\s+(.*?)\s+```", raw_text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.replace("```mermaid", "").replace("```", "").strip()
    return code

def get_mermaid_img(code, format="png"):
    """Generate Mermaid image using mermaid.ink API."""
    state = {
        "code": code,
        "mermaid": {"theme": "default", "securityLevel": "loose"},
        "autoSync": True,
        "updateDiagram": True
    }
    json_str = json.dumps(state)
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed = compressor.compress(json_str.encode('utf-8')) + compressor.flush()
    base64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    
    url = f"https://mermaid.ink/img/pako:{base64_str}"
    if format == "svg":
        url = f"https://mermaid.ink/svg/pako:{base64_str}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

def convert_to_jpg(image_bytes):
    """Convert image bytes to JPG."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        rgb_im = image.convert('RGB')
        output = io.BytesIO()
        rgb_im.save(output, format='JPEG', quality=95)
        return output.getvalue()
    except:
        return None

def validate_mermaid_syntax(code):
    """
    Validate Mermaid syntax and return a list of specific errors/warnings.
    Based on common LLM failure modes.
    """
    errors = []
    
    # 1. Check for spaces after commas in style/classDefs (e.g. "fill:#f9f, stroke:#333")
    if re.search(r":[#a-zA-Z0-9]+,\s+", code):
        errors.append("❌ Style Error: Remove spaces after commas in style definitions (e.g., use 'fill:#fff,stroke:#000', NOT 'fill:#fff, stroke:#000').")
        
    # 2. Check for unclosed blocks
    # Keywords that require an 'end'
    block_keywords = ['subgraph', 'loop', 'opt', 'alt', 'par', 'rect', 'critical', 'break', 'parallel']
    
    total_opens = 0
    total_ends = len(re.findall(r'\\bend\\b', code, re.IGNORECASE))
    
    for kw in block_keywords:
        opens = len(re.findall(f'\\b{kw}\\b', code, re.IGNORECASE))
        total_opens += opens
        
    if total_opens != total_ends:
        errors.append(f"❌ Block Error: Found {total_opens} opening blocks but {total_ends} 'end' statements. Check if all subgraphs/loops are closed.")

    # 3. Gantt Layout Specifics
    if "gantt" in code.lower() and re.search(r'^\s*today\b', code, re.MULTILINE | re.IGNORECASE):
        errors.append("❌ Gantt Error: Found line starting with 'today'. Mermaid does NOT support defining 'today' manually using a date. REMOVE this line completely.")
    
    # Check for invalid comments (//)
    if "//" in code:
        errors.append("❌ Syntax Error: Mermaid uses '%%' for comments, not '//'. Replace '//' with '%%' or remove the comment.")

    # 4. Mindmap specific: Check for text after node definition on the same line
    if "mindmap" in code.lower():
         lines = code.split('\n')
         for i, line in enumerate(lines):
             # Match lines that look like:  ID(Text) AnyThingElse
             # simplified check: if line ends with ')' or ']' or ')', it should probably be the end of the line (ignoring whitespace)
             # Regex explanation:
             # ^\s*       : Start with whitespace
             # \S+        : Node ID (non-whitespace)
             # [\[\(\{]+  : Opening bracket
             # .*         : Content
             # [\]\)\}]+  : Closing bracket
             # \s+\S+     : Space then MORE text (This is the error)
             if re.search(r'^\s*\S+[\[\(\{]+.*[\]\)\}]+.*\s+\S+', line):
                 errors.append(f"❌ Mindmap Error (Line {i+1}): Found text after node definition. Ensure each node is on its own line with NO trailing text. (Content: '{line.strip()}')")
                 break # One is enough to trigger a fix

    return errors
