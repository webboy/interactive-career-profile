from app.core.enums import SourceCategory
from app.services.retrieval.hybrid import HybridRetrievalResult, RetrievedContextSource


def build_context_text(sources: list[RetrievedContextSource]) -> str:
    used_sources = [source for source in sources if source.was_used]
    if not used_sources:
        return ""

    blocks: list[str] = []
    structured = [source for source in used_sources if source.source_type != SourceCategory.DOCUMENT_CHUNK]
    documents = [source for source in used_sources if source.source_type == SourceCategory.DOCUMENT_CHUNK]

    if structured:
        blocks.append("Canonical structured records:")
        for source in structured:
            blocks.append(_format_source(source))

    if documents:
        blocks.append("Supporting document evidence:")
        for source in documents:
            blocks.append(_format_source(source))

    return "\n".join(blocks)


def _format_source(source: RetrievedContextSource) -> str:
    label = source.source_type.value
    return f"[{label}: {source.title}]\n{source.snippet}"


def summarize_used_sources(sources: list[RetrievedContextSource]) -> list[dict[str, str | bool]]:
    return [
        {
            "source_type": source.source_type.value,
            "title": source.title,
            "was_used": source.was_used,
        }
        for source in sources
        if source.was_used
    ]
