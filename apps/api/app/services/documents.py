import uuid
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import (
    DocumentFileType,
    DocumentSourceType,
    DocumentStatus,
    EmbeddingStatus,
    Visibility,
)
from app.db.models.document import Document, DocumentChunk
from app.schemas.documents import DocumentTextCreateRequest, DocumentUpdateRequest
from app.services.chunking import chunk_text
from app.services.extraction import ExtractionError, detect_file_type, extract_text_from_bytes
from app.services.storage.base import StorageDriver
from app.services.storage.factory import get_storage_driver


class DocumentUploadTooLargeError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


def _build_storage_path(document_id: int, filename: str) -> str:
    safe_name = Path(filename).name
    return f"documents/{document_id}/{uuid.uuid4().hex}_{safe_name}"


async def list_documents(
    session: AsyncSession,
    visibility: Visibility | None = None,
    status: DocumentStatus | None = None,
) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
    if visibility is not None:
        query = query.where(Document.visibility == visibility)
    if status is not None:
        query = query.where(Document.status == status)

    result = await session.execute(query)
    return list(result.scalars().all())


async def list_public_document_chunks(session: AsyncSession) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.visibility == Visibility.PUBLIC)
        .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


async def get_document(session: AsyncSession, document_id: int) -> Document | None:
    result = await session.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def get_document_chunk(session: AsyncSession, chunk_id: int) -> DocumentChunk | None:
    result = await session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
    return result.scalar_one_or_none()


async def list_document_chunks(session: AsyncSession, document_id: int) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


async def create_text_document(
    session: AsyncSession,
    payload: DocumentTextCreateRequest,
) -> Document:
    document = Document(
        title=payload.title,
        source_type=DocumentSourceType.PASTED_TEXT,
        file_type=DocumentFileType.TEXT,
        extracted_text=payload.content,
        visibility=payload.visibility,
        status=DocumentStatus.EXTRACTED,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def create_uploaded_document(
    session: AsyncSession,
    *,
    title: str,
    filename: str,
    content: bytes,
    mime_type: str | None,
    visibility: Visibility,
    settings: Settings | None = None,
    storage: StorageDriver | None = None,
) -> Document:
    config = settings or get_settings()
    if len(content) > config.document_upload_max_bytes:
        raise DocumentUploadTooLargeError(
            f"Upload exceeds maximum size of {config.document_upload_max_bytes} bytes"
        )

    file_type = detect_file_type(filename, mime_type)
    driver = storage or get_storage_driver(config)

    document = Document(
        title=title,
        source_type=DocumentSourceType.UPLOAD,
        file_type=file_type,
        original_filename=filename,
        mime_type=mime_type,
        file_size_bytes=len(content),
        visibility=visibility,
        status=DocumentStatus.UPLOADED,
    )
    session.add(document)
    await session.flush()

    storage_path = _build_storage_path(document.id, filename)
    driver.save(storage_path, content)
    document.storage_path = storage_path

    await session.commit()
    await session.refresh(document)
    return document


async def update_document(
    session: AsyncSession,
    document: Document,
    payload: DocumentUpdateRequest,
) -> Document:
    document.title = payload.title
    document.visibility = payload.visibility
    await session.commit()
    await session.refresh(document)
    return document


async def delete_document(
    session: AsyncSession,
    document: Document,
    storage: StorageDriver | None = None,
) -> None:
    driver = storage or get_storage_driver()
    if document.storage_path:
        driver.delete(document.storage_path)
    await session.delete(document)
    await session.commit()


async def extract_document_text(
    session: AsyncSession,
    document: Document,
    storage: StorageDriver | None = None,
) -> Document:
    if document.source_type == DocumentSourceType.PASTED_TEXT:
        if not document.extracted_text:
            document.status = DocumentStatus.FAILED
            document.status_error = "Pasted text document has no content"
            await session.commit()
            await session.refresh(document)
            return document
        document.status = DocumentStatus.EXTRACTED
        document.status_error = None
        await session.commit()
        await session.refresh(document)
        return document

    if not document.storage_path or not document.file_type:
        document.status = DocumentStatus.FAILED
        document.status_error = "Uploaded document is missing storage metadata"
        await session.commit()
        await session.refresh(document)
        return document

    driver = storage or get_storage_driver()
    try:
        content = driver.read(document.storage_path)
        extracted = extract_text_from_bytes(document.file_type, content)
        document.extracted_text = extracted
        document.status = DocumentStatus.EXTRACTED
        document.status_error = None
    except (ExtractionError, OSError, ValueError) as exc:
        document.status = DocumentStatus.FAILED
        document.status_error = str(exc)

    await session.commit()
    await session.refresh(document)
    return document


async def chunk_document(
    session: AsyncSession,
    document: Document,
    settings: Settings | None = None,
) -> tuple[Document, int]:
    config = settings or get_settings()

    if document.status != DocumentStatus.EXTRACTED or not document.extracted_text:
        document.status = DocumentStatus.FAILED
        document.status_error = "Document must be extracted before chunking"
        await session.commit()
        await session.refresh(document)
        return document, 0

    segments = chunk_text(
        document.extracted_text,
        config.document_chunk_size_chars,
        config.document_chunk_overlap_chars,
    )

    await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))

    for segment in segments:
        session.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=segment.chunk_index,
                content=segment.content,
                char_start=segment.char_start,
                char_end=segment.char_end,
                visibility=document.visibility,
            )
        )

    document.status = DocumentStatus.CHUNKED
    document.status_error = None
    document.embedding_status = EmbeddingStatus.PENDING
    document.embedding_error = None

    await session.commit()
    await session.refresh(document)
    return document, len(segments)


async def retry_document_ingestion(
    session: AsyncSession,
    document: Document,
    settings: Settings | None = None,
    storage: StorageDriver | None = None,
) -> tuple[Document, int]:
    document.status_error = None
    document.embedding_error = None
    await session.commit()

    extracted = await extract_document_text(session, document, storage=storage)
    if extracted.status != DocumentStatus.EXTRACTED:
        return extracted, 0

    return await chunk_document(session, extracted, settings=settings)


async def request_document_embedding(
    session: AsyncSession,
    document: Document,
) -> Document:
    if document.status != DocumentStatus.CHUNKED:
        document.embedding_status = EmbeddingStatus.FAILED
        document.embedding_error = "Document must be chunked before embedding can be requested"
    else:
        document.embedding_status = EmbeddingStatus.PENDING
        document.embedding_error = None

    await session.commit()
    await session.refresh(document)
    return document


async def update_document_chunk_visibility(
    session: AsyncSession,
    chunk: DocumentChunk,
    visibility: Visibility,
) -> DocumentChunk:
    chunk.visibility = visibility
    await session.commit()
    await session.refresh(chunk)
    return chunk
