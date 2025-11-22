import streamlit as st
import google.generativeai as genai
from datetime import datetime
import base64
import json
import zlib

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BRAND COLORS ---
PRIMARY_COLOR = "#ED6523"  # Metamorphosis Orange
SECONDARY_COLOR = "#FFF0E6" # Very Light Orange/Cream for backgrounds
ACCENT_COLOR = "#2C3E50"    # Dark Slate Blue for contrast text
BACKGROUND_COLOR = "#F8F9FA" # Modern Light Grey/White for app background
WHITE = "#FFFFFF"

# --- HELPER: MERMAID LIVE URL GENERATOR ---
def generate_mermaid_link(mermaid_code):
    """Generates a link to open the current code in mermaid.live"""
    state = {
        "code": mermaid_code,
        "mermaid": {"theme": "default"},
        "autoSync": True,
        "updateDiagram": True
    }
    json_str = json.dumps(state)
    # Compress using zlib (deflate) without headers to match pako.js used by mermaid.live
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed = compressor.compress(json_str.encode('utf-8')) + compressor.flush()
    base64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://mermaid.live/edit#{base64_str}"

# --- CUSTOM CSS FOR MODERN UI & BRANDING ---
st.markdown(f"""
    <style>
    /* --- FORCE LIGHT THEME & BACKGROUND --- */
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        color: {ACCENT_COLOR};
    }}
    
    /* --- SIDEBAR STYLING --- */
    [data-testid="stSidebar"] {{
        background-color: {WHITE} !important;
        border-right: 1px solid #E0E0E0;
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
    }}
    
    /* --- TYPOGRAPHY & HEADERS --- */
    h1, h2, h3, h4, h5, h6, span[data-testid="stHeader"] {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        color: {ACCENT_COLOR} !important;
    }}
    
    h1 {{
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }}
    
    /* Specific coloring for the main title gradient effect (simulated) */
    .main-title {{
        background: -webkit-linear-gradient(45deg, {PRIMARY_COLOR}, #FF8C42);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* --- INPUT FIELDS & CARDS --- */
    /* Text Area styling */
    .stTextArea textarea {{
        border: 1px solid #E0E0E0 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        padding: 15px !important;
        background-color: {WHITE} !important;
        color: {ACCENT_COLOR} !important;
        font-family: 'Courier New', Courier, monospace !important; /* Monospace for code */
    }}
    .stTextArea textarea:focus {{
        border-color: {PRIMARY_COLOR} !important;
        box-shadow: 0 0 0 2px {SECONDARY_COLOR} !important;
    }}
    
    /* --- DROPDOWN & RADIO STYLING (High Contrast) --- */
    div[data-baseweb="select"] > div {{
        background-color: {WHITE} !important;
        border: 1px solid #E0E0E0 !important;
        color: {ACCENT_COLOR} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="select"] span {{
        color: {ACCENT_COLOR} !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="menu"] {{
        background-color: {WHITE} !important;
        border: 1px solid #E0E0E0 !important;
    }}
    div[data-baseweb="menu"] li {{
        background-color: {WHITE} !important;
        color: {ACCENT_COLOR} !important;
    }}
    div[data-baseweb="menu"] li:hover {{
        background-color: {SECONDARY_COLOR} !important;
        color: {PRIMARY_COLOR} !important;
    }}
    div[role="radiogroup"] label {{
        background-color: transparent !important;
    }}
    div[role="radiogroup"] label p {{
        color: {ACCENT_COLOR} !important;
        font-weight: 500 !important;
    }}

    /* --- BUTTONS --- */
    div.stButton > button, div[data-testid="stDownloadButton"] > button {{
        background: linear-gradient(90deg, {PRIMARY_COLOR} 0%, #FF7E35 100%) !important;
        color: {WHITE} !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 14px 0 rgba(237, 101, 35, 0.39) !important;
        transition: transform 0.2s ease-in-out !important;
        width: 100%;
    }}
    div.stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(237, 101, 35, 0.29) !important;
        color: {WHITE} !important;
    }}

    /* --- GENERATED DOCUMENT STYLING (PAPER LOOK) --- */
    .document-container {{
        background-color: {WHITE};
        padding: 40px;
        border-radius: 4px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #EAEAEA;
        margin-top: 20px;
    }}
    
    .stMarkdown p, .stWrite p, div[data-testid="stMarkdownContainer"] p, 
    .stMarkdown li, .stWrite li, div[data-testid="stMarkdownContainer"] li {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 18px !important;
        line-height: 1.8 !important;
        color: #000000 !important;
    }}
    
    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2 {{
        font-family: 'Times New Roman', Times, serif !important;
        color: {PRIMARY_COLOR} !important;
        border-bottom: 2px solid {SECONDARY_COLOR};
        padding-bottom: 10px;
        margin-top: 30px !important;
    }}
    
    div[data-testid="stMarkdownContainer"] h3 {{
        font-family: 'Times New Roman', Times, serif !important;
        color: #333 !important;
        margin-top: 25px !important;
    }}

    /* --- MERMAID DIAGRAM STYLING --- */
    .mermaid {{
        background-color: #FAFAFA;
        padding: 25px;
        border-radius: 8px;
        border: 1px solid #EEEEEE;
        margin: 25px 0;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- COMPANY CONTEXT ---
METAMORPHOSIS_CONTEXT = """
COMPANY PROFILE: Metamorphosis Systems (Metamorphosis Ltd.)
STATUS: #1 Leading Odoo Silver Partner in Bangladesh.
CORE SERVICES: Odoo ERP Implementation, Customization, Mobile App Dev.
METHODOLOGY: 1. Consultation -> 2. Estimate -> 3. Analysis -> 4. Timeline -> 5. Implementation -> 6. Go Live.
"""

# --- PROMPT ENGINEERING ---
def get_system_instruction(mode, selected_type):
    base_role = f"""
    ROLE: You are the Senior Solutions Architect for Metamorphosis Ltd.
    CONTEXT: {METAMORPHOSIS_CONTEXT}
    TONE: Professional, Corporate, Industry-Standard.
    
    CRITICAL MERMAID SYNTAX RULES (VERY STRICT):
    1. **NO SPACES IN NODE IDs**: `Node A` is ILLEGAL. Use `NodeA` or `Node_A`.
    2. **QUOTES FOR LABELS**: If a label contains spaces or special characters, use quotes. Example: `A["Production (Work Centers)"]`.
    3. **NO SPECIAL CHARS IN IDs**: Do not use `(`, `)`, `/` in IDs.
    """

    if mode == "Diagram Generator":
        return base_role + f"""
        GOAL: Generate a {selected_type} using MermaidJS.
        OUTPUT: ONLY return the valid mermaid code block inside ```mermaid ... ``` tags. Do not add explanations or titles.
        """

    # Full document prompts (Truncated for brevity as they are same as before)
    base_role += "\nFORMATTING: Use Markdown. Use `mermaid` code blocks for diagrams."
    return base_role + f"\nGOAL: Create a {selected_type}."

# --- SIDEBAR UI ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: {PRIMARY_COLOR}; font-size: 28px; margin-bottom: 0;">🦋</h1>
            <h2 style="color: {ACCENT_COLOR}; font-size: 20px; font-weight: 700; margin-top: 5px;">Metamorphosis</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🛠️ Configuration")
    api_key = st.text_input("🔑 Gemini API Key", type="password", help="Get this from Google AI Studio")
    st.markdown("---")
    
    app_mode = st.radio("Select Mode", ["Full Document Generator", "Diagram Live Editor"])
    
    selected_type = ""
    if app_mode == "Full Document Generator":
        selected_type = st.selectbox("📄 Document Type", ["Proposal", "BRD", "SRS", "TRD", "HLD", "API Docs", "UAT Plan"])
    else:
        selected_type = st.selectbox("📊 Diagram Type", ["Flowchart", "Sequence", "ERD", "Gantt", "State", "Class", "User Journey"])

# --- MAIN UI ---
st.markdown(f"""
    <div style="padding: 20px 0; text-align: center;">
        <h1 class="main-title" style="font-size: 42px; margin-bottom: 10px;">Metamorphosis Architect</h1>
        <p style="color: {ACCENT_COLOR}; font-size: 18px; opacity: 0.8;">
            Professional ERP Documentation & Diagram Generator
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- LOGIC ---
if "mermaid_code" not in st.session_state:
    st.session_state.mermaid_code = """graph TD;
    A["Start"] --> B["Process"];
    B --> C["End"];"""

if app_mode == "Diagram Live Editor":
    st.markdown("### ⚡ Live Diagram Preview")
    st.info("Describe your flow below. The AI will generate the diagram visually.")
    
    client_scenario = st.text_area("Describe Diagram Requirements:", height=100)
    
    if st.button(f"🤖 Draft {selected_type}", type="primary"):
        if not api_key:
            st.error("Please provide API Key.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=get_system_instruction(app_mode, selected_type))
                with st.spinner("Architecting diagram..."):
                    response = model.generate_content(f"SCENARIO: {client_scenario}")
                    # Extract code from markdown block if present
                    clean_code = response.text.replace("```mermaid", "").replace("```", "").strip()
                    st.session_state.mermaid_code = clean_code
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    
    # DISPLAY PREVIEW ONLY (No Split Columns)
    st.markdown("#### 👁️ Visual Preview")
    try:
        # Use standard mermaid block
        st.markdown(f"```mermaid\n{st.session_state.mermaid_code}\n```")
    except Exception:
        st.error("Syntax Error in Mermaid Code")
        
    # OPEN IN REAL MERMAID LIVE BUTTON
    st.markdown("<br>", unsafe_allow_html=True)
    live_url = generate_mermaid_link(st.session_state.mermaid_code)
    st.markdown(f"""
        <a href="{live_url}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: {PRIMARY_COLOR}; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                font-weight: bold; 
                cursor: pointer; 
                width: 100%;">
                🚀 Open in Mermaid.live (External)
            </button>
        </a>
    """, unsafe_allow_html=True)

else:
    # FULL DOCUMENT GENERATOR LOGIC (Standard)
    st.markdown(f"### 📝 {selected_type} Requirements")
    client_scenario = st.text_area("Enter details...", height=150)
    
    if st.button("Generate Document", type="primary"):
        if not api_key:
            st.error("Missing API Key")
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=get_system_instruction(app_mode, selected_type))
            with st.spinner("Generating..."):
                response = model.generate_content(f"SCENARIO: {client_scenario}")
                doc_content = response.text
                
                st.markdown(f"""<div class="document-container"><h2>{selected_type}</h2>{doc_content}</div>""", unsafe_allow_html=True)
                
                st.download_button(
                    label="📥 Download Document",
                    data=doc_content,
                    file_name=f"{selected_type}_Metamorphosis.md",
                    mime="text/markdown"
                )

# --- FOOTER ---
st.markdown(
    f"""
    <div style='position: fixed; bottom: 0; left: 0; width: 100%; text-align: center; color: #888; font-size: 12px; padding: 15px; background-color: {WHITE}; border-top: 1px solid #EEE; z-index: 100;'>
        Powered by Google Gemini 2.5 | Metamorphosis Systems Internal Tool
    </div>
    """, 
    unsafe_allow_html=True
)
