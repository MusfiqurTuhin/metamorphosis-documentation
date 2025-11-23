import streamlit as st
import google.generativeai as genai
from datetime import datetime
import base64
import json
import zlib
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BRAND COLORS & THEME ---
PRIMARY_COLOR = "#ED6523"  # Metamorphosis Orange
PRIMARY_GRADIENT = "linear-gradient(135deg, #ED6523 0%, #FF8C42 100%)"
SECONDARY_COLOR = "#FFF0E6" 
ACCENT_COLOR = "#1E293B"    # Dark Slate Blue/Grey
BACKGROUND_COLOR = "#F8FAFC" 
WHITE = "#FFFFFF"
GLASS_BG = "rgba(255, 255, 255, 0.95)"
GLASS_BORDER = "1px solid rgba(255, 255, 255, 0.2)"
SHADOW_SM = "0 2px 4px rgba(0,0,0,0.05)"
SHADOW_MD = "0 8px 30px rgba(0,0,0,0.08)"

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
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15, 8, zlib.Z_DEFAULT_STRATEGY)
    compressed = compressor.compress(json_str.encode('utf-8')) + compressor.flush()
    base64_str = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"https://mermaid.live/edit#{base64_str}"

# --- HELPER: CODE SANITIZER ---
def sanitize_mermaid_code(raw_text):
    """
    Extracts and cleans Mermaid code from LLM output.
    """
    match = re.search(r"```mermaid\s+(.*?)\s+```", raw_text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = raw_text.replace("```mermaid", "").replace("```", "").strip()
    return code

# --- PROMPT REFINER FUNCTION ---
def refine_prompt(original_prompt, context_type):
    """
    Uses Gemini to refine the user's prompt for better accuracy.
    """
    if not original_prompt:
        return ""
        
    system_instruction = """
    ROLE: You are an Expert Prompt Engineer specializing in ERP documentation and system architecture diagrams.
    GOAL: Refine the user's raw input into a structured, detailed, and professional prompt that will yield the best results from an LLM.
    
    INSTRUCTIONS:
    1. Clarify intent: Make vague requests specific.
    2. Add context: Assume standard ERP best practices (Odoo context) if missing.
    3. Structure: Organize into clear sections (Objective, Key Elements, Constraints).
    4. Output: Return ONLY the refined prompt text. Do not add conversational filler.
    """
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
        response = model.generate_content(f"CONTEXT: {context_type}\nRAW INPUT: {original_prompt}")
        return response.text.strip()
    except Exception as e:
        return original_prompt # Fallback if error

# --- CUSTOM CSS FOR MODERN UI ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* GLOBAL STYLES */
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        font-family: 'Inter', sans-serif;
        color: {ACCENT_COLOR};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}

    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        background-color: {WHITE} !important;
        border-right: 1px solid #E2E8F0;
    }}
    
    /* MAIN TITLE */
    .main-title {{
        background: {PRIMARY_GRADIENT};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
        color: #64748B;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 3rem;
    }}

    /* CARDS & CONTAINERS (Glassmorphism) */
    .glass-card {{
        background: {GLASS_BG};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: {SHADOW_MD};
        margin-bottom: 2rem;
    }}

    /* INPUTS */
    .stTextArea textarea {{
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        box-shadow: {SHADOW_SM} !important;
        transition: all 0.2s ease;
    }}
    .stTextArea textarea:focus {{
        border-color: {PRIMARY_COLOR} !important;
        box-shadow: 0 0 0 3px {SECONDARY_COLOR} !important;
    }}

    /* BUTTONS */
    div.stButton > button {{
        background: {PRIMARY_GRADIENT} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(237, 101, 35, 0.3) !important;
        transition: all 0.3s ease !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(237, 101, 35, 0.4) !important;
    }}
    
    /* SECONDARY BUTTON (Refine) */
    .refine-btn button {{
        background: white !important;
        color: {PRIMARY_COLOR} !important;
        border: 1px solid {PRIMARY_COLOR} !important;
        box-shadow: none !important;
    }}
    .refine-btn button:hover {{
        background: {SECONDARY_COLOR} !important;
    }}

    /* MARKDOWN CONTENT */
    .document-container {{
        background: white;
        padding: 3rem;
        border-radius: 8px;
        box-shadow: {SHADOW_MD};
        border: 1px solid #E2E8F0;
        font-family: 'Georgia', serif; /* Professional doc font */
        line-height: 1.8;
    }}
    
    /* MERMAID CONTAINER */
    .mermaid-container {{
        background: white;
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: {SHADOW_SM};
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

# --- SYSTEM INSTRUCTIONS ---
def get_system_instruction(mode, selected_type):
    base_role = f"""
    ROLE: You are the Senior Solutions Architect for Metamorphosis Ltd.
    CONTEXT: {METAMORPHOSIS_CONTEXT}
    TONE: Professional, Corporate, Industry-Standard.
    
    *** CRITICAL MERMAID SYNTAX RULES (STRICT COMPLIANCE REQUIRED) ***
    1. **ALWAYS QUOTE LABELS**: If a node label contains spaces, parentheses `()`, or special chars, you **MUST** use double quotes.
       - ❌ WRONG: `A[Sales Order (SO)]`
       - ✅ RIGHT: `A["Sales Order (SO)"]`
    2. **NO SPACES IN NODE IDs**: IDs must be alphanumeric only.
       - ❌ WRONG: `Node A`
       - ✅ RIGHT: `NodeA` or `Node_A`
    3. **NO SPECIAL CHARS IN IDs**: Do not use `(`, `)`, `/`, `-` in the ID itself.
       - ❌ WRONG: `SO(Created)`
       - ✅ RIGHT: `SO_Created`
    4. **DIRECTION**: ALWAYS use `graph TD` (Top-Down). Do NOT use Left-Right (`LR`) direction. The output MUST be vertical to be A4 compatible.
    """

    if mode == "Diagram Generator":
        return base_role + f"""
        GOAL: Generate a {selected_type} using MermaidJS.
        OUTPUT FORMAT: 
        - You must output ONLY a single Mermaid code block.
        - Wrap it in ```mermaid ... ```.
        - Do NOT write any introduction, conclusion, or text outside the code block.
        """

    # Full document prompts
    base_role += "\nFORMATTING: Use Markdown. Use `mermaid` code blocks for diagrams. Follow the CRITICAL SYNTAX RULES above for every diagram."
    return base_role + f"\nGOAL: Create a {selected_type}."

# --- SIDEBAR UI ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 40px; margin-bottom: 10px;">🦋</div>
            <h3 style="margin:0; color: {ACCENT_COLOR};">Metamorphosis</h3>
            <p style="font-size: 12px; color: #94A3B8; margin-top: 5px;">Architect Edition v2.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Get this from Google AI Studio")
    
    st.markdown("---")
    
    app_mode = st.radio("Select Mode", ["Full Document Generator", "Diagram Live Editor"], 
                        captions=["Generate complete specs", "Visualize flows instantly"])
    
    selected_type = ""
    if app_mode == "Full Document Generator":
        selected_type = st.selectbox("Document Type", ["Proposal", "BRD", "SRS", "TRD", "HLD", "API Docs", "UAT Plan"])
    else:
        selected_type = st.selectbox("Diagram Type", ["Flowchart", "Sequence", "ERD", "Gantt", "State", "Class", "User Journey"])

# --- MAIN UI ---
st.markdown(f"""
    <div style="text-align: center; padding: 40px 0;">
        <h1 class="main-title">Metamorphosis Architect</h1>
        <p class="subtitle">Professional ERP Documentation & Diagram Generator</p>
    </div>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "mermaid_code" not in st.session_state:
    st.session_state.mermaid_code = """graph TD;
    A["Start"] --> B["Process"];
    B --> C["End"];"""

if "doc_content" not in st.session_state:
    st.session_state.doc_content = ""

if "client_scenario" not in st.session_state:
    st.session_state.client_scenario = ""

# --- APPLICATION LOGIC ---

# 1. INPUT SECTION (Shared)
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown(f"### 🎯 {selected_type} Requirements")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Describe your requirements in detail or use the **Refine** tool to optimize your prompt.")
with col2:
    # Refine Button Logic
    if st.button("✨ Refine Prompt", type="secondary", help="Use AI to improve your prompt for better results"):
        if not api_key:
            st.error("API Key required for refinement.")
        elif not st.session_state.client_scenario:
            st.warning("Please enter a draft prompt first.")
        else:
            with st.spinner("Optimizing prompt..."):
                genai.configure(api_key=api_key)
                refined = refine_prompt(st.session_state.client_scenario, selected_type)
                st.session_state.client_scenario = refined
                st.rerun()

# Text Area bound to session state
st.session_state.client_scenario = st.text_area(
    "Input Scenario", 
    value=st.session_state.client_scenario,
    height=150,
    placeholder="E.g., Create a sales process flow for a retail store using Odoo..."
)
st.markdown('</div>', unsafe_allow_html=True)


# 2. GENERATION SECTION
if app_mode == "Diagram Live Editor":
    col_gen, col_preview = st.columns([1, 2])
    
    with col_gen:
        if st.button(f"🚀 Generate {selected_type}", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please provide API Key.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=get_system_instruction(app_mode, selected_type))
                    with st.spinner("Architecting diagram..."):
                        response = model.generate_content(f"SCENARIO: {st.session_state.client_scenario}")
                        clean_code = sanitize_mermaid_code(response.text)
                        st.session_state.mermaid_code = clean_code
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("---")
        # Open in Mermaid Live
        live_url = generate_mermaid_link(st.session_state.mermaid_code)
        st.link_button("🔗 Open in Mermaid.live", live_url, use_container_width=True)
        
        with st.expander("View Source Code"):
            st.code(st.session_state.mermaid_code, language="mermaid")

    with col_preview:
        st.markdown('<div class="mermaid-container">', unsafe_allow_html=True)
        st.markdown("#### Visual Preview")
        try:
            st.markdown(f"```mermaid\n{st.session_state.mermaid_code}\n```")
        except Exception:
            st.error("Syntax Error in Mermaid Code")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # Full Document Generator
    if st.button(f"🚀 Generate {selected_type}", type="primary"):
        if not api_key:
            st.error("Missing API Key")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=get_system_instruction(app_mode, selected_type))
                with st.spinner("Drafting comprehensive document..."):
                    response = model.generate_content(f"SCENARIO: {st.session_state.client_scenario}")
                    st.session_state.doc_content = response.text
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.doc_content:
        st.markdown(f"""<div class="document-container"><h2>{selected_type}</h2>{st.session_state.doc_content}</div>""", unsafe_allow_html=True)
        
        st.download_button(
            label="📥 Download Document",
            data=st.session_state.doc_content,
            file_name=f"{selected_type}_Metamorphosis.md",
            mime="text/markdown"
        )

# --- FOOTER ---
st.markdown(
    f"""
    <div style='margin-top: 50px; text-align: center; color: #94A3B8; font-size: 12px; padding: 20px;'>
        Powered by Google Gemini 2.5 | Metamorphosis Systems Internal Tool
    </div>
    """, 
    unsafe_allow_html=True
)

