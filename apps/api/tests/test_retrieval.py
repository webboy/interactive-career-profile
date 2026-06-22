import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import (
    CareerRecordType,
    DocumentSourceType,
    DocumentStatus,
    EmbeddingStatus,
    ProfileItemType,
    SourceCategory,
    UnansweredPromptReason,
    Visibility,
)
from app.db.models.career_record import CareerRecord
from app.db.models.document import Document, DocumentChunk
from app.db.models.profile_item import ProfileItem
from app.db.models.retrieval_log import RetrievalLog, RetrievalLogItem, UnansweredPrompt
from app.services.embeddings.document_chunks import embed_document_chunk
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.retrieval.document_search import DocumentChunkSearchResult
from app.services.retrieval.hybrid import run_hybrid_retrieval
from app.services.retrieval.structured_selector import select_structured_sources


@pytest.fixture(autouse=True)
def use_fake_embedding_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeEmbeddingProvider(dimensions=1536)

    def _get_provider(settings: Settings | None = None) -> FakeEmbeddingProvider:
        return provider

    monkeypatch.setattr("app.services.embeddings.factory.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.services.embeddings.document_chunks.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.services.retrieval.hybrid.get_embedding_provider", _get_provider)
    monkeypatch.setattr("app.api.routes.admin_retrieval.get_embedding_provider", _get_provider)


async def _seed_public_profile_item(db_session: AsyncSession, *, key: str, label: str, value: str) -> ProfileItem:
    item = ProfileItem(
        key=key,
        type=ProfileItemType.TEXT,
        label=label,
        value=value,
        visibility=Visibility.PUBLIC,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _seed_public_career_record(
    db_session: AsyncSession,
    *,
    title: str,
    content: str,
    record_type: CareerRecordType = CareerRecordType.EXPERIENCE,
) -> CareerRecord:
    record = CareerRecord(
        record_type=record_type,
        title=title,
        summary=content,
        content=content,
        visibility=Visibility.PUBLIC,
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)
    return record


async def _seed_public_document_chunk(
    db_session: AsyncSession,
    *,
    title: str,
    content: str,
    visibility: Visibility = Visibility.PUBLIC,
) -> DocumentChunk:
    document = Document(
        title=title,
        source_type=DocumentSourceType.PASTED_TEXT,
        extracted_text=content,
        visibility=visibility,
        status=DocumentStatus.CHUNKED,
        embedding_status=EmbeddingStatus.PENDING,
    )
    db_session.add(document)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content=content,
        char_start=0,
        char_end=len(content),
        visibility=visibility,
        embedding_status=EmbeddingStatus.PENDING,
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)
    return chunk


@pytest.mark.asyncio
async def test_retrieval_routes_require_auth(client: AsyncClient) -> None:
    assert (await client.post("/api/admin/retrieval/debug", json={"query": "skills"})).status_code == 401
    assert (await client.get("/api/admin/retrieval-logs")).status_code == 401
    assert (await client.get("/api/admin/unanswered-prompts")).status_code == 401
    assert (await client.post("/api/admin/embeddings/document-chunks/run-pending")).status_code == 401


@pytest.mark.asyncio
async def test_structured_only_retrieval_without_embeddings(db_session: AsyncSession) -> None:
    await _seed_public_profile_item(
        db_session,
        key="headline",
        label="Headline",
        value="Senior Platform Engineer",
    )
    await _seed_public_career_record(
        db_session,
        title="Platform Engineer",
        content="Built internal platforms and APIs.",
    )

    sources = await select_structured_sources(db_session, "platform engineer", limit=10)
    assert len(sources) == 2
    assert {source.source_type for source in sources} == {
        SourceCategory.PROFILE_ITEM,
        SourceCategory.CAREER_RECORD,
    }


@pytest.mark.asyncio
async def test_structured_retrieval_excludes_non_public_records(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            ProfileItem(
                key="private-headline",
                type=ProfileItemType.TEXT,
                label="Private Headline",
                value="Hidden platform engineer profile",
                visibility=Visibility.PRIVATE,
            ),
            ProfileItem(
                key="draft-headline",
                type=ProfileItemType.TEXT,
                label="Draft Headline",
                value="Draft platform engineer profile",
                visibility=Visibility.DRAFT,
            ),
            CareerRecord(
                record_type=CareerRecordType.EXPERIENCE,
                title="Private Platform Role",
                content="Private platform engineer history",
                visibility=Visibility.PRIVATE,
            ),
        ]
    )
    await db_session.commit()

    sources = await select_structured_sources(db_session, "platform engineer", limit=10)
    assert sources == []


@pytest.mark.asyncio
async def test_document_evidence_respects_score_threshold(db_session: AsyncSession) -> None:
    async def fake_search(_session, _query, *, limit, threshold):
        score = threshold - 0.1
        if score < threshold:
            return []
        return [
            DocumentChunkSearchResult(
                source_type=SourceCategory.DOCUMENT_CHUNK,
                source_id=1,
                title="Resume",
                snippet="Below threshold evidence",
                visibility=Visibility.PUBLIC,
                score=score,
            )
        ]

    result = await run_hybrid_retrieval(
        db_session,
        "resume evidence",
        document_search_override=fake_search,
        document_score_threshold=0.7,
    )

    document_sources = [source for source in result.sources if source.source_type == SourceCategory.DOCUMENT_CHUNK]
    assert document_sources == []
    assert result.had_usable_context is False
    assert result.unanswered_prompt_id is not None


@pytest.mark.asyncio
async def test_hybrid_retrieval_merges_structured_and_document_sources(db_session: AsyncSession) -> None:
    await _seed_public_career_record(
        db_session,
        title="Platform Engineer",
        content="Canonical platform engineering experience.",
    )

    async def fake_search(_session, _query, *, limit, threshold):
        return [
            DocumentChunkSearchResult(
                source_type=SourceCategory.DOCUMENT_CHUNK,
                source_id=99,
                title="Project Portfolio",
                snippet="Supporting document evidence about delivery.",
                visibility=Visibility.PUBLIC,
                score=0.91,
            )
        ]

    result = await run_hybrid_retrieval(
        db_session,
        "platform engineering delivery",
        document_search_override=fake_search,
    )

    assert result.had_usable_context is True
    source_types = {source.source_type for source in result.sources if source.was_used}
    assert SourceCategory.CAREER_RECORD in source_types
    assert SourceCategory.DOCUMENT_CHUNK in source_types


@pytest.mark.asyncio
async def test_precedence_keeps_structured_sources_ahead_of_documents(db_session: AsyncSession) -> None:
    await _seed_public_career_record(
        db_session,
        title="Platform Engineer",
        content="Canonical structured answer.",
    )

    async def fake_search(_session, _query, *, limit, threshold):
        return [
            DocumentChunkSearchResult(
                source_type=SourceCategory.DOCUMENT_CHUNK,
                source_id=42,
                title="Platform Engineer",
                snippet="Conflicting document evidence.",
                visibility=Visibility.PUBLIC,
                score=0.95,
            )
        ]

    result = await run_hybrid_retrieval(
        db_session,
        "platform engineer",
        document_search_override=fake_search,
    )

    structured = next(
        source for source in result.sources if source.source_type == SourceCategory.CAREER_RECORD
    )
    document = next(
        source for source in result.sources if source.source_type == SourceCategory.DOCUMENT_CHUNK
    )
    assert structured.was_used is True
    assert document.was_used is False
    assert structured.precedence_rank < document.precedence_rank


@pytest.mark.asyncio
async def test_retrieval_logs_and_unanswered_prompts_are_persisted(db_session: AsyncSession) -> None:
    async def empty_search(_session, _query, *, limit, threshold):
        return []

    result = await run_hybrid_retrieval(
        db_session,
        "unknown topic without context",
        document_search_override=empty_search,
    )

    log = await db_session.get(RetrievalLog, result.retrieval_log_id)
    assert log is not None
    assert log.had_usable_context is False

    items = await db_session.execute(
        select(RetrievalLogItem).where(RetrievalLogItem.retrieval_log_id == log.id)
    )
    assert list(items.scalars().all()) == []

    prompt = await db_session.get(UnansweredPrompt, result.unanswered_prompt_id)
    assert prompt is not None
    assert prompt.reason == UnansweredPromptReason.NO_CONTEXT


@pytest.mark.asyncio
async def test_embed_document_chunk_updates_ready_state(db_session: AsyncSession) -> None:
    chunk = await _seed_public_document_chunk(
        db_session,
        title="Resume",
        content="Built hybrid retrieval systems.",
    )
    provider = FakeEmbeddingProvider(dimensions=1536)

    updated = await embed_document_chunk(db_session, chunk, provider=provider)

    assert updated.embedding_status == EmbeddingStatus.READY
    assert updated.embedding is not None
    assert len(updated.embedding) == 1536
    assert updated.embedding_error is None


@pytest.mark.asyncio
async def test_admin_debug_retrieval_endpoint(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_public_profile_item(
        db_session,
        key="location",
        label="Location",
        value="Berlin, Germany",
    )

    response = await auth_client.post(
        "/api/admin/retrieval/debug",
        json={"query": "Berlin location"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["had_usable_context"] is True
    assert payload["retrieval_log_id"] >= 1
    assert any(source["source_type"] == SourceCategory.PROFILE_ITEM for source in payload["sources"])

    logs_response = await auth_client.get("/api/admin/retrieval-logs")
    assert logs_response.status_code == 200
    assert len(logs_response.json()) >= 1

    log_detail_response = await auth_client.get(
        f"/api/admin/retrieval-logs/{payload['retrieval_log_id']}"
    )
    assert log_detail_response.status_code == 200
    assert log_detail_response.json()["query"] == "Berlin location"


@pytest.mark.asyncio
async def test_admin_embed_document_chunk_route(auth_client: AsyncClient, db_session: AsyncSession) -> None:
    chunk = await _seed_public_document_chunk(
        db_session,
        title="Notes",
        content="Embedding route test content.",
    )

    response = await auth_client.post(f"/api/admin/document-chunks/{chunk.id}/embed")
    assert response.status_code == 200
    payload = response.json()
    assert payload["chunk_id"] == chunk.id
    assert payload["embedding_status"] == EmbeddingStatus.READY


@pytest.mark.asyncio
async def test_non_public_document_chunks_are_not_selected_structurally(db_session: AsyncSession) -> None:
    await _seed_public_document_chunk(
        db_session,
        title="Private Notes",
        content="platform engineer private notes",
        visibility=Visibility.PRIVATE,
    )

    sources = await select_structured_sources(db_session, "platform engineer private notes", limit=10)
    assert sources == []
