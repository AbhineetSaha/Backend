import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-pro")

def generate_answer(query: str, context: str) -> str:
    prompt = f"""
    You are an expert assistant.
    Use only the following context to answer the question accurately and concisely.
    If the answer is not in the context, say "I couldn’t find that in the document."

    Context:
    {context}

    Question: {query}
    Answer:
    """
    res = model.generate_content(prompt)
    return (res.text or "").strip()
