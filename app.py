import streamlit as st
import google.generativeai as genai
from datetime import datetime

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
    }}
    .stTextArea textarea:focus {{
        border-color: {PRIMARY_COLOR} !important;
        box-shadow: 0 0 0 2px {SECONDARY_COLOR} !important;
    }}
    
    /* Selectbox & Radio styling */
    div[data-baseweb="select"] > div, div[data-baseweb="radio"] {{
        border-radius: 8px !important;
        background-color: {WHITE} !important;
        border: 1px solid #E0E0E0 !important;
        color: {ACCENT_COLOR} !important;
    }}
    /* Ensure dropdown options are visible */
    div[data-baseweb="popover"] li {{
        color: {ACCENT_COLOR} !important; 
    }}
    div[data-baseweb="select"] span {{
        color: {ACCENT_COLOR} !important;
    }}
    
    /* Radio button text color */
    div[role="radiogroup"] label p {{
        color: {ACCENT_COLOR} !important;
    }}

    /* --- BUTTONS --- */
    /* Target both regular buttons and download buttons */
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
    
    /* Text styles inside the document container */
    .stMarkdown p, .stWrite p, div[data-testid="stMarkdownContainer"] p, 
    .stMarkdown li, .stWrite li, div[data-testid="stMarkdownContainer"] li {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 18px !important;
        line-height: 1.8 !important;
        color: #000000 !important; /* Pure black for document text */
    }}
    
    /* Headers inside the document */
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

# --- COMPANY CONTEXT (THE KNOWLEDGE BASE) ---
METAMORPHOSIS_CONTEXT = """
COMPANY PROFILE: Metamorphosis Systems (Metamorphosis Ltd.)
STATUS: #1 Leading Odoo Silver Partner in Bangladesh.
ESTABLISHED: 2016.
EXPERIENCE: 8+ years, Projects in BD, NZ, Saudi Arabia, South Sudan.

CORE SERVICES:
1. Odoo ERP Implementation (Analysis, Config, Migration, Training).
2. Odoo Customization & Module Dev.
3. Consultancy (Business Analysis, Finance).
4. Native Mobile App Dev (iOS/Android synced with Odoo).
5. Custom Web Development.

REFERENCE CLIENTS:
- Manufacturing: Alauddin Textile Mills, Hasan Rubber, Skydragos (Denim).
- Retail: Bangladesh Armed Services Board, Agami Ltd.
- FMCG: Grameen Danone, Jabed Agro.
- NGO: Friendship NGO.

METHODOLOGY (6 Stages):
1. Free Consultation -> 2. Global Estimate -> 3. Deep Analysis -> 4. Estimate/Timeline -> 5. Implementation -> 6. Go Live.
"""

# --- PROMPT ENGINEERING FUNCTIONS ---
def get_system_instruction(mode, selected_type):
    """Returns the specific persona and structure based on mode and type."""
    
    base_role = f"""
    ROLE: You are the Senior Solutions Architect for Metamorphosis Ltd.
    CONTEXT: {METAMORPHOSIS_CONTEXT}
    TONE: Professional, Corporate, Industry-Standard.
    
    CRITICAL MERMAID SYNTAX RULES (VERY STRICT):
    1. **NO SPACES IN NODE IDs**: `Node A` is ILLEGAL. Use `NodeA` or `Node_A`.
    2. **QUOTES FOR LABELS**: If a label contains spaces or special characters (like parens), you MUST use double quotes.
       - WRONG: `A[Production (Work Centers)]`
       - RIGHT: `A["Production (Work Centers)"]`
    3. **AVOID SPECIAL CHARACTERS IN IDs**: Do not use `(`, `)`, `/`, or `-` inside the ID itself.
    4. **VALIDATION**: Before outputting, check: Did I use quotes for text? Did I remove spaces from IDs?
    """

    # --- LOGIC FOR DIAGRAM ONLY MODE ---
    if mode == "Diagram Generator":
        return base_role + f"""
        GOAL: Generate a {selected_type} using MermaidJS syntax based on the user's description.
        OUTPUT FORMAT:
        - Provide a brief title (H2).
        - Provide the Mermaid code block.
        - Keep explanations minimal.
        
        SPECIFIC DIAGRAM INSTRUCTIONS:
        - If Flowchart: Use `graph TD` or `graph LR`.
        - If Sequence: Use `sequenceDiagram`.
        - If ERD: Use `erDiagram`.
        - If Gantt: Use `gantt`.
        - If Class: Use `classDiagram`.
        - If State: Use `stateDiagram-v2`.
        """

    # --- LOGIC FOR FULL DOCUMENT MODE ---
    # Base formatting for documents
    base_role += """
    FORMATTING: 
    - Use Markdown for structure.
    - For any diagrams, charts, or flows, you MUST use a `mermaid` code block.
    """

    if selected_type == "Proposal":
        return base_role + """
        GOAL: Create a Sales Proposal.
        STRUCTURE:
        1. Executive Summary
        2. Understanding of Requirements (Pain Points)
        3. Proposed Solution (Odoo Modules Mapping) - **Include a high-level Mermaid flowchart (graph TD) of the proposed modules.**
        4. Metamorphosis Advantage (Why Us?)
        5. Relevant Case Studies
        6. Implementation Methodology (The 6 Stages) - **Include a simple Mermaid Gantt chart for the timeline.**
        7. Investment & Timeline (Estimate)
        """
    
    elif selected_type == "BRD (Business Req Doc)":
        return base_role + """
        GOAL: Create a Business Requirement Document (BRD).
        STRUCTURE:
        1. Project Background
        2. Business Objectives (SMART goals)
        3. Stakeholders Analysis
        4. In-Scope vs. Out-of-Scope
        5. Current Process (As-Is) vs. Proposed Process (To-Be) - **Use two separate Mermaid flowcharts (graph TD) to illustrate these processes.**
        6. Business Risks
        """

    elif selected_type == "SRS (Software Req Spec)":
        return base_role + """
        GOAL: Create a Software Requirements Specification (SRS).
        STRUCTURE:
        1. Introduction
        2. Functional Requirements (Detailed Features, User Stories)
        3. System Architecture - **Include a high-level Mermaid component diagram (graph TD).**
        4. Non-Functional Requirements
        5. System Interfaces
        6. User Roles & Permissions
        """

    elif selected_type == "TRD (Technical Req Doc)":
        return base_role + """
        GOAL: Create a Technical Requirements Document (TRD).
        STRUCTURE:
        1. System Architecture - **Include a detailed Mermaid deployment diagram.**
        2. Database Design - **Include a Mermaid Entity-Relationship Diagram (ERD) for key modules (erDiagram).**
        3. Tech Stack
        4. Integration Details - **Include a Mermaid sequence diagram (sequenceDiagram) for a key API interaction.**
        5. Security Protocols
        6. Server Specifications
        """

    elif selected_type == "HLD (High-Level Design)":
        return base_role + """
        GOAL: Create a High-Level Design (HLD) document.
        STRUCTURE:
        1. Architectural Overview - **Include a Mermaid high-level system architecture diagram.**
        2. Component Diagram - **Include a Mermaid diagram showing Odoo modules and their interactions.**
        3. Data Flow Diagrams (DFD) - **Include a Mermaid flowchart illustrating the flow of data.**
        4. Technology Dependencies
        5. Deployment Strategy
        """
        
    elif selected_type == "API Documentation":
        return base_role + """
        GOAL: Create API Documentation for custom Odoo endpoints.
        STRUCTURE:
        1. Authentication (XML-RPC / JSON-RPC)
        2. Base URL & Environment
        3. Authentication Flow - **Include a Mermaid sequence diagram (sequenceDiagram).**
        4. Endpoints (List specific endpoints)
           - Method (GET/POST)
           - Payload Params
           - Success Response (JSON)
           - Error Codes
        """

    elif selected_type == "UAT Plan (Test Plan)":
        return base_role + """
        GOAL: Create a User Acceptance Testing (UAT) Plan.
        STRUCTURE:
        1. Introduction & Testing Scope
        2. Test Environment Setup
        3. Roles & Responsibilities
        4. Testing Workflow - **Include a Mermaid flowchart (graph TD) of the defect reporting process.**
        5. Test Cases (Table format)
        6. Sign-off Criteria
        """

    return base_role

# --- SIDEBAR UI ---
with st.sidebar:
    # Branding Header
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: {PRIMARY_COLOR}; font-size: 28px; margin-bottom: 0;">🦋</h1>
            <h2 style="color: {ACCENT_COLOR}; font-size: 20px; font-weight: 700; margin-top: 5px;">Metamorphosis</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🛠️ Configuration")
    
    api_key = st.text_input("🔑 Gemini API Key", type="password", help="Get this from Google AI Studio")
    
    st.markdown("---")
    
    # Mode Selection
    app_mode = st.radio("Select Mode", ["Full Document Generator", "Diagram Generator"])
    
    selected_type = ""
    
    if app_mode == "Full Document Generator":
        selected_type = st.selectbox(
            "📄 Document Type",
            [
                "Proposal",
                "BRD (Business Req Doc)",
                "SRS (Software Req Spec)",
                "TRD (Technical Req Doc)",
                "HLD (High-Level Design)",
                "API Documentation",
                "UAT Plan (Test Plan)"
            ]
        )
        st.info(f"Generating comprehensive **{selected_type}**.")
        
    else:
        selected_type = st.selectbox(
            "📊 Diagram Type",
            [
                "Flowchart (Process Flow)",
                "Sequence Diagram (Interactions)",
                "ERD (Entity Relationship)",
                "Gantt Chart (Timeline)",
                "State Diagram (Status)",
                "Class Diagram (Structure)",
                "User Journey (Experience)"
            ]
        )
        st.info(f"Generating specific **{selected_type}** in MermaidJS.")

# --- MAIN UI ---
# Main Header
st.markdown(f"""
    <div style="padding: 20px 0; text-align: center;">
        <h1 class="main-title" style="font-size: 42px; margin-bottom: 10px;">Metamorphosis Architect</h1>
        <p style="color: {ACCENT_COLOR}; font-size: 18px; opacity: 0.8;">
            Professional ERP Documentation & Diagram Generator
        </p>
    </div>
    """, unsafe_allow_html=True)

# Scenario Input Card
st.markdown(f"### 📝 {app_mode.split()[0]} Requirements")
client_scenario = st.text_area(
    "Enter details here...",
    height=150,
    placeholder="e.g. A sales approval process where Manager approves orders > $5000...",
    label_visibility="collapsed"
)

# Action Button centered
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    btn_label = f"🚀 Generate {selected_type.split()[0]}"
    generate_btn = st.button(btn_label, type="primary", use_container_width=True)

# --- GENERATION LOGIC ---
if generate_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not client_scenario:
        st.warning("Please describe the scenario first.")
    else:
        try:
            # Configure API
            genai.configure(api_key=api_key)
            
            # Setup Model
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=get_system_instruction(app_mode, selected_type)
            )

            # UI Feedback
            with st.spinner(f"Architecting your {selected_type}... Please wait..."):
                # Generate
                response = model.generate_content(f"SCENARIO: {client_scenario}")
                doc_content = response.text

            # Display Result
            st.success("✅ Generated Successfully!")
            
            # Document Container
            st.markdown(f"""<div class="document-container">""", unsafe_allow_html=True)
            
            # Render Title
            st.markdown(f"## {selected_type}")
            
            # Render Content with Mermaid Diagrams
            st.markdown(doc_content, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

            # Download Section
            st.markdown("<br>", unsafe_allow_html=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{selected_type.split()[0]}_Metamorphosis_{timestamp}.md"
            
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.download_button(
                    label="📥 Download Output (.md)",
                    data=doc_content,
                    file_name=filename,
                    mime="text/markdown",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- FOOTER ---
st.markdown(
    f"""
    <div style='position: fixed; bottom: 0; left: 0; width: 100%; text-align: center; color: #888; font-size: 12px; padding: 15px; background-color: {WHITE}; border-top: 1px solid #EEE; z-index: 100;'>
        Powered by Google Gemini 2.5 | Metamorphosis Systems Internal Tool | 
        <a href="https://mermaid.live/" target="_blank" style="color: {PRIMARY_COLOR}; text-decoration: none;">
            Open Mermaid Live Editor ↗
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)
