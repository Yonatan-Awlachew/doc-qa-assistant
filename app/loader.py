"""
Step 1 of RAG: read a file and get its text, page by page.
v2: supports PDF, Word (.docx) and plain text (.txt, .md).

Every function returns the SAME format, so the rest of the code does not care
about the file type:
    [{"source": "name.pdf", "page": 1, "text": "..."}, ...]
"""
import os

from docx import Document
from pypdf import PdfReader

TEXT_PAGE_SIZE = 3000  # .txt/.docx have no real pages: we cut them every 3000 characters


def clean_text(text):
    return " ".join(text.split())  # remove extra spaces and line breaks


def load_pdf(file_path, display_name):
    reader = PdfReader(file_path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if len(text) > 0:  # skip empty pages (for example, image-only pages)
            pages.append({"source": display_name, "page": page_number, "text": text})
    return pages


def split_into_pages(text, display_name):
    """For files without real pages: make 'pages' of about 3000 characters."""
    pages = []
    for i in range(0, len(text), TEXT_PAGE_SIZE):
        piece = text[i:i + TEXT_PAGE_SIZE]
        pages.append({"source": display_name, "page": len(pages) + 1, "text": piece})
    return pages


def load_docx(file_path, display_name):
    document = Document(file_path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    text = clean_text(" ".join(paragraphs))
    return split_into_pages(text, display_name)


def load_txt(file_path, display_name):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = clean_text(f.read())
    return split_into_pages(text, display_name)


def load_file(file_path, display_name):
    """Choose the right reader from the file extension."""
    extension = os.path.splitext(display_name)[1].lower()
    if extension == ".pdf":
        return load_pdf(file_path, display_name)
    if extension == ".docx":
        return load_docx(file_path, display_name)
    if extension in (".txt", ".md"):
        return load_txt(file_path, display_name)
    raise ValueError(f"Unsupported file type: {extension}")


def count_pdf_pages(file_path):
    return len(PdfReader(file_path).pages)