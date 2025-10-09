from pypdf import PdfReader

def load_pdf(file_like):
    reader = PdfReader(file_like)
    text = ""
    for page in reader.pages:
        t = page.extract_text() or ""
        if t:
            text += t + "\n"
    return text.strip()
