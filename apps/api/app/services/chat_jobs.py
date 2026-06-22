import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import ChatJobStatus
from app.db.models.chat_job import ChatJob
from app.schemas.public import PublicChatResponse, PublicSourceSummary
from app.services.agent.graph import run_agent_turn
from app.services.llm.factory import get_llm_provider
from app.services.llm.base import LLMProvider


PUBLIC_JOB_FAILURE_MESSAGE = "The chat response could not be prepared. Please try again."


async def create_chat_job(
    session: AsyncSession,
    *,
    session_id: str,
    conversation_id: int,
    message: str,
    language: str | None,
) -> ChatJob:
    job = ChatJob(
        id=str(uuid.uuid4()),
        session_id=session_id,
        conversation_id=conversation_id,
        request_message=message,
        request_language=language,
        status=ChatJobStatus.QUEUED,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_chat_job(session: AsyncSession, job_id: str) -> ChatJob | None:
    result = await session.execute(select(ChatJob).where(ChatJob.id == job_id))
    return result.scalar_one_or_none()


async def execute_chat_job(
    job_id: str,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    llm_provider: LLMProvider | None = None,
) -> None:
    provider = llm_provider or get_llm_provider(settings)
    async with session_factory() as session:
        job = await get_chat_job(session, job_id)
        if job is None:
            return

        job.status = ChatJobStatus.PROCESSING
        await session.commit()

        try:
            result = await run_agent_turn(
                session,
                job.request_message,
                conversation_id=job.conversation_id,
                session_id=job.session_id,
                language=job.request_language,
                settings=settings,
                llm_provider=provider,
            )
        except Exception as exc:  # pragma: no cover - covered through injected failure in tests.
            job.status = ChatJobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return

        job.status = ChatJobStatus.COMPLETED
        job.assistant_message = result.assistant_message
        job.response_language = result.language
        job.refused = result.refused
        job.grounded = result.grounded
        job.sources_json = json.dumps(
            [
                {
                    "source_type": str(source["source_type"]),
                    "title": str(source["title"]),
                }
                for source in result.sources
            ]
        )
        job.completed_at = datetime.now(timezone.utc)
        await session.commit()


def build_public_response_from_job(job: ChatJob) -> PublicChatResponse | None:
    if job.status != ChatJobStatus.COMPLETED or job.assistant_message is None:
        return None

    raw_sources = json.loads(job.sources_json or "[]")
    return PublicChatResponse(
        conversation_id=job.conversation_id,
        session_id=job.session_id,
        assistant_message=job.assistant_message,
        language=job.response_language or job.request_language or "en",
        refused=bool(job.refused),
        grounded=bool(job.grounded),
        sources=[
            PublicSourceSummary(
                source_type=str(source["source_type"]),
                title=str(source["title"]),
            )
            for source in raw_sources
            if isinstance(source, dict) and "source_type" in source and "title" in source
        ],
    )
