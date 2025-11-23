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
    initial_sidebar_state="expanded"
)

# --- THEME CONFIGURATION ---
THEME = {
    "primary": "#F97316",  # Vibrant Orange
    "primary_gradient": "linear-gradient(135deg, #F97316 0%, #FB923C 100%)",
    "secondary": "#FFF7ED", # Orange-50
    "bg": "#F8FAFC",        # Slate-50
    "surface": "#FFFFFF",
    "text": "#1E293B",      # Slate-800
    "text_light": "#64748B", # Slate-500
    "border": "#E2E8F0",    # Slate-200
    "glass": "rgba(255, 255, 255, 0.9)",
    "glass_shadow": "0 8px 32px 0 rgba(31, 38, 135, 0.07)"
}

# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400&display=swap');

    /* BASE STYLES */
    .stApp {{
        background-color: {THEME['bg']};
        font-family: 'Outfit', sans-serif;
        color: {THEME['text']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: {THEME['text']};
    }}
    
    code, pre, .stCodeBlock {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* SIDEBAR */
    [data-testid="stSidebar"] {{
        background-color: {THEME['surface']} !important;
        border-right: 1px solid {THEME['border']};
    }}
    
    /* NAVIGATION STYLING */
    .nav-header {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {THEME['text_light']};
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }}

    /* CARDS & CONTAINERS */
    .glass-card {{
        background: {THEME['glass']};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {THEME['border']};
        border-radius: 20px;
        padding: 2rem;
        box-shadow: {THEME['glass_shadow']};
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .glass-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
    }}

    /* BUTTONS */
    div.stButton > button {{
        background: {THEME['primary_gradient']} !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.25) !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(249, 115, 22, 0.35) !important;
    }}
    div.stButton > button:active {{
        transform: translateY(0);
    }}

    /* SECONDARY BUTTONS */
    button[kind="secondary"] {{
        background: white !important;
        color: {THEME['primary']} !important;
        border: 1px solid {THEME['primary']} !important;
    }}

    /* INPUTS */
    .stTextArea textarea, .stTextInput input {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: white !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        transition: border-color 0.2s ease;
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 3px {THEME['secondary']} !important;
    }}

    /* ALERTS */
    div[data-baseweb="notification"] {{
        border-radius: 12px !important;
    }}
    
    /* CUSTOM HERO */
    .hero-title {{
        background: {THEME['primary_gradient']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
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
    """
    Strictly validates Mermaid code against common syntax errors.
    Returns (is_valid, error_message)
    """
    # 1. Check for unquoted labels with special characters
    # Pattern: id[Label with spaces] -> Bad
    # Pattern: id["Label with spaces"] -> Good
    
    # This regex looks for node definitions like A[Content] where Content contains spaces/special chars but isn't quoted
    # It's a heuristic, not a full parser.
    lines = code.split('\n')
    for i, line in enumerate(lines):
        # Check for node IDs that are not alphanumeric (e.g., "Node A")
        # Matches "Node A[" or "Node-A["
        bad_id_match = re.search(r'^(\s*)([a-zA-Z0-9_]*[^a-zA-Z0-9_\s\[]+[a-zA-Z0-9_]*)\s*\[', line)
        if bad_id_match:
             return False, f"Line {i+1}: Node ID '{bad_id_match.group(2)}' contains invalid characters. Use alphanumeric and underscores only."

        # Check for unquoted labels
        # Look for [text] where text has spaces and no quotes
        # This is tricky, but we can check if it starts with "
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

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🦋</div>
            <h3 style="margin:0; font-size: 1.25rem;">Metamorphosis</h3>
            <p style="font-size: 0.8rem; color: {THEME['text_light']};">Architect Suite v3.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="nav-header">Workspace</p>', unsafe_allow_html=True)
    
    # Custom Radio Styling via CSS is hard, so we use standard radio but clean
    selected_page = st.radio(
        "Navigate",
        ["Home", "Prompt Rewriter", "Diagram Architect", "Document Scribe"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown('<p class="nav-header">Settings</p>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", help="Required for AI features")
    
    if not api_key:
        st.warning("⚠️ API Key missing")

# --- PAGE: HOME ---
if selected_page == "Home":
    st.markdown(f"""
        <div style="text-align: center; padding: 4rem 0;">
            <h1 class="hero-title">Welcome to the Architect</h1>
            <p style="font-size: 1.25rem; color: {THEME['text_light']}; max-width: 600px; margin: 0 auto;">
                The all-in-one suite for Metamorphosis Systems to design, document, and visualize ERP solutions with precision.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="glass-card" style="height: 100%;">
                <h3>✨ Prompt Rewriter</h3>
                <p style="color: {THEME['text_light']};">Turn messy thoughts into precise, engineer-grade prompts for maximum AI accuracy.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="glass-card" style="height: 100%;">
                <h3>📊 Diagram Architect</h3>
                <p style="color: {THEME['text_light']};">Generate error-free Mermaid.js diagrams. Strict syntax enforcement ensures compatibility.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="glass-card" style="height: 100%;">
                <h3>📝 Document Scribe</h3>
                <p style="color: {THEME['text_light']};">Draft comprehensive BRDs, SRSs, and Technical Specs in seconds.</p>
            </div>
        """, unsafe_allow_html=True)

# --- PAGE: PROMPT REWRITER ---
elif selected_page == "Prompt Rewriter":
    st.markdown("## ✨ Prompt Rewriter")
    st.markdown("Transform vague ideas into high-fidelity prompts for the Architect or Scribe.")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("### 📥 Messy Input")
        raw_prompt = st.text_area("Dump your thoughts here...", height=300, placeholder="e.g., i need a login flow for odoo where user forgets password and gets email...")
        
        if st.button("Rewrite & Optimize", type="primary"):
            if not api_key:
                st.error("Please provide an API Key in the sidebar.")
            elif not raw_prompt:
                st.warning("Please enter some text to rewrite.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    
                    system_prompt = """
                    ROLE: Expert Prompt Engineer for ERP Systems.
                    GOAL: Rewrite the user's raw input into a structured, highly detailed prompt optimized for LLM generation.
                    
                    OUTPUT FORMAT:
                    1. **Optimized Prompt**: The exact text the user should copy.
                    2. **Explanation**: Brief bullet points on what was improved.
                    
                    RULES:
                    - Add missing technical context (Odoo specific modules, standard ERP flows).
                    - Use clear sections (Objective, Actors, Steps, Constraints).
                    - Tone: Professional and Technical.
                    """
                    
                    with st.spinner("Analyzing and restructuring..."):
                        response = model.generate_content(f"{system_prompt}\n\nUSER INPUT: {raw_prompt}")
                        st.session_state.rewritten_result = response.text
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_output:
        st.markdown("### 📤 Optimized Result")
        if "rewritten_result" in st.session_state:
            st.markdown(f"""
                <div class="glass-card">
                    {st.session_state.rewritten_result}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("The optimized prompt will appear here.")

# --- PAGE: DIAGRAM ARCHITECT ---
elif selected_page == "Diagram Architect":
    st.markdown("## 📊 Diagram Architect")
    st.markdown("Generate strict, error-free Mermaid.js diagrams.")
    
    diagram_type = st.selectbox("Diagram Type", ["Flowchart (TD)", "Sequence Diagram", "ER Diagram", "State Diagram", "Gantt Chart"])
    
    diagram_prompt = st.text_area("Diagram Requirements (Paste optimized prompt here)", height=150)
    
    if st.button("Generate Diagram", type="primary"):
        if not api_key:
            st.error("Please provide an API Key.")
        else:
            try:
                genai.configure(api_key=api_key)
                
                # STRICT SYSTEM PROMPT
                system_instruction = f"""
                ROLE: Senior Solutions Architect.
                GOAL: Generate a valid Mermaid.js {diagram_type} code block.
                
                *** CRITICAL SYNTAX RULES (STRICT ENFORCEMENT) ***
                1. **NODE IDs**: MUST be alphanumeric + underscores ONLY. NO spaces, hyphens, or special chars.
                   - BAD: `Node A`, `user-login`
                   - GOOD: `NodeA`, `User_Login`
                2. **LABELS**: MUST be double-quoted if they contain spaces or special chars.
                   - BAD: `A[User Login]`
                   - GOOD: `A["User Login"]`
                3. **DIRECTION**: Use `graph TD` for flowcharts.
                4. **OUTPUT**: ONLY the code block. No text before or after.
                """
                
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
                
                with st.spinner("Architecting..."):
                    response = model.generate_content(f"REQUIREMENTS: {diagram_prompt}")
                    clean_code = sanitize_mermaid_code(response.text)
                    
                    # Validate
                    is_valid, msg = validate_mermaid_code(clean_code)
                    
                    if is_valid:
                        st.session_state.generated_mermaid = clean_code
                        st.success("Generation Successful & Validated!")
                    else:
                        st.session_state.generated_mermaid = clean_code
                        st.warning(f"⚠️ Potential Syntax Issue Detected: {msg}")
                        
            except Exception as e:
                st.error(f"Error: {e}")

    if "generated_mermaid" in st.session_state:
        st.markdown("### Preview")
        
        col_preview, col_code = st.columns([2, 1])
        
        with col_preview:
            st.markdown(f"""
                <div class="glass-card" style="text-align: center; background: white;">
                    <br>
                    <pre class="mermaid">
{st.session_state.generated_mermaid}
                    </pre>
                </div>
            """, unsafe_allow_html=True)
            
            # Load Mermaid JS
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
                height=500,
                scrolling=True
            )

        with col_code:
            st.markdown("### Source Code")
            st.code(st.session_state.generated_mermaid, language="mermaid")
            
            live_url = generate_mermaid_link(st.session_state.generated_mermaid)
            st.link_button("🚀 Open in Mermaid.live", live_url, use_container_width=True)

# --- PAGE: DOCUMENT SCRIBE ---
elif selected_page == "Document Scribe":
    st.markdown("## 📝 Document Scribe")
    st.markdown("Generate professional documentation.")
    
    doc_type = st.selectbox("Document Type", ["Business Requirement Doc (BRD)", "Technical Design Doc (TDD)", "API Specification", "User Manual"])
    doc_prompt = st.text_area("Project Details", height=200)
    
    if st.button("Draft Document", type="primary"):
        if not api_key:
            st.error("Please provide an API Key.")
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
        st.download_button("📥 Download Markdown", st.session_state.generated_doc, "document.md")
        st.markdown(f"""
            <div class="glass-card" style="background: white;">
                {st.session_state.generated_doc}
            </div>
        """, unsafe_allow_html=True)


