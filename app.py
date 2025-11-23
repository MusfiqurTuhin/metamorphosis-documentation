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

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- THEME CONFIGURATION (Deep Ocean / Neo-SaaS) ---
THEME = {
    "primary": "#4F46E5",       # Electric Indigo
    "primary_hover": "#4338CA", # Indigo-700
    "accent": "#0EA5E9",        # Sky-500
    "bg": "#F8FAFC",            # Cultured (Slate-50)
    "surface": "#FFFFFF",       # Pure White
    "text_main": "#0F172A",     # Slate-900
    "text_secondary": "#64748B",# Slate-500
    "border": "#E2E8F0",        # Slate-200
    "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "shadow_md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* BASE RESET */
    .stApp {{
        background-color: {THEME['bg']};
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: {THEME['text_main']};
    }}
    
    p, li, label, .stMarkdown {{
        color: {THEME['text_secondary']};
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    code {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
    }}

    /* CENTRALIZED LAYOUT CONTAINER */
    .block-container {{
        max-width: 1000px !important;
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
    }}

    /* NAVIGATION (PILL STYLE) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: {THEME['surface']};
        padding: 0.5rem;
        border-radius: 9999px; /* Pill shape */
        box-shadow: {THEME['shadow_sm']};
        border: 1px solid {THEME['border']};
        margin-bottom: 3rem;
        display: inline-flex;
        width: auto;
        margin-left: auto;
        margin-right: auto;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 2.5rem;
        padding: 0 1.5rem;
        border-radius: 9999px;
        background-color: transparent;
        border: none;
        color: {THEME['text_secondary']};
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {THEME['primary']} !important;
        color: white !important;
        box-shadow: {THEME['shadow_sm']};
    }}

    /* CARDS (NEO-SAAS) */
    .feature-card {{
        background-color: {THEME['surface']};
        border: 1px solid transparent;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: {THEME['shadow_md']};
        transition: all 0.3s ease;
        height: 100%;
    }}
    .feature-card:hover {{
        transform: translateY(-2px);
        box-shadow: {THEME['shadow_lg']};
        border-color: {THEME['border']};
    }}

    /* INPUTS (FOCUS GLOW) */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
        padding: 0.85rem !important;
        background-color: {THEME['surface']} !important;
        color: {THEME['text_main']} !important;
        box-shadow: {THEME['shadow_sm']} !important;
        transition: all 0.2s ease;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15) !important; /* Indigo Glow */
    }}

    /* BUTTONS (TACTILE) */
    div.stButton > button {{
        background: linear-gradient(180deg, {THEME['primary']} 0%, {THEME['primary_hover']} 100%) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.1), inset 0 1px 0 0 rgba(255,255,255,0.1) !important;
        transition: transform 0.1s ease !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
    }}
    div.stButton > button:active {{
        transform: translateY(0);
    }}

    /* HEADER */
    .app-header {{
        text-align: center;
        margin-bottom: 1rem;
    }}
    .logo {{
        font-size: 3rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['accent']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .app-title {{
        font-size: 2rem;
        font-weight: 700;
        color: {THEME['text_main']};
        margin: 0;
        letter-spacing: -0.03em;
    }}
    .app-subtitle {{
        font-size: 1rem;
        color: {THEME['text_secondary']};
        margin-top: 0.5rem;
    }}
    
    /* CHIPS / TAGS */
    .chip {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background-color: {THEME['bg']};
        border: 1px solid {THEME['border']};
        color: {THEME['text_secondary']};
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }}
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def generate_mermaid_link(mermaid_code):
    """Generates a link to open the current code in mermaid.live"""
    state = {
        "code": mermaid_code,
        "mermaid": {"theme": "default"},
        "autoSync": True,
        "updateDiagram": True
    }
    json_str = json.dumps(state)
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed = compressor.compress(json_str.encode('utf-8')) + compressor.flush()
    base64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://mermaid.live/edit#{base64_str}"

def get_mermaid_img(code, format="png"):
    """Fetches the diagram image from mermaid.ink using compressed encoding."""
    state = {
        "code": code,
        "mermaid": {"theme": "default"},
        "autoSync": True,
        "updateDiagram": True
    }
    json_str = json.dumps(state)
    # Use zlib compression (same as mermaid.live) to handle large diagrams
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed = compressor.compress(json_str.encode('utf-8')) + compressor.flush()
    base64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    
    url = f"https://mermaid.ink/img/pako:{base64_str}"
    if format == "svg":
        url = f"https://mermaid.ink/svg/pako:{base64_str}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Verify it's actually an image
            content_type = response.headers.get('Content-Type', '')
            if format == "png" and "image/png" not in content_type:
                return None
            if format == "svg" and "image/svg" not in content_type:
                return None
            return response.content
    except:
        return None
    return None

def create_pdf(text, image_bytes=None):
    """Creates a PDF with text and optional image."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add Image if provided
    if image_bytes:
        import tempfile
        import os
        
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            # Center image roughly
            # A4 width is 210mm. Margins are usually 10mm.
            # We use 190mm width.
            pdf.image(tmp_path, x=10, w=190)
            pdf.ln(10)
        except Exception as e:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, f"Error embedding image: {str(e)}", ln=True)
            pdf.set_text_color(0, 0, 0)
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # Add Text
    # FPDF doesn't handle markdown or utf-8 perfectly out of the box, 
    # so we do a basic latin-1 encode/replace to prevent crashes.
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

def create_docx(text):
    """Creates a DOCX file from text."""
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def validate_mermaid_code(code):
    """Strictly validates Mermaid code against common syntax errors."""
    lines = code.split('\n')
    for i, line in enumerate(lines):
        bad_id_match = re.search(r'^(\s*)([a-zA-Z0-9_]*[^a-zA-Z0-9_\s\[]+[a-zA-Z0-9_]*)\s*\[', line)
        if bad_id_match:
             return False, f"Line {i+1}: Node ID '{bad_id_match.group(2)}' contains invalid characters. Use alphanumeric and underscores only."
        label_match = re.search(r'\[(.*?)\]', line)
        if label_match:
            content = label_match.group(1)
            if not content.startswith('"') and not content.endswith('"'):
                if any(c in content for c in " ()/-"):
                    return False, f"Line {i+1}: Label '{content}' must be double-quoted. Example: `id[\"{content}\"]`"
    return True, "Valid"

def sanitize_mermaid_code(raw_text):
    """Extracts code block and attempts to fix common issues."""
    match = re.search(r"```mermaid\s+(.*?)\s+```", raw_text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.replace("```mermaid", "").replace("```", "").strip()
    return code

# --- HEADER ---
st.markdown(f"""
    <div class="app-header">
        <div class="logo">🦋</div>
        <h1 class="app-title">Metamorphosis Architect</h1>
        <p class="app-subtitle">Precision Tools for Digital Transformation</p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.markdown("### Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI features")
    if not api_key:
        st.warning("⚠️ API Key missing")
    st.markdown("---")
    st.caption("v5.1.0 (Enhanced Downloads)")

# --- TOP NAVIGATION ---
tab_home, tab_rewriter, tab_diagram, tab_docs = st.tabs([
    "Dashboard", 
    "Prompt Refiner", 
    "Diagrams", 
    "Documents"
])

# --- TAB: DASHBOARD ---
with tab_home:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="feature-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">✨</div>
                <h4>Prompt Refiner</h4>
                <p>Transform vague ideas into structured, engineer-grade prompts for any context.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="feature-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📊</div>
                <h4>Diagrams</h4>
                <p>Generate strict, error-free Mermaid.js diagrams. Visualizes flows and architectures.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="feature-card">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📝</div>
                <h4>Documents</h4>
                <p>Draft professional technical documentation, specs, and manuals in seconds.</p>
            </div>
        """, unsafe_allow_html=True)

# --- TAB: PROMPT REFINER ---
with tab_rewriter:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_rw_1, col_rw_2 = st.columns([1, 1])
    
    with col_rw_1:
        st.markdown("### Input")
        context_type = st.selectbox("Context", ["General", "Coding / Engineering", "Business / Strategy", "Creative Writing"], index=0)
        raw_prompt = st.text_area("Draft Idea", height=250, placeholder="Describe what you want to achieve...")
        
        if st.button("Refine Prompt", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key required.")
            elif not raw_prompt:
                st.warning("Please enter a draft.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    
                    system_prompt = """
                    ROLE: Expert Prompt Engineer.
                    GOAL: Rewrite the user's raw input into a structured, highly effective prompt for an LLM.
                    
                    INSTRUCTIONS:
                    1. Analyze the user's intent and selected context.
                    2. Add necessary structure (Context, Task, Constraints, Output Format).
                    3. Improve clarity and remove ambiguity.
                    4. Output ONLY the optimized prompt.
                    """
                    
                    with st.spinner("Refining..."):
                        prompt_input = f"{system_prompt}\n\nCONTEXT: {context_type}\nINPUT: {raw_prompt}"
                        response = model.generate_content(prompt_input)
                        st.session_state.rewritten_result = response.text
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_rw_2:
        st.markdown("### Result")
        if "rewritten_result" in st.session_state:
            st.text_area("Optimized Prompt", value=st.session_state.rewritten_result, height=335)
        else:
            st.info("Your refined prompt will appear here.")

# --- TAB: DIAGRAMS ---
with tab_diagram:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_d_input, col_d_preview = st.columns([1, 2])
    
    with col_d_input:
        st.markdown("### Configuration")
        diagram_type = st.selectbox("Type", ["Flowchart (TD)", "Sequence Diagram", "ER Diagram", "State Diagram", "Gantt Chart"])
        diagram_prompt = st.text_area("Requirements", height=200, placeholder="Paste your refined prompt here...")
        
        if st.button("Generate Diagram", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key required.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    system_instruction = f"""
                    ROLE: Senior Solutions Architect. GOAL: Generate valid Mermaid.js {diagram_type}.
                    RULES: 1. Alphanumeric IDs only (No spaces). 2. Double-quote all labels. 3. Output only code.
                    """
                    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
                    with st.spinner("Generating..."):
                        response = model.generate_content(f"REQUIREMENTS: {diagram_prompt}")
                        clean_code = sanitize_mermaid_code(response.text)
                        is_valid, msg = validate_mermaid_code(clean_code)
                        
                        st.session_state.generated_mermaid = clean_code
                        if not is_valid:
                            st.warning(f"⚠️ Syntax Warning: {msg}")
                        else:
                            st.success("Generated successfully.")
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_d_preview:
        st.markdown("### Preview")
        if "generated_mermaid" in st.session_state:
            st.components.v1.html(
                f"""
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
                <div class="mermaid" style="display: flex; justify-content: center;">
                    {st.session_state.generated_mermaid}
                </div>
                """,
                height=400,
                scrolling=True
            )
            
            # --- DOWNLOAD OPTIONS ---
            st.markdown("#### Downloads")
            d_col1, d_col2, d_col3 = st.columns(3)
            
            # Fetch Images
            png_data = get_mermaid_img(st.session_state.generated_mermaid, "png")
            svg_data = get_mermaid_img(st.session_state.generated_mermaid, "svg")
            
            with d_col1:
                if png_data:
                    st.download_button("Download PNG", png_data, "diagram.png", "image/png", use_container_width=True)
            with d_col2:
                if svg_data:
                    st.download_button("Download SVG", svg_data, "diagram.svg", "image/svg+xml", use_container_width=True)
            with d_col3:
                if png_data:
                    pdf_data = create_pdf("Diagram Export", png_data)
                    st.download_button("Download PDF", pdf_data, "diagram.pdf", "application/pdf", use_container_width=True)

            with st.expander("View Source Code"):
                st.code(st.session_state.generated_mermaid, language="mermaid")
            
            live_url = generate_mermaid_link(st.session_state.generated_mermaid)
            st.link_button("Open in Mermaid.live", live_url)

# --- TAB: DOCUMENTS ---
with tab_docs:
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### Document Generator")
    
    col_doc_1, col_doc_2 = st.columns([1, 2])
    
    with col_doc_1:
        doc_type = st.selectbox("Type", ["Business Requirement Doc (BRD)", "Technical Design Doc (TDD)", "API Specification"])
        doc_prompt = st.text_area("Details", height=200, placeholder="Describe the project...")
        
        if st.button("Generate Document", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key required.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    with st.spinner("Drafting..."):
                        response = model.generate_content(f"Write a professional {doc_type} for: {doc_prompt}. Use Markdown.")
                        st.session_state.generated_doc = response.text
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_doc_2:
        if "generated_doc" in st.session_state:
            st.markdown("#### Downloads")
            doc_col1, doc_col2, doc_col3 = st.columns(3)
            
            with doc_col1:
                st.download_button("Download MD", st.session_state.generated_doc, "document.md", use_container_width=True)
            
            with doc_col2:
                docx_data = create_docx(st.session_state.generated_doc)
                st.download_button("Download DOCX", docx_data, "document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            
            with doc_col3:
                pdf_doc_data = create_pdf(st.session_state.generated_doc)
                st.download_button("Download PDF", pdf_doc_data, "document.pdf", "application/pdf", use_container_width=True)

            st.markdown("---")
            st.markdown(st.session_state.generated_doc)
