import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.enums import (
    AgentIntent,
    EmailDeliveryStatus,
    LeadStatus,
    ToolCallStatus,
)
from app.db.models.conversation import ToolCall
from app.db.models.lead import FollowUpRequest, JobSubmission, MeetingRequest
from app.db.session import get_db_session
from app.main import create_app
from app.services.agent.graph import run_agent_turn
from app.services.email import FakeEmailSender, set_fake_email_sender
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.mcp.client import ApiMcpClient, InternalApiMcpTransport, set_mcp_client
from tests.test_retrieval import _seed_public_career_record


@pytest.fixture(autouse=True)
def use_fake_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.llm.fake_provider import FakeLLMProvider

    provider = FakeLLMProvider()

    def _get_provider(settings: Settings | None = None) -> FakeLLMProvider:
        return provider

    monkeypatch.setattr("app.services.llm.factory.get_llm_provider", _get_provider)
    monkeypatch.setattr("app.services.agent.graph.get_llm_provider", _get_provider)


@pytest.fixture(autouse=True)
def use_fake_embedding_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeEmbeddingProvider(dimensions=1536)

    def _get_provider(settings: Settings | None = None) -> FakeEmbeddingProvider:
        return provider

    monkeypatch.setattr("app.services.embeddings.factory.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.services.retrieval.hybrid.get_embedding_provider", _get_provider)


@pytest.fixture(autouse=True)
def configure_mcp_client(db_engine) -> None:
    app = create_app()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    settings = get_settings()
    set_fake_email_sender(FakeEmailSender())
    set_mcp_client(
        ApiMcpClient(
            settings=settings,
            transport=InternalApiMcpTransport(settings=settings, app=app),
        )
    )
    yield
    set_fake_email_sender(None)
    set_mcp_client(None)
    app.dependency_overrides.clear()


@pytest.fixture
def internal_headers() -> dict[str, str]:
    settings = get_settings()
    return {"X-MCP-Internal-Token": settings.mcp_internal_api_token}


@pytest.mark.asyncio
async def test_internal_mcp_routes_require_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/internal/mcp/meeting-requests",
        json={
            "requester_name": "Ada Lovelace",
            "requester_email": "ada@example.com",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_meeting_request_persists_and_emails(
    client: AsyncClient,
    db_session: AsyncSession,
    internal_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/internal/mcp/meeting-requests",
        headers=internal_headers,
        json={
            "requester_name": "Ada Lovelace",
            "requester_email": "ada@example.com",
            "organization": "Analytical Engines",
            "message": "Would like to discuss platform work.",
            "preferred_times": "Next week afternoons",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == LeadStatus.SENT.value
    assert payload["admin_email_status"] == EmailDeliveryStatus.SENT.value
    assert payload["requester_email_status"] == EmailDeliveryStatus.SENT.value

    meeting = await db_session.get(MeetingRequest, payload["id"])
    assert meeting is not None
    assert meeting.requester_name == "Ada Lovelace"


@pytest.mark.asyncio
async def test_follow_up_request_persists_and_emails(
    client: AsyncClient,
    db_session: AsyncSession,
    internal_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/internal/mcp/follow-up-requests",
        headers=internal_headers,
        json={
            "requester_email": "recruiter@example.com",
            "question": "Can you share more about leadership experience?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == LeadStatus.SENT.value

    follow_up = await db_session.get(FollowUpRequest, payload["id"])
    assert follow_up is not None
    assert "leadership" in follow_up.question


@pytest.mark.asyncio
async def test_job_submission_role_fit_has_no_salary_claims(
    client: AsyncClient,
    db_session: AsyncSession,
    internal_headers: dict[str, str],
) -> None:
    await _seed_public_career_record(
        db_session,
        title="Backend Engineer",
        content="Built APIs and distributed systems.",
    )

    response = await client.post(
        "/api/internal/mcp/job-submissions",
        headers=internal_headers,
        json={
            "requester_email": "hiring@example.com",
            "company": "Example Corp",
            "role_title": "Backend Engineer",
            "job_description": "Looking for API and distributed systems experience.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    summary = (payload["role_fit_summary"] or "").lower()
    assert "salary" not in summary
    assert "€" not in summary
    assert "$" not in summary
    assert payload["retrieval_log_id"] is not None

    submission = await db_session.get(JobSubmission, payload["id"])
    assert submission is not None
    assert submission.role_fit_summary is not None


@pytest.mark.asyncio
async def test_skill_evidence_uses_structured_precedence(
    client: AsyncClient,
    db_session: AsyncSession,
    internal_headers: dict[str, str],
) -> None:
    await _seed_public_career_record(
        db_session,
        title="Platform Engineer",
        content="Canonical structured platform evidence.",
    )

    response = await client.post(
        "/api/internal/mcp/skill-evidence",
        headers=internal_headers,
        json={"query": "platform engineer"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["had_usable_context"] is True
    assert "Canonical structured platform evidence" in payload["summary"]


@pytest.mark.asyncio
async def test_mcp_client_records_tool_call_success(
    db_session: AsyncSession,
    db_engine,
) -> None:
    from app.services.conversations import create_conversation

    fake_sender = FakeEmailSender()
    set_fake_email_sender(fake_sender)
    settings = get_settings()
    app = create_app()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = ApiMcpClient(
        settings=settings,
        transport=InternalApiMcpTransport(settings=settings, app=app),
    )
    conversation = await create_conversation(db_session)

    result = await client.call_tool(
        db_session,
        conversation_id=conversation.id,
        tool_name="send_follow_up_question",
        arguments={
            "requester_email": "qa@example.com",
            "question": "What is your notice period?",
        },
    )

    assert result.success is True
    tool_calls = await db_session.execute(select(ToolCall).where(ToolCall.conversation_id == conversation.id))
    tool_call = tool_calls.scalar_one()
    assert tool_call.tool_name == "send_follow_up_question"
    assert tool_call.status == ToolCallStatus.SUCCESS


@pytest.mark.asyncio
async def test_mcp_client_records_tool_call_failure(db_session: AsyncSession) -> None:
    from app.services.conversations import create_conversation

    class FailingTransport:
        async def invoke_tool(self, tool_name: str, arguments: dict) -> dict:
            raise RuntimeError("transport failure")

    settings = get_settings()
    client = ApiMcpClient(settings=settings, transport=FailingTransport())
    conversation = await create_conversation(db_session)

    result = await client.call_tool(
        db_session,
        conversation_id=conversation.id,
        tool_name="request_meeting",
        arguments={"requester_name": "Test", "requester_email": "test@example.com"},
    )

    assert result.success is False
    tool_calls = await db_session.execute(select(ToolCall).where(ToolCall.conversation_id == conversation.id))
    tool_call = tool_calls.scalar_one()
    assert tool_call.status == ToolCallStatus.FAILED


@pytest.mark.asyncio
async def test_agent_routes_meeting_request_through_mcp(db_session: AsyncSession) -> None:
    message = (
        "Please schedule a meeting with me. My name is Jordan Lee. "
        "Email: jordan@example.com. Preferred times: Tuesday morning."
    )
    result = await run_agent_turn(db_session, message)

    assert result.intent == AgentIntent.MEETING_REQUEST
    assert "meeting request has been recorded" in result.assistant_message.lower()

    tool_calls = await db_session.execute(select(ToolCall))
    tool_call = tool_calls.scalars().first()
    assert tool_call is not None
    assert tool_call.tool_name == "request_meeting"
    assert tool_call.status == ToolCallStatus.SUCCESS


@pytest.mark.asyncio
async def test_agent_routes_skill_evidence_through_mcp(db_session: AsyncSession) -> None:
    await _seed_public_career_record(
        db_session,
        title="Data Engineer",
        content="Built data pipelines and analytics platforms.",
    )

    result = await run_agent_turn(
        db_session,
        "Show skill evidence for data engineering",
    )

    assert result.intent == AgentIntent.SKILL_EVIDENCE
    assert "data pipelines" in result.assistant_message.lower()

    tool_calls = await db_session.execute(select(ToolCall))
    tool_call = tool_calls.scalars().first()
    assert tool_call is not None
    assert tool_call.tool_name == "get_skill_evidence"


@pytest.mark.asyncio
async def test_salary_question_still_refused_before_mcp(db_session: AsyncSession) -> None:
    message = "Schedule a meeting and tell me your salary expectation. Email: pay@example.com"
    result = await run_agent_turn(db_session, message)

    assert result.refused is True
    tool_calls = await db_session.execute(select(ToolCall))
    assert tool_calls.scalars().first() is None


@pytest.mark.asyncio
async def test_admin_lead_and_tool_call_routes_require_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/admin/leads/meeting-requests")).status_code == 401
    assert (await client.get("/api/admin/leads/follow-up-requests")).status_code == 401
    assert (await client.get("/api/admin/leads/job-submissions")).status_code == 401
    assert (await client.get("/api/admin/tool-calls")).status_code == 401


@pytest.mark.asyncio
async def test_admin_lead_and_tool_call_routes_return_records(
    auth_client: AsyncClient,
    client: AsyncClient,
    internal_headers: dict[str, str],
) -> None:
    meeting_response = await client.post(
        "/api/internal/mcp/meeting-requests",
        headers=internal_headers,
        json={
            "requester_name": "Admin Visible",
            "requester_email": "visible@example.com",
        },
    )
    assert meeting_response.status_code == 200

    meetings = await auth_client.get("/api/admin/leads/meeting-requests")
    assert meetings.status_code == 200
    assert any(item["requester_email"] == "visible@example.com" for item in meetings.json())

    tool_calls = await auth_client.get("/api/admin/tool-calls")
    assert tool_calls.status_code == 200
    assert isinstance(tool_calls.json()["tool_calls"], list)
