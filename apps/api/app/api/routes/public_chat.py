from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ChatJobStatus
from app.db.session import get_db_session
from app.schemas.public import PublicChatJobCreateResponse, PublicChatJobStatusResponse, PublicChatRequest
from app.services.chat_dispatcher import dispatch_chat_job
from app.services.chat_jobs import (
    PUBLIC_JOB_FAILURE_MESSAGE,
    build_public_response_from_job,
    create_chat_job,
    get_chat_job,
)
from app.services.conversations import ConversationSessionMismatchError, resolve_public_conversation_id

router = APIRouter(prefix="/api/public", tags=["public"])


@router.post("/chat", response_model=PublicChatJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def public_chat(
    payload: PublicChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PublicChatJobCreateResponse:
    try:
        conversation_id = await resolve_public_conversation_id(
            session,
            session_id=payload.session_id,
            conversation_id=payload.conversation_id,
            language=payload.language,
        )
        job = await create_chat_job(
            session,
            session_id=payload.session_id,
            conversation_id=conversation_id,
            message=payload.message,
            language=payload.language,
        )
    except ConversationSessionMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    dispatch_chat_job(job.id)

    return PublicChatJobCreateResponse(
        job_id=job.id,
        conversation_id=conversation_id,
        session_id=payload.session_id,
        status=job.status,
    )


@router.get("/chat/jobs/{job_id}", response_model=PublicChatJobStatusResponse)
async def public_chat_job_status(
    job_id: str,
    session_id: str = Query(min_length=1, max_length=255),
    session: AsyncSession = Depends(get_db_session),
) -> PublicChatJobStatusResponse:
    job = await get_chat_job(session, job_id)
    if job is None or job.session_id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat job not found")

    response = build_public_response_from_job(job)
    error_message = PUBLIC_JOB_FAILURE_MESSAGE if job.status == ChatJobStatus.FAILED else None
    return PublicChatJobStatusResponse(
        job_id=job.id,
        conversation_id=job.conversation_id,
        session_id=job.session_id,
        status=job.status,
        response=response,
        error_message=error_message,
    )
