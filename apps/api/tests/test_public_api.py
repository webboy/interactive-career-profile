import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.enums import CareerRecordType, ChatJobStatus, Visibility
from app.db.models.career_record import CareerRecord
from app.services.chat_jobs import execute_chat_job, get_chat_job
from app.services.conversations import create_conversation
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.llm.fake_provider import FakeLLMProvider
from tests.test_retrieval import _seed_public_career_record, _seed_public_profile_item

_dispatched_job_ids: list[str] = []
_test_session_factory: async_sessionmaker[AsyncSession] | None = None


@pytest.fixture(autouse=True)
def use_fake_embedding_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeEmbeddingProvider(dimensions=1536)

    def _get_provider(settings: Settings | None = None) -> FakeEmbeddingProvider:
        return provider

    monkeypatch.setattr("app.services.embeddings.factory.get_embedding_provider", _get_provider)
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
    global _test_session_factory
    _dispatched_job_ids.clear()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    _test_session_factory = session_factory

    def _dispatch(job_id: str) -> None:
        _dispatched_job_ids.append(job_id)

    monkeypatch.setattr("app.api.routes.public_chat.dispatch_chat_job", _dispatch)


async def _run_dispatched_chat_jobs() -> None:
    assert _test_session_factory is not None
    while _dispatched_job_ids:
        job_id = _dispatched_job_ids.pop(0)
        await execute_chat_job(
            job_id,
            session_factory=_test_session_factory,
            settings=Settings(),
            llm_provider=FakeLLMProvider(),
        )


async def _submit_chat(
    client: AsyncClient,
    *,
    message: str,
    session_id: str,
    conversation_id: int | None = None,
) -> dict:
    payload: dict[str, str | int] = {"message": message, "session_id": session_id}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id
    response = await client.post("/api/public/chat", json=payload)
    assert response.status_code == 202
    return response.json()


async def _poll_chat_job(
    client: AsyncClient,
    *,
    job_id: str,
    session_id: str,
) -> dict:
    response = await client.get(
        f"/api/public/chat/jobs/{job_id}",
        params={"session_id": session_id},
    )
    assert response.status_code == 200
    return response.json()


async def _submit_and_poll(
    client: AsyncClient,
    *,
    message: str,
    session_id: str,
    conversation_id: int | None = None,
) -> tuple[dict, dict]:
    created = await _submit_chat(
        client,
        message=message,
        session_id=session_id,
        conversation_id=conversation_id,
    )
    await _run_dispatched_chat_jobs()
    polled = {}
    for _ in range(20):
        polled = await _poll_chat_job(
            client,
            job_id=created["job_id"],
            session_id=session_id,
        )
        if polled["status"] in {ChatJobStatus.COMPLETED, ChatJobStatus.FAILED}:
            break
        await asyncio.sleep(0.01)
    return created, polled


@pytest.mark.asyncio
async def test_public_chat_does_not_require_auth(client: AsyncClient) -> None:
    created, polled = await _submit_and_poll(
        client,
        message="Hello",
        session_id="public-session-1",
    )
    assert created["session_id"] == "public-session-1"
    assert created["status"] == ChatJobStatus.QUEUED
    assert "assistant_message" not in created
    assert polled["status"] == ChatJobStatus.COMPLETED
    assert polled["response"]["session_id"] == "public-session-1"
    assert "assistant_message" in polled["response"]


@pytest.mark.asyncio
async def test_public_settings_returns_minimal_metadata(client: AsyncClient) -> None:
    response = await client.get("/api/public/settings")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"]
    assert payload["app_url"]
    assert payload["default_language"]
    assert isinstance(payload["supported_languages"], list)
    assert "smtp" not in payload
    assert "secret" not in str(payload).lower()


@pytest.mark.asyncio
async def test_public_chat_reuses_session_conversation(client: AsyncClient) -> None:
    session_id = "reuse-session-abc"
    first = await _submit_chat(client, message="First message", session_id=session_id)
    second = await _submit_chat(client, message="Second message", session_id=session_id)
    assert first["conversation_id"] == second["conversation_id"]


@pytest.mark.asyncio
async def test_public_chat_continues_with_matching_conversation_id(client: AsyncClient) -> None:
    session_id = "continue-session-xyz"
    first = await _submit_chat(client, message="Initial turn", session_id=session_id)
    conversation_id = first["conversation_id"]

    second = await _submit_chat(
        client,
        message="Follow-up turn",
        session_id=session_id,
        conversation_id=conversation_id,
    )
    assert second["conversation_id"] == conversation_id


@pytest.mark.asyncio
async def test_public_chat_rejects_conversation_session_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    conversation = await create_conversation(db_session, session_id="owner-session")
    response = await client.post(
        "/api/public/chat",
        json={
            "message": "Hijack attempt",
            "session_id": "other-session",
            "conversation_id": conversation.id,
        },
    )
    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_public_chat_job_rejects_session_mismatch(client: AsyncClient) -> None:
    created = await _submit_chat(
        client,
        message="Hello",
        session_id="job-owner-session",
    )
    response = await client.get(
        f"/api/public/chat/jobs/{created['job_id']}",
        params={"session_id": "other-session"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_chat_unknown_job_returns_404(client: AsyncClient) -> None:
    response = await client.get(
        "/api/public/chat/jobs/missing-job",
        params={"session_id": "session-404"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_chat_unknown_conversation_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/public/chat",
        json={
            "message": "Missing conversation",
            "session_id": "session-404",
            "conversation_id": 99999,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_public_chat_salary_question_is_refused(client: AsyncClient) -> None:
    _, polled = await _submit_and_poll(
        client,
        message="What is your salary expectation?",
        session_id="salary-session",
    )
    payload = polled["response"]
    assert payload["refused"] is True
    assert "salary" in payload["assistant_message"].lower()
    assert "retrieval_log_id" not in payload
    assert "unanswered_prompt_id" not in payload
    assert "intent" not in payload
    assert "policy_decision" not in payload


@pytest.mark.asyncio
async def test_public_chat_grounded_answer_includes_safe_sources(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _seed_public_career_record(
        db_session,
        title="Platform Engineer",
        content="Built internal platforms and APIs.",
    )

    _, polled = await _submit_and_poll(
        client,
        message="Tell me about your platform engineering experience",
        session_id="grounded-session",
    )
    payload = polled["response"]
    assert payload["refused"] is False
    assert payload["grounded"] is True
    assert "Platform Engineer" in payload["assistant_message"]
    assert payload["sources"]
    for source in payload["sources"]:
        assert set(source.keys()) == {"source_type", "title"}
        assert "source_id" not in source
        assert "snippet" not in source
        assert "score" not in source


@pytest.mark.asyncio
async def test_public_chat_unsupported_question_is_refused(client: AsyncClient) -> None:
    _, polled = await _submit_and_poll(
        client,
        message="Tell me about quantum chemistry research",
        session_id="unsupported-session",
    )
    payload = polled["response"]
    assert payload["refused"] is True
    assert payload["sources"] == []


@pytest.mark.asyncio
async def test_public_chat_failed_job_returns_safe_error(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    db_engine: AsyncEngine,
) -> None:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _fail_job(job_id: str) -> None:
        async with session_factory() as session:
            job = await get_chat_job(session, job_id)
            assert job is not None
            job.status = ChatJobStatus.FAILED
            job.error_message = "internal boom"
            await session.commit()

    def _dispatch_failure(job_id: str) -> None:
        _dispatched_job_ids.append(job_id)

    monkeypatch.setattr("app.api.routes.public_chat.dispatch_chat_job", _dispatch_failure)

    created = await _submit_chat(
        client,
        message="Hello",
        session_id="failed-job-session",
    )
    await _fail_job(created["job_id"])
    polled = {}
    for _ in range(20):
        polled = await _poll_chat_job(
            client,
            job_id=created["job_id"],
            session_id="failed-job-session",
        )
        if polled["status"] == ChatJobStatus.FAILED:
            break
        await asyncio.sleep(0.01)
    assert polled["status"] == ChatJobStatus.FAILED
    assert polled["response"] is None
    assert polled["error_message"]
    assert "internal boom" not in polled["error_message"]


@pytest.mark.asyncio
async def test_public_chat_excludes_private_records_from_sources(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _seed_public_profile_item(
        db_session,
        key="headline",
        label="Headline",
        value="Public Headline",
    )
    private_record = CareerRecord(
        record_type=CareerRecordType.EXPERIENCE,
        title="Secret Project",
        summary="Private confidential work.",
        content="Private confidential work.",
        visibility=Visibility.PRIVATE,
    )
    db_session.add(private_record)
    await db_session.commit()

    _, polled = await _submit_and_poll(
        client,
        message="What is your headline?",
        session_id="private-filter-session",
    )
    payload = polled["response"]
    source_titles = [source["title"] for source in payload["sources"]]
    assert "Secret Project" not in source_titles
    assert "Public Headline" in payload["assistant_message"]


@pytest.mark.asyncio
async def test_public_legal_pages_remain_readable(client: AsyncClient) -> None:
    privacy = await client.get("/api/public/privacy")
    terms = await client.get("/api/public/terms")
    assert privacy.status_code == 200
    assert terms.status_code == 200
