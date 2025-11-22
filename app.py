import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide"
)

# --- BRAND COLORS ---
# Derived from the Metamorphosis logo
PRIMARY_COLOR = "#002F55"  # Dark Blue
SECONDARY_COLOR = "#70D0C6" # Light Teal
BACKGROUND_COLOR = "#FFFFFF" # White
TEXT_COLOR = "#000000"       # Black

# --- CUSTOM CSS FOR BRANDING & DOCUMENTS ---
st.markdown(f"""
    <style>
    /* --- General App Styling --- */
    /* Main Title and Headers */
    h1, h2, h3, h4, h5, h6, span[data-testid="stHeader"] {{
        color: {PRIMARY_COLOR} !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: #f0f6f9 !important; /* A very light tint of the teal */
        border-right: 2px solid {SECONDARY_COLOR};
    }}
    
    /* Buttons */
    div.stButton > button {{
        background-color: {PRIMARY_COLOR} !important;
        color: {BACKGROUND_COLOR} !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
    }}
    div.stButton > button:hover {{
        background-color: {SECONDARY_COLOR} !important;
        color: {PRIMARY_COLOR} !important;
    }}

    /* --- Document Content Styling (Times New Roman) --- */
    /* Target the main markdown output */
    .stMarkdown p, .stWrite p, div[data-testid="stMarkdownContainer"] p, 
    .stMarkdown li, .stWrite li, div[data-testid="stMarkdownContainer"] li {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 18px !important;
        line-height: 1.6 !important;
        color: {TEXT_COLOR} !important;
    }}
    
    /* Headers within the generated document */
    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2, 
    div[data-testid="stMarkdownContainer"] h3 {{
        font-family: 'Times New Roman', Times, serif !important;
        color: {PRIMARY_COLOR} !important;
        margin-top: 1.5em !important;
    }}

    /* --- Mermaid Diagram Styling --- */
    .mermaid {{
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 20px 0;
        font-family: 'Times New Roman', Times, serif !important;
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
def get_system_instruction(doc_type):
    """Returns the specific persona and structure based on doc type."""
    
    base_role = f"""
    ROLE: You are the Senior Solutions Architect and Lead Technical Writer for Metamorphosis Ltd.
    CONTEXT: {METAMORPHOSIS_CONTEXT}
    TONE: Professional, Corporate, Industry-Standard.
    FORMATTING: 
    - Use Markdown for structure.
    - For any diagrams, charts, or flows, you MUST use a `mermaid` code block.
    - Example:
      ```mermaid
      graph TD;
          A-->B;
          A-->C;
          B-->D;
          C-->D;
      ```
    """

    if doc_type == "Proposal":
        return base_role + """
        GOAL: Create a Sales Proposal.
        STRUCTURE:
        1. Executive Summary
        2. Understanding of Requirements (Pain Points)
        3. Proposed Solution (Odoo Modules Mapping) - **Include a high-level Mermaid flowchart of the proposed modules.**
        4. Metamorphosis Advantage (Why Us?)
        5. Relevant Case Studies
        6. Implementation Methodology (The 6 Stages) - **Include a simple Mermaid Gantt chart for the timeline.**
        7. Investment & Timeline (Estimate)
        """
    
    elif doc_type == "BRD (Business Req Doc)":
        return base_role + """
        GOAL: Create a Business Requirement Document (BRD).
        FOCUS: Business goals, stakeholders, scope, and high-level constraints.
        STRUCTURE:
        1. Project Background
        2. Business Objectives (SMART goals)
        3. Stakeholders Analysis
        4. In-Scope vs. Out-of-Scope
        5. Current Process (As-Is) vs. Proposed Process (To-Be) - **Use two separate Mermaid flowcharts to illustrate these processes.**
        6. Business Risks
        """

    elif doc_type == "SRS (Software Req Spec)":
        return base_role + """
        GOAL: Create a Software Requirements Specification (SRS).
        FOCUS: Functional and Non-Functional requirements.
        STRUCTURE:
        1. Introduction
        2. Functional Requirements (Detailed Features, User Stories)
        3. System Architecture - **Include a high-level Mermaid component diagram.**
        4. Non-Functional Requirements (Performance, Security, Reliability)
        5. System Interfaces (Odoo API, External Hardware)
        6. User Roles & Permissions
        """

    elif doc_type == "TRD (Technical Req Doc)":
        return base_role + """
        GOAL: Create a Technical Requirements Document (TRD).
        FOCUS: Technology stack, Odoo architecture, Server specs.
        STRUCTURE:
        1. System Architecture (Odoo.sh / On-premise) - **Include a detailed Mermaid deployment diagram.**
        2. Database Design - **Include a Mermaid Entity-Relationship Diagram (ERD) for key modules.**
        3. Tech Stack (Python, XML, JS, PostgreSQL)
        4. Integration Details (API Endpoints) - **Include a Mermaid sequence diagram for a key API interaction.**
        5. Security Protocols (SSL, Access Control)
        6. Server Specifications
        """

    elif doc_type == "HLD (High-Level Design)":
        return base_role + """
        GOAL: Create a High-Level Design (HLD) document.
        FOCUS: System modularity, data flow, and architectural diagrams.
        STRUCTURE:
        1. Architectural Overview - **Include a Mermaid high-level system architecture diagram.**
        2. Component Diagram - **Include a Mermaid diagram showing Odoo modules and their interactions.**
        3. Data Flow Diagrams (DFD) - **Include a Mermaid flowchart illustrating the flow of data between major components (e.g., Sales -> Inventory -> Accounting).**
        4. Technology Dependencies
        5. Deployment Strategy
        """
        
    elif doc_type == "API Documentation":
        return base_role + """
        GOAL: Create API Documentation for custom Odoo endpoints.
        FOCUS: Endpoints, Methods, Request/Response examples.
        STRUCTURE:
        1. Authentication (XML-RPC / JSON-RPC)
        2. Base URL & Environment
        3. Authentication Flow - **Include a Mermaid sequence diagram showing how to authenticate and get a session token.**
        4. Endpoints (List specific endpoints relevant to the scenario)
           - Method (GET/POST)
           - Payload Params
           - Success Response (JSON)
           - Error Codes
        """

    elif doc_type == "UAT Plan (Test Plan)":
        return base_role + """
        GOAL: Create a User Acceptance Testing (UAT) Plan.
        FOCUS: Test cases, acceptance criteria, pass/fail conditions.
        STRUCTURE:
        1. Introduction & Testing Scope
        2. Test Environment Setup
        3. Roles & Responsibilities
        4. Testing Workflow - **Include a Mermaid flowchart of the defect reporting and resolution process.**
        5. Test Cases (Table format: ID, Scenario, Steps, Expected Result)
           - Include cases for Sales, Purchase, Inventory, Accounting.
        6. Sign-off Criteria
        """

    return base_role

# --- SIDEBAR UI ---
with st.sidebar:
    # Use the primary color for the logo text
    st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>Metamorphosis Architect</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: {SECONDARY_COLOR};'>Configuration</h3>", unsafe_allow_html=True)
    
    api_key = st.text_input("🔑 Google Gemini API Key", type="password", help="Get this from Google AI Studio")
    
    doc_type = st.selectbox(
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
    
    st.info(f"**Mode:** {doc_type}\n\nGenerates professional docs tailored for Odoo Implementation with Metamorphosis branding.")

# --- MAIN UI ---
# Use the primary color for the main title
st.markdown(f"<h1 style='color: {PRIMARY_COLOR}; text-align: center;'>🦋 Metamorphosis Document Architect</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color: {SECONDARY_COLOR}; text-align: center;'>Generate Professional ERP Documentation</h3>", unsafe_allow_html=True)

client_scenario = st.text_area(
    "📝 Client Scenario / Requirements",
    height=150,
    placeholder="Example: A textile manufacturing company in Narayanganj with 400 employees. They are facing issues with inventory tracking, wastage management, and syncing accounting with production. They need a full Odoo implementation."
)

# Use a container to center the button
with st.container():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button("🚀 Generate Document", type="primary", use_container_width=True)

# --- GENERATION LOGIC ---
if generate_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not client_scenario:
        st.warning("Please enter a client scenario.")
    else:
        try:
            # Configure API
            genai.configure(api_key=api_key)
            
            # Setup Model
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=get_system_instruction(doc_type)
            )

            # UI Feedback
            with st.spinner(f"Architecting your {doc_type}... this takes about 20-30 seconds..."):
                # Generate
                response = model.generate_content(f"CLIENT SCENARIO: {client_scenario}")
                doc_content = response.text

            # Display Result
            st.success("✅ Document Generated Successfully!")
            
            # Layout for title and content
            st.markdown("---")
            st.markdown(f"<h2 style='color: {PRIMARY_COLOR};'>{doc_type} for Client</h2>", unsafe_allow_html=True)
            
            # Render the content with Mermaid diagrams
            st.markdown(doc_content, unsafe_allow_html=True)
            
            st.markdown("---")

            # Download Button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{doc_type.split()[0]}_Metamorphosis_{timestamp}.md"
            
            # Use a container to center the download button
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Download Document (.md)",
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
    <div style='position: fixed; bottom: 0; width: 100%; text-align: center; color: {PRIMARY_COLOR}; font-size: 12px; padding: 10px; background-color: {BACKGROUND_COLOR}; border-top: 1px solid #e0e0e0;'>
        Powered by Google Gemini 2.0 | Metamorphosis Systems Internal Tool
    </div>
    """, 
    unsafe_allow_html=True
)
