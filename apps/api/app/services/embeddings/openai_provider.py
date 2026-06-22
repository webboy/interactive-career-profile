from openai import AsyncOpenAI

from app.core.config import Settings
from app.services.embeddings.base import EmbeddingProvider


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embedding provider")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model
        self._dimensions = settings.embedding_dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_text(self, text: str) -> list[float]:
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]


def create_openai_embedding_provider(settings: Settings) -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(settings)
