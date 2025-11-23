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

# --- THEME CONFIGURATION (Standard Modern - Indigo/Slate) ---
THEME = {
    "primary": "#4F46E5",       # Indigo-600
    "primary_hover": "#4338CA", # Indigo-700
    "bg": "#F3F4F6",            # Gray-100 (App Background)
    "surface": "#FFFFFF",       # White (Card Background)
    "text_main": "#111827",     # Gray-900
    "text_secondary": "#6B7280",# Gray-500
    "border": "#E5E7EB",        # Gray-200
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap');

    /* BASE RESET */
    .stApp {{
        background-color: {THEME['bg']};
        font-family: 'Inter', sans-serif;
        color: {THEME['text_main']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: {THEME['text_main']};
    }}
    
    p, li, label, .stMarkdown {{
        color: {THEME['text_secondary']};
        font-size: 0.95rem;
        line-height: 1.5;
    }}

    /* HEADER NAVIGATION */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
        background-color: {THEME['surface']};
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 2rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 2.5rem;
        white-space: nowrap;
        background-color: transparent;
        border: none;
        color: {THEME['text_secondary']};
        font-weight: 500;
        font-size: 0.95rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {THEME['primary']} !important;
        font-weight: 600;
        border-bottom: 2px solid {THEME['primary']} !important;
    }}

    /* CARDS */
    .feature-card {{
        background-color: {THEME['surface']};
        border: 1px solid {THEME['border']};
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        height: 100%;
    }}

    /* INPUTS */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        background-color: {THEME['surface']} !important;
        color: {THEME['text_main']} !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important; /* Indigo ring */
    }}

    /* BUTTONS */
    div.stButton > button {{
        background-color: {THEME['primary']} !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.25rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        transition: background-color 0.15s ease !important;
    }}
    div.stButton > button:hover {{
        background-color: {THEME['primary_hover']} !important;
    }}

    /* APP HEADER */
    .app-header {{
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
    }}
    .logo {{
        font-size: 1.5rem;
        margin-right: 0.75rem;
        background: {THEME['surface']};
        padding: 0.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid {THEME['border']};
    }}
    .app-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {THEME['text_main']};
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
        <div>
            <h1 class="app-title">Metamorphosis Architect</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.markdown("### Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI features")
    if not api_key:
        st.warning("⚠️ API Key missing")
    st.markdown("---")
    st.caption("v4.0.0 (Standard Modern)")

# --- TOP NAVIGATION ---
tab_home, tab_rewriter, tab_diagram, tab_docs = st.tabs([
    "Dashboard", 
    "Prompt Refiner", 
    "Diagrams", 
    "Documents"
])

# --- TAB: DASHBOARD ---
with tab_home:
    st.markdown("### Dashboard")
    st.markdown("Select a tool to begin.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="feature-card">
                <h4>✨ Prompt Refiner</h4>
                <p>General-purpose prompt engineering tool. Improves clarity and structure for any request.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="feature-card">
                <h4>📊 Diagrams</h4>
                <p>Generate strict Mermaid.js diagrams. Visualizes flows, sequences, and ERDs.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="feature-card">
                <h4>📝 Documents</h4>
                <p>Draft professional technical documentation and specifications.</p>
            </div>
        """, unsafe_allow_html=True)

# --- TAB: PROMPT REFINER (GENERIC) ---
with tab_rewriter:
    st.markdown("### ✨ Generic Prompt Refiner")
    st.markdown("Refine any prompt for better AI performance. Not limited to ERPs.")
    
    col_rw_1, col_rw_2 = st.columns([1, 1])
    
    with col_rw_1:
        context_type = st.text_input("Context (Optional)", placeholder="e.g. Coding, Creative Writing, Business...")
        raw_prompt = st.text_area("Your Draft", height=250, placeholder="Type your rough idea here...")
        
        if st.button("Refine Prompt", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key required.")
            elif not raw_prompt:
                st.warning("Please enter a draft.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    
                    # GENERIC SYSTEM PROMPT
                    system_prompt = """
                    ROLE: Expert Prompt Engineer.
                    GOAL: Rewrite the user's raw input into a structured, highly effective prompt for an LLM.
                    
                    INSTRUCTIONS:
                    1. Analyze the user's intent.
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
        st.markdown("#### Refined Output")
        if "rewritten_result" in st.session_state:
            st.text_area("Copy this:", value=st.session_state.rewritten_result, height=320)
        else:
            st.info("Your refined prompt will appear here.")

# --- TAB: DIAGRAMS ---
with tab_diagram:
    st.markdown("### 📊 Diagram Generator")
    
    col_d_input, col_d_preview = st.columns([1, 2])
    
    with col_d_input:
        diagram_type = st.selectbox("Type", ["Flowchart (TD)", "Sequence Diagram", "ER Diagram", "State Diagram", "Gantt Chart"])
        diagram_prompt = st.text_area("Requirements", height=200, placeholder="Paste your refined prompt here...")
        
        if st.button("Generate", type="primary", use_container_width=True):
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

# --- TAB: DOCUMENTS ---
with tab_docs:
    st.markdown("### 📝 Document Generator")
    
    doc_type = st.selectbox("Type", ["Business Requirement Doc (BRD)", "Technical Design Doc (TDD)", "API Specification"])
    doc_prompt = st.text_area("Details", height=150, placeholder="Describe the project...")
    
    if st.button("Generate Document", type="primary"):
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

    if "generated_doc" in st.session_state:
        st.markdown("---")
        st.download_button("Download Markdown", st.session_state.generated_doc, "document.md")
        st.markdown(st.session_state.generated_doc)


