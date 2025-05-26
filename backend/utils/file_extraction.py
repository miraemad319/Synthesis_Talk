from pdfminer.high_level import extract_text
from docx import Document

# Extract text content from a PDF file using pdfminer
def extract_text_from_pdf(file_path):
    try:
        return extract_text(file_path)
    except Exception as e:
        return f"Error extracting PDF text: {e}"

# Read plain text from a .txt file
def extract_text_from_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading TXT file: {e}"

# Extract text from a Word (.docx) file using python-docx
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        return f"Error reading DOCX file: {e}"
