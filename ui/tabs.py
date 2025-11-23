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
    st.warning("⚠️ You must provide your own Google Gemini API Key to use this application.")
    
    api_input = st.text_input("Gemini API Key", type="password", placeholder="Enter your API key here...")
    if st.button("💾 Save & Verify", type="primary"):
        if api_input:
            client = GeminiClient(user_api_key=api_input)
            # Try a simple generation to verify
            res = client.generate_content("Test")
            if "Error" not in res and "Quota" not in res and res.strip():
                st.session_state.api_key = api_input
                st.success("✅ Verified & Saved!")
            else:
                st.error("❌ Invalid API Key or verification failed. Please check your key.")
        else:
            st.error("❌ Please enter an API key.")
    
    if "api_key" in st.session_state:
        st.success(f"✅ Active Key: {st.session_state.api_key[:12]}...")

    st.markdown("---")
    
    # Bengali User Manual for API Key Creation (using st.info for guaranteed visibility)
    st.markdown("### 📘 কীভাবে Google AI Studio থেকে API Key তৈরি করবেন")
    st.info("""
**Google AI Studio API Key তৈরির ধাপসমূহ:**

১. প্রথমে Google AI Studio (https://aistudio.google.com/) ওয়েবসাইটে যান।

২. আপনার Google অ্যাকাউন্ট দিয়ে সাইন ইন করুন।

৩. বাম পাশের মেনু থেকে "Get API key" বাটনে ক্লিক করুন।

৪. "Create API key" বাটনে ক্লিক করুন।

৫. আপনার যদি কোনো প্রজেক্ট না থাকে, তবে "Create API key in new project" সিলেক্ট করুন।

৬. কিছুক্ষণ অপেক্ষা করুন, একটি পপ-আপ উইন্ডোতে আপনার নতুন API Key দেখতে পাবেন।

৭. "Copy" বাটনে ক্লিক করে Key-টি কপি করুন।

৮. এবার এই অ্যাপের "Gemini API Key" বক্সে পেস্ট করে "Save & Verify" বাটনে ক্লিক করুন।

**দ্রষ্টব্য:** Google AI Studio-তে API Key তৈরি করা সম্পূর্ণ বিনামূল্যে (Free Tier ব্যবহারকারীদের জন্য)।
    """)

def _render_prompt_refiner_tab():
    st.markdown("### ✨ Prompt Refiner")
    col1, col2 = st.columns(2)
    with col1:
        template = st.selectbox("Template", ["None"] + list(st.session_state.get('PROMPT_TEMPLATES', {}).keys()), key="refiner_template")
        if template != "None":
            st.info(st.session_state.PROMPT_TEMPLATES[template])
        context = st.selectbox("Context", ["General", "Software Engineering", "Data Science", "Legal", "Medical", "Business", "Creative"], key="refiner_context")
        tone = st.select_slider("Tone", ["Casual", "Neutral", "Professional", "Academic"], key="refiner_tone")
        complexity = st.slider("Complexity", 1, 10, 7, key="refiner_complexity")
        prompt_input = st.text_area("Prompt", height=200, key="refiner_prompt")
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
    st.caption("Generate professional documents like BRDs, TDDs, and Manuals. Upload context files for better accuracy.")
    col1, col2 = st.columns([1, 2])
    with col1:
        doc_type = st.selectbox("Type", ["BRD", "TDD", "API Spec", "User Manual", "SOP", "Report", "Other"], key="doc_type")
        doc_style = st.selectbox("Style", ["Professional", "Academic", "Technical", "Simple"], key="doc_style")
        include_toc = st.checkbox("Include Table of Contents", value=True, key="doc_toc")
        include_meta = st.checkbox("Include Metadata", key="doc_meta")
        if include_meta:
            author = st.text_input("Author", key="doc_author")
            version = st.text_input("Version", "1.0", key="doc_version")
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

def _render_diagram_generator_tab():
    st.markdown("### 📊 Diagram Generator")
    col1, col2 = st.columns([1, 2])
    with col1:
        diagram_template = st.selectbox("Template", ["None"] + list(st.session_state.get('DIAGRAM_TEMPLATES', {}).keys()), key="diagram_template")
        diagram_theme = st.selectbox("Theme", ["default", "dark", "forest", "neutral"], key="diagram_theme")
        diagram_type = st.selectbox("Type", ["Flowchart", "Sequence", "ER Diagram", "Gantt", "Mindmap"], key="diagram_type")
        base_code = st.session_state.DIAGRAM_TEMPLATES.get(diagram_template, "") if diagram_template != "None" else ""
        custom_code = st.text_area("Custom Mermaid Code", value=base_code, height=200, key="diagram_code")
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
        language = st.selectbox("Language", ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go"], key="code_lang")
        framework = st.selectbox("Framework", ["None"] + list(st.session_state.get('CODE_FRAMEWORKS', {}).get(language, [])), key="code_framework")
        style = st.selectbox("Style", ["OOP", "Functional", "Procedural"], key="code_style")
        show_advanced = st.checkbox("Show Advanced Options", key="code_advanced")
        if show_advanced:
            include_docs = st.checkbox("Include Documentation", True, key="code_docs")
            include_types = st.checkbox("Include Type Hints", True, key="code_types")
            include_tests = st.checkbox("Generate Unit Tests", key="code_tests_check")
        code_req = st.text_area("Requirements", height=250, key="code_req")
    with col2:
        if st.button("⚡ Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Generate {language} code. Framework: {framework}. Style: {style}."
            if show_advanced:
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
                
                if show_advanced and include_tests:
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
        compression = st.slider("Compression Ratio", 10, 90, 50, key="sum_compression")
        format_type = st.selectbox("Format", ["Paragraph", "Bullet Points", "Key Points"], key="sum_format")
        show_advanced = st.checkbox("Show Advanced Options", key="sum_advanced")
        if show_advanced:
            extract_info = st.multiselect("Extract", ["Names", "Dates", "Numbers", "Locations"], key="sum_extract")
            multilingual = st.checkbox("Multi‑language Support", key="sum_multi")
        text = st.text_area("Text to Summarize", height=350, key="sum_text")
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
        target_lang = st.selectbox("Target Language", ["Spanish", "French", "German", "Chinese", "Japanese", "Korean", "Arabic", "Hindi", "Bengali", "Portuguese", "Russian", "Italian"], key="trans_lang")
        show_advanced = st.checkbox("Show Advanced Options", key="trans_advanced")
        if show_advanced:
            formality = st.select_slider("Formality", ["Casual", "Neutral", "Formal"], key="trans_formality")
            preserve_format = st.checkbox("Preserve Formatting", True, key="trans_format")
        text = st.text_area("Text to Translate", height=300, key="trans_text")
    with col2:
        if st.button("🚀 Translate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Translate to {target_lang}."
            if show_advanced:
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
        template = st.selectbox("Template", ["Meeting Request", "Follow-up", "Introduction"], key="email_template")
        tone = st.select_slider("Tone", ["Casual", "Neutral", "Formal"], key="email_tone")
        length = st.select_slider("Length", ["Brief", "Standard", "Detailed"], key="email_length")
        subject = st.text_input("Subject", key="email_subject")
        body = st.text_area("Email Body", height=250, key="email_body")
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
        show_advanced = st.checkbox("Show Advanced Options", key="analyze_advanced")
        if show_advanced:
            depth = st.select_slider("Analysis Depth", ["Quick", "Standard", "Comprehensive"], key="analyze_depth")
            grammar = st.checkbox("Grammar Check", key="analyze_grammar")
            seo = st.checkbox("SEO Analysis", key="analyze_seo")
        text = st.text_area("Content to Analyze", height=400, key="analyze_text")
    with col2:
        if st.button("🔍 Analyze", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = "Analyze readability, sentiment, keywords, word/sentence count."
            if show_advanced:
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
        q_type = st.selectbox("Type", ["MCQ", "True/False", "Short Answer", "Mixed"], key="quiz_type")
        num_q = st.slider("Number of Questions", 5, 30, 10, key="quiz_num")
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], key="quiz_diff")
        show_advanced = st.checkbox("Show Advanced Options", key="quiz_advanced")
        if show_advanced:
            include_answers = st.checkbox("Include Answer Key", True, key="quiz_answers")
            randomize = st.checkbox("Randomize Order", key="quiz_random")
            points = st.number_input("Points per Question", 1, 10, 1, key="quiz_points")
        topic = st.text_area("Topic/Content", height=250, key="quiz_topic")
    with col2:
        if st.button("🎯 Generate", type="primary"):
            client = GeminiClient(st.session_state.get("api_key"))
            sys_prompt = f"Create {num_q} {q_type} questions. Difficulty: {difficulty}."
            if show_advanced and include_answers:
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
