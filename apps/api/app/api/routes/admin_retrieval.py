from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api.dependencies.auth import require_admin_user
from app.core.config import get_settings
from app.db.models.retrieval_log import RetrievalLog
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.embeddings import DocumentChunkEmbeddingActionResponse, RunPendingEmbeddingsResponse
from app.schemas.retrieval import (
    RetrievalDebugRequest,
    RetrievalDebugResponse,
    RetrievalLogResponse,
    RetrievedSourceResponse,
    UnansweredPromptResponse,
)
from app.services.documents import get_document_chunk
from app.services.embeddings.document_chunks import (
    DocumentChunkEmbeddingError,
    embed_document_chunk,
    run_pending_document_chunk_embeddings,
)
from app.services.embeddings.factory import get_embedding_provider
from app.services.retrieval.hybrid import (
    list_retrieval_logs,
    list_unanswered_prompts,
    run_hybrid_retrieval,
)

router = APIRouter(prefix="/api/admin", tags=["admin-retrieval"])


@router.post(
    "/document-chunks/{chunk_id}/embed",
    response_model=DocumentChunkEmbeddingActionResponse,
)
async def admin_embed_document_chunk(
    chunk_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentChunkEmbeddingActionResponse:
    chunk = await get_document_chunk(session, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document chunk not found")

    settings = get_settings()
    provider = get_embedding_provider(settings)

    try:
        updated = await embed_document_chunk(session, chunk, provider=provider, settings=settings)
    except DocumentChunkEmbeddingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return DocumentChunkEmbeddingActionResponse(
        chunk_id=updated.id,
        embedding_status=updated.embedding_status.value,
        embedding_error=updated.embedding_error,
    )


@router.post(
    "/embeddings/document-chunks/run-pending",
    response_model=RunPendingEmbeddingsResponse,
)
async def admin_run_pending_document_chunk_embeddings(
    limit: int = Query(default=50, ge=1, le=500),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> RunPendingEmbeddingsResponse:
    settings = get_settings()
    provider = get_embedding_provider(settings)
    result = await run_pending_document_chunk_embeddings(
        session,
        limit=limit,
        provider=provider,
        settings=settings,
    )
    return RunPendingEmbeddingsResponse(**result)


@router.post("/retrieval/debug", response_model=RetrievalDebugResponse)
async def admin_debug_retrieval(
    payload: RetrievalDebugRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> RetrievalDebugResponse:
    settings = get_settings()
    result = await run_hybrid_retrieval(
        session,
        payload.query,
        language=payload.language,
        session_id=payload.session_id,
        intent_hints=payload.intent_hints,
        structured_limit=payload.structured_limit,
        document_limit=payload.document_limit,
        document_score_threshold=payload.document_score_threshold,
        settings=settings,
    )

    return RetrievalDebugResponse(
        retrieval_log_id=result.retrieval_log_id,
        had_usable_context=result.had_usable_context,
        unanswered_prompt_id=result.unanswered_prompt_id,
        sources=[
            RetrievedSourceResponse(
                source_type=source.source_type,
                source_id=source.source_id,
                title=source.title,
                snippet=source.snippet,
                visibility=source.visibility,
                score=source.score,
                was_used=source.was_used,
                precedence_rank=source.precedence_rank,
            )
            for source in result.sources
        ],
    )


@router.get("/retrieval-logs", response_model=list[RetrievalLogResponse])
async def admin_list_retrieval_logs(
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[RetrievalLogResponse]:
    logs = await list_retrieval_logs(session, limit=limit)
    return [
        RetrievalLogResponse(
            id=log.id,
            query=log.query,
            language=log.language,
            session_id=log.session_id,
            structured_limit=log.structured_limit,
            document_limit=log.document_limit,
            document_score_threshold=log.document_score_threshold,
            had_usable_context=log.had_usable_context,
            created_at=log.created_at,
            items=[],
        )
        for log in logs
    ]


@router.get("/retrieval-logs/{log_id}", response_model=RetrievalLogResponse)
async def admin_get_retrieval_log(
    log_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> RetrievalLogResponse:
    result = await session.execute(
        select(RetrievalLog)
        .options(selectinload(RetrievalLog.items))
        .where(RetrievalLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retrieval log not found")

    return RetrievalLogResponse.model_validate(log, from_attributes=True)


@router.get("/unanswered-prompts", response_model=list[UnansweredPromptResponse])
async def admin_list_unanswered_prompts(
    limit: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[UnansweredPromptResponse]:
    prompts = await list_unanswered_prompts(session, limit=limit)
    return [UnansweredPromptResponse.model_validate(prompt) for prompt in prompts]
