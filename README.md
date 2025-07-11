# 🕰️ EcoScribe :"Bringing historical documents back to life with AI-powered clarity, context, and creativity."
EcoScribe is an AI-powered document restoration and intelligence platform that revives scanned, historical, and damaged documents using OCR and Generative AI. From text extraction to intelligent restoration and summarization, EcoScribe helps bring lost or degraded documents back to life — with modern usability.

(uploads/EcoScribe.png)

---
## 🌐 Live Demo

🔗 **Deployed App**: [[Try EcoScribe on Streamlit Cloud](https://ecoscribe-ai.streamlit.app/)](https://ecoscribe-ai.streamlit.app/)  
---

## 🚀 Features

- 📤 **Upload Scanned Documents**  
  Upload one or multiple scanned or damaged documents for processing.

- ✂️ **Crop Images for Optimal OCR**  
  Interactive cropping UI to isolate the text regions before OCR.

- 🌍 **Multilingual OCR Support**  
  OCR support for English, Hindi, Marathi, Telugu, Arabic, Spanish (and extendable).

- 🧠 **Smart OCR with Accuracy Highlighting**  
  Extract text with confidence scoring, and view word-level color highlights.

- 🛠️ **AI-Based Restoration (GenAI & RAG)**  
  Restore incomplete or degraded text using Gemini and Retrieval-Augmented Generation.

- ✏️ **Inline Text Editing + Feedback Refinement**  
  Edit extracted text manually and regenerate output with user feedback.

- 📌 **Summarization + Metadata Extraction**  
  Automatically generate summaries, titles, and keywords from restored text.

- 📑 **Document Classification**  
  Use LLMs to identify document type (e.g., legal, academic, historical).

- 🎨 **AI Poster & Storyboard Generator**  
  Turn your documents into visual generation prompts for posters or slides.

- 📦 **Export Options**  
  Download restored or summarized content in TXT, PDF, or JSON formats.

- 💬 **Gemini Chat Assistant**  
  Ask contextual questions, explain restored content, or clarify decisions.

---

## 🧠 Tech Stack

- **Frontend**: Streamlit (Responsive UI + Theming)
- **OCR Engine**: Tesseract OCR + Custom Preprocessing
- **AI Models**: Gemini 1.5 (Google Generative AI)
- **GenAI Integration**: LangChain + FAISS (RAG support)
- **Backend Utilities**: Python, OpenCV, PIL, dotenv, FPDF

---

## 🛠️ Setup Instructions

1. **Clone the repository**
```bash
git clone (https://github.com/Samruddhi-jadh/EcoScribe)
cd ecoscribe
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Add your API key**
**Create a .env file and add your Gemini API key:**
```bash
GEMINI_API_KEY=your_api_key_here
```

4. **Run the streamlit app**
```bash
streamlit run app.py
```
5. **Repository Structure**
ecoscribe/
├── app.py
├── genai/
│   ├── restore_text.py
│   ├── summarize_text.py
│   ├── classify_text.py
│   └── title_keyword.py
├── ocr/
│   └── ocr_utils.py
├── requirements.txt
├── .env
└── uploads/

6. **🔮 Future Scope**
- 🧠 Fine-tuned domain-specific restoration (legal/historical)

- 📚 Vector DB integration for RAG with custom knowledge bases

- 🗂 Bulk export tools & admin dashboards

- 🌍 Language expansion with inline translation

- 🧩 Plugin architecture for modular AI workflows
