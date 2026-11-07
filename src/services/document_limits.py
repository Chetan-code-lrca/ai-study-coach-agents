"""Resource limits for uploaded study documents."""

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_CHARS = 50_000
MAX_PDF_PAGES = 100
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


def validate_upload_size(size: int) -> None:
    """Reject empty or oversized uploads before parsing their contents."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 1:
        raise ValueError("The uploaded file is empty or has an invalid size.")
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("Files must be 10 MB or smaller. Split the document and retry.")


def validate_extracted_text(text: str) -> str:
    """Keep extracted/pasted text within a predictable prompt and memory budget."""
    if not isinstance(text, str):
        raise ValueError("The extracted document content is not text.")
    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError(
            f"Extracted text exceeds {MAX_DOCUMENT_CHARS:,} characters. "
            "Split the document into smaller sections and retry."
        )
    return text
