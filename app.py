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
import ui.tabs as ui

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

# --- THEME CONFIGURATION (Modern Orange/Black/White) ---
THEME = {
    "primary": "#FF5A36",        # Vibrant Orange
    "primary_dark": "#E04828",   # Darker Orange for hover
    "accent": "#FF8C42",         # Lighter Orange accent
    "success": "#10B981",        # Emerald (keep for success states)
    "bg": "#000000",             # Black background
    "surface": "#1A1A1A",        # Dark gray for cards
    "text_main": "#FFFFFF",      # White for text
    "text_secondary": "#CCCCCC", # Light gray for secondary text  
    "border": "#FF5A36",         # Orange borders
    "shadow": "0 8px 32px rgba(255, 90, 54, 0.3)",
    "shadow_lg": "0 16px 48px rgba(255, 90, 54, 0.4)",
    "box_shadow_hover": "0 12px 40px rgba(255, 90, 54, 0.5)"
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {{
            --primary: {THEME['primary']};
            --primary-dark: {THEME['primary_dark']};
            --accent: {THEME['accent']};
            --bg: {THEME['bg']};
            --surface: {THEME['surface']};
            --text-main: {THEME['text_main']};
            --text-secondary: {THEME['text_secondary']};
            --border: {THEME['border']};
            --shadow: {THEME['shadow']};
            --shadow-lg: {THEME['shadow_lg']};
        }}

        /* Global Font Settings */
        html, body, [class*="css"], .stMarkdown {{
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }}

        /* App Background */
        .stApp {{
            background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        }}

        /* Main Container */
        .block-container {{
            max-width: 1400px !important;
            margin: 2rem auto !important;
            background: var(--surface);
            border: 2px solid var(--primary);
            box-shadow: var(--shadow);
            padding: 2.5rem !important;
            border-radius: 16px;
        }}

        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', sans-serif;
            color: var(--text-main) !important;
            font-weight: 700;
        }}
        h1 {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px rgba(255, 90, 54, 0.4) !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 0.75rem 1.5rem !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(255, 90, 54, 0.6) !important;
        }}
        .stButton > button:active {{
            transform: translateY(0px) !important;
        }}

        /* Download Buttons */
        .stDownloadButton > button {{
            background: var(--surface) !important;
            color: var(--primary) !important;
            border: 2px solid var(--primary) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        .stDownloadButton > button:hover {{
            background: var(--primary) !important;
            color: white !important;
            transform: translateY(-2px) !important;
        }}

        /* Inputs */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea, 
        .stSelectbox > div > div > div, 
        .stNumberInput > div > div > input {{
            background-color: var(--surface) !important;
            border: 2px solid rgba(255, 90, 54, 0.3) !important;
            border-radius: 12px !important;
            color: var(--text-main) !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
        }}
        .stTextInput > div > div > input:focus, 
        .stTextArea > div > div > textarea:focus {{
            box-shadow: 0 0 0 2px var(--primary) !important;
            border-color: var(--primary) !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: transparent;
            border-bottom: 2px solid rgba(255, 90, 54, 0.2);
        }}
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border: none;
            border-radius: 8px 8px 0 0;
            padding: 12px 24px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            color: var(--text-secondary);
            transition: all 0.3s ease;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(255, 90, 54, 0.1);
            color: var(--primary);
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
            color: white !important;
            box-shadow: 0 -4px 12px rgba(255, 90, 54, 0.3);
        }}

        /* Sliders */
        .stSlider > div > div > div > div {{
            background: var(--primary) !important;
        }}

        /* Success/Info/Warning/Error boxes */
        .stAlert {{
            background-color: var(--surface);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            color: var(--text-main);
        }}

        /* Code blocks */
        .stCodeBlock {{
            background-color: var(--surface) !important;
            border: 1px solid rgba(255, 90, 54, 0.2) !important;
            border-radius: 8px !important;
        }}

        /* Separator */
        hr {{
            border-color: rgba(255, 90, 54, 0.3) !important;
        }}

        /* Expander */
        .streamlit-expanderHeader {{
            background: var(--surface) !important;
            border: 2px solid rgba(255, 90, 54, 0.2) !important;
            border-radius: 12px !important;
            color: var(--text-main) !important;
        }}
        .streamlit-expanderHeader:hover {{
            border-color: var(--primary) !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Header with logo
# Header with logo - Centered
st.markdown(
    """
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 2rem;">
        <img src="https://www.metamorphosis.com.bd/web/image/website/1/logo/Metamorphosis?unique=1d24751" width="180" style="margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 3rem; background: linear-gradient(135deg, #FF5A36 0%, #FF8C42 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Metamorphosis Studio</h1>
        <p style="font-size: 1.2rem; color: #CCCCCC; margin-top: 0.5rem;">🚀 Advanced AI-Powered Documentation & Development Suite</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# Render the application tabs
ui.render_tabs()

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="color: #64748B;">Metamorphosis Studio Pro | Powered by Google Gemini</p>
    <p class="bangla-text" style="color: #64748B;">মেটামরফসিস স্টুডিও প্রো 🦋</p>
</div>
""", unsafe_allow_html=True)
