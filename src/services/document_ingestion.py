"""Bounded extraction of study text from user-uploaded documents."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
from pypdf import PdfReader

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_CHARS = 50_000
MAX_PDF_PAGES = 100
MAX_DOCX_EXPANDED_BYTES = 50 * 1024 * 1024
SUPPORTED_DOCUMENT_TYPES = {"txt", "pdf", "docx", "csv", "json"}


def extract_uploaded_text(uploaded_file: Any) -> str:
    """Extract a bounded text preview from a Streamlit-style uploaded file.

    The upload is size-checked before calling getvalue() when the upload object
    exposes its size. Extracted content is capped before it can be sent to an
    external model provider.
    """
    filename = str(getattr(uploaded_file, "name", ""))
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_DOCUMENT_TYPES:
        raise ValueError("Unsupported file type. Use TXT, PDF, DOCX, CSV, or JSON.")

    declared_size = getattr(uploaded_file, "size", None)
    if isinstance(declared_size, int) and declared_size > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 10 MiB upload limit.")

    data = uploaded_file.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 10 MiB upload limit.")

    if suffix in {"txt", "csv", "json"}:
        text = data.decode("utf-8", errors="replace")

    elif suffix == "pdf":
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDF exceeds the {MAX_PDF_PAGES}-page limit.")

        chunks: list[str] = []
        remaining = MAX_DOCUMENT_CHARS
        for page in reader.pages:
            if remaining <= 0:
                break
            page_text = page.extract_text() or ""
            chunk = page_text[:remaining]
            chunks.append(chunk)
            remaining -= len(chunk)
        text = "\n\n".join(chunks)

    elif suffix == "docx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            expanded_size = sum(info.file_size for info in archive.infolist())
        if expanded_size > MAX_DOCX_EXPANDED_BYTES:
            raise ValueError("DOCX expands beyond the 50 MiB processing limit.")

        document = Document(io.BytesIO(data))
        chunks: list[str] = []
        remaining = MAX_DOCUMENT_CHARS
        for paragraph in document.paragraphs:
            if remaining <= 0:
                break
            paragraph_text = paragraph.text
            if paragraph_text:
                chunk = paragraph_text[:remaining]
                chunks.append(chunk)
                remaining -= len(chunk)
        text = "\n".join(chunks)

    else:  # pragma: no cover - the allowlist above is exhaustive
        raise ValueError("Unsupported file type.")

    return text[:MAX_DOCUMENT_CHARS]
