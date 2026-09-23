# FILE: app/loader.py
"""
Step 1 of RAG: read the PDF files and get their text, page by page.
We keep the page number so we can show citations later.
"""
import os
from pypdf import PdfReader


def load_pdf(file_path):
    """Read one PDF. Return a list of pages like {"source": ..., "page": ..., "text": ...}."""
    reader = PdfReader(file_path)
    file_name = os.path.basename(file_path)

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())  # remove extra spaces and line breaks

        if len(text) > 0:  # skip empty pages (for example, image-only pages)
            pages.append({"source": file_name, "page": page_number, "text": text})

    return pages


def load_all_pdfs(folder):
    """Read every PDF inside a folder."""
    all_pages = []
    for file_name in sorted(os.listdir(folder)):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(folder, file_name)
            pages = load_pdf(file_path)
            print(f"Loaded {file_name}: {len(pages)} pages with text")
            all_pages.extend(pages)
    return all_pages