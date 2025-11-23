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
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Studio - Pro",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for history and favorites
if 'history' not in st.session_state:
    st.session_state.history = {}
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {
        'theme': 'gradient',
        'font_size': 'medium',
        'show_advanced': False
    }

# --- THEME CONFIGURATION ---
THEME = {
    "primary": "#6366F1",
    "primary_dark": "#4F46E5",
    "accent": "#06B6D4",
    "success": "#10B981",
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "text_main": "#0F172A",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    "shadow_lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
}

# --- TEMPLATES ---
PROMPT_TEMPLATES = {
    "Code Review": "Review this code for: 1) Best practices 2) Security issues 3) Performance optimizations 4) Potential bugs",
    "Blog Post": "Write a blog post about [TOPIC]. Target audience: [AUDIENCE]. Tone: [TONE]. Include: Introduction, 3-5 main points, conclusion.",
    "Email Template": "Write a professional email for [PURPOSE]. Recipient: [WHO]. Key points: [POINTS]",
    "Documentation": "Create technical documentation for [FEATURE]. Include: Overview, Usage, Examples, API reference",
    "Marketing Copy": "Create marketing copy for [PRODUCT]. Focus on: Benefits, unique value, call-to-action"
}

DIAGRAM_TEMPLATES = {
    "User Flow": "sequenceDiagram\n    User->>System: Action\n    System->>Database: Query\n    Database-->>System: Result\n    System-->>User: Response",
    "ER Basic": "erDiagram\n    CUSTOMER ||--o{ ORDER : places\n    ORDER ||--|{ LINE-ITEM : contains",
    "Flowchart": "flowchart TD\n    Start([Start]) --> Decision{Decision?}\n    Decision -->|Yes| Process[Process]\n    Decision -->|No| End([End])",
    "Mindmap": "mindmap\n  root((Central Idea))\n    Branch1\n      Subtopic1\n      Subtopic2\n    Branch2"
}

EMAIL_TEMPLATES = {
    "Meeting Request": "Subject: Meeting Request - [TOPIC]\n\nHi [NAME],\n\nI would like to schedule a meeting to discuss [TOPIC].\n\nAvailable times:\n- [TIME1]\n- [TIME 2]\n\nBest regards",
    "Follow-up": "Subject: Following up on [TOPIC]\n\nHi [NAME],\n\nI wanted to follow up on our conversation about [TOPIC].\n\n[DETAILS]\n\nLooking forward to your response.",
    "Introduction": "Subject: Introduction - [YOUR NAME]\n\nHi [NAME],\n\nMy name is [YOUR NAME] and I'm reaching out regarding [PURPOSE].\n\n[BRIEF INTRO]\n\nThank you for your time."
}

CODE_FRAMEWORKS = {
    "Python": ["Django", "Flask", "FastAPI", "Streamlit", "None"],
    "JavaScript": ["React", "Vue", "Angular", "Express", "Next.js", "None"],
    "Java": ["Spring Boot", "Jakarta EE", "None"],
    "TypeScript": ["React", "Angular", "Next.js", "NestJS", "None"]
}

# --- HELPER FUNCTIONS ---

def add_to_history(feature, content, title="Untitled"):
    """Add item to history"""
    if feature not in st.session_state.history:
        st.session_state.history[feature] = []
    
    st.session_state.history[feature].insert(0, {
        'title': title,
        'content': content,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    # Keep only last 10 items
    st.session_state.history[feature] = st.session_state.history[feature][:10]

def save_to_favorites(content, feature, title):
    """Save item to favorites"""
    st.session_state.favorites.append({
        'feature': feature,
        'title': title,
        'content': content,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    })

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

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700;800&family=Tiro+Bangla:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }}
    
    .block-container {{
        max-width: 1600px !important;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        box-shadow: {THEME['shadow_lg']};
        margin: 2rem auto !important;
    }}
    
    h1, h2, h3, h4 {{
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700;
    }}
    
    .bangla-text {{
        font-family: 'Tiro Bangla', serif !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.75rem;
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['accent']} 100%);
        padding: 0.75rem;
        border-radius: 16px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: white !important;
        color: {THEME['primary']} !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['primary_dark']} 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.75rem !important;
        font-weight: 600 !important;
    }}
    
    .success-box {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid {THEME['success']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # User Preferences
    with st.expander("🎨 Preferences"):
        font_size = st.select_slider("Font Size", ["Small", "Medium", "Large"], value="Medium")
        show_advanced = st.checkbox("Show Advanced Options", value=False)
        st.session_state.user_prefs['show_advanced'] = show_advanced
    
    # History
    with st.expander("📜 Recent History"):
        if st.session_state.history:
            for feature, items in st.session_state.history.items():
                if items:
                    st.markdown(f"**{feature}**")
                    for idx, item in enumerate(items[:3]):
                        st.caption(f"• {item['title']} - {item['timestamp']}")
        else:
            st.info("No history yet")
    
    # Favorites
    with st.expander("⭐ Favorites"):
        if st.session_state.favorites:
            for idx, fav in enumerate(st.session_state.favorites[-5:]):
                st.caption(f"• {fav['title']} ({fav['feature']})")
        else:
            st.info("No favorites yet")
    
    st.markdown("---")
    if st.button("🗑️ Clear All Data"):
        st.session_state.history = {}
        st.session_state.favorites = []
        st.success("Data cleared!")

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, {THEME['primary']}, {THEME['accent']}); border-radius: 20px; margin-bottom: 2rem;">
        <div style="font-size: 3.5rem; animation: float 3s ease-in-out infinite;">🦋</div>
        <h1 style="color: white; margin: 0;">Metamorphosis Studio Pro</h1>
        <p style="color: rgba(255,255,255,0.9);">Ultimate AI Workspace with Advanced Features</p>
        <p class="bangla-text" style="color: rgba(255,255,255,0.85);">সম্পূর্ণ AI কর্মক্ষেত্র - উন্নত ফিচার সহ</p>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs([
    "🔑 API", "✨ Prompts", "📊 Diagrams", "📝 Docs",
    "💻 Code", "📚 Summarize", "🌐 Translate", 
    "✉️ Emails", "🔍 Analyze", "📝 Quizzes"
])

# === TAB 1: API KEY ===
with tabs[0]:
    st.markdown("### 🔑 API Key Management")
    
    api_input = st.text_input("Gemini API Key", type="password")
    if st.button("💾 Save & Verify", type="primary"):
        if api_input:
            try:
                genai.configure(api_key=api_input)
                model = genai.GenerativeModel("gemini-2.5-flash")
                model.generate_content("Test")
                st.session_state.api_key = api_input
                st.markdown('<div class="success-box">✅ Verified!</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ {e}")
    
    if "api_key" in st.session_state:
        st.success(f"Active: {st.session_state.api_key[:8]}...")

# === TAB 2: PROMPT REFINER ===
with tabs[1]:
    st.markdown("### ✨ Advanced Prompt Refiner")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Template Selection
        template = st.selectbox("📚 Template", ["None"] + list(PROMPT_TEMPLATES.keys()))
        if template != "None":
            st.info(f"Template: {PROMPT_TEMPLATES[template][:100]}...")
        
        # Controls
        context = st.selectbox("Context", ["General", "Software Engineering", "Data Science", "Legal", "Medical", "Business", "Creative"])
        tone = st.select_slider("Tone", ["Casual", "Neutral", "Professional", "Academic"])
        complexity = st.slider("Complexity", 1, 10, 7)
        
        if show_advanced:
            length = st.select_slider("Output Length", ["Brief", "Standard", "Detailed"])
            format_type = st.selectbox("Format", ["Paragraph", "Bullet Points", "Numbered List"])
        
        # Input
        base_text = PROMPT_TEMPLATES.get(template, "") if template != "None" else ""
        prompt_input = st.text_area("Draft Prompt", value=base_text, height=200)
        char_count = len(prompt_input)
        st.caption(f"📊 {char_count} characters | {len(prompt_input.split())} words")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Refine", type="primary", use_container_width=True):
                if "api_key" in st.session_state and prompt_input:
                    try:
                        genai.configure(api_key=st.session_state.api_key)
                        model = genai.GenerativeModel("gemini-2.5-flash")
                        sys_prompt = f"Refine prompt. Context: {context}. Tone: {tone}. Complexity: {complexity}/10. No **bold**."
                        res = model.generate_content(f"{sys_prompt}\n{prompt_input}")
                        st.session_state.refined_prompt = res.text.replace("**", "")
                        add_to_history("Prompts", st.session_state.refined_prompt, f"{context} prompt")
                    except Exception as e:
                        st.error(f"❌ {e}")
        
        with col_btn2:
            if 'refined_prompt' in st.session_state:
                if st.button("⭐ Save Favorite", use_container_width=True):
                    save_to_favorites(st.session_state.refined_prompt, "Prompts", f"{context} prompt")
                    st.success("Saved!")
    
    with col2:
        st.markdown("#### 📋 Refined Output")
        if "refined_prompt" in st.session_state:
            st.text_area("Result", st.session_state.refined_prompt, height=450)
            st.download_button("📥 Download", st.session_state.refined_prompt, "prompt.txt")
        else:
            st.info("Output will appear here")

# === TAB 3: DIAGRAMS ===
with tabs[2]:
    st.markdown("### 📊 Diagram Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Template & Theme
        diagram_template = st.selectbox("📐 Template", ["None"] + list(DIAGRAM_TEMPLATES.keys()))
        diagram_theme = st.selectbox("🎨 Theme", ["default", "dark", "forest", "neutral"])
        diagram_type = st.selectbox("Type", ["Flowchart", "Sequence", "ER Diagram", "Gantt", "Mindmap"])
        
        # Requirements
        base_code = DIAGRAM_TEMPLATES.get(diagram_template, "") if diagram_template != "None" else ""
        reqs = st.text_area("Requirements", value=base_code if not base_code.startswith("```") else "", height=200)
        
        if show_advanced:
            export_size = st.selectbox("Export Size", ["Standard", "Large (2x)", "Extra Large (4x)"])
            include_legend = st.checkbox("Include Legend")
        
        if st.button("🎨 Generate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Generate Mermaid {diagram_type}. Quote labels. Code only."
                    res = model.generate_content(f"{sys_prompt}\n{reqs}")
                    st.session_state.mermaid_code = sanitize_mermaid_code(res.text)
                    add_to_history("Diagrams", st.session_state.mermaid_code, diagram_type)
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "mermaid_code" in st.session_state:
            st.markdown("#### 👁️ Preview")
            st.components.v1.html(
                f"""
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true, theme: '{diagram_theme}' }});
                </script>
                <div class="mermaid">{st.session_state.mermaid_code}</div>
                """,
                height=500
            )
            
            # Downloads
            st.markdown("#### 💾 Downloads")
            dc1, dc2, dc3, dc4 = st.columns(4)
            
            png_bytes = get_mermaid_img(st.session_state.mermaid_code, "png")
            svg_bytes = get_mermaid_img(st.session_state.mermaid_code, "svg")
            
            with dc1:
                if png_bytes: st.download_button("PNG", png_bytes, "diagram.png", use_container_width=True)
            with dc2:
                if png_bytes:
                    jpg_bytes = convert_to_jpg(png_bytes)
                    if jpg_bytes: st.download_button("JPG", jpg_bytes, "diagram.jpg", use_container_width=True)
            with dc3:
                if svg_bytes: st.download_button("SVG", svg_bytes, "diagram.svg", use_container_width=True)
            with dc4:
                if png_bytes: st.download_button("PDF", create_pdf("Diagram", png_bytes), "diagram.pdf", use_container_width=True)
            
            # Edit Mode
            with st.expander("✏️ Edit Code"):
                edited_code = st.text_area("Mermaid Code", st.session_state.mermaid_code, height=200)
                if st.button("🔄 Update Preview"):
                    st.session_state.mermaid_code = edited_code
                    st.rerun()

# === TAB 4: DOCUMENTS ===
with tabs[3]:
    st.markdown("### 📝 Document Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        doc_type = st.selectbox("Type", ["BRD", "TDD", "API Spec", "User Manual", "SOP", "Report", "Other"])
        doc_style = st.selectbox("Style", ["Professional", "Academic", "Technical", "Simple"])
        
        if show_advanced:
            include_toc = st.checkbox("Include Table of Contents", value=True)
            include_meta = st.checkbox("Include Metadata")
            if include_meta:
                author = st.text_input("Author")
                version = st.text_input("Version", "1.0")
        
        doc_details = st.text_area("Content Details", height=300)
        
        if st.button("📄 Generate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Write {doc_type}. Style: {doc_style}. Markdown format."
                    if show_advanced and include_toc:
                        sys_prompt += " Include TOC."
                    res = model.generate_content(f"{sys_prompt}\n{doc_details}")
                    st.session_state.doc_content = res.text
                    add_to_history("Documents", st.session_state.doc_content, doc_type)
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "doc_content" in st.session_state:
            st.markdown("#### 👁️ Preview")
            st.markdown(st.session_state.doc_content)
            st.markdown("---")
            
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("MD", st.session_state.doc_content, "doc.md", use_container_width=True)
            with dl2:
                st.download_button("DOCX", create_docx(st.session_state.doc_content), "doc.docx", use_container_width=True)
            with dl3:
                st.download_button("PDF", create_pdf(st.session_state.doc_content), "doc.pdf", use_container_width=True)

# === TAB 5: CODE GENERATOR ===
with tabs[4]:
    st.markdown("### 💻 Code Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        language = st.selectbox("Language", ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go"])
        framework = st.selectbox("Framework", CODE_FRAMEWORKS.get(language, ["None"]))
        style = st.selectbox("Style", ["OOP", "Functional", "Procedural"])
        
        if show_advanced:
            include_docs = st.checkbox("Include Documentation", value=True)
            include_types = st.checkbox("Include Type Hints", value=True)
            include_tests = st.checkbox("Generate Unit Tests")
            include_deps = st.checkbox("Generate Dependencies")
        
        code_req = st.text_area("Requirements", height=250)
        
        if st.button("⚡ Generate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Generate {language} code. Framework: {framework}. Style: {style}."
                    if show_advanced:
                        if include_docs: sys_prompt += " Include docs."
                        if include_types: sys_prompt += " Include types."
                    res = model.generate_content(f"{sys_prompt}\n{code_req}")
                    st.session_state.generated_code = res.text
                    add_to_history("Code", st.session_state.generated_code, f"{language} code")
                    
                    # Generate tests if requested
                    if show_advanced and include_tests:
                        test_res = model.generate_content(f"Generate unit tests for:\n{res.text}")
                        st.session_state.generated_tests = test_res.text
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "generated_code" in st.session_state:
            st.markdown("#### 💻 Generated Code")
            st.code(st.session_state.generated_code, language=language.lower())
            st.download_button("📥 Download", st.session_state.generated_code, f"code.{language[:2].lower()}")
            
            if show_advanced and 'generated_tests' in st.session_state:
                with st.expander("🧪 Unit Tests"):
                    st.code(st.session_state.generated_tests, language=language.lower())

# === TAB 6: SUMMARIZER ===
with tabs[5]:
    st.markdown("### 📚 Text Summarizer")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        compression = st.slider("Compression Ratio", 10, 90, 50, help="% of original length")
        format_type = st.selectbox("Format", ["Paragraph", "Bullet Points", "Key Points"])
        
        if show_advanced:
            extract_info = st.multiselect("Extract", ["Names", "Dates", "Numbers", "Locations"])
            multilingual = st.checkbox("Multi-language Support")
        
        text_to_summarize = st.text_area("Text", height=350)
        word_count = len(text_to_summarize.split())
        st.caption(f"📊 {word_count} words → ~{int(word_count * compression / 100)} words")
        
        if st.button("📊 Summarize", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Summarize to {compression}% length. Format: {format_type}."
                    res = model.generate_content(f"{sys_prompt}\n{text_to_summarize}")
                    st.session_state.summary = res.text
                    add_to_history("Summaries", st.session_state.summary, f"{compression}% summary")
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "summary" in st.session_state:
            st.markdown("#### 📄 Summary")
            st.markdown(st.session_state.summary)
            st.download_button("📥 Download", st.session_state.summary, "summary.txt")

# === TAB 7: TRANSLATOR ===
with tabs[6]:
    st.markdown("### 🌐 Translation Tool")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        target_lang = st.selectbox("Target Language", [
            "Spanish", "French", "German", "Chinese", "Japanese", "Korean",
            "Arabic", "Hindi", "Bengali", "Portuguese", "Russian", "Italian"
        ])
        
        if show_advanced:
            formality = st.select_slider("Formality", ["Casual", "Neutral", "Formal"])
            preserve_format = st.checkbox("Preserve Formatting", value=True)
        
        text_to_translate = st.text_area("Text", height=350)
        
        if st.button("🌐 Translate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Translate to {target_lang}."
                    if show_advanced:
                        sys_prompt += f" Formality: {formality}."
                    res = model.generate_content(f"{sys_prompt}\n{text_to_translate}")
                    st.session_state.translation = res.text
                    add_to_history("Translations", st.session_state.translation, f"To {target_lang}")
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "translation" in st.session_state:
            st.markdown(f"#### 🎯 {target_lang}")
            st.text_area("Result", st.session_state.translation, height=400)
            st.download_button("📥 Download", st.session_state.translation, f"translation_{target_lang.lower()}.txt")

# === TAB 8: EMAIL WRITER ===
with tabs[7]:
    st.markdown("### ✉️ Email Draft Generator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        email_template = st.selectbox("Template", ["None"] + list(EMAIL_TEMPLATES.keys()))
        email_type = st.selectbox("Type", ["Formal Business", "Casual", "Marketing", "Follow-up", "Thank You"])
        email_tone = st.select_slider("Tone", ["Very Formal", "Formal", "Neutral", "Friendly"])
        
        if show_advanced:
            include_subject = st.checkbox("Auto-generate Subject", value=True)
            signature = st.text_area("Signature", "Best regards,\n[Your Name]")
        
        base_email = EMAIL_TEMPLATES.get(email_template, "") if email_template != "None" else ""
        email_context = st.text_area("Key Points", value=base_email, height=200)
        
        if st.button("✉️ Generate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Write {email_type} email. Tone: {email_tone}."
                    if show_advanced and include_subject:
                        sys_prompt += " Include subject line."
                    res = model.generate_content(f"{sys_prompt}\n{email_context}")
                    st.session_state.email_draft = res.text
                    add_to_history("Emails", st.session_state.email_draft, email_type)
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "email_draft" in st.session_state:
            st.markdown("#### 📨 Draft")
            st.text_area("Email", st.session_state.email_draft, height=500)
            st.download_button("📥 Download", st.session_state.email_draft, "email.txt")

# === TAB 9: CONTENT ANALYZER ===
with tabs[8]:
    st.markdown("### 🔍 Content Analyzer")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if show_advanced:
            analysis_depth = st.select_slider("Analysis Depth", ["Quick", "Standard", "Comprehensive"])
            check_grammar = st.checkbox("Grammar Check")
            check_seo = st.checkbox("SEO Analysis")
        
        text_to_analyze = st.text_area("Content", height=400)
        
        if st.button("🔍 Analyze", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = """Analyze:
1. Readability Score (1-10)
2. Sentiment Analysis
3. Top 5 Keywords
4. Word/Sentence Count
5. Improvement Suggestions"""
                    if show_advanced:
                        if check_grammar: sys_prompt += "\n6. Grammar Issues"
                        if check_seo: sys_prompt += "\n7. SEO Recommendations"
                    
                    res = model.generate_content(f"{sys_prompt}\n{text_to_analyze}")
                    st.session_state.analysis = res.text
                    add_to_history("Analysis", st.session_state.analysis, "Content analysis")
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "analysis" in st.session_state:
            st.markdown("#### 📊 Analysis")
            st.markdown(st.session_state.analysis)
            st.download_button("📥 Download", st.session_state.analysis, "analysis.txt")

# === TAB 10: QUIZ GENERATOR ===
with tabs[9]:
    st.markdown("### 📝 Quiz Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        question_type = st.selectbox("Type", ["MCQ", "True/False", "Short Answer", "Mixed"])
        num_questions = st.slider("Questions", 5, 30, 10)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"])
        
        if show_advanced:
            include_answers = st.checkbox("Include Answer Key", value=True)
            randomize = st.checkbox("Randomize Order")
            point_value = st.number_input("Points per Question", 1, 10, 1)
        
        quiz_topic = st.text_area("Topic/Content", height=250)
        
        if st.button("🎯 Generate", type="primary"):
            if "api_key" in st.session_state:
                try:
                    genai.configure(api_key=st.session_state.api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    sys_prompt = f"Create {num_questions} {question_type} questions. Difficulty: {difficulty}."
                    if show_advanced and include_answers:
                        sys_prompt += " Include answer key."
                    res = model.generate_content(f"{sys_prompt}\n{quiz_topic}")
                    st.session_state.quiz = res.text
                    add_to_history("Quizzes", st.session_state.quiz, f"{num_questions} questions")
                except Exception as e:
                    st.error(f"❌ {e}")
    
    with col2:
        if "quiz" in st.session_state:
            st.markdown("#### 📋 Quiz")
            st.markdown(st.session_state.quiz)
            
            dl1, dl2, dl3 = st.columns(3)
            with dl1:
                st.download_button("TXT", st.session_state.quiz, "quiz.txt", use_container_width=True)
            with dl2:
                st.download_button("DOCX", create_docx(st.session_state.quiz), "quiz.docx", use_container_width=True)
            with dl3:
                st.download_button("PDF", create_pdf(st.session_state.quiz), "quiz.pdf", use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="color: #64748B;">Metamorphosis Studio Pro | Powered by Google Gemini</p>
    <p class="bangla-text" style="color: #64748B;">মেটামরফসিস স্টুডিও প্রো 🦋</p>
</div>
""", unsafe_allow_html=True)
