from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import SourceCategory, UnansweredPromptReason, Visibility
from app.db.models.retrieval_log import RetrievalLog, RetrievalLogItem, UnansweredPrompt
from app.services.embeddings.factory import get_embedding_provider
from app.services.retrieval.document_search import DocumentChunkSearchResult, search_public_document_chunks
from app.services.retrieval.structured_selector import StructuredSource, select_structured_sources


STRUCTURED_PRECEDENCE_BASE = 0
DOCUMENT_PRECEDENCE_BASE = 1000


@dataclass(frozen=True)
class RetrievedContextSource:
    source_type: SourceCategory
    source_id: int
    title: str
    snippet: str
    visibility: Visibility
    score: float | None
    was_used: bool
    precedence_rank: int


@dataclass(frozen=True)
class HybridRetrievalResult:
    retrieval_log_id: int
    had_usable_context: bool
    sources: list[RetrievedContextSource]
    unanswered_prompt_id: int | None = None


async def run_hybrid_retrieval(
    session: AsyncSession,
    query: str,
    *,
    language: str | None = None,
    session_id: str | None = None,
    intent_hints: list[str] | None = None,
    structured_limit: int | None = None,
    document_limit: int | None = None,
    document_score_threshold: float | None = None,
    settings: Settings | None = None,
    document_search_override=None,
) -> HybridRetrievalResult:
    config = settings or get_settings()
    structured_cap = structured_limit or config.retrieval_structured_limit
    document_cap = document_limit or config.retrieval_document_limit
    threshold = (
        document_score_threshold
        if document_score_threshold is not None
        else config.retrieval_document_score_threshold
    )

    structured_sources = await select_structured_sources(
        session,
        query,
        limit=structured_cap,
        intent_hints=intent_hints,
    )

    document_sources: list[DocumentChunkSearchResult] = []
    if document_search_override is not None:
        document_sources = await document_search_override(
            session,
            query,
            limit=document_cap,
            threshold=threshold,
        )
    else:
        provider = get_embedding_provider(config)
        query_embedding = await provider.embed_text(query)
        document_sources = await search_public_document_chunks(
            session,
            query_embedding,
            limit=document_cap,
            threshold=threshold,
        )

    merged_sources = _merge_sources(structured_sources, document_sources)
    used_sources = [source for source in merged_sources if source.was_used]
    had_usable_context = len(used_sources) > 0

    retrieval_log = RetrievalLog(
        query=query,
        language=language,
        session_id=session_id,
        structured_limit=structured_cap,
        document_limit=document_cap,
        document_score_threshold=threshold,
        had_usable_context=had_usable_context,
    )
    session.add(retrieval_log)
    await session.flush()

    for source in merged_sources:
        session.add(
            RetrievalLogItem(
                retrieval_log_id=retrieval_log.id,
                source_type=source.source_type,
                source_id=source.source_id,
                title=source.title,
                snippet=source.snippet,
                score=source.score,
                visibility=source.visibility,
                was_used=source.was_used,
                precedence_rank=source.precedence_rank,
            )
        )

    unanswered_prompt_id: int | None = None
    if not had_usable_context:
        reason = (
            UnansweredPromptReason.BELOW_THRESHOLD
            if structured_sources or document_sources
            else UnansweredPromptReason.NO_CONTEXT
        )
        unanswered_prompt = UnansweredPrompt(
            query=query,
            reason=reason,
            language=language,
            session_id=session_id,
            retrieval_log_id=retrieval_log.id,
        )
        session.add(unanswered_prompt)
        await session.flush()
        unanswered_prompt_id = unanswered_prompt.id

    await session.commit()
    await session.refresh(retrieval_log)

    return HybridRetrievalResult(
        retrieval_log_id=retrieval_log.id,
        had_usable_context=had_usable_context,
        sources=merged_sources,
        unanswered_prompt_id=unanswered_prompt_id,
    )


def _merge_sources(
    structured_sources: list[StructuredSource],
    document_sources: list[DocumentChunkSearchResult],
) -> list[RetrievedContextSource]:
    merged: list[RetrievedContextSource] = []

    for index, source in enumerate(structured_sources):
        merged.append(
            RetrievedContextSource(
                source_type=source.source_type,
                source_id=source.source_id,
                title=source.title,
                snippet=source.snippet,
                visibility=source.visibility,
                score=source.score,
                was_used=True,
                precedence_rank=STRUCTURED_PRECEDENCE_BASE + index,
            )
        )

    structured_titles = {source.title.lower() for source in structured_sources}

    document_rank = 0
    for source in document_sources:
        conflicts_with_structured = source.title.lower() in structured_titles
        merged.append(
            RetrievedContextSource(
                source_type=source.source_type,
                source_id=source.source_id,
                title=source.title,
                snippet=source.snippet,
                visibility=source.visibility,
                score=source.score,
                was_used=not conflicts_with_structured,
                precedence_rank=DOCUMENT_PRECEDENCE_BASE + document_rank,
            )
        )
        document_rank += 1

    merged.sort(key=lambda item: item.precedence_rank)
    return merged


async def get_retrieval_log(session: AsyncSession, log_id: int) -> RetrievalLog | None:
    result = await session.execute(select(RetrievalLog).where(RetrievalLog.id == log_id))
    return result.scalar_one_or_none()


async def list_retrieval_logs(session: AsyncSession, *, limit: int = 50) -> list[RetrievalLog]:
    result = await session.execute(
        select(RetrievalLog).order_by(RetrievalLog.created_at.desc(), RetrievalLog.id.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def list_unanswered_prompts(session: AsyncSession, *, limit: int = 50) -> list[UnansweredPrompt]:
    result = await session.execute(
        select(UnansweredPrompt)
        .order_by(UnansweredPrompt.created_at.desc(), UnansweredPrompt.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
