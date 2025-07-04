# genai/classify_text.py

import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use Gemini 1.5 Flash model
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

def classify_document_type(text):
    global model
    if model is None:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

    prompt = f"""You are an intelligent AI trained to classify documents into one of the following categories:
- Legal
- Historical
- Academic
- General

Read the following text and assign the most appropriate category. Also explain why.

--- Document Start ---
{text}
--- Document End ---

Return output in this format:
Category: <Best match>
Reason: <Short reason>"""
    response = model.generate_content(prompt)
    return response.text.strip()
