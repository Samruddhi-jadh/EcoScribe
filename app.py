import streamlit as st
import os, json, zipfile
from io import BytesIO
import json
import base64
import streamlit.components.v1 as components
from fpdf import FPDF
from dotenv import load_dotenv
from streamlit_cropper import st_cropper
from PIL import Image
import google.generativeai as genai
from genai.classify_text import classify_document_type
from genai.summarize_text import summarize_and_extract
from genai.restore_text import restore_text_with_gemini
from genai.title_keyword import extract_title_and_keywords
from ocr.ocr_utils import perform_ocr, simulate_damaged_text
from genai.restore_text import restore_text_with_rag


# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
os.makedirs("uploads", exist_ok=True)

def clickable_text(text, key_prefix):
    """Returns HTML where each word is clickable."""
    words = text.split()
    html = ""
    for i, word in enumerate(words):
        safe_word = word.replace('"', '&quot;')
        html += f'''
        <button onclick="document.getElementById('{key_prefix}_input').value = '{safe_word}'"
                style="border:none;background:transparent;color:#0a84ff;cursor:pointer;padding:1px;">{word}</button> '''
    return html

# Page Config
st.set_page_config(page_title="EcoScribe - OCR", layout="wide", initial_sidebar_state="expanded")
for key in ["restored_text", "extracted_results", "ocr_accuracy", "summary_texts", "titles", "keywords_map", "classifications", "cropped_files"]: # Add 'cropped_files' here as it's a list that needs initialization
    if key not in st.session_state:
        st.session_state[key] = {} if key not in ["cropped_files"] else [] # Initialize cropped_files as a list

def render_progress_timeline():
    if "uploaded_files" not in st.session_state or not st.session_state.uploaded_files:
        return

    st.markdown("### 🧾 Session Progress")

    # Iterate through the original uploaded files to track their individual progress
    for full_path in st.session_state.uploaded_files:
        # Use the full_path itself as the identifier for all checks
        file_identifier = full_path
        display_name = os.path.basename(full_path) # For display purposes only

        st.markdown(f"**📄 {display_name}**")

        steps = [
            ("📤 Uploaded", "uploaded_files"),
            ("✂️ Cropped", "cropped_files"),
            ("🧠 OCR Done", "extracted_results"),
            ("🔁 Restored", "restored_text"),
            ("📌 Summary", "summary_texts"),
            ("📑 Title/Keywords", "titles"),
            ("📂 Classified", "classifications"),
            ("📦 Exported", None),  # Optional future step
        ]

        for label, key in steps:
            completed = False
            if key:
                data = st.session_state.get(key)
                if data:
                    if isinstance(data, dict):
                        # Check if the file_identifier (full path) is a key in the dictionary
                        completed = file_identifier in data
                    elif isinstance(data, list):
                        # For lists (like cropped_files), check if the cropped version exists for this original file
                        # We need to be careful here: if you're replacing the original with a cropped one in the list,
                        # the check should be based on the path of the cropped file.
                        # For simplicity and consistency with other steps, let's assume 'cropped_files'
                        # will also store full paths like 'uploads/cropped_original.png'
                        # A better approach for 'cropped' would be to store a mapping of original_path: cropped_path
                        # For now, let's ensure that if a cropped file exists for the *original* file, it's marked.
                        if key == "cropped_files":
                            # This check now looks for a cropped file that *originated* from the current file_identifier
                            completed = any(os.path.basename(file_identifier) in os.path.basename(f) for f in data)
                        else:
                            completed = file_identifier in data # This might not be used for lists if they're not paths

            check = "✅" if completed else "⬜"
            st.markdown(f"{check} {label}")

        st.markdown("---")

# --- Sidebar Navigation ---
with st.sidebar:
    theme = st.radio("🌓 Choose Theme", ["🌞 Light Mode", "🌚 Dark Mode"], horizontal=True)
    steps =  [
        "🏠 Home",
        "📤 Upload Documents",
        "✂️ Crop Images",
        "🧠 Batch OCR",
        "📝 View Extracted Text",
        "🔁 Damage & Restore",
        "📌 Summary & Metadata",
        "📑 Title & Keywords",
        "📦 Export",
        "📂 Classify Document",
        "💬 Chat Assistant",
        "🎨 Poster & Storyboard Generator"
    ]
    section = st.radio("🔹 Navigate", steps, index=0)
    st.markdown("---")
    render_progress_timeline()
    st.caption("Crafted with ❤️ using Streamlit")

# --- Theme Styles ---
if theme == "🌚 Dark Mode":
    st.markdown("""
    <style>
        .stApp { background-color: #1e1e2f; color: #f0f0f0; }
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"],
        .stRadio > div,
        .stDownloadButton button {
            background-color: #2c2c4e;
            color: #00f0ff !important;
        }
        .stButton button {
            background-color: #4454ff;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
        <style>
        .stApp { background: #f5f5f5; color: #111; }
        .stButton>button { background: #003B73 !important; color: #fff;}
        .stDownloadButton>button { background: #007ACC !important; }
        .card { background: #ffffff; padding:12px; border-radius:8px; margin-bottom:8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .card h4 { margin:4px;}
        </style>
    """, unsafe_allow_html=True)

# --- Branding ---
# Display the image first using Streamlit (not in the HTML)
# Function to convert image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Center the image with fixed width
image_base64 = get_base64_image("uploads/EcoScribe.png")  # Use your actual path
st.markdown(
    f"""
    <div style='text-align: center; margin-top:10px; margin-bottom:10px;'>
        <img src='data:image/png;base64,{image_base64}' width='200'/>
    </div>
    """,
    unsafe_allow_html=True
)

# Then show the styled HTML header
st.markdown("""
    <div style='text-align:center; padding:1rem; background:linear-gradient(90deg,#00CCFF,#0044CC); border-radius:8px;'>
        <h1 style='color:#fff; margin:0;'>🕰️ EcoScribe 🕰️</h1>
        <p style='color:#eef; font-style:italic; margin:4px;'>"Bringing historical documents back to life with AI-powered clarity, context, and creativity."</p>
    </div>
""", unsafe_allow_html=True)

# Helper: progress tracker
progress_index = steps.index(section) + 1
st.progress(progress_index / len(steps))
 
# --- 🏠 Home Page ---
if section == "🏠 Home":
    st.markdown("---")

    st.markdown("""
    <div style='text-align:center; font-size:1.05rem; line-height:1.6;'>
        <h3>🧭 Use the sidebar to navigate through each feature:</h3>
        <p>📤 Upload scanned documents</p>
        <p>✂️ Crop and prepare for OCR</p>
        <p>🧠 Perform OCR and evaluate accuracy</p>
        <p>🔁 Restore damaged text with GenAI or RAG</p>
        <p>📌 Summarize, extract titles and keywords</p>
        <p>🎨 Generate storyboards or AI image prompts</p>
        <p>💬 Ask Gemini chatbot for help</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("🚀 Start by clicking **'📤 Upload Documents'** in the sidebar.")

 
# --- 📤 Upload Documents ---
elif section == "📤 Upload Documents":
    st.header("📤 Upload Documents")
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []

    uploaded_files = st.file_uploader(
        "Upload one or more scanned documents",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if uploaded_files:
        uploaded_paths = []
        for file in uploaded_files:
            path = os.path.join("uploads", file.name)
            with open(path, "wb") as f:
                f.write(file.getbuffer())
            uploaded_paths.append(path)
        st.session_state.uploaded_files = uploaded_paths
        st.success(f"✅ {len(uploaded_paths)} file(s) uploaded.")
        st.image(uploaded_paths, caption="Uploaded Images", use_column_width=True)

# --- ✂️ Crop Uploaded Images ---
elif section == "✂️ Crop Images":
    st.header("✂️ Crop Scanned Document for Better OCR")

    if "uploaded_files" not in st.session_state or not st.session_state.uploaded_files:
        st.warning("⚠️ Please upload documents first.")
    else:
        # Use a copy to avoid modifying list during iteration if we remove files
        current_uploaded_files = list(st.session_state.uploaded_files)

        for img_path in current_uploaded_files:
            st.subheader(f"🖼️ {os.path.basename(img_path)}")

            # Load image
            image = Image.open(img_path)
            cropped_img = st_cropper(
                image,
                realtime_update=True,
                box_color="#00FFAA",
                aspect_ratio=None
            )

            # Save cropped image to replace original if user wants
            # Create a unique name for the cropped file to avoid conflicts and track it
            cropped_file_name = f"cropped_{os.path.basename(img_path)}"
            save_path = os.path.join("uploads", cropped_file_name)

            if st.button(f"💾 Save Cropped Version of {os.path.basename(img_path)}", key=f"save_crop_{img_path}"):
                cropped_img.save(save_path)

                # Update session state for cropped files.
                # It's crucial to associate the original file with its cropped version.
                # A dictionary mapping original path to cropped path would be ideal here.
                # For simplicity with your current structure, let's add the cropped path to a list
                # and ensure it's checked in render_progress_timeline.
                # We also need to decide if cropping *replaces* the original for future steps
                # or if the cropped version is just an *alternative*.
                # Given your OCR section's 'ocr_source', it seems it should be an alternative.
                if save_path not in st.session_state.cropped_files:
                    st.session_state.cropped_files.append(save_path)

                st.success("✅ Cropped image saved and will be used for OCR.")

            # Display cropped image preview if available
            if os.path.exists(save_path):
                st.image(save_path, caption=f"Preview: {cropped_file_name}", use_column_width=True)


# --- 🧠 Batch OCR ---
elif section == "🧠 Batch OCR":
    st.header("🧠 Run OCR on Uploaded Documents")

    if "uploaded_files" not in st.session_state or not st.session_state.uploaded_files:
        st.warning("⚠️ Please upload documents first.")
    else:
        # OCR Options
        psm_options = {
            3: "Fully automatic page segmentation",
            4: "Column-wise reading",
            6: "Uniform block of text",
            7: "Single line",
            11: "Sparse text",
            12: "Sparse w/ OCR engine"
        }
        langs = {
            "English": "eng",
            "Hindi": "hin",
            "Marathi": "mar",
            "Telugu": "tel",
            "Arabic": "ara",
            "Spanish": "spa"
        }

        # User Selections
        psm = st.selectbox("Select PSM Mode", list(psm_options.keys()), format_func=lambda x: f"{x} - {psm_options[x]}")
        lang = st.selectbox("OCR Language", list(langs.keys()))

        # Helper for confidence visualization
        def highlight_ocr_text(text, word_confidences):
            words = text.split()
            highlighted = []
            for word in words:
                confidence = word_confidences.get(word.strip(), 100)  # default 100%
                color = "green" if confidence >= 85 else "orange" if confidence >= 70 else "red"
                highlighted.append(f'<span style="color:{color}">{word}</span>')
            return " ".join(highlighted)

        # Run OCR Button
        if st.button("🔍 Run OCR for All Files"):
            st.session_state.extracted_results = {}
            st.session_state.ocr_accuracy = {}

            # Determine OCR source: cropped file > original
            ocr_source_map = {}
            for original_path in st.session_state.uploaded_files:
                cropped = next((cp for cp in st.session_state.cropped_files if os.path.basename(original_path) in os.path.basename(cp)), None)
                ocr_source_map[original_path] = cropped if cropped else original_path

            with st.spinner("Running OCR on all files..."):
                for original_path, path_to_ocr in ocr_source_map.items():
                    text, accuracy = perform_ocr(path_to_ocr, psm=psm, lang=langs[lang])
                    st.session_state.extracted_results[original_path] = text
                    st.session_state.ocr_accuracy[original_path] = accuracy

            st.success("✅ OCR complete for all documents!")

        # Show Results
        for original_path, text in st.session_state.extracted_results.items():
            st.subheader(f"📄 {os.path.basename(original_path)}")

            # Confidence simulation (replace with real data if available)
            word_confidences = {w: 80 + (i % 20) for i, w in enumerate(text.split())}
            highlighted_html = highlight_ocr_text(text, word_confidences)
            st.markdown("### 🔎 OCR Confidence Highlight", unsafe_allow_html=True)
            st.markdown(highlighted_html, unsafe_allow_html=True)

            # Inline edit + GenAI reprocess
            edited_text = st.text_area("✏️ Edit OCR Text", text, height=250, key=f"edit_ocr_{original_path}")
            if st.button("🔁 Reprocess with GenAI", key=f"reprocess_btn_{original_path}"):
                new_summary = summarize_and_extract(edited_text)
                st.session_state.summary_texts[original_path] = new_summary
                st.success("✅ Reprocessed and updated summary.")

            # Accuracy info
            st.info(f"🔍 Estimated OCR Accuracy: **{st.session_state.ocr_accuracy.get(original_path, 0)}%**")

            # Export confidence heatmap as HTML
            if st.button("📥 Export OCR Heatmap (HTML)", key=f"export_heatmap_{original_path}"):
                heatmap_html = highlight_ocr_text(text, word_confidences)
                export_path = os.path.join("uploads", f"ocr_heatmap_{os.path.basename(original_path)}.html")
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(heatmap_html)
                with open(export_path, "rb") as f:
                    st.download_button(
                        "📄 Download Heatmap",
                        f,
                        file_name=os.path.basename(export_path),
                        mime="text/html",
                        key=f"download_heatmap_{original_path}"
                    )



# --- 📝 View Extracted Text ---
elif section == "📝 View Extracted Text":
    st.header("📝 Extracted Text")
    if "extracted_results" not in st.session_state or not st.session_state.extracted_results:
        st.info("⚠️ No OCR output found.")
    else:
        for file_path, text in st.session_state.extracted_results.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")

            # Show OCR confidence score
            accuracy = st.session_state.ocr_accuracy.get(file_path, 0)
            st.markdown(f"🔍 **Estimated OCR Accuracy:** `{accuracy}%`")

            # Optionally show as progress bar
            st.progress(accuracy / 100)

            st.text_area("Extracted Text", text, height=300)


# --- 🔁 Damage & Restore ---
elif section == "🔁 Damage & Restore":
    st.header("🔁 Simulate Damage & Restore Text")
    if "extracted_results" not in st.session_state or not st.session_state.extracted_results:
        st.warning("⚠️ Please complete OCR first.")
    else:
        for file_path, text in st.session_state.extracted_results.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")
            damaged = simulate_damaged_text(text)
            style = st.radio(f"Restoration Style for {os.path.basename(file_path)}", ["simple", "legal", "academic"], key=f"style_{file_path}")

            # Ensure restored_text is initialized for each file if not already
            if file_path not in st.session_state.restored_text:
                st.session_state.restored_text[file_path] = ""

            if st.button(f"🛠️ Restore {os.path.basename(file_path)}", key=f"restore_btn_toggle_{file_path}"):
                with st.spinner("Restoring..."):
                    restored = restore_text_with_rag(damaged, style=style)

                    st.session_state.restored_text[file_path] = restored # Store using full path
                st.success("✅ Restoration Done!")

            # Show Before/After Comparison Side by Side
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🧱 Damaged Text")
                st.text_area("Damaged Text", damaged, height=250, key=f"damaged_{file_path}")

            with col2:
                st.markdown("#### 🛠️ Restored Text")
                restored_output = st.session_state.restored_text.get(file_path, "")
                st.markdown("#### 🛠️ Restored Output (Click any word to ask why it was used)")
                html = clickable_text(restored_output, key_prefix=os.path.basename(file_path))
                components.html(html, height=150, scrolling=True)

                clicked_word = st.text_input("🔍 Ask Why this Word was Used", key=f"{file_path}_input")

                if st.button("🤔 Explain Word Choice", key=f"explain_btn_{file_path}"):
                    full_context = restored_output
                    explanation_prompt = f"""
                You're an explainable AI model for document restoration.

                The following text was restored from a damaged document:
                \"\"\"{full_context}\"\"\"

                The user clicked on the word: **{clicked_word}**

                Explain **why** this word may have been chosen by the AI model. Consider:
                - Writing style (e.g., academic, legal)
                - Context around the word
                - Relevance to the document’s theme

                Keep the explanation concise but insightful.
                """
                    with st.spinner("Thinking..."):
                        explanation = restore_text_with_gemini(explanation_prompt)
                        st.success("✅ Explanation:")
                        st.markdown(f"> {explanation}")


            user_feedback = st.text_area("💬 Provide Feedback to Improve Restoration", "", key=f"feedback_input_{file_path}")
            use_rag = st.checkbox("🔍 Use RAG-based Contextual Restoration", key=f"use_rag_{file_path}")

            if st.button(f"🛠️ Restore {os.path.basename(file_path)}", key=f"restore_btn_{os.path.basename(file_path).replace('.', '_').replace(' ', '_')}"):
                with st.spinner("Restoring..."):
                    if use_rag:
                        restored = restore_text_with_rag(damaged, style=style)
                    else:
                        restored = restore_text_with_gemini(damaged, style=style)
                    st.session_state.restored_text[file_path] = restored
                st.success("✅ Restoration Done!")

            if st.button("📨 Submit Feedback", key=f"submit_feedback_{file_path}"):
                # Simulate prompt enhancement (optionally log for fine-tuning later)
                enhanced_prompt = f"Feedback: {user_feedback}\nText: {restored_output}"
                refined_output = restore_text_with_gemini(enhanced_prompt)
                st.session_state.restored_text[file_path] = refined_output
                st.success("✅ Restoration refined with feedback.")



# --- 📌 Summary & Metadata ---
elif section == "📌 Summary & Metadata":
    st.header("📌 Generate Summary & Metadata")
    if "restored_text" not in st.session_state or not st.session_state.restored_text:
        st.warning("⚠️ Please restore text first.")
    else:
        for file_path, restored_text in st.session_state.restored_text.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")
            st.text_area("Restored Text", restored_text, height=250)
            if st.button(f"📄 Summarize {os.path.basename(file_path)}", key=f"summarize_btn_{file_path}"):
                with st.spinner("Summarizing..."):
                    summary = summarize_and_extract(restored_text)
                    st.session_state.summary_texts[file_path] = summary # Store using full path
                st.success("✅ Summary Generated!")

            if file_path in st.session_state.summary_texts:
                st.text_area("Summary", st.session_state.summary_texts[file_path], height=200)

# --- 📑 Title & Keywords ---
elif section == "📑 Title & Keywords":
    st.header("📑 Title & Keywords Extraction")
    if "restored_text" not in st.session_state or not st.session_state.restored_text:
        st.warning("⚠️ Please restore text first.")
    else:
        for file_path, restored_text in st.session_state.restored_text.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")
            if st.button(f"🎯 Extract for {os.path.basename(file_path)}", key=f"extract_btn_{file_path}"):
                with st.spinner("Extracting..."):
                    title, keywords = extract_title_and_keywords(restored_text)
                    st.session_state.titles[file_path] = title # Store using full path
                    st.session_state.keywords_map[file_path] = keywords # Store using full path
                st.success("✅ Extraction Complete!")

            if file_path in st.session_state.titles:
                st.text_input("Title", st.session_state.titles[file_path], key=f"title_input_{file_path}")

            if file_path in st.session_state.keywords_map:
                st.text_area("Keywords", ", ".join(st.session_state.keywords_map[file_path]), height=100, key=f"keywords_area_{file_path}")

# --- 📦 Export Section ---
elif section == "📦 Export":
    st.header("📦 Export Content")
    if "restored_text" not in st.session_state or not st.session_state.restored_text:
        st.warning("⚠️ Please restore content first.")
    else:
        for file_path, content in st.session_state.restored_text.items():
            file_name = os.path.basename(file_path)
            export_type = st.selectbox(f"Export Format for {file_name}", ["TXT", "PDF", "JSON"], key=f"export_type_{file_name}")
            export_data = st.radio(f"Export What for {file_name}", ["Restored Text", "Summary"], key=f"choice_data_{file_name}")
            text = content if export_data == "Restored Text" else st.session_state.summary_texts.get(file_path, "")
            base = "restored" if export_data == "Restored Text" else "summary"

            if export_type == "TXT":
                st.download_button("📄 Download TXT", data=text, file_name=f"{base}_{file_name}.txt", key=f"dl_txt_{file_name}")
            elif export_type == "JSON":
                json_data = {"type": export_data, "text": text}
                st.download_button("🧾 Download JSON", data=json.dumps(json_data, indent=2), file_name=f"{base}_{file_name}.json", key=f"dl_json_{file_name}")
            elif export_type == "PDF":
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in text.split("\n"):
                    pdf.multi_cell(0, 10, line)
                pdf_output_path = os.path.join("uploads", f"{base}_{file_name}.pdf") # Save to uploads to ensure path is correct
                pdf.output(pdf_output_path)
                with open(pdf_output_path, "rb") as f:
                    st.download_button("📕 Download PDF", data=f, file_name=os.path.basename(pdf_output_path), mime="application/pdf", key=f"dl_pdf_{file_name}")

# --- 📂 Classify Document ---
elif section == "📂 Classify Document":
    st.header("📂 Classify Document Type")
    if "restored_text" not in st.session_state or not st.session_state.restored_text:
        st.warning("⚠️ Please restore content first.")
    else:
        for file_path, restored in st.session_state.restored_text.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")
            if st.button(f"🔍 Classify {os.path.basename(file_path)}", key=f"classify_btn_{file_path}"):
                with st.spinner("Classifying..."):
                    result = classify_document_type(restored)
                    st.session_state.classifications[file_path] = result # Store using full path
                st.success("✅ Classification Complete!")
            if file_path in st.session_state.classifications:
                st.text_area("Classification", st.session_state.classifications[file_path], height=200, key=f"classification_output_{file_path}")

# --- 💬 Chat with Assistant ---
elif section == "💬 Chat Assistant":
    st.header("💬 EcoScribe Assistant")
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error("🚨 GOOGLE_API_KEY not set in .env file")
    else:
        # Initialize the generative model for chat
        # The change is here: Directly use "gemini-pro" as the model name.
        # The library handles the correct API version (v1) automatically.
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        # Chat UI
        st.title("🧠 Gemini Chatbot")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_input = st.text_input("You:", key="user_input")

        if user_input:
            try:
                with st.spinner("Gemini is thinking..."):
                    # For conversational turns, it's better to use chat sessions
                    # to maintain context. If you just want single-turn responses,
                    # model.generate_content(user_input) is fine.
                    # For a true chatbot, you'd want to initialize a chat session:
                    # chat = model.start_chat(history=st.session_state.chat_history)
                    # response = chat.send_message(user_input)
                    
                    # For simplicity, sticking to generate_content, but be aware
                    # it won't have conversational memory unless you manage it explicitly.
                    response = model.generate_content(user_input)
                    reply = response.text
                    st.session_state.chat_history.append(("You", user_input))
                    st.session_state.chat_history.append(("Gemini", reply))
            except Exception as e:
                st.error(f"❌ Gemini Error: {e}")

        for role, message in st.session_state.chat_history:
            st.markdown(f"**{role}:** {message}")
# --- 🎨 Poster Prompt Generation ---
elif section == "🎨 Poster & Storyboard Generator":
    st.header("🎨 Generate AI Poster Prompts")

    if "restored_text" not in st.session_state or not st.session_state.restored_text:
        st.warning("⚠️ Please restore content first.")
    else:
        for file_path, restored_text in st.session_state.restored_text.items():
            st.subheader(f"📄 {os.path.basename(file_path)}")

            poster_key = f"poster_prompt_{file_path}"

            if st.button(f"🎬 Generate Poster Prompt for {os.path.basename(file_path)}", key=f"poster_btn_{file_path}"):
                with st.spinner("Crafting visual scene description..."):
                    poster_prompt = restore_text_with_gemini(f"""
You are a creative poster scene generator.

Based on the following slide image context and extracted description, generate a **visually rich prompt** suitable for DALL·E or Stable Diffusion:

---
📸 Slide context (summary of visual elements):
- Text-heavy slide about Old English history
- Mentions Anglo-Frisian settlers, dialects like Mercian, Northumbrian, Kentish, West Saxon
- Mentions runic alphabet
- Suggests early medieval Britain

📝 Extracted OCR Text:
\"\"\"{restored_text}\"\"\"

🖼️ Goal:
Create a vivid image generation prompt describing a **poster or storyboard scene** with accurate setting, mood, and atmosphere. Be creative and historically inspired.
""")

                    st.session_state[poster_key] = poster_prompt
                st.success("✅ Poster Prompt Generated!")

            # Display if poster prompt already exists
            if poster_key in st.session_state:
                prompt_text = st.session_state[poster_key]
                st.text_area("🎨 Generated Poster Prompt", prompt_text, height=250)

                # ✅ Copy Prompt Button
                st.download_button(
                    label="📋 Copy Prompt",
                    data=prompt_text,
                    file_name="poster_prompt.txt",
                    mime="text/plain",
                    key=f"copy_btn_{file_path}"
                )

                # 🔗 Links to AI image generators
                st.markdown("#### 🔗 Generate Image Using:")
                st.markdown(f"""
- [🖼️ Craiyon (Free)](https://www.craiyon.com/)
- [🎨 Hugging Face Diffusion](https://huggingface.co/spaces/stabilityai/stable-diffusion)
- [🧠 DALL·E (OpenAI)](https://openai.com/dall-e)
                """, unsafe_allow_html=True)

                st.info("✨ Copy the prompt and paste it into your favorite image tool to generate visual posters.")
