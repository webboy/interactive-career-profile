from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import DocumentStatus, EmbeddingStatus, Visibility
from app.db.models.document import Document, DocumentChunk
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.factory import get_embedding_provider


class DocumentChunkEmbeddingError(Exception):
    pass


async def embed_document_chunk(
    session: AsyncSession,
    chunk: DocumentChunk,
    *,
    provider: EmbeddingProvider | None = None,
    settings: Settings | None = None,
) -> DocumentChunk:
    config = settings or get_settings()
    embedding_provider = provider or get_embedding_provider(config)

    try:
        embedding = await embedding_provider.embed_text(chunk.content)
        chunk.embedding = embedding
        chunk.embedding_status = EmbeddingStatus.READY
        chunk.embedding_error = None
    except Exception as exc:
        chunk.embedding_status = EmbeddingStatus.FAILED
        chunk.embedding_error = str(exc)
        await session.commit()
        await session.refresh(chunk)
        raise DocumentChunkEmbeddingError(str(exc)) from exc

    await session.commit()
    await session.refresh(chunk)
    await _sync_document_embedding_status(session, chunk.document_id)
    return chunk


async def run_pending_document_chunk_embeddings(
    session: AsyncSession,
    *,
    limit: int = 50,
    visibility: Visibility | None = Visibility.PUBLIC,
    provider: EmbeddingProvider | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    config = settings or get_settings()
    embedding_provider = provider or get_embedding_provider(config)

    query = (
        select(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.status == DocumentStatus.CHUNKED,
            DocumentChunk.embedding_status == EmbeddingStatus.PENDING,
        )
        .order_by(DocumentChunk.id)
        .limit(limit)
    )
    if visibility is not None:
        query = query.where(DocumentChunk.visibility == visibility)

    result = await session.execute(query)
    chunks = list(result.scalars().all())

    processed = 0
    failed = 0
    for chunk in chunks:
        try:
            await embed_document_chunk(
                session,
                chunk,
                provider=embedding_provider,
                settings=config,
            )
            processed += 1
        except DocumentChunkEmbeddingError:
            failed += 1

    return {"processed": processed, "failed": failed, "requested": len(chunks)}


async def _sync_document_embedding_status(session: AsyncSession, document_id: int) -> None:
    document = await session.get(Document, document_id)
    if document is None:
        return

    result = await session.execute(
        select(DocumentChunk.embedding_status).where(DocumentChunk.document_id == document_id)
    )
    statuses = list(result.scalars().all())
    if not statuses:
        return

    if any(status == EmbeddingStatus.FAILED for status in statuses):
        document.embedding_status = EmbeddingStatus.FAILED
        document.embedding_error = "One or more document chunks failed embedding"
    elif all(status == EmbeddingStatus.READY for status in statuses):
        document.embedding_status = EmbeddingStatus.READY
        document.embedding_error = None
    else:
        document.embedding_status = EmbeddingStatus.PENDING
        document.embedding_error = None

    await session.commit()
    await session.refresh(document)
