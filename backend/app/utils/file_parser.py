import io
import os
import email
from email import policy
from email.parser import BytesParser
from typing import Tuple
from pypdf import PdfReader
from docx import Document
from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".eml"}


def validate_file(file: UploadFile) -> Tuple[str, str]:
    """
    Validates file extension and size.
    Returns (filename, extension_lower).
    Raises HTTPException if invalid.
    """
    filename = file.filename or "unknown"
    _, ext = os.path.splitext(filename)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext_lower}'. Allowed types: PDF, DOCX, TXT, EML."
        )

    return filename, ext_lower


async def extract_text_from_upload(file: UploadFile) -> str:
    """
    Reads upload content safely up to MAX_FILE_SIZE_BYTES and parses based on extension.
    """
    filename, ext_lower = validate_file(file)

    # Read bytes safely with size check
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of 10 MB (received {len(content) / (1024*1024):.2f} MB)."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    try:
        if ext_lower == ".pdf":
            return extract_from_pdf(content)
        elif ext_lower == ".docx":
            return extract_from_docx(content)
        elif ext_lower == ".txt":
            return extract_from_txt(content)
        elif ext_lower == ".eml":
            return extract_from_eml(content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext_lower}")
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Document parsing error for '%s': %s", filename, str(e))
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse document '{filename}'. Please ensure the document is not corrupted or password-protected."
        )


def extract_from_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    extracted_text = []
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            extracted_text.append(f"--- Page {idx + 1} ---\n{page_text}")
    
    full_text = "\n\n".join(extracted_text).strip()
    if not full_text:
        raise ValueError("No readable text found in PDF. Note that image-only/scanned PDFs require text layers.")
    return full_text


def extract_from_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # Also extract text from tables if any
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
            if row_text:
                paragraphs.append(row_text)
    
    full_text = "\n".join(paragraphs).strip()
    if not full_text:
        raise ValueError("No readable text found in DOCX file.")
    return full_text


def extract_from_txt(content: bytes) -> str:
    # Try utf-8 first, fallback to latin-1
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")
    
    if not text.strip():
        raise ValueError("Text file is empty or contains only whitespace.")
    return text.strip()


def extract_from_eml(content: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(content)
    parts = []

    # Extract headers
    headers = []
    for h in ["Subject", "From", "To", "Date", "Cc"]:
        val = msg.get(h)
        if val:
            headers.append(f"{h}: {val}")
    if headers:
        parts.append("\n".join(headers))

    # Extract body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get_content_disposition() or "")
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_content()
                break
    else:
        body = msg.get_content()

    if body:
        parts.append(str(body).strip())

    full_text = "\n\n".join(parts).strip()
    if not full_text:
        raise ValueError("Could not extract readable text content from EML file.")
    return full_text
