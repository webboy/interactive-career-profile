import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import CareerRecordType, Visibility
from app.db.models.career_record import CareerRecord
from app.services.conversations import create_conversation
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.llm.fake_provider import FakeLLMProvider
from tests.test_retrieval import _seed_public_career_record, _seed_public_profile_item


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
    monkeypatch.setattr("app.api.routes.public_chat.get_llm_provider", _get_provider)


@pytest.mark.asyncio
async def test_public_chat_does_not_require_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/public/chat",
        json={
            "message": "Hello",
            "session_id": "public-session-1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "public-session-1"
    assert "assistant_message" in payload


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
    first = await client.post(
        "/api/public/chat",
        json={"message": "First message", "session_id": session_id},
    )
    second = await client.post(
        "/api/public/chat",
        json={"message": "Second message", "session_id": session_id},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["conversation_id"] == second.json()["conversation_id"]


@pytest.mark.asyncio
async def test_public_chat_continues_with_matching_conversation_id(client: AsyncClient) -> None:
    session_id = "continue-session-xyz"
    first = await client.post(
        "/api/public/chat",
        json={"message": "Initial turn", "session_id": session_id},
    )
    conversation_id = first.json()["conversation_id"]

    second = await client.post(
        "/api/public/chat",
        json={
            "message": "Follow-up turn",
            "session_id": session_id,
            "conversation_id": conversation_id,
        },
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id


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
    response = await client.post(
        "/api/public/chat",
        json={
            "message": "What is your salary expectation?",
            "session_id": "salary-session",
        },
    )
    assert response.status_code == 200
    payload = response.json()
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

    response = await client.post(
        "/api/public/chat",
        json={
            "message": "Tell me about your platform engineering experience",
            "session_id": "grounded-session",
        },
    )
    assert response.status_code == 200
    payload = response.json()
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
    response = await client.post(
        "/api/public/chat",
        json={
            "message": "Tell me about quantum chemistry research",
            "session_id": "unsupported-session",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["refused"] is True
    assert payload["sources"] == []


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

    response = await client.post(
        "/api/public/chat",
        json={
            "message": "What is your headline?",
            "session_id": "private-filter-session",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    source_titles = [source["title"] for source in payload["sources"]]
    assert "Secret Project" not in source_titles
    assert "Public Headline" in payload["assistant_message"]


@pytest.mark.asyncio
async def test_public_legal_pages_remain_readable(client: AsyncClient) -> None:
    privacy = await client.get("/api/public/privacy")
    terms = await client.get("/api/public/terms")
    assert privacy.status_code == 200
    assert terms.status_code == 200
