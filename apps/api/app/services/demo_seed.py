from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import (
    CareerRecordType,
    DocumentFileType,
    DocumentSourceType,
    DocumentStatus,
    EmailDeliveryStatus,
    EmbeddingStatus,
    LeadStatus,
    MessageRole,
    ProfileItemType,
    SourceCategory,
    ToolCallStatus,
    Visibility,
)
from app.db.models.career_record import CareerRecord
from app.db.models.conversation import Conversation, Message, ToolCall
from app.db.models.document import Document, DocumentChunk
from app.db.models.lead import FollowUpRequest, JobSubmission, MeetingRequest
from app.db.models.profile_item import ProfileItem
from app.db.models.retrieval_log import RetrievalLog, RetrievalLogItem, UnansweredPrompt
from app.schemas.career_records import CareerRecordCreateRequest, CareerRecordUpdateRequest
from app.schemas.documents import DocumentTextCreateRequest
from app.schemas.profile import ProfileItemCreateRequest, ProfileItemUpdateRequest
from app.services.career_records import create_career_record, update_career_record
from app.services.conversations import add_message, create_conversation, record_tool_call
from app.services.documents import chunk_document, create_text_document, list_document_chunks
from app.services.embeddings.document_chunks import embed_document_chunk, run_pending_document_chunk_embeddings
from app.services.legal_pages import update_legal_page
from app.services.profile_items import create_profile_item, update_profile_item
from app.services.retrieval.hybrid import run_hybrid_retrieval
from app.services.settings import upsert_setting
from app.services.users import create_user, get_user_by_email, update_user_password

DEMO_SOURCE = "demo-seed"
DEMO_KEY_PREFIX = "demo."
DEMO_SESSION_ID = "demo-seed-session"

DEMO_ADMIN_EMAIL_DEFAULT = "demo-admin@example.com"
DEMO_ADMIN_PASSWORD_DEFAULT = "change-me-demo-password"

DEMO_MEETING_EMAIL = "demo-meeting@example.com"
DEMO_FOLLOWUP_EMAIL = "demo-followup@example.com"
DEMO_JOB_EMAIL = "demo-job@example.com"

DEMO_DOCUMENT_TITLES = frozenset(
    {
        "Demo: Platform Migration Case Study",
        "Demo: Reference Letter — Northstar Labs",
        "Demo: Thesis — Distributed Event Processing",
        "Demo: Private Interview Notes",
    }
)

DEMO_CAREER_TITLES = frozenset(
    {
        "Senior Platform Engineer — Northstar Labs",
        "Platform Migration Program",
        "M.Sc. Distributed Systems",
    }
)

_EMBEDDED_DEMO_ASSETS: dict[str, str] = {
    "case-study-platform-migration.md": """# Platform Migration Case Study

Alex Rivera led a multi-region platform migration for Northstar Labs while serving as Senior Platform Engineer.

## Context

The legacy deployment stack relied on manual releases and inconsistent observability. Alex designed a Kubernetes-based platform with GitOps workflows, standardized service templates, and automated rollout gates.

## Outcomes

- Reduced deployment lead time from days to under one hour.
- Introduced SLO dashboards and incident runbooks adopted by three product teams.
- Mentored two engineers through platform onboarding and on-call readiness.
""",
    "reference-letter-northstar.md": """# Reference Letter — Northstar Labs

Alex Rivera served as Senior Platform Engineer on our core infrastructure team and relocated to our Munich office during the engagement.

Alex became the primary owner of our internal developer platform and was recognized for calm incident leadership and clear documentation.
""",
    "thesis-distributed-systems.md": """# Thesis Excerpt — Reliable Event Processing

Author: Alex Rivera

This work evaluates backpressure strategies for event-driven microservice architectures, including idempotent consumer design and observability signals that predict cascading failures.
""",
}


@dataclass(frozen=True)
class DemoSeedResult:
    admin_email: str
    profile_items: int
    career_records: int
    documents: int
    document_chunks: int
    conversations: int
    retrieval_logs: int
    unanswered_prompts: int
    leads: int
    tool_calls: int
    settings: int
    reset_applied: bool


def _demo_asset_path(filename: str) -> Path | None:
    candidates: list[Path] = []
    for parent in Path(__file__).resolve().parents:
        candidates.append(parent / "data" / "demo" / filename)
    candidates.append(Path.cwd() / "data" / "demo" / filename)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_demo_asset(filename: str) -> str:
    asset_path = _demo_asset_path(filename)
    if asset_path is not None:
        return asset_path.read_text(encoding="utf-8")
    return _EMBEDDED_DEMO_ASSETS[filename]


async def _get_profile_item_by_key(session: AsyncSession, key: str) -> ProfileItem | None:
    result = await session.execute(select(ProfileItem).where(ProfileItem.key == key))
    return result.scalar_one_or_none()


async def _upsert_profile_item(
    session: AsyncSession,
    *,
    key: str,
    item_type: ProfileItemType,
    label: str,
    value: str,
    visibility: Visibility,
    sort_order: int,
) -> ProfileItem:
    existing = await _get_profile_item_by_key(session, key)
    if existing is None:
        return await create_profile_item(
            session,
            ProfileItemCreateRequest(
                key=key,
                type=item_type,
                label=label,
                value=value,
                visibility=visibility,
                source=DEMO_SOURCE,
                sort_order=sort_order,
            ),
        )

    return await update_profile_item(
        session,
        existing,
        ProfileItemUpdateRequest(
            key=key,
            type=item_type,
            label=label,
            value=value,
            visibility=visibility,
            source=DEMO_SOURCE,
            sort_order=sort_order,
        ),
    )


async def _get_career_record_by_title(session: AsyncSession, title: str) -> CareerRecord | None:
    result = await session.execute(
        select(CareerRecord).where(
            CareerRecord.title == title,
            CareerRecord.source == DEMO_SOURCE,
        )
    )
    return result.scalar_one_or_none()


async def _upsert_career_record(
    session: AsyncSession,
    *,
    record_type: CareerRecordType,
    title: str,
    summary: str,
    content: str,
    visibility: Visibility,
    sort_order: int,
    start_date: date | None = None,
    end_date: date | None = None,
    tags: str | None = None,
) -> CareerRecord:
    existing = await _get_career_record_by_title(session, title)
    payload = CareerRecordCreateRequest(
        record_type=record_type,
        title=title,
        summary=summary,
        content=content,
        visibility=visibility,
        source=DEMO_SOURCE,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        sort_order=sort_order,
        embedding_status=EmbeddingStatus.NOT_REQUIRED,
    )
    if existing is None:
        return await create_career_record(session, payload)

    return await update_career_record(
        session,
        existing,
        CareerRecordUpdateRequest.model_validate(payload.model_dump()),
    )


async def _get_document_by_title(session: AsyncSession, title: str) -> Document | None:
    result = await session.execute(select(Document).where(Document.title == title))
    return result.scalar_one_or_none()


async def _upsert_text_document(
    session: AsyncSession,
    *,
    title: str,
    content: str,
    visibility: Visibility,
    settings: Settings,
) -> tuple[Document, int]:
    document = await _get_document_by_title(session, title)
    if document is None:
        document = await create_text_document(
            session,
            DocumentTextCreateRequest(title=title, content=content, visibility=visibility),
        )
    else:
        document.extracted_text = content
        document.visibility = visibility
        document.status = DocumentStatus.EXTRACTED
        document.status_error = None
        await session.commit()
        await session.refresh(document)

    document, chunks_created = await chunk_document(session, document, settings=settings)
    return document, chunks_created


async def _upsert_admin_user(session: AsyncSession, *, email: str, password: str) -> None:
    existing = await get_user_by_email(session, email)
    if existing is None:
        await create_user(session, email, password)
        return
    await update_user_password(session, existing, password)


async def _seed_settings(session: AsyncSession) -> int:
    entries = [
        ("demo.public_headline", "Senior Platform Engineer (Demo)", False),
        ("demo.contact_mode", "email_only", False),
        ("demo.internal_note", "Seeded demo configuration for local verification.", True),
    ]
    for key, value, is_secret in entries:
        await upsert_setting(session, key=key, value=value, is_secret=is_secret)
    return len(entries)


async def _seed_legal_pages(session: AsyncSession) -> None:
    privacy = (
        "Privacy Policy (Demo)\n\n"
        "This demo deployment stores public chat conversations, retrieval logs, and lead submissions "
        "for local verification. Do not enter real personal data."
    )
    terms = (
        "Terms of Use (Demo)\n\n"
        "The demo assistant answers only from public structured records and public document chunks. "
        "Salary and phone-number questions are refused by policy."
    )
    await update_legal_page(session, "privacy", "Privacy Policy", privacy)
    await update_legal_page(session, "terms", "Terms of Use", terms)


async def _get_demo_conversation(session: AsyncSession) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(Conversation.session_id == DEMO_SESSION_ID)
    )
    return result.scalar_one_or_none()


async def _seed_conversation_and_tool_calls(session: AsyncSession) -> tuple[Conversation, int]:
    conversation = await _get_demo_conversation(session)
    if conversation is None:
        conversation = await create_conversation(session, session_id=DEMO_SESSION_ID, language="en")
        await add_message(
            session,
            conversation,
            role=MessageRole.USER,
            content="Tell me about Alex's platform engineering experience.",
        )
        await add_message(
            session,
            conversation,
            role=MessageRole.ASSISTANT,
            content=(
                "Alex Rivera is a Senior Platform Engineer focused on internal platforms, "
                "GitOps, and reliability practices."
            ),
        )
    else:
        messages = await session.execute(
            select(Message).where(Message.conversation_id == conversation.id)
        )
        if not list(messages.scalars().all()):
            await add_message(
                session,
                conversation,
                role=MessageRole.USER,
                content="Tell me about Alex's platform engineering experience.",
            )
            await add_message(
                session,
                conversation,
                role=MessageRole.ASSISTANT,
                content=(
                    "Alex Rivera is a Senior Platform Engineer focused on internal platforms, "
                    "GitOps, and reliability practices."
                ),
            )

    tool_calls = await session.execute(
        select(ToolCall).where(ToolCall.conversation_id == conversation.id)
    )
    existing_tool_calls = list(tool_calls.scalars().all())
    if not existing_tool_calls:
        await record_tool_call(
            session,
            conversation,
            tool_name="get_skill_evidence",
            status=ToolCallStatus.SUCCESS,
            request_payload='{"skill":"platform engineering"}',
            response_payload='{"evidence":["Demo: Platform Migration Case Study"]}',
        )
        await record_tool_call(
            session,
            conversation,
            tool_name="request_meeting",
            status=ToolCallStatus.SUCCESS,
            request_payload='{"requester_email":"demo-meeting@example.com"}',
            response_payload='{"status":"queued"}',
        )
        return conversation, 2

    return conversation, len(existing_tool_calls)


async def _get_demo_lead_count(session: AsyncSession) -> int:
    meeting = await session.execute(
        select(MeetingRequest).where(MeetingRequest.requester_email == DEMO_MEETING_EMAIL)
    )
    follow_up = await session.execute(
        select(FollowUpRequest).where(FollowUpRequest.requester_email == DEMO_FOLLOWUP_EMAIL)
    )
    job = await session.execute(
        select(JobSubmission).where(JobSubmission.requester_email == DEMO_JOB_EMAIL)
    )
    return (
        len(list(meeting.scalars().all()))
        + len(list(follow_up.scalars().all()))
        + len(list(job.scalars().all()))
    )


async def _seed_leads(session: AsyncSession, *, retrieval_log_id: int | None) -> int:
    if await _get_demo_lead_count(session) > 0:
        return await _get_demo_lead_count(session)

    meeting = MeetingRequest(
        requester_name="Taylor Morgan",
        requester_email=DEMO_MEETING_EMAIL,
        organization="Demo Hiring Team",
        message="We would like to schedule a technical interview.",
        preferred_times="Tue-Thu afternoons CET",
        status=LeadStatus.REVIEWED,
        admin_email_status=EmailDeliveryStatus.NOT_REQUIRED,
        requester_email_status=EmailDeliveryStatus.NOT_REQUIRED,
    )
    follow_up = FollowUpRequest(
        requester_email=DEMO_FOLLOWUP_EMAIL,
        question="Can Alex share more detail about the platform migration program?",
        status=LeadStatus.NEW,
        admin_email_status=EmailDeliveryStatus.NOT_REQUIRED,
        requester_email_status=EmailDeliveryStatus.NOT_REQUIRED,
    )
    job = JobSubmission(
        requester_email=DEMO_JOB_EMAIL,
        company="Demo Corp",
        role_title="Staff Platform Engineer",
        job_description="Own internal developer platform roadmap and SRE practices.",
        role_fit_summary="Strong overlap with Northstar Labs platform work and distributed systems research.",
        retrieval_log_id=retrieval_log_id,
        status=LeadStatus.NEW,
        admin_email_status=EmailDeliveryStatus.NOT_REQUIRED,
        requester_email_status=EmailDeliveryStatus.NOT_REQUIRED,
    )
    session.add_all([meeting, follow_up, job])
    await session.commit()
    return 3


async def _seed_retrieval_artifacts(session: AsyncSession) -> tuple[int, int, int | None]:
    existing_logs = await session.execute(
        select(RetrievalLog).where(RetrievalLog.session_id == DEMO_SESSION_ID)
    )
    logs = list(existing_logs.scalars().all())
    if logs:
        prompts = await session.execute(
            select(UnansweredPrompt).where(UnansweredPrompt.session_id == DEMO_SESSION_ID)
        )
        return len(logs), len(list(prompts.scalars().all())), logs[0].id

    grounded = await run_hybrid_retrieval(
        session,
        "Where is Alex Rivera based as Senior Platform Engineer?",
        session_id=DEMO_SESSION_ID,
        language="en",
    )
    unanswered = await run_hybrid_retrieval(
        session,
        "zzzz-nonexistent-quantum-chemistry-topic-demo",
        session_id=DEMO_SESSION_ID,
        language="en",
    )

    logs = await session.execute(
        select(RetrievalLog).where(RetrievalLog.session_id == DEMO_SESSION_ID)
    )
    log_count = len(list(logs.scalars().all()))

    prompts = await session.execute(
        select(UnansweredPrompt).where(UnansweredPrompt.session_id == DEMO_SESSION_ID)
    )
    prompt_list = list(prompts.scalars().all())

    retrieval_log_id = grounded.retrieval_log_id or unanswered.retrieval_log_id
    return log_count, len(prompt_list), retrieval_log_id


async def clear_demo_data(session: AsyncSession) -> None:
    demo_conversation = await _get_demo_conversation(session)
    if demo_conversation is not None:
        await session.delete(demo_conversation)
        await session.commit()

    await session.execute(delete(JobSubmission).where(JobSubmission.requester_email == DEMO_JOB_EMAIL))
    await session.execute(
        delete(FollowUpRequest).where(FollowUpRequest.requester_email == DEMO_FOLLOWUP_EMAIL)
    )
    await session.execute(
        delete(MeetingRequest).where(MeetingRequest.requester_email == DEMO_MEETING_EMAIL)
    )

    demo_log_ids = await session.execute(
        select(RetrievalLog.id).where(RetrievalLog.session_id == DEMO_SESSION_ID)
    )
    log_ids = [row[0] for row in demo_log_ids.all()]
    if log_ids:
        await session.execute(
            delete(UnansweredPrompt).where(UnansweredPrompt.retrieval_log_id.in_(log_ids))
        )
        await session.execute(delete(RetrievalLogItem).where(RetrievalLogItem.retrieval_log_id.in_(log_ids)))
        await session.execute(delete(RetrievalLog).where(RetrievalLog.id.in_(log_ids)))

    await session.execute(
        delete(UnansweredPrompt).where(UnansweredPrompt.session_id == DEMO_SESSION_ID)
    )

    for title in DEMO_DOCUMENT_TITLES:
        document = await _get_document_by_title(session, title)
        if document is not None:
            await session.delete(document)

    await session.execute(delete(CareerRecord).where(CareerRecord.source == DEMO_SOURCE))
    await session.execute(
        delete(ProfileItem).where(ProfileItem.key.like(f"{DEMO_KEY_PREFIX}%"))
    )
    await session.commit()


async def run_demo_seed(
    session: AsyncSession,
    *,
    admin_email: str = DEMO_ADMIN_EMAIL_DEFAULT,
    admin_password: str = DEMO_ADMIN_PASSWORD_DEFAULT,
    reset_demo_data: bool = False,
    settings: Settings | None = None,
) -> DemoSeedResult:
    config = settings or get_settings()
    reset_applied = False
    if reset_demo_data:
        await clear_demo_data(session)
        reset_applied = True

    await _upsert_admin_user(session, email=admin_email, password=admin_password)
    settings_count = await _seed_settings(session)
    await _seed_legal_pages(session)

    profile_specs = [
        ("headline", ProfileItemType.TEXT, "Headline", "Senior Platform Engineer", Visibility.PUBLIC, 1),
        ("location", ProfileItemType.LOCATION, "Location", "Berlin, Germany", Visibility.PUBLIC, 2),
        ("availability", ProfileItemType.AVAILABILITY, "Availability", "Open to senior platform roles in the EU", Visibility.PUBLIC, 3),
        ("languages", ProfileItemType.LANGUAGE, "Languages", "English, German, Serbian", Visibility.PUBLIC, 4),
        ("email", ProfileItemType.EMAIL, "Contact Email", "alex.rivera.demo@example.com", Visibility.PUBLIC, 5),
        ("private_note", ProfileItemType.TEXT, "Private Note", "Internal recruiter-only note.", Visibility.PRIVATE, 10),
        ("draft_pitch", ProfileItemType.TEXT, "Draft Pitch", "Work-in-progress positioning statement.", Visibility.DRAFT, 11),
    ]
    for suffix, item_type, label, value, visibility, sort_order in profile_specs:
        await _upsert_profile_item(
            session,
            key=f"{DEMO_KEY_PREFIX}{suffix}",
            item_type=item_type,
            label=label,
            value=value,
            visibility=visibility,
            sort_order=sort_order,
        )

    await _upsert_career_record(
        session,
        record_type=CareerRecordType.EXPERIENCE,
        title="Senior Platform Engineer — Northstar Labs",
        summary="Owns internal developer platform, GitOps, and reliability practices.",
        content=(
            "Alex Rivera served as Senior Platform Engineer at Northstar Labs in Berlin, Germany. "
            "Led platform migration, observability rollouts, and on-call readiness for product teams."
        ),
        visibility=Visibility.PUBLIC,
        sort_order=1,
        start_date=date(2021, 3, 1),
        end_date=date(2025, 12, 31),
        tags="platform,gitops,sre",
    )
    await _upsert_career_record(
        session,
        record_type=CareerRecordType.PROJECT,
        title="Platform Migration Program",
        summary="Multi-region migration to Kubernetes with GitOps workflows.",
        content="Delivered standardized deployment pipelines and reduced release lead time.",
        visibility=Visibility.PUBLIC,
        sort_order=2,
    )
    await _upsert_career_record(
        session,
        record_type=CareerRecordType.EDUCATION,
        title="M.Sc. Distributed Systems",
        summary="Research on reliable event processing and backpressure strategies.",
        content="Thesis work on idempotent consumers and failure observability in microservices.",
        visibility=Visibility.PUBLIC,
        sort_order=3,
    )

    document_specs = [
        (
            "Demo: Platform Migration Case Study",
            _load_demo_asset("case-study-platform-migration.md"),
            Visibility.PUBLIC,
        ),
        (
            "Demo: Reference Letter — Northstar Labs",
            _load_demo_asset("reference-letter-northstar.md"),
            Visibility.PUBLIC,
        ),
        (
            "Demo: Thesis — Distributed Event Processing",
            _load_demo_asset("thesis-distributed-systems.md"),
            Visibility.PUBLIC,
        ),
        (
            "Demo: Private Interview Notes",
            "Private interview notes that must never appear in public retrieval.",
            Visibility.PRIVATE,
        ),
    ]

    documents_created = 0
    for title, content, visibility in document_specs:
        await _upsert_text_document(
            session,
            title=title,
            content=content,
            visibility=visibility,
            settings=config,
        )
        documents_created += 1

    await run_pending_document_chunk_embeddings(session, settings=config)

    all_demo_chunks = await session.execute(
        select(DocumentChunk).join(Document).where(Document.title.in_(DEMO_DOCUMENT_TITLES))
    )
    chunk_list = list(all_demo_chunks.scalars().all())
    chunk_count = len(chunk_list)

    retrieval_logs, unanswered_prompts, retrieval_log_id = await _seed_retrieval_artifacts(session)
    conversation, tool_calls = await _seed_conversation_and_tool_calls(session)
    leads = await _seed_leads(session, retrieval_log_id=retrieval_log_id)

    return DemoSeedResult(
        admin_email=admin_email,
        profile_items=len(profile_specs),
        career_records=len(DEMO_CAREER_TITLES),
        documents=documents_created,
        document_chunks=chunk_count,
        conversations=1,
        retrieval_logs=retrieval_logs,
        unanswered_prompts=unanswered_prompts,
        leads=leads,
        tool_calls=tool_calls,
        settings=settings_count,
        reset_applied=reset_applied,
    )


async def count_demo_seed_records(session: AsyncSession) -> dict[str, int]:
    profile_items = await session.execute(
        select(ProfileItem).where(ProfileItem.key.like(f"{DEMO_KEY_PREFIX}%"))
    )
    career_records = await session.execute(
        select(CareerRecord).where(CareerRecord.source == DEMO_SOURCE)
    )
    documents = await session.execute(select(Document).where(Document.title.in_(DEMO_DOCUMENT_TITLES)))
    conversations = await session.execute(
        select(Conversation).where(Conversation.session_id == DEMO_SESSION_ID)
    )
    retrieval_logs = await session.execute(
        select(RetrievalLog).where(RetrievalLog.session_id == DEMO_SESSION_ID)
    )
    unanswered_prompts = await session.execute(
        select(UnansweredPrompt).where(UnansweredPrompt.session_id == DEMO_SESSION_ID)
    )
    leads = await _get_demo_lead_count(session)

    return {
        "profile_items": len(list(profile_items.scalars().all())),
        "career_records": len(list(career_records.scalars().all())),
        "documents": len(list(documents.scalars().all())),
        "conversations": len(list(conversations.scalars().all())),
        "retrieval_logs": len(list(retrieval_logs.scalars().all())),
        "unanswered_prompts": len(list(unanswered_prompts.scalars().all())),
        "leads": leads,
    }
