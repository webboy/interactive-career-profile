from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EmbeddingStatus, SourceCategory, Visibility
from app.db.models.document import DocumentChunk


@dataclass(frozen=True)
class DocumentChunkSearchResult:
    source_type: SourceCategory
    source_id: int
    title: str
    snippet: str
    visibility: Visibility
    score: float


async def search_public_document_chunks(
    session: AsyncSession,
    query_embedding: list[float],
    *,
    limit: int,
    threshold: float,
) -> list[DocumentChunkSearchResult]:
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return []

    embedding_literal = _to_vector_literal(query_embedding)
    statement = text(
        """
        SELECT
            dc.id,
            dc.content,
            dc.visibility,
            d.title AS document_title,
            1 - (dc.embedding <=> CAST(:query_embedding AS vector)) AS score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.visibility = 'public'
          AND dc.embedding_status = 'ready'
          AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
    )

    result = await session.execute(
        statement,
        {
            "query_embedding": embedding_literal,
            "limit": limit,
        },
    )
    rows = result.mappings().all()

    matches: list[DocumentChunkSearchResult] = []
    for row in rows:
        score = float(row["score"])
        if score < threshold:
            continue
        matches.append(
            DocumentChunkSearchResult(
                source_type=SourceCategory.DOCUMENT_CHUNK,
                source_id=int(row["id"]),
                title=str(row["document_title"]),
                snippet=str(row["content"]),
                visibility=Visibility.PUBLIC,
                score=score,
            )
        )

    return matches


async def list_document_chunk_candidates(
    session: AsyncSession,
    chunk_ids: list[int],
) -> list[DocumentChunk]:
    if not chunk_ids:
        return []

    result = await session.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
    return list(result.scalars().all())


def _to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
