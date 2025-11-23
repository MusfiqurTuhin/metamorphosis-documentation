import streamlit as st
import google.generativeai as genai
import re
import json
import base64
import zlib

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- THEME CONFIGURATION (Clean SaaS) ---
THEME = {
    "primary": "#EA580C",       # Orange-600 (High contrast, professional)
    "primary_hover": "#C2410C", # Orange-700
    "bg": "#FFFFFF",            # Pure White
    "secondary_bg": "#F8FAFC",  # Slate-50 (Subtle contrast)
    "text_main": "#0F172A",     # Slate-900 (Sharp text)
    "text_secondary": "#475569",# Slate-600 (Softer text)
    "border": "#E2E8F0",        # Slate-200
    "success": "#10B981",       # Emerald-500
    "error": "#EF4444",         # Red-500
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap');

    /* BASE RESET & TYPOGRAPHY */
    .stApp {{
        background-color: {THEME['bg']};
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: {THEME['text_main']};
    }}
    
    p, li, label, .stMarkdown {{
        color: {THEME['text_secondary']};
        font-size: 1rem;
        line-height: 1.6;
    }}

    /* TOP NAVIGATION (TABS) */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
        border-bottom: 1px solid {THEME['border']};
        padding-bottom: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 3rem;
        white-space: nowrap;
        background-color: transparent;
        border: none;
        color: {THEME['text_secondary']};
        font-weight: 500;
        font-size: 1rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {THEME['primary']} !important;
        border-bottom: 2px solid {THEME['primary']} !important;
    }}

    /* CARDS & CONTAINERS */
    .feature-card {{
        background-color: {THEME['bg']};
        border: 1px solid {THEME['border']};
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: box-shadow 0.2s ease;
        height: 100%;
    }}
    .feature-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
    }}

    /* INPUTS */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        background-color: {THEME['bg']} !important;
        color: {THEME['text_main']} !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.2) !important; /* Orange ring */
    }}

    /* BUTTONS */
    div.stButton > button {{
        background-color: {THEME['primary']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
        transition: background-color 0.15s ease !important;
    }}
    div.stButton > button:hover {{
        background-color: {THEME['primary_hover']} !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }}

    /* SECONDARY BUTTONS (Outline) */
    button[kind="secondary"] {{
        background-color: white !important;
        color: {THEME['text_main']} !important;
        border: 1px solid {THEME['border']} !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }}

    /* HEADER */
    .app-header {{
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid {THEME['border']};
    }}
    .logo {{
        font-size: 2rem;
        margin-right: 1rem;
    }}
    .app-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {THEME['text_main']};
        margin: 0;
    }}
    .app-subtitle {{
        font-size: 0.875rem;
        color: {THEME['text_secondary']};
        margin: 0;
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

def validate_mermaid_code(code):
    """Strictly validates Mermaid code against common syntax errors."""
    lines = code.split('\n')
    for i, line in enumerate(lines):
        # Check for node IDs that are not alphanumeric
        bad_id_match = re.search(r'^(\s*)([a-zA-Z0-9_]*[^a-zA-Z0-9_\s\[]+[a-zA-Z0-9_]*)\s*\[', line)
        if bad_id_match:
             return False, f"Line {i+1}: Node ID '{bad_id_match.group(2)}' contains invalid characters. Use alphanumeric and underscores only."

        # Check for unquoted labels
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
        <div>
            <h1 class="app-title">Metamorphosis Architect</h1>
            <p class="app-subtitle">Professional ERP Documentation Suite</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR (SETTINGS ONLY) ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI features")
    if not api_key:
        st.warning("⚠️ Please enter your API Key to use the tools.")
    
    st.markdown("---")
    st.markdown(f"""
        <div style="font-size: 0.75rem; color: {THEME['text_secondary']};">
            v3.1.0 (Human-Centric Build)<br>
            © Metamorphosis Systems
        </div>
    """, unsafe_allow_html=True)

# --- TOP NAVIGATION ---
tab_home, tab_rewriter, tab_diagram, tab_docs = st.tabs([
    "🏠 Dashboard", 
    "✨ Prompt Rewriter", 
    "📊 Diagram Architect", 
    "📝 Document Scribe"
])

# --- TAB: DASHBOARD ---
with tab_home:
    st.markdown("### Welcome Back")
    st.markdown("Select a tool from the tabs above to get started.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="feature-card">
                <h4>✨ Prompt Rewriter</h4>
                <p>Turn vague ideas into precise, engineer-grade prompts. Essential for getting the best results from AI.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="feature-card">
                <h4>📊 Diagram Architect</h4>
                <p>Create strict, error-free Mermaid.js diagrams. Visualizes flows, sequences, and ERDs instantly.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="feature-card">
                <h4>📝 Document Scribe</h4>
                <p>Draft comprehensive technical documentation (BRD, SRS, API Specs) with professional formatting.</p>
            </div>
        """, unsafe_allow_html=True)

# --- TAB: PROMPT REWRITER ---
with tab_rewriter:
    st.markdown("### ✨ Prompt Rewriter")
    st.markdown("Optimize your request before generating diagrams or documents.")
    
    col_rw_1, col_rw_2 = st.columns([1, 1])
    
    with col_rw_1:
        raw_prompt = st.text_area("Your Draft Idea", height=250, placeholder="e.g., I need a sales flow for Odoo where the manager approves orders over $500...")
        
        if st.button("Optimize Prompt", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key required.")
            elif not raw_prompt:
                st.warning("Please enter a draft.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    system_prompt = "ROLE: Expert Prompt Engineer. GOAL: Rewrite user input into a structured, detailed prompt for an ERP Architect AI. OUTPUT: Only the optimized prompt."
                    with st.spinner("Refining..."):
                        response = model.generate_content(f"{system_prompt}\n\nINPUT: {raw_prompt}")
                        st.session_state.rewritten_result = response.text
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_rw_2:
        st.markdown("#### Optimized Result")
        if "rewritten_result" in st.session_state:
            st.text_area("Copy this:", value=st.session_state.rewritten_result, height=250)
        else:
            st.info("Your optimized prompt will appear here.")

# --- TAB: DIAGRAM ARCHITECT ---
with tab_diagram:
    st.markdown("### 📊 Diagram Architect")
    
    col_d_input, col_d_preview = st.columns([1, 2])
    
    with col_d_input:
        diagram_type = st.selectbox("Diagram Type", ["Flowchart (TD)", "Sequence Diagram", "ER Diagram", "State Diagram", "Gantt Chart"])
        diagram_prompt = st.text_area("Diagram Requirements", height=200, placeholder="Paste your optimized prompt here...")
        
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
                    with st.spinner("Architecting..."):
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
        if "generated_mermaid" in st.session_state:
            st.markdown("#### Preview")
            st.components.v1.html(
                f"""
                <script type="module">
                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
                <div class="mermaid">
                    {st.session_state.generated_mermaid}
                </div>
                """,
                height=400,
                scrolling=True
            )
            
            with st.expander("View Code"):
                st.code(st.session_state.generated_mermaid, language="mermaid")
            
            live_url = generate_mermaid_link(st.session_state.generated_mermaid)
            st.link_button("Open in Mermaid.live", live_url)

# --- TAB: DOCUMENT SCRIBE ---
with tab_docs:
    st.markdown("### 📝 Document Scribe")
    
    doc_type = st.selectbox("Document Type", ["Business Requirement Doc (BRD)", "Technical Design Doc (TDD)", "API Specification"])
    doc_prompt = st.text_area("Project Details", height=150, placeholder="Describe the module or feature...")
    
    if st.button("Draft Document", type="primary"):
        if not api_key:
            st.error("API Key required.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                with st.spinner("Writing..."):
                    response = model.generate_content(f"Write a professional {doc_type} for: {doc_prompt}. Use Markdown.")
                    st.session_state.generated_doc = response.text
            except Exception as e:
                st.error(f"Error: {e}")

    if "generated_doc" in st.session_state:
        st.markdown("---")
        st.download_button("Download Markdown", st.session_state.generated_doc, "document.md")
        st.markdown(st.session_state.generated_doc)


