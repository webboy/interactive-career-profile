from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.services.agent.context import build_context_text, summarize_used_sources
from app.services.retrieval.hybrid import run_hybrid_retrieval


@dataclass(frozen=True)
class EvidenceToolResult:
    query: str
    summary: str
    retrieval_log_id: int | None
    sources: list[dict[str, str | bool]]
    had_usable_context: bool


async def run_evidence_tool(
    session: AsyncSession,
    query: str,
    *,
    settings: Settings | None = None,
    intent_hints: list[str] | None = None,
    document_search_override=None,
) -> EvidenceToolResult:
    config = settings or get_settings()
    retrieval_result = await run_hybrid_retrieval(
        session,
        query,
        intent_hints=intent_hints,
        settings=config,
        document_search_override=document_search_override,
    )

    context_text = build_context_text(retrieval_result.sources)
    if not retrieval_result.had_usable_context or not context_text:
        summary = "No verified public evidence was found for that query."
    else:
        summary = context_text

    return EvidenceToolResult(
        query=query,
        summary=summary,
        retrieval_log_id=retrieval_result.retrieval_log_id,
        sources=summarize_used_sources(retrieval_result.sources),
        had_usable_context=retrieval_result.had_usable_context,
    )
