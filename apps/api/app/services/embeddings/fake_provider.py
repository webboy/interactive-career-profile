import hashlib
import math


class FakeEmbeddingProvider:
    """Deterministic local embedding provider for tests without network calls."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_text(self, text: str) -> list[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [_deterministic_vector(text, self._dimensions) for text in texts]


def _deterministic_vector(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    index = 0
    while len(values) < dimensions:
        chunk = digest[index % len(digest)]
        values.append((chunk / 255.0) * 2.0 - 1.0)
        index += 1

    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]
