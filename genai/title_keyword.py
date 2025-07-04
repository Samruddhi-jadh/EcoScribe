import google.generativeai as genai
import os

# Load API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Set this in .env file

def extract_title_and_keywords(text):
    prompt = f"""
    You are an AI document assistant.

    Analyze the following document and return:
    1. A concise and informative title (max 12 words)
    2. 5 to 10 relevant keywords

    Document:
    \"\"\"{text}\"\"\"

    Format your response as:
    Title: <title here>
    Keywords: <comma-separated list>
    """

    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")
    response = model.generate_content(prompt)

    output = response.text.strip()
    lines = output.splitlines()

    title = ""
    keywords = []

    for line in lines:
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("keywords:"):
            keywords = [kw.strip() for kw in line.split(":", 1)[1].split(',')]

    return title, keywords
