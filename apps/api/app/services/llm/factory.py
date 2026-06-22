from app.core.config import Settings, get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.fake_provider import FakeLLMProvider
from app.services.llm.openai_provider import create_openai_llm_provider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    config = settings or get_settings()
    provider_name = (config.llm_provider or "openai").lower()

    if provider_name == "fake":
        return FakeLLMProvider()

    if provider_name == "openai":
        return create_openai_llm_provider(config)

    raise ValueError(f"Unsupported LLM provider: {provider_name}")
