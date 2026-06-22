from app.services.agent.prompts import build_grounding_prompt
from app.services.llm.base import LLMMessage, LLMProvider


async def verify_grounding(
    provider: LLMProvider,
    *,
    context_text: str,
    answer: str,
) -> bool:
    prompt = build_grounding_prompt(context_text, answer)
    response = await provider.complete(
        [
            LLMMessage(role="system", content="You verify whether answers are grounded in context."),
            LLMMessage(role="user", content=prompt),
        ]
    )
    normalized = response.strip().upper()
    return normalized.startswith("YES")
