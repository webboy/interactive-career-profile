import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.db.session import create_engine
from app.services.chat_jobs import execute_chat_job
from app.worker.celery_app import celery_app


@celery_app.task(name="chat_jobs.run")
def run_chat_job_task(job_id: str) -> None:
    asyncio.run(_run_chat_job(job_id))


async def _run_chat_job(job_id: str) -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        await execute_chat_job(
            job_id,
            session_factory=session_factory,
            settings=settings,
        )
    finally:
        await engine.dispose()
