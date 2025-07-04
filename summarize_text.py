# genai/summarize_text.py

import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini with your API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use the Gemini Pro model (more stable than Flash)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

def summarize_and_extract(text):
    prompt = f"""
You are a smart AI document assistant.

Your task is to:
1. Summarize the document in 2-3 lines.
2. Extract structured metadata if available.

Only use the content provided below and do NOT hallucinate.
If any field is not present in the document, return "Not found".

--- Document Start ---
{text}
--- Document End ---

Return the result in this structured format exactly:

Summary:
<Brief summary>

Metadata:
- Title: <Document title or subject>
- Author/Signatory: <Name of person or organization>
- Date: <Any date mentioned>
- Keywords: <Important keywords, comma-separated>
- Domain: <Choose one: Historical, Legal, Academic, General>
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini API Error: {str(e)}"
