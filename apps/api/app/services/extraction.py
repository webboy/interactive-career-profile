import io
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.enums import DocumentFileType


class ExtractionError(Exception):
    pass


def detect_file_type(filename: str, mime_type: str | None = None) -> DocumentFileType:
    extension = Path(filename).suffix.lower()
    mapping = {
        ".pdf": DocumentFileType.PDF,
        ".docx": DocumentFileType.DOCX,
        ".txt": DocumentFileType.TXT,
        ".md": DocumentFileType.MARKDOWN,
        ".markdown": DocumentFileType.MARKDOWN,
    }
    if extension in mapping:
        return mapping[extension]

    if mime_type == "application/pdf":
        return DocumentFileType.PDF
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocumentFileType.DOCX
    if mime_type in {"text/plain"}:
        return DocumentFileType.TXT
    if mime_type in {"text/markdown"}:
        return DocumentFileType.MARKDOWN

    raise ExtractionError(f"Unsupported file type for {filename}")


def extract_text_from_bytes(file_type: DocumentFileType, content: bytes) -> str:
    if file_type == DocumentFileType.PDF:
        return _extract_pdf(content)
    if file_type == DocumentFileType.DOCX:
        return _extract_docx(content)
    if file_type in {DocumentFileType.TXT, DocumentFileType.MARKDOWN, DocumentFileType.TEXT}:
        return content.decode("utf-8")

    raise ExtractionError(f"Unsupported file type: {file_type}")


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ExtractionError("No text could be extracted from PDF")
    return text


def _extract_docx(content: bytes) -> str:
    document = DocxDocument(io.BytesIO(content))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ExtractionError("No text could be extracted from DOCX")
    return text
