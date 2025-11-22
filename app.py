import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Architect",
    page_icon="🦋",
    layout="wide"
)

# --- CUSTOM CSS FOR TIMES NEW ROMAN & PAPER LOOK ---
st.markdown("""
    <style>
    /* Import Fonts if needed, but standard Times New Roman usually works natively */
    
    /* Target the main markdown output */
    .stMarkdown, .stWrite, div[data-testid="stMarkdownContainer"] p {
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 18px !important;
        line-height: 1.6 !important;
        color: #000000 !important;
    }
    
    /* Headers in the document */
    div[data-testid="stMarkdownContainer"] h1, 
    div[data-testid="stMarkdownContainer"] h2, 
    div[data-testid="stMarkdownContainer"] h3 {
        font-family: 'Times New Roman', Times, serif !important;
        color: #2c3e50 !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
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
    TONE: Professional, Corporate, Industry-Standard, 'Times New Roman' formal style.
    """

    if doc_type == "Proposal":
        return base_role + """
        GOAL: Create a Sales Proposal.
        STRUCTURE:
        1. Executive Summary
        2. Understanding of Requirements (Pain Points)
        3. Proposed Solution (Odoo Modules Mapping)
        4. Metamorphosis Advantage (Why Us?)
        5. Relevant Case Studies
        6. Implementation Methodology (The 6 Stages)
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
        5. Current Process (As-Is) vs. Proposed Process (To-Be)
        6. Business Risks
        """

    elif doc_type == "SRS (Software Req Spec)":
        return base_role + """
        GOAL: Create a Software Requirements Specification (SRS).
        FOCUS: Functional and Non-Functional requirements.
        STRUCTURE:
        1. Introduction
        2. Functional Requirements (Detailed Features, User Stories)
        3. Non-Functional Requirements (Performance, Security, Reliability)
        4. System Interfaces (Odoo API, External Hardware)
        5. User Roles & Permissions
        """

    elif doc_type == "TRD (Technical Req Doc)":
        return base_role + """
        GOAL: Create a Technical Requirements Document (TRD).
        FOCUS: Technology stack, Odoo architecture, Server specs.
        STRUCTURE:
        1. System Architecture (Odoo.sh / On-premise)
        2. Database Design (PostgreSQL schema highlights)
        3. Tech Stack (Python, XML, JS, PostgreSQL)
        4. Integration Details (API Endpoints)
        5. Security Protocols (SSL, Access Control)
        6. Server Specifications
        """

    elif doc_type == "HLD (High-Level Design)":
        return base_role + """
        GOAL: Create a High-Level Design (HLD) document.
        FOCUS: System modularity, data flow, and architectural diagrams (described in text).
        STRUCTURE:
        1. Architectural Overview
        2. Component Diagram Description (Odoo Modules interaction)
        3. Data Flow Diagrams (Description of flow from Sales -> Inventory -> Accounting)
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
        3. Endpoints (List specific endpoints relevant to the scenario)
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
        4. Test Cases (Table format: ID, Scenario, Steps, Expected Result)
           - Include cases for Sales, Purchase, Inventory, Accounting.
        5. Defect Management Process
        6. Sign-off Criteria
        """

    return base_role

# --- SIDEBAR UI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2921/2921226.png", width=50) # Placeholder icon
    st.title("Configuration")
    
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
    
    st.info(f"**Mode:** {doc_type}\n\nGenerates industry-standard docs tailored for Odoo Implementation.")

# --- MAIN UI ---
st.title("🦋 Metamorphosis Document Architect")
st.markdown("### Generate Professional ERP Documentation")

client_scenario = st.text_area(
    "📝 Client Scenario / Requirements",
    height=150,
    placeholder="Example: A textile manufacturing company in Narayanganj with 400 employees. They are facing issues with inventory tracking, wastage management, and syncing accounting with production. They need a full Odoo implementation."
)

generate_btn = st.button("🚀 Generate Document", type="primary")

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
                model_name="gemini-2.5-flash", # Updated to gemini-2.5-flash as requested
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
            st.markdown(f"## {doc_type} for Client")
            st.markdown(doc_content)
            st.markdown("---")

            # Download Button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{doc_type.split()[0]}_Metamorphosis_{timestamp}.md"
            
            st.download_button(
                label="📥 Download Document (.md)",
                data=doc_content,
                file_name=filename,
                mime="text/markdown"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- FOOTER ---
st.markdown(
    """
    <div style='position: fixed; bottom: 0; width: 100%; text-align: center; color: grey; font-size: 12px; padding: 10px;'>
        Powered by Google Gemini 2.0 | Metamorphosis Systems Internal Tool
    </div>
    """, 
    unsafe_allow_html=True
)
