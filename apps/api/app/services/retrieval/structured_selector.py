from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CareerRecordType, SourceCategory, Visibility
from app.db.models.career_record import CareerRecord
from app.db.models.profile_item import ProfileItem
from app.services.career_records import list_public_career_records
from app.services.profile_items import list_public_profile_items


INTENT_RECORD_TYPE_MAP: dict[str, CareerRecordType] = {
    "experience": CareerRecordType.EXPERIENCE,
    "experiences": CareerRecordType.EXPERIENCE,
    "project": CareerRecordType.PROJECT,
    "projects": CareerRecordType.PROJECT,
    "skill": CareerRecordType.SKILL,
    "skills": CareerRecordType.SKILL,
    "education": CareerRecordType.EDUCATION,
    "certification": CareerRecordType.CERTIFICATION,
    "certifications": CareerRecordType.CERTIFICATION,
    "language": CareerRecordType.LANGUAGE,
    "languages": CareerRecordType.LANGUAGE,
    "achievement": CareerRecordType.ACHIEVEMENT,
    "achievements": CareerRecordType.ACHIEVEMENT,
    "leadership": CareerRecordType.LEADERSHIP,
    "availability": CareerRecordType.AVAILABILITY,
}


@dataclass(frozen=True)
class StructuredSource:
    source_type: SourceCategory
    source_id: int
    title: str
    snippet: str
    visibility: Visibility
    score: float
    record_type: str | None = None


def _tokenize_query(query: str) -> list[str]:
    return [token for token in query.lower().split() if token]


def _text_matches(query_tokens: list[str], *fields: str | None) -> tuple[bool, float]:
    if not query_tokens:
        return True, 1.0

    searchable = " ".join(field for field in fields if field).lower()
    if not searchable:
        return False, 0.0

    matches = sum(1 for token in query_tokens if token in searchable)
    if matches == 0:
        return False, 0.0

    return True, matches / len(query_tokens)


def _resolve_intent_record_types(intent_hints: list[str]) -> set[CareerRecordType]:
    resolved: set[CareerRecordType] = set()
    for hint in intent_hints:
        record_type = INTENT_RECORD_TYPE_MAP.get(hint.lower())
        if record_type is not None:
            resolved.add(record_type)
    return resolved


def _profile_item_source(item: ProfileItem, score: float) -> StructuredSource:
    return StructuredSource(
        source_type=SourceCategory.PROFILE_ITEM,
        source_id=item.id,
        title=item.label,
        snippet=item.value,
        visibility=item.visibility,
        score=score,
        record_type=item.type.value,
    )


def _career_record_source(record: CareerRecord, score: float) -> StructuredSource:
    snippet = record.summary or record.content
    return StructuredSource(
        source_type=SourceCategory.CAREER_RECORD,
        source_id=record.id,
        title=record.title,
        snippet=snippet,
        visibility=record.visibility,
        score=score,
        record_type=record.record_type.value,
    )


async def select_structured_sources(
    session: AsyncSession,
    query: str,
    *,
    limit: int,
    intent_hints: list[str] | None = None,
) -> list[StructuredSource]:
    hints = intent_hints or []
    query_tokens = _tokenize_query(query)
    intent_record_types = _resolve_intent_record_types(hints)

    profile_items = await list_public_profile_items(session)
    career_records = await list_public_career_records(session)

    candidates: list[StructuredSource] = []

    for item in profile_items:
        if item.visibility != Visibility.PUBLIC:
            continue
        matched, score = _text_matches(query_tokens, item.key, item.label, item.value)
        if matched:
            candidates.append(_profile_item_source(item, score))

    for record in career_records:
        if record.visibility != Visibility.PUBLIC:
            continue
        if intent_record_types and record.record_type not in intent_record_types:
            continue
        matched, score = _text_matches(
            query_tokens,
            record.title,
            record.summary,
            record.content,
            record.tags,
        )
        if matched:
            candidates.append(_career_record_source(record, score))

    if not candidates and not query_tokens:
        for item in profile_items:
            candidates.append(_profile_item_source(item, 1.0))
        for record in career_records:
            if not intent_record_types or record.record_type in intent_record_types:
                candidates.append(_career_record_source(record, 1.0))

    candidates.sort(key=lambda source: (-source.score, source.source_type.value, source.source_id))
    return candidates[:limit]
