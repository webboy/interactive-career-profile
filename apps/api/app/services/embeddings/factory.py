from app.core.config import Settings, get_settings
from app.services.embeddings.base import EmbeddingProvider
from app.services.embeddings.fake_provider import FakeEmbeddingProvider
from app.services.embeddings.openai_provider import create_openai_embedding_provider


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    config = settings or get_settings()
    provider_name = (config.embedding_provider or "openai").lower()

    if provider_name == "fake":
        return FakeEmbeddingProvider(dimensions=config.embedding_dimensions)

    if provider_name == "openai":
        return create_openai_embedding_provider(config)

    raise ValueError(f"Unsupported embedding provider: {provider_name}")
