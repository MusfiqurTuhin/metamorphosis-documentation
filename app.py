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
    page_title="Metamorphosis Studio",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- THEME CONFIGURATION (Modern Gradient Design) ---
THEME = {
    "primary": "#6366F1",        # Indigo-500
    "primary_dark": "#4F46E5",   # Indigo-600
    "accent": "#06B6D4",         # Cyan-500
    "success": "#10B981",        # Emerald-500
    "bg": "#F8FAFC",             # Slate-50
    "surface": "#FFFFFF",        # White
    "text_main": "#0F172A",      # Slate-900
    "text_secondary": "#64748B", # Slate-500
    "border": "#E2E8F0",         # Slate-200
    "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700;800&family=Tiro+Bangla:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap');

    /* BASE RESET */
    .stApp {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    /* MAIN CONTAINER WITH GLASSMORPHISM */
    .block-container {{
        max-width: 1400px !important;
        padding-top: 2rem !important;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        box-shadow: {THEME['shadow_lg']};
        margin: 2rem auto !important;
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700;
        color: {THEME['text_main']};
        letter-spacing: -0.02em;
    }}
    
    p, li, label, .stMarkdown {{
        color: {THEME['text_secondary']};
        font-size: 0.95rem;
        line-height: 1.6;
    }}
    
    code {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
        background-color: #F1F5F9;
        padding: 2px 6px;
        border-radius: 4px;
    }}
    
    /* BANGLA TEXT */
    .bangla-text {{
        font-family: 'Tiro Bangla', serif !important;
        font-size: 0.9rem;
        line-height: 1.8;
        color: {THEME['text_secondary']};
    }}

    /* NAVIGATION (Modern Gradient Tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.75rem;
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['accent']} 100%);
        padding: 0.75rem 1rem;
        border-radius: 16px;
        box-shadow: {THEME['shadow']};
        margin-bottom: 2rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 3rem;
        padding: 0 1.75rem;
        background-color: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        font-weight: 600;
        font-size: 0.95rem;
        border-radius: 12px;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: white !important;
        color: {THEME['primary']} !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: rgba(255, 255, 255, 0.3);
        transform: translateY(-1px);
    }}

    /* CARDS */
    div[data-testid="stExpander"] {{
        border: 1px solid {THEME['border']};
        border-radius: 12px;
        background-color: {THEME['surface']};
        box-shadow: {THEME['shadow']};
        transition: all 0.3s ease;
    }}
    
    div[data-testid="stExpander"]:hover {{
        box-shadow: {THEME['shadow_lg']};
        transform: translateY(-2px);
    }}

    /* INPUTS */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        border: 2px solid {THEME['border']} !important;
        border-radius: 12px !important;
        padding: 0.85rem !important;
        background-color: {THEME['surface']} !important;
        color: {THEME['text_main']} !important;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }}
    
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    }}

    /* BUTTONS */
    div.stButton > button {{
        background: linear-gradient(135deg, {THEME['text_main']} 0%, #1e293b 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.75rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: {THEME['shadow']};
    }}
    
    div.stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: {THEME['shadow_lg']};
    }}
    
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['primary_dark']} 100%) !important;
    }}
    
    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, {THEME['primary_dark']} 0%, #4338CA 100%) !important;
    }}

    /* HEADER */
    .studio-header {{
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['accent']} 100%);
        border-radius: 20px;
        box-shadow: {THEME['shadow_lg']};
    }}
    
    .studio-logo {{
        font-size: 3.5rem;
        margin-bottom: 0.5rem;
        animation: float 3s ease-in-out infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .studio-title {{
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .studio-subtitle {{
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
        font-weight: 500;
    }}
    
    .studio-subtitle-bangla {{
        font-family: 'Tiro Bangla', serif !important;
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.85);
        margin-top: 0.25rem;
    }}
    
    /* INFO BOX */
    .info-box {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-left: 4px solid {THEME['primary']};
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }}
    
    /* SUCCESS MESSAGE */
    .success-box {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid {THEME['success']};
        padding: 1rem 1.25rem;
        border-radius: 8px;
        color: #065f46;
        font-weight: 500;
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

def sanitize_mermaid_code(raw_text):
    match = re.search(r"```mermaid\s+(.*?)\s+```", raw_text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.replace("```mermaid", "").replace("```", "").strip()
    return code

# --- HEADER ---
st.markdown(f"""
    <div class="studio-header">
        <div class="studio-logo">🦋</div>
        <h1 class="studio-title">Metamorphosis Studio</h1>
        <p class="studio-subtitle">Transform Ideas into Visual Intelligence</p>
        <p class="studio-subtitle-bangla">ধারণাকে দৃশ্যমান বুদ্ধিমত্তায় রূপান্তরিত করুন</p>
    </div>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
tabs = st.tabs(["🔑 API Key", "✨ Prompt Refiner", "📊 Diagrams", "📝 Documents"])

# --- TAB 1: API KEY MANAGEMENT ---
with tabs[0]:
    st.markdown("### 🔑 API Key Management")
    st.markdown('<p class="bangla-text">📌 <b>এপিআই কী ম্যানেজমেন্ট</b> - আপনার Google Gemini API Key দিয়ে সকল ফিচার আনলক করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা (How to Use)", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> নিচের বক্সে আপনার Gemini API Key লিখুন<br>
        <b>ধাপ ২:</b> "Save & Verify Key" বাটনে ক্লিক করুন<br>
        <b>ধাপ ৩:</b> সফলভাবে যাচাই হলে, অন্যান্য ট্যাবগুলো ব্যবহার করতে পারবেন
        </div>
        """, unsafe_allow_html=True)
    
    col_key1, col_key2 = st.columns([2, 1])
    with col_key1:
        api_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...", help="Enter your Google Gemini API key")
        if st.button("💾 Save & Verify Key", type="primary"):
            if not api_input:
                st.error("⚠️ Please enter a key.")
            else:
                try:
                    genai.configure(api_key=api_input)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content("Test")
                    st.session_state.api_key = api_input
                    st.markdown('<div class="success-box">✅ Key Verified & Saved Successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Invalid Key: {e}")
    
    if "api_key" in st.session_state:
        st.markdown(f'<div class="info-box">🔐 Active Key: <code>{st.session_state.api_key[:8]}...</code></div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ No active API Key. Please save a key to unlock features.")

# --- TAB 2: PROMPT REFINER ---
with tabs[1]:
    st.markdown("### ✨ Advanced Prompt Refiner")
    st.markdown('<p class="bangla-text">📌 <b>প্রম্পট রিফাইনার</b> - আপনার সাধারণ ধারণাকে শক্তিশালী প্রম্পটে পরিণত করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা (How to Use)", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Context নির্বাচন করুন (যেমন: Software Engineering, Legal)<br>
        <b>ধাপ ২:</b> Tone এবং Complexity সেট করুন<br>
        <b>ধাপ ৩:</b> আপনার মূল ধারণা লিখুন<br>
        <b>ধাপ ৪:</b> "Refine Prompt" বাটনে ক্লিক করুন<br>
        <b>ফলাফল:</b> AI একটি উন্নত, স্ট্রাকচার্ড প্রম্পট তৈরি করবে
        </div>
        """, unsafe_allow_html=True)
    
    col_ref1, col_ref2 = st.columns([1, 1])
    
    with col_ref1:
        st.markdown("#### ⚙️ Configuration")
        context = st.selectbox("📁 Context", [
            "General", "Software Engineering", "Data Science", "Legal", "Medical", 
            "Academic Writing", "Creative Writing", "Business Strategy", "Marketing", "HR"
        ])
        tone = st.select_slider("🎭 Tone", options=["Casual", "Neutral", "Professional", "Academic"])
        complexity = st.slider("🎯 Complexity Level", 1, 10, 7)
        
        raw_prompt = st.text_area("✍️ Draft Prompt", height=200, placeholder="Enter your rough idea here...")
        
        if st.button("🚀 Refine Prompt", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Please set your API Key first.")
            elif not raw_prompt:
                st.warning("⚠️ Please enter a draft prompt.")
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
                    with st.spinner("🔄 Refining your prompt..."):
                        res = model.generate_content(f"{sys_prompt}\nINPUT: {raw_prompt}")
                        st.session_state.refined_prompt = res.text.replace("**", "")
                        st.markdown('<div class="success-box">✅ Prompt refined successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_ref2:
        st.markdown("#### 📋 Refined Output")
        if "refined_prompt" in st.session_state:
            st.text_area("Result", value=st.session_state.refined_prompt, height=400)
        else:
            st.info("💡 Your refined prompt will appear here.")

# --- TAB 3: DIAGRAMS ---
with tabs[2]:
    st.markdown("### 📊 Diagram Generator")
    st.markdown('<p class="bangla-text">📌 <b>ডায়াগ্রাম জেনারেটর</b> - যেকোনো টেক্সট থেকে সুন্দর ডায়াগ্রাম তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা (How to Use)", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Diagram Type নির্বাচন করুন<br>
        <b>ধাপ ২:</b> যেকোনো ফরম্যাটে আপনার প্রয়োজনীয়তা লিখুন (এলোমেলো হলেও চলবে!)<br>
        <b>ধাপ ৩:</b> "Generate Diagram" বাটনে ক্লিক করুন<br>
        <b>ধাপ ৪:</b> ডায়াগ্রাম দেখুন এবং PNG/JPG/SVG/PDF ফরম্যাটে ডাউনলোড করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_diag1, col_diag2 = st.columns([1, 2])
    
    with col_diag1:
        d_type = st.selectbox("📐 Diagram Type", ["Flowchart", "Sequence", "Class", "State", "ER Diagram", "Gantt", "Mindmap", "Pie Chart"])
        d_reqs = st.text_area("📝 Requirements (Messy Text OK)", height=200, placeholder="Describe the diagram in any format you like...")
        
        if st.button("🎨 Generate Diagram", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
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
                    with st.spinner("🔄 Generating diagram..."):
                        res = model.generate_content(f"{sys_prompt}\nREQ: {d_reqs}")
                        code = sanitize_mermaid_code(res.text)
                        st.session_state.mermaid_code = code
                        st.markdown('<div class="success-box">✅ Diagram generated successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_diag2:
        if "mermaid_code" in st.session_state:
            st.markdown("#### 👁️ Preview")
            st.components.v1.html(
                f"""
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
                <div class="mermaid" style="display: flex; justify-content: center; padding: 2rem; background: white; border-radius: 12px;">
                    {st.session_state.mermaid_code}
                </div>
                """,
                height=500,
                scrolling=True
            )
            
            st.markdown("#### 💾 Downloads")
            dc1, dc2, dc3, dc4 = st.columns(4)
            
            png_bytes = get_mermaid_img(st.session_state.mermaid_code, "png")
            svg_bytes = get_mermaid_img(st.session_state.mermaid_code, "svg")
            
            with dc1:
                if png_bytes: st.download_button("📥 PNG", png_bytes, "diagram.png", "image/png", use_container_width=True)
            with dc2:
                if png_bytes:
                    jpg_bytes = convert_to_jpg(png_bytes)
                    if jpg_bytes: st.download_button("📥 JPG", jpg_bytes, "diagram.jpg", "image/jpeg", use_container_width=True)
            with dc3:
                if svg_bytes: st.download_button("📥 SVG", svg_bytes, "diagram.svg", "image/svg+xml", use_container_width=True)
            with dc4:
                if png_bytes:
                    pdf_bytes = create_pdf("Diagram", png_bytes)
                    st.download_button("📥 PDF", pdf_bytes, "diagram.pdf", "application/pdf", use_container_width=True)
            
            with st.expander("💻 View Source Code"):
                st.code(st.session_state.mermaid_code, language="mermaid")

# --- TAB 4: DOCUMENTS ---
with tabs[3]:
    st.markdown("### 📝 Professional Document Generator")
    st.markdown('<p class="bangla-text">📌 <b>ডকুমেন্ট জেনারেটর</b> - পেশাদার ডকুমেন্ট সেকেন্ডেই তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা (How to Use)", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Document Type নির্বাচন করুন (অথবা "Other" দিয়ে নিজের টাইপ লিখুন)<br>
        <b>ধাপ ২:</b> ডকুমেন্টের বিস্তারিত তথ্য লিখুন<br>
        <b>ধাপ ৩:</b> "Generate Document" বাটনে ক্লিক করুন<br>
        <b>ধাপ ৪:</b> MD/DOCX/PDF ফরম্যাটে ডাউনলোড করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_doc1, col_doc2 = st.columns([1, 2])
    
    with col_doc1:
        doc_type = st.selectbox("📄 Document Type", [
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
        
        custom_doc_type = ""
        if doc_type == "Other (Specify Below)":
            custom_doc_type = st.text_input("✏️ Specify Document Type", placeholder="e.g., Recipe Book, Travel Guide...")
            final_doc_type = custom_doc_type if custom_doc_type else "Custom Document"
        else:
            final_doc_type = doc_type
        
        doc_details = st.text_area("📋 Content Details", height=300, placeholder="Describe what the document should contain...")
        
        if st.button("📄 Generate Document", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not doc_details:
                st.warning("⚠️ Please enter content details.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = "ROLE: Technical Writer. OUTPUT: Professional Markdown. NO conversational filler."
                    with st.spinner("📝 Writing document..."):
                        res = model.generate_content(f"{sys_prompt}\nTYPE: {final_doc_type}\nDETAILS: {doc_details}")
                        st.session_state.doc_content = res.text
                        st.markdown('<div class="success-box">✅ Document generated successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_doc2:
        if "doc_content" in st.session_state:
            st.markdown("#### 👁️ Preview")
            st.markdown(st.session_state.doc_content)
            st.markdown("---")
            
            st.markdown("#### 💾 Downloads")
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("📥 Download MD", st.session_state.doc_content, "document.md", use_container_width=True)
            with dl2:
                docx = create_docx(st.session_state.doc_content)
                st.download_button("📥 Download DOCX", docx, "document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with dl3:
                pdf = create_pdf(st.session_state.doc_content)
                st.download_button("📥 Download PDF", pdf, "document.pdf", "application/pdf", use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 1rem;">
    <p>Made with ❤️ by Metamorphosis Studio | Powered by Google Gemini</p>
    <p class="bangla-text">মেটামরফসিস স্টুডিওতে আপনাকে স্বাগতম 🦋</p>
</div>
""", unsafe_allow_html=True)
