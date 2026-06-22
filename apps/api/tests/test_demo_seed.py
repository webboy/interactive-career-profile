import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import (
    ChatJobStatus,
    SourceCategory,
    Visibility,
)
from app.core.security import verify_password
from app.db.models.document import Document, DocumentChunk
from app.db.models.lead import FollowUpRequest, JobSubmission, MeetingRequest
from app.db.models.profile_item import ProfileItem
from app.db.models.retrieval_log import RetrievalLog, UnansweredPrompt
from app.db.models.user import User
from app.services.demo_seed import (
    DEMO_ADMIN_EMAIL_DEFAULT,
    DEMO_ADMIN_PASSWORD_DEFAULT,
    DEMO_KEY_PREFIX,
    DEMO_SESSION_ID,
    DEMO_SOURCE,
    count_demo_seed_records,
    run_demo_seed,
)
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.llm.fake_provider import FakeLLMProvider
from app.services.retrieval.hybrid import run_hybrid_retrieval
from app.services.users import get_user_by_email
import tests.test_public_api as public_api_tests

_dispatched_job_ids: list[str] = []


@pytest.fixture(autouse=True)
def use_fake_embedding_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeEmbeddingProvider(dimensions=1536)

    def _get_provider(settings: Settings | None = None) -> FakeEmbeddingProvider:
        return provider

    monkeypatch.setattr("app.services.embeddings.factory.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.services.embeddings.document_chunks.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.services.retrieval.hybrid.get_embedding_provider", _get_provider)


@pytest.fixture(autouse=True)
def use_fake_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeLLMProvider()

    def _get_provider(settings: Settings | None = None) -> FakeLLMProvider:
        return provider

    monkeypatch.setattr("app.services.llm.factory.get_llm_provider", _get_provider)
    monkeypatch.setattr("app.services.agent.graph.get_llm_provider", _get_provider)


@pytest.fixture(autouse=True)
def run_chat_jobs_inline(
    monkeypatch: pytest.MonkeyPatch,
    db_engine: AsyncEngine,
) -> None:
    public_api_tests._dispatched_job_ids.clear()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    public_api_tests._test_session_factory = session_factory

    def _dispatch(job_id: str) -> None:
        public_api_tests._dispatched_job_ids.append(job_id)

    monkeypatch.setattr("app.api.routes.public_chat.dispatch_chat_job", _dispatch)


async def _seed_demo(db_session: AsyncSession) -> None:
    await run_demo_seed(
        db_session,
        admin_email=DEMO_ADMIN_EMAIL_DEFAULT,
        admin_password=DEMO_ADMIN_PASSWORD_DEFAULT,
        settings=Settings(
            llm_provider="fake",
            embedding_provider="fake",
        ),
    )


@pytest.mark.asyncio
async def test_demo_seed_creates_expected_records(db_session: AsyncSession) -> None:
    result = await run_demo_seed(
        db_session,
        admin_email=DEMO_ADMIN_EMAIL_DEFAULT,
        admin_password=DEMO_ADMIN_PASSWORD_DEFAULT,
        settings=Settings(llm_provider="fake", embedding_provider="fake"),
    )

    assert result.profile_items == 7
    assert result.career_records == 3
    assert result.documents == 4
    assert result.document_chunks >= 4
    assert result.conversations == 1
    assert result.retrieval_logs >= 2
    assert result.unanswered_prompts >= 1
    assert result.leads == 3
    assert result.tool_calls == 2
    assert result.settings == 3

    counts = await count_demo_seed_records(db_session)
    assert counts["profile_items"] == 7
    assert counts["career_records"] == 3
    assert counts["documents"] == 4
    assert counts["conversations"] == 1
    assert counts["leads"] == 3


@pytest.mark.asyncio
async def test_demo_seed_is_idempotent(db_session: AsyncSession) -> None:
    settings = Settings(llm_provider="fake", embedding_provider="fake")
    first = await run_demo_seed(db_session, settings=settings)
    second = await run_demo_seed(db_session, settings=settings)

    assert first.profile_items == second.profile_items
    assert first.documents == second.documents
    assert first.leads == second.leads

    counts = await count_demo_seed_records(db_session)
    assert counts["profile_items"] == 7
    assert counts["documents"] == 4
    assert counts["leads"] == 3


@pytest.mark.asyncio
async def test_demo_seed_creates_admin_user_and_legal_content(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    user = await get_user_by_email(db_session, DEMO_ADMIN_EMAIL_DEFAULT)
    assert user is not None
    assert verify_password(DEMO_ADMIN_PASSWORD_DEFAULT, user.password_hash)

    privacy = await db_session.execute(select(ProfileItem).where(ProfileItem.key == f"{DEMO_KEY_PREFIX}headline"))
    assert privacy.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_demo_seed_documents_include_public_and_private_chunks(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    public_chunks = await db_session.execute(
        select(DocumentChunk)
        .join(Document)
        .where(
            Document.title == "Demo: Platform Migration Case Study",
            DocumentChunk.visibility == Visibility.PUBLIC,
        )
    )
    private_doc = await db_session.execute(
        select(Document).where(Document.title == "Demo: Private Interview Notes")
    )
    private = private_doc.scalar_one()
    private_chunks = await db_session.execute(
        select(DocumentChunk).where(
            DocumentChunk.document_id == private.id,
            DocumentChunk.visibility == Visibility.PRIVATE,
        )
    )

    assert list(public_chunks.scalars().all())
    assert list(private_chunks.scalars().all())


@pytest.mark.asyncio
async def test_demo_seed_structured_precedence_over_document_conflict(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    result = await run_hybrid_retrieval(
        db_session,
        "Berlin location Northstar Labs platform engineer",
        session_id="demo-precedence-test",
        language="en",
    )

    structured = next(
        source
        for source in result.sources
        if source.source_type in {SourceCategory.PROFILE_ITEM, SourceCategory.CAREER_RECORD}
        and "Berlin" in source.snippet
    )
    assert structured.was_used is True
    document_sources = [
        source for source in result.sources if source.source_type == SourceCategory.DOCUMENT_CHUNK
    ]
    if document_sources:
        document = document_sources[0]
        assert structured.was_used is True
        assert document.was_used is False
        assert structured.precedence_rank < document.precedence_rank


@pytest.mark.asyncio
async def test_seeded_public_chat_salary_and_phone_refusals(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    _, salary = await public_api_tests._submit_and_poll(
        client,
        message="What is your salary expectation?",
        session_id="demo-salary-session",
    )
    assert salary["response"]["refused"] is True
    assert "salary" in salary["response"]["assistant_message"].lower()

    _, phone = await public_api_tests._submit_and_poll(
        client,
        message="What is your phone number?",
        session_id="demo-phone-session",
    )
    assert phone["response"]["refused"] is True
    assert "phone" in phone["response"]["assistant_message"].lower()


@pytest.mark.asyncio
async def test_seeded_public_chat_grounded_answer(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    _, polled = await public_api_tests._submit_and_poll(
        client,
        message="Tell me about Alex's platform engineering experience",
        session_id="demo-grounded-session",
    )
    payload = polled["response"]
    assert payload["refused"] is False
    assert payload["grounded"] is True
    assert payload["sources"]


@pytest.mark.asyncio
async def test_seeded_public_chat_unsupported_fallback(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    _, polled = await public_api_tests._submit_and_poll(
        client,
        message="zzzz-nonexistent-quantum-chemistry-topic-demo",
        session_id="demo-unsupported-session",
    )
    assert polled["response"]["refused"] is True


@pytest.mark.asyncio
async def test_seeded_async_chat_job_lifecycle(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    created = await public_api_tests._submit_chat(
        client,
        message="What platform migration outcomes can you share?",
        session_id="demo-async-session",
    )
    assert created["status"] == ChatJobStatus.QUEUED

    await public_api_tests._run_dispatched_chat_jobs()

    polled = {}
    for _ in range(20):
        polled = await public_api_tests._poll_chat_job(
            client,
            job_id=created["job_id"],
            session_id="demo-async-session",
        )
        if polled["status"] in {ChatJobStatus.COMPLETED, ChatJobStatus.FAILED}:
            break
        await asyncio.sleep(0.01)

    assert polled["status"] == ChatJobStatus.COMPLETED
    assert polled["response"]["assistant_message"]


@pytest.mark.asyncio
async def test_seeded_admin_lists_expose_demo_records(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    profile = await auth_client.get("/api/admin/profile-items")
    records = await auth_client.get("/api/admin/career-records")
    documents = await auth_client.get("/api/admin/documents")
    conversations = await auth_client.get("/api/admin/conversations")
    retrieval_logs = await auth_client.get("/api/admin/retrieval-logs")
    unanswered = await auth_client.get("/api/admin/unanswered-prompts")
    meetings = await auth_client.get("/api/admin/leads/meeting-requests")
    follow_ups = await auth_client.get("/api/admin/leads/follow-up-requests")
    jobs = await auth_client.get("/api/admin/leads/job-submissions")
    tool_calls = await auth_client.get("/api/admin/tool-calls")

    assert profile.status_code == 200
    assert any(item["key"].startswith(DEMO_KEY_PREFIX) for item in profile.json())
    assert records.status_code == 200
    assert any(record["source"] == DEMO_SOURCE for record in records.json())
    assert documents.status_code == 200
    assert any(doc["title"].startswith("Demo:") for doc in documents.json())
    assert conversations.status_code == 200
    assert any(row["session_id"] == DEMO_SESSION_ID for row in conversations.json())
    assert retrieval_logs.status_code == 200
    assert len(retrieval_logs.json()) >= 1
    assert unanswered.status_code == 200
    assert len(unanswered.json()) >= 1
    assert meetings.status_code == 200
    assert follow_ups.status_code == 200
    assert jobs.status_code == 200
    assert tool_calls.status_code == 200
    assert len(tool_calls.json()["tool_calls"]) >= 2


@pytest.mark.asyncio
async def test_demo_seed_reset_clears_and_reseeds(db_session: AsyncSession) -> None:
    settings = Settings(llm_provider="fake", embedding_provider="fake")
    await run_demo_seed(db_session, settings=settings)

    result = await run_demo_seed(db_session, settings=settings, reset_demo_data=True)
    assert result.reset_applied is True

    logs = await db_session.execute(select(RetrievalLog).where(RetrievalLog.session_id == DEMO_SESSION_ID))
    assert len(list(logs.scalars().all())) >= 2

    leads = await db_session.execute(select(MeetingRequest))
    assert len(list(leads.scalars().all())) >= 1


@pytest.mark.asyncio
async def test_demo_leads_are_persisted_with_expected_emails(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    meeting = await db_session.execute(select(MeetingRequest))
    follow_up = await db_session.execute(select(FollowUpRequest))
    job = await db_session.execute(select(JobSubmission))

    meeting_rows = list(meeting.scalars().all())
    follow_up_rows = list(follow_up.scalars().all())
    job_rows = list(job.scalars().all())

    assert any(row.requester_email.endswith("@example.com") for row in meeting_rows)
    assert follow_up_rows
    assert job_rows
    assert job_rows[0].retrieval_log_id is not None


@pytest.mark.asyncio
async def test_demo_seed_does_not_create_duplicate_users(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)
    await _seed_demo(db_session)

    users = await db_session.execute(select(User).where(User.email == DEMO_ADMIN_EMAIL_DEFAULT))
    assert len(list(users.scalars().all())) == 1


@pytest.mark.asyncio
async def test_private_demo_profile_items_are_not_public(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    private_items = await db_session.execute(
        select(ProfileItem).where(ProfileItem.key == f"{DEMO_KEY_PREFIX}private_note")
    )
    item = private_items.scalar_one()
    assert item.visibility == Visibility.PRIVATE

    result = await run_hybrid_retrieval(
        db_session,
        "private recruiter-only note",
        session_id="demo-private-filter",
    )
    assert all(source.source_id != item.id for source in result.sources)


@pytest.mark.asyncio
async def test_seeded_unanswered_prompts_are_listed(db_session: AsyncSession) -> None:
    await _seed_demo(db_session)

    prompts = await db_session.execute(
        select(UnansweredPrompt).where(UnansweredPrompt.session_id == DEMO_SESSION_ID)
    )
    assert list(prompts.scalars().all())
