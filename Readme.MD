# Metamorphosis Studio

> **A modern, AI‑powered UI for rapid content creation** – Prompt Refiner, Document Generator, Code Generator, Summarizer, Translator, Email Writer, Content Analyzer, Quiz Generator, and Mermaid Diagram Generator.

---

## ✨ Overview
Metamorphosis Studio is a Streamlit‑based web application that leverages Google Gemini (or alternative LLMs) to transform user input into polished outputs.  The UI follows a **single‑column, premium “Neo‑SaaS” design** with vibrant orange‑black‑white palette, glass‑morphism cards, and smooth micro‑animations.

---

## 🚀 Features
| Feature | Description |
|---------|-------------|
| **Prompt Refiner** | Refine prompts with tone, complexity, and context selection. |
| **Document Generator** | Generate BRD, TDD, API Spec, User Manual, SOP, Report, **Presentation**, **Meeting Minutes** (Bangla & English), and more. Includes live preview and download (MD, DOCX, PDF). |
| **Code Generator** | Supports 13 languages (Python, JavaScript, TypeScript, Java, C++, Go, C#, Ruby, PHP, Swift, Kotlin, Rust, Shell Script) with optional frameworks. |
| **Summarizer** | Summarize text with configurable compression and format. |
| **Translator** | Bangla ↔ English translation with formality control. |
| **Email Writer** | Choose from 8 email templates (Thank You, Apology, Feedback Request, Sales Pitch, Customer Support, Announcement, etc.). |
| **Content Analyzer** | Grammar, SEO, and deep‑analysis options. |
| **Quiz Generator** | Generate MCQ, True/False, Short Answer, Mixed, **Fill in the Blank** quizzes. |
| **Mermaid Diagram Generator** | Generate Flowchart, Sequence, ER Diagram, Gantt, Mindmap.  Errors are auto‑corrected with a secondary AI call; code is displayed as copy‑able text with links to external editors (Mermaid Live, Mermaid Docs, Kroki). |

---

## 🛠️ Installation
```bash
# Clone the repository
git clone https://github.com/your‑username/metamorphosis‑studio.git
cd metamorphosis‑studio

# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # on macOS / Linux
# .venv\Scripts\activate   # on Windows

# Install dependencies
pip install -r requirements.txt
```

### API Key
The app requires a **Google Gemini API key**.  Provide it in the **API** tab of the UI – the key is stored only in `st.session_state` and never written to disk.

---

## ▶️ Usage
```bash
streamlit run app.py
```
Open the URL shown in the terminal (usually `http://localhost:8501`).  Navigate through the tabs to access each feature.  All actions are performed in‑app; for diagrams you can copy the generated Mermaid code and paste it into any of the linked editors.

---

## 🎨 Design System
The UI uses custom CSS variables for theming (light/dark mode toggle stored in `st.session_state`).  Components follow a **soft‑lift card** style with focus‑glow inputs and pill‑style navigation.

---

## 🤝 Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome‑feature`).
3. Make your changes and ensure the app still runs (`streamlit run app.py`).
4. Submit a pull request with a clear description.

---

## 📄 License
This project is licensed under the **MIT License**.

---

## 📸 Screenshots
*(Add screenshots in `docs/` and reference them here, e.g. `![Home Tab](docs/home.png)`) *

---

*Happy coding!*
