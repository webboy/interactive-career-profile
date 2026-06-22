from openai import AsyncOpenAI

from app.core.config import Settings
from app.services.llm.base import LLMMessage, LLMProvider


class OpenAILLMProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI LLM provider")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._max_tokens = settings.agent_max_tokens
        self._temperature = settings.agent_temperature

    async def complete(self, messages: list[LLMMessage]) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        content = response.choices[0].message.content
        return content or ""


def create_openai_llm_provider(settings: Settings) -> LLMProvider:
    return OpenAILLMProvider(settings)
