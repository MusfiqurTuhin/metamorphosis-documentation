# ui/tabs.py

"""UI rendering for Metamorphosis Studio.
All Streamlit UI code lives here. Business logic is delegated to
`services.helpers` and `services.gemini_client`.
"""

import streamlit as st
from services import helpers
from services.gemini_client import GeminiClient

# ---------------------------------------------------------------------------
# Helper wrappers to keep UI code concise
# ---------------------------------------------------------------------------

def _render_api_tab():
    st.markdown("### 🔑 API Key Management")
    st.info("ℹ️ The system uses a default API key. You can override it with your own key below.")
    
    api_input = st.text_input("Gemini API Key", type="password")
    if st.button("💾 Save & Verify", type="primary"):
        if api_input:
            client = GeminiClient(user_api_key=api_input)
            # Try a simple generation to verify
            res = client.generate_content("Test")
            if "Error" not in res and "Quota" not in res:
                st.session_state.api_key = api_input
                st.success("✅ Verified & Saved!")
            else:
                st.error(res)
    
    if "api_key" in st.session_state:
        st.success(f"Active User Key: {st.session_state.api_key[:8]}…")
    else:
        st.info("Using System Default Key")

def _render_prompt_refiner_tab():
    st.markdown("### ✨ Prompt Refiner")
    col1, col2 = st.columns(2)
    with col1:
        template = st.selectbox("Template", ["None"] + list(st.session_state.get('PROMPT_TEMPLATES', {}).keys()))
        if template != "None":
            st.info(st.session_state.PROMPT_TEMPLATES[template])
        context = st.selectbox("Context", ["General", "Software Engineering", "Data Science", "Legal", "Medical", "Business", "Creative"])
        tone = st.select_slider("Tone", ["Casual", "Neutral", "Professional", "Academic"])
        complexity = st.slider("Complexity", 1, 10, 7)
        prompt_input = st.text_area("Prompt", height=200)
    with col2:
        if st.button("🚀 Refine", type="primary"):
            if prompt_input:
                client = GeminiClient(st.session_state.get("api_key"))
                sys_prompt = f"Refine prompt. Context: {context}. Tone: {tone}. Complexity: {complexity}/10."
                res = client.generate_content(f"{sys_prompt}\n{prompt_input}")
                
                if "⚠️" in res or "❌" in res:
                    st.markdown(res)
                else:
                    st.session_state.refined_prompt = res.replace("**", "")
                    helpers.add_to_history(st, "Prompts", st.session_state.refined_prompt, f"{context} prompt")
                    st.success("✅ Refined!")
        
        if "refined_prompt" in st.session_state:
            st.text_area("Result", st.session_state.refined_prompt, height=300)
            if st.button("⭐ Save Favorite"):
                helpers.save_to_favorites(st, st.session_state.refined_prompt, "Prompts", f"{context} prompt")
                st.success("Saved!")

def _render_document_generator_tab():
    st.markdown("### 📝 Document Generator")
    col1, col2 = st.columns([1, 2])
    with col1:
        doc_type = st.selectbox("Type", ["BRD", "TDD", "API Spec", "User Manual", "SOP", "Report", "Other"])
        doc_style = st.selectbox("Style", ["Professional", "Academic", "Technical", "Simple"])
        include_toc = st.checkbox("Include Table of Contents", value=True)
        include_meta = st.checkbox("Include Metadata")
        if include_meta:
            author = st.text_input("Author")
            version = st.text_input("Version", "1.0")
        # Context file upload
        st.markdown("#### 📤 Upload Context File (Optional)")
        uploaded_file = st.file_uploader(
            "Upload company profile, reference docs, etc.",
            type=["txt", "md", "pdf", "docx"],
            key="doc_context_upload",
        )
        context_text = helpers.extract_context_text(uploaded_file)
        if context_text:
            st.success(f"✅ Loaded {len(context_text)} characters from {uploaded_file.name}")
        doc_details = st.text_area("Content Details", height=250, key="doc_details_input")
    with col2:
        if st.button("📄 Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Write {doc_type}. Style: {doc_style}. Markdown format."
            if include_toc:
                sys_prompt += " Include TOC."
            if include_meta:
                sys_prompt += f" Author: {author}. Version: {version}."
            full_prompt = sys_prompt + "\n" + doc_details
            if context_text:
                full_prompt += f"\n\nCONTEXT FROM UPLOADED FILE:\n{context_text[:5000]}"
            
            res = client.generate_content(full_prompt)
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.doc_content = res
                helpers.add_to_history(st, "Documents", st.session_state.doc_content, doc_type)
                st.success("✅ Document generated!")

    # ----- Download / Export Section -----
    if "doc_content" in st.session_state:
        st.markdown("#### 📥 Downloads & Export")
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button("📥 MD", st.session_state.doc_content, "document.md", use_container_width=True)
        with dl2:
            st.download_button("📥 DOCX", helpers.create_docx(st.session_state.doc_content), "document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with dl3:
            st.download_button("📥 PDF", helpers.create_pdf(st.session_state.doc_content), "document.pdf", "application/pdf", use_container_width=True)
        # Google Docs export
        st.markdown("#### 📄 Export to Google Docs")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.text_area("Step 1: Select All (Ctrl+A) and Copy (Ctrl+C):", st.session_state.doc_content, height=120, key="gdocs_export_area")
        with col_b:
            st.markdown("""
            <a href="https://docs.google.com/document/create" target="_blank">
                <button style="
                    width: 100%;
                    padding: 1.25rem;
                    background: linear-gradient(135deg, #4285F4 0%, #34A853 100%);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 1.1rem;
                    cursor: pointer;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.3)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';">
                    📄 Open Google Docs
                </button>
            </a>
            <p style="font-size: 0.85rem; color: #666; margin-top: 0.75rem; text-align: center;">
                Then paste (Ctrl+V or Cmd+V)
            </p>
            """, unsafe_allow_html=True)
        st.info("💡 Quick tip: After copying, the Google Docs button opens a new document where you can paste immediately!")
        st.download_button("📄 Download as TXT (for Google Docs import)", st.session_state.doc_content, "document.txt", "text/plain", use_container_width=True)

def _render_diagram_generator_tab():
    st.markdown("### 📊 Diagram Generator")
    col1, col2 = st.columns([1, 2])
    with col1:
        diagram_template = st.selectbox("Template", ["None"] + list(st.session_state.get('DIAGRAM_TEMPLATES', {}).keys()))
        diagram_theme = st.selectbox("Theme", ["default", "dark", "forest", "neutral"])
        diagram_type = st.selectbox("Type", ["Flowchart", "Sequence", "ER Diagram", "Gantt", "Mindmap"])
        base_code = st.session_state.DIAGRAM_TEMPLATES.get(diagram_template, "") if diagram_template != "None" else ""
        custom_code = st.text_area("Custom Mermaid Code", value=base_code, height=200)
    with col2:
        if st.button("🎨 Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"You are a Mermaid diagram expert. Generate syntactically perfect Mermaid code for a {diagram_type}."
            res = client.generate_content(f"{sys_prompt}\n{custom_code}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.mermaid_code = helpers.sanitize_mermaid_code(res)
                helpers.add_to_history(st, "Diagrams", st.session_state.mermaid_code, diagram_type)
                st.success("✅ Diagram generated!")

    if "mermaid_code" in st.session_state:
        st.markdown("#### 👁️ Preview")
        st.markdown(st.session_state.mermaid_code)
        # Download options
        st.markdown("#### 💾 Downloads")
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            png = helpers.get_mermaid_img(st.session_state.mermaid_code, "png")
            if png:
                st.download_button("PNG", png, "diagram.png", use_container_width=True)
        with dl2:
            if png:
                jpg = helpers.convert_to_jpg(png)
                if jpg:
                    st.download_button("JPG", jpg, "diagram.jpg", use_container_width=True)
        with dl3:
            svg = helpers.get_mermaid_img(st.session_state.mermaid_code, "svg")
            if svg:
                st.download_button("SVG", svg, "diagram.svg", use_container_width=True)
        # Edit mode
        with st.expander("✏️ Edit Code"):
            edited = st.text_area("Mermaid Code", st.session_state.mermaid_code, height=200)
            if st.button("🔄 Update Preview"):
                st.session_state.mermaid_code = edited
                st.rerun()

def _render_code_generator_tab():
    st.markdown("### 💻 Code Generator")
    col1, col2 = st.columns([1, 2])
    with col1:
        language = st.selectbox("Language", ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go"])
        framework = st.selectbox("Framework", ["None"] + list(st.session_state.get('CODE_FRAMEWORKS', {}).get(language, [])))
        style = st.selectbox("Style", ["OOP", "Functional", "Procedural"])
        if st.checkbox("Show Advanced Options"):
            include_docs = st.checkbox("Include Documentation", True)
            include_types = st.checkbox("Include Type Hints", True)
            include_tests = st.checkbox("Generate Unit Tests")
            include_deps = st.checkbox("Generate Dependencies")
        code_req = st.text_area("Requirements", height=250)
    with col2:
        if st.button("⚡ Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Generate {language} code. Framework: {framework}. Style: {style}."
            if st.checkbox("Show Advanced Options"):
                if include_docs:
                    sys_prompt += " Include docs."
                if include_types:
                    sys_prompt += " Include types."
            
            res = client.generate_content(f"{sys_prompt}\n{code_req}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.generated_code = res
                helpers.add_to_history(st, "Code", st.session_state.generated_code, f"{language} code")
                
                if st.checkbox("Show Advanced Options") and include_tests:
                    test_res = client.generate_content(f"Generate unit tests for:\n{res}")
                    if "⚠️" not in test_res and "❌" not in test_res:
                        st.session_state.generated_tests = test_res

    if "generated_code" in st.session_state:
        st.markdown("#### 💻 Generated Code")
        st.code(st.session_state.generated_code, language=language.lower())
        st.download_button("📥 Download", st.session_state.generated_code, f"code.{language[:2].lower()}")
        if "generated_tests" in st.session_state:
            with st.expander("🧪 Unit Tests"):
                st.code(st.session_state.generated_tests, language=language.lower())

def _render_summarizer_tab():
    st.markdown("### 📚 Summarizer")
    col1, col2 = st.columns(2)
    with col1:
        compression = st.slider("Compression Ratio", 10, 90, 50)
        format_type = st.selectbox("Format", ["Paragraph", "Bullet Points", "Key Points"])
        if st.checkbox("Show Advanced Options"):
            extract_info = st.multiselect("Extract", ["Names", "Dates", "Numbers", "Locations"])
            multilingual = st.checkbox("Multi‑language Support")
        text = st.text_area("Text to Summarize", height=350)
    with col2:
        if st.button("🔍 Summarize", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Summarize to {compression}% length. Format: {format_type}."
            res = client.generate_content(f"{sys_prompt}\n{text}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.summary = res
                helpers.add_to_history(st, "Summaries", st.session_state.summary, f"{compression}% summary")

    if "summary" in st.session_state:
        st.markdown("#### 📄 Summary")
        st.markdown(st.session_state.summary)
        st.download_button("📥 Download", st.session_state.summary, "summary.txt")

def _render_translator_tab():
    st.markdown("### 🌐 Translator")
    col1, col2 = st.columns(2)
    with col1:
        target_lang = st.selectbox("Target Language", ["Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Arabic", "Hindi", "Bengali", "Portuguese", "Russian", "Italian"])
        if st.checkbox("Show Advanced Options"):
            formality = st.select_slider("Formality", ["Casual", "Neutral", "Formal"])
            preserve_format = st.checkbox("Preserve Formatting", True)
        text = st.text_area("Text to Translate", height=300)
    with col2:
        if st.button("🚀 Translate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Translate to {target_lang}."
            if st.checkbox("Show Advanced Options"):
                sys_prompt += f" Formality: {formality}."
            res = client.generate_content(f"{sys_prompt}\n{text}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.translation = res
                helpers.add_to_history(st, "Translations", st.session_state.translation, f"To {target_lang}")

    if "translation" in st.session_state:
        st.markdown(f"#### 🎯 {target_lang}")
        st.text_area("Result", st.session_state.translation, height=300)
        st.download_button("📥 Download", st.session_state.translation, f"translation_{target_lang.lower()}.txt")

def _render_email_writer_tab():
    st.markdown("### ✉️ Email Writer")
    col1, col2 = st.columns(2)
    with col1:
        template = st.selectbox("Template", ["Meeting Request", "Follow-up", "Introduction"])
        tone = st.select_slider("Tone", ["Casual", "Neutral", "Formal"])
        length = st.select_slider("Length", ["Brief", "Standard", "Detailed"])
        subject = st.text_input("Subject")
        body = st.text_area("Email Body", height=250)
    with col2:
        if st.button("✉️ Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Write an email. Template: {template}. Tone: {tone}. Length: {length}."
            res = client.generate_content(f"{sys_prompt}\nSubject: {subject}\n\n{body}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.email = res
                helpers.add_to_history(st, "Emails", st.session_state.email, template)

    if "email" in st.session_state:
        st.markdown("#### 📧 Email Draft")
        st.text_area("Result", st.session_state.email, height=300)
        st.download_button("📥 Download", st.session_state.email, "email.txt")

def _render_analyzer_tab():
    st.markdown("### 🔍 Content Analyzer")
    col1, col2 = st.columns(2)
    with col1:
        if st.checkbox("Show Advanced Options"):
            depth = st.select_slider("Analysis Depth", ["Quick", "Standard", "Comprehensive"])
            grammar = st.checkbox("Grammar Check")
            seo = st.checkbox("SEO Analysis")
        text = st.text_area("Content to Analyze", height=400)
    with col2:
        if st.button("🔍 Analyze", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = "Analyze readability, sentiment, keywords, word/sentence count."
            if st.checkbox("Show Advanced Options"):
                if grammar:
                    sys_prompt += " Include grammar check."
                if seo:
                    sys_prompt += " Include SEO suggestions."
            res = client.generate_content(f"{sys_prompt}\n{text}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.analysis = res
                helpers.add_to_history(st, "Analysis", st.session_state.analysis, "Content analysis")

    if "analysis" in st.session_state:
        st.markdown("#### 📊 Analysis Result")
        st.markdown(st.session_state.analysis)
        st.download_button("📥 Download", st.session_state.analysis, "analysis.txt")

def _render_quiz_generator_tab():
    st.markdown("### 📝 Quiz Generator")
    col1, col2 = st.columns(2)
    with col1:
        q_type = st.selectbox("Type", ["MCQ", "True/False", "Short Answer", "Mixed"])
        num_q = st.slider("Number of Questions", 5, 30, 10)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"])
        if st.checkbox("Show Advanced Options"):
            include_answers = st.checkbox("Include Answer Key", True)
            randomize = st.checkbox("Randomize Order")
            points = st.number_input("Points per Question", 1, 10, 1)
        topic = st.text_area("Topic/Content", height=250)
    with col2:
        if st.button("🎯 Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Create {num_q} {q_type} questions. Difficulty: {difficulty}."
            if st.checkbox("Show Advanced Options") and include_answers:
                sys_prompt += " Include answer key."
            res = client.generate_content(f"{sys_prompt}\n{topic}")
            
            if "⚠️" in res or "❌" in res:
                st.markdown(res)
            else:
                st.session_state.quiz = res
                helpers.add_to_history(st, "Quizzes", st.session_state.quiz, f"{num_q} questions")

    if "quiz" in st.session_state:
        st.markdown("#### 📋 Quiz")
        st.markdown(st.session_state.quiz)
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.download_button("TXT", st.session_state.quiz, "quiz.txt")
        with dl2:
            st.download_button("DOCX", helpers.create_docx(st.session_state.quiz), "quiz.docx")
        with dl3:
            st.download_button("PDF", helpers.create_pdf(st.session_state.quiz), "quiz.pdf")

def render_tabs():
    """Render the full tab interface.
    This function is imported by `app.py` and called after the header.
    """
    tabs = st.tabs([
        "🔑 API",
        "✨ Prompt Refiner",
        "📊 Diagram Generator",
        "📝 Document Generator",
        "💻 Code Generator",
        "📚 Summarizer",
        "🌐 Translator",
        "✉️ Email Writer",
        "🔍 Analyzer",
        "📝 Quiz Generator",
    ])
    with tabs[0]:
        _render_api_tab()
    with tabs[1]:
        _render_prompt_refiner_tab()
    with tabs[2]:
        _render_diagram_generator_tab()
    with tabs[3]:
        _render_document_generator_tab()
    with tabs[4]:
        _render_code_generator_tab()
    with tabs[5]:
        _render_summarizer_tab()
    with tabs[6]:
        _render_translator_tab()
    with tabs[7]:
        _render_email_writer_tab()
    with tabs[8]:
        _render_analyzer_tab()
    with tabs[9]:
        _render_quiz_generator_tab()

# End of ui/tabs.py
