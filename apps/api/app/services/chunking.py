from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkSegment:
    chunk_index: int
    content: str
    char_start: int
    char_end: int


def chunk_text(
    text: str,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
) -> list[ChunkSegment]:
    if chunk_size_chars <= 0:
        raise ValueError("chunk_size_chars must be greater than zero")
    if chunk_overlap_chars < 0:
        raise ValueError("chunk_overlap_chars must be zero or greater")
    if chunk_overlap_chars >= chunk_size_chars:
        raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")

    normalized = text.strip()
    if not normalized:
        return []

    segments: list[ChunkSegment] = []
    start = 0
    chunk_index = 0

    while start < len(normalized):
        end = min(start + chunk_size_chars, len(normalized))
        content = normalized[start:end].strip()
        if content:
            segments.append(
                ChunkSegment(
                    chunk_index=chunk_index,
                    content=content,
                    char_start=start,
                    char_end=end,
                )
            )
            chunk_index += 1

        if end >= len(normalized):
            break

        start = max(end - chunk_overlap_chars, start + 1)

    return segments
