import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("🚨 GOOGLE_API_KEY is not set in the .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini model (use 1.5 Pro or Flash depending on availability)
gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")


# 🔁 Simple Restoration (No RAG)
def restore_text_with_gemini(damaged_text, style="simple"):
    prompt = f"""
You are an expert document restoration assistant.

Restore the following damaged or incomplete text in a {style} writing style:

Damaged Text:
\"\"\"
{damaged_text}
\"\"\"

Provide the most accurate and readable restoration.
"""
    response = gemini_model.generate_content(prompt)
    return response.text.strip()


# 📚 RAG-based Retrieval
def retrieve_context(query_text):
    try:
        vectorstore = FAISS.load_local("rag_vector_db", OpenAIEmbeddings())
        results = vectorstore.similarity_search(query_text, k=2)
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        return "Context retrieval failed due to missing vector DB. Proceeding without external context."


# 🧠 RAG-Aware Restoration
def restore_text_with_rag(damaged_text, style="simple"):
    context = retrieve_context(damaged_text[:300])  # Use first 300 chars for query

    prompt = f"""
You are an AI restoration expert trained in restoring {style} style texts.

Use the context below to reconstruct the missing parts of the damaged text as faithfully and factually as possible.

Context:
\"\"\"
{context}
\"\"\"

Damaged Text:
\"\"\"
{damaged_text}
\"\"\"

Reconstruct the text while preserving its original meaning and tone.
"""
    response = gemini_model.generate_content(prompt)
    return response.text.strip()
