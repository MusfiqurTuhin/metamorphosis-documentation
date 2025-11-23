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
    "bg": "#F8FAFC",             #Slate-50
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

    .stApp {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    .block-container {{
        max-width: 1400px !important;
        padding-top: 2rem !important;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        box-shadow: {THEME['shadow_lg']};
        margin: 2rem auto !important;
    }}
    
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
    
    .bangla-text {{
        font-family: 'Tiro Bangla', serif !important;
        font-size: 0.9rem;
        line-height: 1.8;
        color: {THEME['text_secondary']};
    }}

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
    
    .info-box {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-left: 4px solid {THEME['primary']};
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
    }}
    
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

# --- NAVIGATION (10 TABS) ---
tabs = st.tabs([
    "🔑 API Key", 
    "✨ Prompt Refiner", 
    "📊 Diagrams", 
    "📝 Documents",
    "💻 Code Gen",
    "📚 Summarizer",
    "🌐 Translator",
    "✉️ Email Writer",
    "🔍 Analyzer",
    "📝 Quiz Maker"
])

# --- TAB 1: API KEY ---
with tabs[0]:
    st.markdown("### 🔑 API Key Management")
    st.markdown('<p class="bangla-text">📌 <b>এপিআই কী ম্যানেজমেন্ট</b> - আপনার Google Gemini API Key দিয়ে সকল ফিচার আনলক করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> নিচের বক্সে আপনার Gemini API Key লিখুন<br>
        <b>ধাপ ২:</b> "Save & Verify Key" বাটনে ক্লিক করুন<br>
        <b>ধাপ ৩:</b> সফলভাবে যাচাই হলে, অন্যান্য ট্যাবগুলো ব্যবহার করতে পারবেন
        </div>
        """, unsafe_allow_html=True)
    
    col_key1, col_key2 = st.columns([2, 1])
    with col_key1:
        api_input = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if st.button("💾 Save & Verify Key", type="primary"):
            if not api_input:
                st.error("⚠️ Please enter a key.")
            else:
                try:
                    genai.configure(api_key=api_input)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content("Test")
                    st.session_state.api_key = api_input
                    st.markdown('<div class="success-box">✅ Key Verified & Saved!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Invalid Key: {e}")
    
    if "api_key" in st.session_state:
        st.markdown(f'<div class="info-box">🔐 Active Key: <code>{st.session_state.api_key[:8]}...</code></div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ No active API Key. Please save a key.")

# --- TAB 2: PROMPT REFINER ---
with tabs[1]:
    st.markdown("### ✨ Advanced Prompt Refiner")
    st.markdown('<p class="bangla-text">📌 <b>প্রম্পট রিফাইনার</b> - আপনার সাধারণ ধারণাকে শক্তিশালী প্রম্পটে পরিণত করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Context নির্বাচন করুন<br>
        <b>ধাপ ২:</b> Tone এবং Complexity সেট করুন<br>
        <b>ধাপ ৩:</b> আপনার মূল ধারণা লিখুন<br>
        <b>ধাপ ৪:</b> "Refine Prompt" বাটনে ক্লিক করুন
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
        complexity = st.slider("🎯 Complexity", 1, 10, 7)
        
        raw_prompt = st.text_area("✍️ Draft Prompt", height=200, placeholder="Enter your idea...")
        
        if st.button("🚀 Refine Prompt", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not raw_prompt:
                st.warning("⚠️ Enter a draft.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"ROLE: Prompt Engineer. CONTEXT: {context}. TONE: {tone}. COMPLEXITY: {complexity}/10. Refine this prompt. No **bolding**."
                    with st.spinner("🔄 Refining..."):
                        res = model.generate_content(f"{sys_prompt}\nINPUT: {raw_prompt}")
                        st.session_state.refined_prompt = res.text.replace("**", "")
                        st.markdown('<div class="success-box">✅ Refined!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_ref2:
        st.markdown("#### 📋 Output")
        if "refined_prompt" in st.session_state:
            st.text_area("Result", value=st.session_state.refined_prompt, height=400)
        else:
            st.info("💡 Output will appear here.")

# --- TAB 3: DIAGRAMS ---
with tabs[2]:
    st.markdown("### 📊 Diagram Generator")
    st.markdown('<p class="bangla-text">📌 <b>ডায়াগ্রাম জেনারেটর</b> - যেকোনো টেক্সট থেকে সুন্দর ডায়াগ্রাম তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Diagram Type নির্বাচন করুন<br>
        <b>ধাপ ২:</b> প্রয়োজনীয়তা লিখুন<br>
        <b>ধাপ ৩:</b> "Generate" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        d_type = st.selectbox("📐 Type", ["Flowchart", "Sequence", "Class", "State", "ER Diagram", "Gantt", "Mindmap", "Pie"])
        d_reqs = st.text_area("📝 Requirements", height=200, placeholder="Describe...")
        
        if st.button("🎨 Generate", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Generate valid Mermaid code for {d_type}. Quote labels. Code block only."
                    with st.spinner("🔄 Generating..."):
                        res = model.generate_content(f"{sys_prompt}\nREQ: {d_reqs}")
                        st.session_state.mermaid_code = sanitize_mermaid_code(res.text)
                        st.markdown('<div class="success-box">✅ Generated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_d2:
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
                if png_bytes: st.download_button("PNG", png_bytes, "diagram.png", "image/png", use_container_width=True)
            with dc2:
                if png_bytes:
                    jpg_bytes = convert_to_jpg(png_bytes)
                    if jpg_bytes: st.download_button("JPG", jpg_bytes, "diagram.jpg", "image/jpeg", use_container_width=True)
            with dc3:
                if svg_bytes: st.download_button("SVG", svg_bytes, "diagram.svg", "image/svg+xml", use_container_width=True)
            with dc4:
                if png_bytes: st.download_button("PDF", create_pdf("Diagram", png_bytes), "diagram.pdf", "application/pdf", use_container_width=True)

# --- TAB 4: DOCUMENTS ---
with tabs[3]:
    st.markdown("### 📝 Document Generator")
    st.markdown('<p class="bangla-text">📌 <b>ডকুমেন্ট জেনারেটর</b> - পেশাদার ডকুমেন্ট তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Document Type নির্বাচন করুন<br>
        <b>ধাপ ২:</b> বিস্তারিত তথ্য লিখুন<br>
        <b>ধাপ ৩:</b> "Generate" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_doc1, col_doc2 = st.columns([1, 2])
    
    with col_doc1:
        doc_type = st.selectbox("📄 Type", [
            "BRD", "TDD", "API Spec", "User Manual", "Project Charter", 
            "SOP", "Meeting Minutes", "Research Report", "Other"
        ])
        
        if doc_type == "Other":
            doc_type = st.text_input("Specify", placeholder="e.g., Recipe")
        
        doc_details = st.text_area("📋 Details", height=300, placeholder="Describe content...")
        
        if st.button("📄 Generate", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not doc_details:
                st.warning("⚠️ Enter details.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    with st.spinner("📝 Writing..."):
                        res = model.generate_content(f"Write professional {doc_type}. Markdown format.\n{doc_details}")
                        st.session_state.doc_content = res.text
                        st.markdown('<div class="success-box">✅ Generated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_doc2:
        if "doc_content" in st.session_state:
            st.markdown("#### 👁️ Preview")
            st.markdown(st.session_state.doc_content)
            st.markdown("---")
            
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("MD", st.session_state.doc_content, "doc.md", use_container_width=True)
            with dl2:
                st.download_button("DOCX", create_docx(st.session_state.doc_content), "doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with dl3:
                st.download_button("PDF", create_pdf(st.session_state.doc_content), "doc.pdf", "application/pdf", use_container_width=True)

# --- TAB 5: CODE GENERATOR ---
with tabs[4]:
    st.markdown("### 💻 Code Generator")
    st.markdown('<p class="bangla-text">📌 <b>কোড জেনারেটর</b> - যেকোনো প্রোগ্রামিং ভাষায় কোড তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Programming Language নির্বাচন করুন<br>
        <b>ধাপ ২:</b> Code Style এবং Documentation সেট করুন<br>
        <b>ধাপ ৩:</b> আপনার প্রয়োজনীয়তা লিখুন<br>
        <b>ধাপ ৪:</b> "Generate Code" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_code1, col_code2 = st.columns([1, 2])
    
    with col_code1:
        language = st.selectbox("🔧 Language", ["Python", "JavaScript", "Java", "C++", "TypeScript", "Go", "Rust", "PHP"])
        style = st.selectbox("🎨 Style", ["OOP", "Functional", "Procedural"])
        with_docs = st.checkbox("📄 Include Documentation", value=True)
        with_types = st.checkbox("🏷️ Include Type Hints", value=True)
        
        code_req = st.text_area("💡 Requirements", height=200, placeholder="Describe what the code should do...")
        
        if st.button("⚡ Generate Code", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not code_req:
                st.warning("⚠️ Enter requirements.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"""Generate production-ready {language} code.
Style: {style}
Documentation: {'Yes' if with_docs else 'No'}
Type Hints: {'Yes' if with_types else 'No'}
Return ONLY the code with comments."""
                    with st.spinner("⚙️ Generating code..."):
                        res = model.generate_content(f"{sys_prompt}\nREQ: {code_req}")
                        st.session_state.generated_code = res.text
                        st.markdown('<div class="success-box">✅ Code generated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_code2:
        st.markdown("#### 💻 Generated Code")
        if "generated_code" in st.session_state:
            st.code(st.session_state.generated_code, language=language.lower())
            st.download_button("📥 Download Code", st.session_state.generated_code, f"code.{language.lower()[:2]}", use_container_width=True)
        else:
            st.info("💡 Code will appear here.")

# --- TAB 6: SUMMARIZER ---
with tabs[5]:
    st.markdown("### 📚 Text Summarizer")
    st.markdown('<p class="bangla-text">📌 <b>টেক্সট সামারাইজার</b> - দীর্ঘ ডকুমেন্ট সংক্ষিপ্ত করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Summary Length নির্বাচন করুন<br>
        <b>ধাপ ২:</b> Format নির্বাচন করুন<br>
        <b>ধাপ ৩:</b> আপনার টেক্সট পেস্ট করুন<br>
        <b>ধাপ ৪:</b> "Summarize" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_sum1, col_sum2 = st.columns([1, 1])
    
    with col_sum1:
        length = st.select_slider("📏 Length", options=["Short", "Medium", "Long"])
        format_type = st.selectbox("📋 Format", ["Bullet Points", "Paragraph", "Key Points Only"])
        
        text_to_summarize = st.text_area("📝 Text to Summarize", height=300, placeholder="Paste your long text here...")
        
        if st.button("📊 Summarize", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not text_to_summarize:
                st.warning("⚠️ Enter text.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Summarize this text. Length: {length}. Format: {format_type}."
                    with st.spinner("📖 Summarizing..."):
                        res = model.generate_content(f"{sys_prompt}\n{text_to_summarize}")
                        st.session_state.summary = res.text
                        st.markdown('<div class="success-box">✅ Summarized!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_sum2:
        st.markdown("#### 📄 Summary")
        if "summary" in st.session_state:
            st.markdown(st.session_state.summary)
            st.download_button("📥 Download Summary", st.session_state.summary, "summary.txt", use_container_width=True)
        else:
            st.info("💡 Summary will appear here.")

# --- TAB 7: TRANSLATOR ---
with tabs[6]:
    st.markdown("### 🌐 Translation Tool")
    st.markdown('<p class="bangla-text">📌 <b>অনুবাদ টুল</b> - ৫০+ ভাষায় অনুবাদ করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Target Language নির্বাচন করুন<br>
        <b>ধাপ ২:</b> আপনার টেক্সট লিখুন<br>
        <b>ধাপ ৩:</b> "Translate" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_trans1, col_trans2 = st.columns([1, 1])
    
    with col_trans1:
        target_lang = st.selectbox("🌍 Target Language", [
            "Spanish", "French", "German", "Chinese", "Japanese", "Korean", 
            "Arabic", "Hindi", "Bengali", "Portuguese", "Russian", "Italian"
        ])
        
        text_to_translate = st.text_area("📝 Text to Translate", height=300, placeholder="Enter text...")
        
        if st.button("🌐 Translate", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not text_to_translate:
                st.warning("⚠️ Enter text.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Translate to {target_lang}. Preserve formatting. Output only translation."
                    with st.spinner("🔄 Translating..."):
                        res = model.generate_content(f"{sys_prompt}\n{text_to_translate}")
                        st.session_state.translation = res.text
                        st.markdown('<div class="success-box">✅ Translated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_trans2:
        st.markdown(f"#### 🎯 Translation ({target_lang})")
        if "translation" in st.session_state:
            st.text_area("Result", value=st.session_state.translation, height=350)
            st.download_button("📥 Download", st.session_state.translation, f"translation_{target_lang.lower()}.txt", use_container_width=True)
        else:
            st.info("💡 Translation will appear here.")

# --- TAB 8: EMAIL WRITER ---
with tabs[7]:
    st.markdown("### ✉️ Email Draft Generator")
    st.markdown('<p class="bangla-text">📌 <b>ইমেইল জেনারেটর</b> - পেশাদার ইমেইল তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Email Type নির্বাচন করুন<br>
        <b>ধাপ ২:</b> Tone এবং Length সেট করুন<br>
        <b>ধাপ ৩:</b> Key Points লিখুন<br>
        <b>ধাপ ৪:</b> "Generate Email" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_email1, col_email2 = st.columns([1, 1])
    
    with col_email1:
        email_type = st.selectbox("📧 Email Type", ["Formal Business", "Casual", "Marketing", "Follow-up", "Thank You", "Apology", "Request"])
        email_tone = st.select_slider("🎭 Tone", options=["Very Formal", "Formal", "Neutral", "Friendly", "Casual"])
        email_length = st.select_slider("📏 Length", options=["Brief", "Standard", "Detailed"])
        
        email_context = st.text_area("💡 Key Points", height=200, placeholder="What should the email discuss?")
        
        if st.button("✉️ Generate Email", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not email_context:
                st.warning("⚠️ Enter key points.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Write {email_type} email. Tone: {email_tone}. Length: {email_length}. Include subject line."
                    with st.spinner("✍️ Writing email..."):
                        res = model.generate_content(f"{sys_prompt}\nContext: {email_context}")
                        st.session_state.email_draft = res.text
                        st.markdown('<div class="success-box">✅ Email generated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_email2:
        st.markdown("#### 📨 Email Draft")
        if "email_draft" in st.session_state:
            st.text_area("Draft", value=st.session_state.email_draft, height=450)
            st.download_button("📥 Download", st.session_state.email_draft, "email_draft.txt", use_container_width=True)
        else:
            st.info("💡 Email will appear here.")

# --- TAB 9: CONTENT ANALYZER ---
with tabs[8]:
    st.markdown("### 🔍 Content Analyzer")
    st.markdown('<p class="bangla-text">📌 <b>কন্টেন্ট বিশ্লেষক</b> - লেখার মান যাচাই করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> আপনার টেক্সট পেস্ট করুন<br>
        <b>ধাপ ২:</b> "Analyze" বাটনে ক্লিক করুন<br>
        <b>ফলাফল:</b> Readability, Sentiment, Keywords পাবেন
        </div>
        """, unsafe_allow_html=True)
    
    col_analyze1, col_analyze2 = st.columns([1, 1])
    
    with col_analyze1:
        text_to_analyze = st.text_area("📝 Text to Analyze", height=400, placeholder="Paste your content here...")
        
        if st.button("🔍 Analyze", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not text_to_analyze:
                st.warning("⚠️ Enter text.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = """Analyze this content:
1. Readability Score (1-10)
2. Sentiment (Positive/Negative/Neutral with %)
3. Top 5 Keywords
4. Word/Sentence Count
5. SEO Suggestions
Format as structured report."""
                    with st.spinner("🔍 Analyzing..."):
                        res = model.generate_content(f"{sys_prompt}\n{text_to_analyze}")
                        st.session_state.analysis = res.text
                        st.markdown('<div class="success-box">✅ Analysis complete!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_analyze2:
        st.markdown("#### 📊 Analysis Report")
        if "analysis" in st.session_state:
            st.markdown(st.session_state.analysis)
            st.download_button("📥 Download Report", st.session_state.analysis, "analysis.txt", use_container_width=True)
        else:
            st.info("💡 Analysis will appear here.")

# --- TAB 10: QUIZ GENERATOR ---
with tabs[9]:
    st.markdown("### 📝 Quiz Generator")
    st.markdown('<p class="bangla-text">📌 <b>কুইজ জেনারেটর</b> - যেকোনো বিষয়ে কুইজ তৈরি করুন</p>', unsafe_allow_html=True)
    
    with st.expander("📖 ব্যবহার নির্দেশিকা", expanded=False):
        st.markdown("""
        <div class="bangla-text">
        <b>ধাপ ১:</b> Question Type এবং সংখ্যা নির্বাচন করুন<br>
        <b>ধাপ ২:</b> Difficulty Level সেট করুন<br>
        <b>ধাপ ৩:</b> Topic/Content লিখুন<br>
        <b>ধাপ ৪:</b> "Generate Quiz" বাটনে ক্লিক করুন
        </div>
        """, unsafe_allow_html=True)
    
    col_quiz1, col_quiz2 = st.columns([1, 2])
    
    with col_quiz1:
        question_type = st.selectbox("❓ Question Type", ["Multiple Choice", "True/False", "Short Answer", "Mixed"])
        num_questions = st.slider("📊 Number of Questions", 5, 20, 10)
        difficulty = st.select_slider("🎯 Difficulty", options=["Easy", "Medium", "Hard"])
        include_answers = st.checkbox("✅ Include Answer Key", value=True)
        
        quiz_topic = st.text_area("📚 Topic/Content", height=250, placeholder="Enter the topic or paste content to create quiz from...")
        
        if st.button("🎯 Generate Quiz", type="primary"):
            if "api_key" not in st.session_state:
                st.error("⚠️ Set API Key first.")
            elif not quiz_topic:
                st.warning("⚠️ Enter topic/content.")
            else:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"""Create {num_questions} {question_type} questions.
Difficulty: {difficulty}
Answer key: {'Include at end' if include_answers else 'No'}
Format clearly with numbering."""
                    with st.spinner("📝 Creating quiz..."):
                        res = model.generate_content(f"{sys_prompt}\nTOPIC/CONTENT: {quiz_topic}")
                        st.session_state.quiz = res.text
                        st.markdown('<div class="success-box">✅ Quiz generated!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col_quiz2:
        st.markdown("#### 📋 Generated Quiz")
        if "quiz" in st.session_state:
            st.markdown(st.session_state.quiz)
            st.markdown("---")
            
            qd1, qd2, qd3 = st.columns(3)
            with qd1:
                st.download_button("📥 TXT", st.session_state.quiz, "quiz.txt", use_container_width=True)
            with qd2:
                st.download_button("📥 DOCX", create_docx(st.session_state.quiz), "quiz.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            with qd3:
                st.download_button("📥 PDF", create_pdf(st.session_state.quiz), "quiz.pdf", "application/pdf", use_container_width=True)
        else:
            st.info("💡 Quiz will appear here.")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 1rem;">
    <p>Made with ❤️ by Metamorphosis Studio | Powered by Google Gemini</p>
    <p class="bangla-text">মেটামরফসিস স্টুডিওতে আপনাকে স্বাগতম 🦋</p>
</div>
""", unsafe_allow_html=True)
