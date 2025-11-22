import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Metamorphosis Enterprise Architect",
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4F46E5; /* Indigo */
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 20px;
        background-color: #F9FAFB;
    }
    .stButton button {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #4338CA;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "generated_doc" not in st.session_state:
    st.session_state.generated_doc = None
if "doc_stage" not in st.session_state:
    st.session_state.doc_stage = "interview" # options: interview, generating, finished

# --- SYSTEM PROMPTS & TEMPLATES ---
METAMORPHOSIS_DEFAULT_PROFILE = """
COMPANY: Metamorphosis Systems (Metamorphosis Ltd.)
STATUS: #1 Leading Odoo Silver Partner in Bangladesh.
EXPERIENCE: 8+ years, Multi-country projects (BD, NZ, Saudi Arabia, South Sudan).
MISSION: Transform businesses through tailored, cost-effective Odoo ERP solutions.
SERVICES: Odoo Implementation, Consultancy, Mobile App Dev, Web Dev.
METHODOLOGY: 1. Consultation -> 2. Global Estimate -> 3. Analysis -> 4. Timeline -> 5. Implementation -> 6. Go Live.
"""

DOC_TYPES = {
    "Proposal": {
        "role": "Senior Solution Architect",
        "goal": "Sales & Value Proposition",
        "focus": "Pain points, ROI, Timeline, Budget, Implementation Phases",
        "structure": "Executive Summary, Problem Statement, Proposed Solution (Odoo Modules), Methodology, Commercials."
    },
    "BRD (Business Req Doc)": {
        "role": "Lead Business Analyst",
        "goal": "Capture Business Needs",
        "focus": "Stakeholders, In-Scope/Out-Scope, Business Objectives, Risks, Success Metrics",
        "structure": "Project Background, Objectives, Scope (In/Out), Stakeholder Analysis, Functional Requirements (High Level)."
    },
    "SRS (Software Req Spec)": {
        "role": "Senior Systems Analyst",
        "goal": "Detailed Functional Specs",
        "focus": "User Stories, User Personas, Detailed Features, Reporting, Access Rights",
        "structure": "User Personas, Functional Requirements (Detailed), Non-Functional Req, System Interfaces, Reporting."
    },
    "TRD (Technical Req Doc)": {
        "role": "Chief Technology Officer (CTO)",
        "goal": "Tech Stack & Infrastructure",
        "focus": "Hosting, Security, Integrations, Data Migration, Backup Strategy, CI/CD",
        "structure": "System Architecture, Tech Stack, Security Protocols, Database Strategy, API Strategy, Deployment."
    },
    "HLD (High-Level Design)": {
        "role": "Principal Software Architect",
        "goal": "System Architecture",
        "focus": "Component Interaction, Data Flow, Microservices vs Monolith, External Systems",
        "structure": "Architecture Diagram (Mermaid), Component Description, Data Flow, Technology Choices."
    },
    "API Documentation": {
        "role": "Senior Backend Developer",
        "goal": "Interface Definitions",
        "focus": "Endpoints, Methods (GET/POST), Payloads, Response Codes, Authentication",
        "structure": "Authentication, Base URL, Endpoints List, Request/Response Examples, Error Codes."
    },
    "UAT Plan (Test Plan)": {
        "role": "QA Lead",
        "goal": "Quality Assurance",
        "focus": "Test Scenarios, Acceptance Criteria, Test Data, Bug Reporting Process",
        "structure": "Test Strategy, Scope, Test Environment, Test Cases (Table format), Entry/Exit Criteria."
    }
}

# --- HELPER FUNCTIONS ---

def get_architect_prompt(doc_type, company_profile):
    info = DOC_TYPES[doc_type]
    return f"""
    *** IDENTITY ACTIVATION ***
    ROLE: {info['role']} at {company_profile.splitlines()[0]}
    TASK: Conduct a professional interview to gather information for a {doc_type}.
    GOAL: {info['goal']}
    FOCUS AREAS: {info['focus']}
    
    *** INSTRUCTIONS ***
    1. Start by introducing yourself and asking the FIRST most critical question.
    2. Ask ONE question at a time. Do not overwhelm the user.
    3. Wait for the user's answer before asking the next question.
    4. If the user is vague, ask clarifying questions.
    5. Keep a professional, consultative tone.
    6. Once you have enough information (usually 5-7 interactions), ask if they are ready to generate the document.
    
    CONTEXT INFO:
    {company_profile}
    """

def get_writer_prompt(doc_type, chat_history, company_profile):
    info = DOC_TYPES[doc_type]
    return f"""
    *** DOCUMENT GENERATION MODE ***
    You are a {info['role']}.
    Based on the INTERVIEW TRANSCRIPT below, generate a professional, industry-standard {doc_type}.
    
    *** REQUIREMENTS ***
    1. FORMAT: Markdown.
    2. STRUCTURE: Follow standard industry structure: {info['structure']}
    3. DIAGRAMS: Include at least one Mermaid.js diagram (flowchart, sequence, or ERD) where appropriate. Wrap it in ```mermaid ... ``` block.
    4. TONE: Professional, Corporate, Clear.
    5. BRANDING: Use the Company Profile context ({company_profile}) to highlight specific methodologies or strengths.
    
    *** INTERVIEW TRANSCRIPT ***
    {chat_history}
    
    *** OUTPUT ***
    Generate the full document now.
    """

# --- SIDEBAR ---
with st.sidebar:
    st.title("🦋 Configuration")
    
    # API Key Setup
    api_key = st.text_input("Gemini API Key", type="password", help="Get key from aistudio.google.com")
    
    st.divider()
    
    # Project Settings
    st.subheader("📂 Project Details")
    selected_doc_type = st.selectbox("Document Type", list(DOC_TYPES.keys()))
    
    with st.expander("🏢 Company Profile (Editable)"):
        company_profile = st.text_area("Edit Context", value=METAMORPHOSIS_DEFAULT_PROFILE, height=150)
    
    st.divider()
    
    # Action Buttons
    if st.button("♻️ Reset / Start New"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.session_state.generated_doc = None
        st.session_state.doc_stage = "interview"
        st.rerun()

# --- MAIN APP LOGIC ---

st.markdown('<div class="main-header">🦋 Metamorphosis Enterprise Architect</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">AI-Powered Generator for: <b>{selected_doc_type}</b></div>', unsafe_allow_html=True)

if not api_key:
    st.warning("⚠️ Please enter your Google Gemini API Key in the sidebar to proceed.")
    st.stop()

# Configure Gemini
genai.configure(api_key=api_key)

# Initialize Chat Session if needed
if st.session_state.chat_session is None:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Using 1.5 Flash for speed and large context
            system_instruction=get_architect_prompt(selected_doc_type, company_profile)
        )
        st.session_state.chat_session = model.start_chat(history=[])
        
        # Initial Greeting
        response = st.session_state.chat_session.send_message("Start the interview.")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Failed to initialize AI: {e}")

# --- DISPLAY CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- USER INPUT & INTERVIEW LOOP ---
if st.session_state.doc_stage == "interview":
    if prompt := st.chat_input("Type your answer here..."):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. AI Response
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                ai_text = response.text
                
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
                with st.chat_message("assistant"):
                    st.markdown(ai_text)
            except Exception as e:
                st.error(f"API Error: {e}")

# --- GENERATION TRIGGER ---
st.markdown("---")
col1, col2 = st.columns([1, 2])

with col1:
    st.info("When the interview is complete, click Generate.")
    if st.button("🚀 Generate Final Document", type="primary", use_container_width=True):
        st.session_state.doc_stage = "generating"
        st.rerun()

# --- DOCUMENT GENERATION STAGE ---
if st.session_state.doc_stage == "generating":
    with st.status("🏗️ Architecting Document...", expanded=True) as status:
        st.write("📝 Compiling interview notes...")
        time.sleep(1)
        st.write("🧠 Analyzing requirements...")
        time.sleep(1)
        st.write("🎨 Drafting content and diagrams...")
        
        # Compile history text
        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        
        # Call AI for Final Doc
        try:
            writer_model = genai.GenerativeModel("gemini-1.5-pro") # Use Pro for higher quality writing
            final_response = writer_model.generate_content(
                get_writer_prompt(selected_doc_type, history_text, company_profile)
            )
            st.session_state.generated_doc = final_response.text
            st.session_state.doc_stage = "finished"
            status.update(label="✅ Document Ready!", state="complete", expanded=False)
        except Exception as e:
            st.error(f"Generation Error: {e}")
            status.update(label="❌ Failed", state="error")

# --- FINAL OUTPUT DISPLAY ---
if st.session_state.doc_stage == "finished" and st.session_state.generated_doc:
    st.markdown("## 📄 Generated Document Preview")
    
    tab1, tab2 = st.tabs(["Reading View", "Raw Markdown"])
    
    with tab1:
        # Render Markdown including Mermaid diagrams
        st.markdown(st.session_state.generated_doc, unsafe_allow_html=True)
        
    with tab2:
        st.code(st.session_state.generated_doc, language="markdown")

    # Download Button
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"Metamorphosis_{selected_doc_type.split()[0]}_{timestamp}.md"
    
    st.download_button(
        label="📥 Download Document (Markdown)",
        data=st.session_state.generated_doc,
        file_name=filename,
        mime="text/markdown",
        type="primary"
    )
