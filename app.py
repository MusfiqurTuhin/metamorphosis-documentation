import streamlit as st
import google.generativeai as genai
import re
import json
import base64
import zlib
import requests
from fpdf import FPDF
from docx import Document
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Site A-Z",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- THEME CONFIGURATION (Orange / Black / White) ---
THEME = {
    "primary": "#FF5722",       # Deep Orange
    "primary_hover": "#E64A19", # Darker Orange
    "bg": "#FFFFFF",            # Pure White
    "surface": "#FAFAFA",       # Off-White
    "text_main": "#000000",     # Black
    "text_secondary": "#424242",# Dark Gray
    "border": "#E0E0E0",        # Light Gray
    "shadow": "0 2px 5px rgba(0,0,0,0.1)"
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* BASE RESET */
    .stApp {{
        background-color: {THEME['bg']};
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700;
        color: {THEME['text_main']};
        letter-spacing: -0.5px;
    }}
    
    p, li, label, .stMarkdown {{
        color: {THEME['text_secondary']};
        font-size: 1rem;
        line-height: 1.6;
    }}
    
    code {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem;
        background-color: #F5F5F5;
        padding: 2px 4px;
        border-radius: 4px;
    }}

    /* NAVIGATION (Orange Tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background-color: {THEME['surface']};
        padding: 0.5rem 1rem;
        border-radius: 8px;
        border: 1px solid {THEME['border']};
        margin-bottom: 2rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 3rem;
        padding: 0 1.5rem;
        background-color: transparent;
        border: none;
        color: {THEME['text_secondary']};
        font-weight: 600;
        font-size: 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {THEME['primary']} !important;
        color: white !important;
        box-shadow: {THEME['shadow']};
    }}

    /* CARDS & CONTAINERS */
    .block-container {{
        max-width: 1200px !important;
        padding-top: 2rem !important;
    }}
    
    div[data-testid="stExpander"] {{
        border: 1px solid {THEME['border']};
        border-radius: 8px;
        background-color: {THEME['surface']};
    }}

    /* INPUTS */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        border: 2px solid {THEME['border']} !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        background-color: white !important;
        color: {THEME['text_main']} !important;
        transition: border-color 0.2s;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: none !important;
    }}

    /* BUTTONS */
    div.stButton > button {{
        background-color: {THEME['text_main']} !important; /* Black Buttons */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: background-color 0.2s !important;
    }}
    div.stButton > button:hover {{
        background-color: {THEME['primary']} !important; /* Orange on Hover */
        color: white !important;
    }}
    
    /* PRIMARY BUTTON OVERRIDE */
    div.stButton > button[kind="primary"] {{
        background-color: {THEME['primary']} !important;
        color: white !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: {THEME['primary_hover']} !important;
    }}

    /* HEADER */
    .site-header {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid {THEME['border']};
    }}
    .site-title {{
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        color: {THEME['primary']};
    }}
    .site-subtitle {{
        font-size: 1.2rem;
        color: {THEME['text_main']};
        margin-left: 1rem;
        font-weight: 600;
    }}
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def get_mermaid_img(code, format="png"):
    """Fetches diagram from mermaid.ink with compression."""
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
    """Converts image bytes (PNG) to JPG using Pillow."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        rgb_im = image.convert('RGB')
        output = io.BytesIO()
        rgb_im.save(output, format='JPEG', quality=95)
        return output.getvalue()
    except:
        return None

def create_pdf(text, image_bytes=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    if image_bytes:
        import tempfile
        import os
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
    
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

def create_docx(text):
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def validate_mermaid_code(code):
    """Linter for Mermaid code."""
    errors = []
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if '[' in line and ']' in line:
            match = re.search(r'\[(.*?)\]', line)
            if match:
                content = match.group(1)
                if not (content.startswith('"') and content.endswith('"')):
                    if any(c in content for c in "()-"):
                        errors.append(f"Line {i+1}: Label '{content}' needs quotes.")
    if errors:
        return False, " | ".join(errors[:3])
    return True, "Valid"

def sanitize_mermaid_code(raw_text):
    match = re.search(r"```mermaid\s+(.*?)\s+```", raw_text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.replace("```mermaid", "").replace("```", "").strip()
    return code

# --- HEADER ---
st.markdown(f"""
    <div class="site-header">
        <span class="site-title">Site A-Z</span>
        <span class="site-subtitle">AI Workspace</span>
    </div>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
tabs = st.tabs(["🔑 API Key", "✨ Prompt Refiner", "📊 Diagrams", "📝 Documents"])

# --- TAB 1: API KEY MANAGEMENT ---
with tabs[0]:
    st.markdown("### 🔑 API Key Management")
    st.markdown("Enter your Google Gemini API Key to unlock the workspace.")
    
    col_key1, col_key2 = st.columns([2, 1])
    with col_key1:
        api_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if st.button("Save & Verify Key"):
            if not api_input:
                st.error("Please enter a key.")
            else:
                try:
                    genai.configure(api_key=api_input)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content("Test")
                    st.session_state.api_key = api_input
                    st.success("✅ Key Verified & Saved!")
                except Exception as e:
                    st.error(f"❌ Invalid Key: {e}")
    
    if "api_key" in st.session_state:
        st.info(f"Active Key: {st.session_state.api_key[:5]}... (Stored in Session)")
    else:
        st.warning("⚠️ No active API Key. Features will be locked.")

# --- TAB 2: PROMPT REFINER ---
with tabs[1]:
    st.markdown("### ✨ Advanced Prompt Refiner")
    
    col_ref1, col_ref2 = st.columns([1, 1])
    
    with col_ref1:
        st.markdown("#### Configuration")
        context = st.selectbox("Context", [
            "General", "Software Engineering", "Data Science", "Legal", "Medical", 
            "Academic Writing", "Creative Writing", "Business Strategy", "Marketing", "HR"
        ])
        tone = st.select_slider("Tone", options=["Casual", "Neutral", "Professional", "Academic"])
        complexity = st.slider("Complexity Level", 1, 10, 7)
        
        raw_prompt = st.text_area("Draft Prompt", height=200, placeholder="Enter your rough idea here...")
        
        if st.button("Refine Prompt", type="primary"):
            if "api_key" not in st.session_state:
                st.error("Please set your API Key first.")
            elif not raw_prompt:
                st.warning("Enter a draft prompt.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"""
                    ROLE: Expert Prompt Engineer.
                    GOAL: Refine the user's prompt for maximum LLM performance.
                    CONTEXT: {context}. TONE: {tone}. COMPLEXITY: {complexity}/10.
                    RULES:
                    1. Remove all markdown bolding (no **text**).
                    2. Structure with clear headers (Context, Task, Constraints).
                    3. Be precise and concise.
                    """
                    with st.spinner("Refining..."):
                        res = model.generate_content(f"{sys_prompt}\nINPUT: {raw_prompt}")
                        st.session_state.refined_prompt = res.text.replace("**", "") # Strip bolding
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_ref2:
        st.markdown("#### Refined Output")
        if "refined_prompt" in st.session_state:
            st.text_area("Result", value=st.session_state.refined_prompt, height=400)
        else:
            st.info("Output will appear here.")

# --- TAB 3: DIAGRAMS ---
with tabs[2]:
    st.markdown("### 📊 Diagram Generator")
    
    col_diag1, col_diag2 = st.columns([1, 2])
    
    with col_diag1:
        d_type = st.selectbox("Diagram Type", ["Flowchart", "Sequence", "Class", "State", "ER Diagram", "Gantt", "Mindmap", "Pie Chart"])
        d_reqs = st.text_area("Requirements (Messy Text OK)", height=200, placeholder="Describe the diagram in any format...")
        
        if st.button("Generate Diagram", type="primary"):
            if "api_key" not in st.session_state:
                st.error("Set API Key first.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"""
                    ROLE: Mermaid.js Expert. GOAL: Valid code for {d_type}.
                    RULES:
                    1. Quote ALL labels with spaces: id["Label Text"].
                    2. Escape parentheses in labels: "Text (Info)" -> "Text [Info]".
                    3. ER: Use `||--o{{` syntax.
                    4. Gantt: `YYYY-MM-DD`.
                    OUTPUT: Code block only.
                    """
                    with st.spinner("Generating..."):
                        res = model.generate_content(f"{sys_prompt}\nREQ: {d_reqs}")
                        code = sanitize_mermaid_code(res.text)
                        st.session_state.mermaid_code = code
                        st.success("✅ Diagram Generated!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_diag2:
        if "mermaid_code" in st.session_state:
            st.components.v1.html(
                f"""
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
                <div class="mermaid" style="display: flex; justify-content: center;">
                    {st.session_state.mermaid_code}
                </div>
                """,
                height=500,
                scrolling=True
            )
            
            # Downloads
            st.markdown("#### Downloads")
            dc1, dc2, dc3, dc4 = st.columns(4)
            
            png_bytes = get_mermaid_img(st.session_state.mermaid_code, "png")
            svg_bytes = get_mermaid_img(st.session_state.mermaid_code, "svg")
            
            with dc1:
                if png_bytes: st.download_button("PNG", png_bytes, "diag.png", "image/png", use_container_width=True)
            with dc2:
                if png_bytes:
                    jpg_bytes = convert_to_jpg(png_bytes)
                    if jpg_bytes: st.download_button("JPG", jpg_bytes, "diag.jpg", "image/jpeg", use_container_width=True)
            with dc3:
                if svg_bytes: st.download_button("SVG", svg_bytes, "diag.svg", "image/svg+xml", use_container_width=True)
            with dc4:
                if png_bytes:
                    pdf_bytes = create_pdf("Diagram", png_bytes)
                    st.download_button("PDF", pdf_bytes, "diag.pdf", "application/pdf", use_container_width=True)
            
            with st.expander("Source Code"):
                st.code(st.session_state.mermaid_code, language="mermaid")

# --- TAB 4: DOCUMENTS ---
with tabs[3]:
    st.markdown("### 📝 Professional Documents")
    
    col_doc1, col_doc2 = st.columns([1, 2])
    
    with col_doc1:
        doc_type = st.selectbox("Document Type", [
            "Business Requirements Document (BRD)",
            "Technical Design Document (TDD)",
            "API Specification",
            "User Manual",
            "Project Charter",
            "Standard Operating Procedure (SOP)",
            "Meeting Minutes",
            "Research Report",
            "Other (Specify Below)"
        ])
        
        # Show text input only if "Other" is selected
        custom_doc_type = ""
        if doc_type == "Other (Specify Below)":
            custom_doc_type = st.text_input("Specify Document Type", placeholder="e.g., Recipe Book, Travel Guide...")
            final_doc_type = custom_doc_type if custom_doc_type else "Custom Document"
        else:
            final_doc_type = doc_type
        
        doc_details = st.text_area("Content Details", height=300, placeholder="Describe what the document should contain...")
        
        if st.button("Generate Document", type="primary"):
            if "api_key" not in st.session_state:
                st.error("Set API Key first.")
            elif not doc_details:
                st.warning("Enter content details.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = "ROLE: Technical Writer. OUTPUT: Professional Markdown. NO conversational filler."
                    with st.spinner("Writing..."):
                        res = model.generate_content(f"{sys_prompt}\nTYPE: {final_doc_type}\nDETAILS: {doc_details}")
                        st.session_state.doc_content = res.text
                        st.success("✅ Document Generated!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_doc2:
        if "doc_content" in st.session_state:
            st.markdown("#### Preview")
            st.markdown(st.session_state.doc_content)
            st.markdown("---")
            
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("Download MD", st.session_state.doc_content, "doc.md", use_container_width=True)
            with dl2:
                docx = create_docx(st.session_state.doc_content)
                st.download_button("Download DOCX", docx, "doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with dl3:
                pdf = create_pdf(st.session_state.doc_content)
                st.download_button("Download PDF", pdf, "doc.pdf", "application/pdf", use_container_width=True)
