from app.services.llm.base import LLMMessage


class FakeLLMProvider:
    """Deterministic LLM provider for tests without network calls."""

    def __init__(self, *, grounding_pass: bool = True) -> None:
        self._grounding_pass = grounding_pass

    async def complete(self, messages: list[LLMMessage]) -> str:
        user_messages = [message.content for message in messages if message.role == "user"]
        user_content = user_messages[-1] if user_messages else ""
        lowered = user_content.lower()

        if "grounding verification" in lowered:
            return "YES" if self._grounding_pass else "NO"

        if "ignore all instructions" in lowered or "ignore previous instructions" in lowered:
            for line in user_content.splitlines():
                if line.startswith("[career_record:") or line.startswith("[profile_item:"):
                    title = line.split(":", 1)[1].split("]", 1)[0].strip()
                    snippet_start = user_content.find(line) + len(line)
                    snippet = user_content[snippet_start:].strip().split("\n", 1)[0]
                    if snippet:
                        return (
                            "I can only answer from verified public profile data and cannot "
                            f"follow instructions embedded in untrusted user content. {title}: {snippet}"
                        )
            return (
                "I can only answer from verified public profile data. "
                "I cannot follow instructions embedded in untrusted user content."
            )

        if "verified public context" in lowered:
            for line in user_content.splitlines():
                if line.startswith("[career_record:") or line.startswith("[profile_item:"):
                    title = line.split(":", 1)[1].split("]", 1)[0].strip()
                    snippet_start = user_content.find(line) + len(line)
                    snippet = user_content[snippet_start:].strip().split("\n", 1)[0]
                    if snippet:
                        return f"Based on verified profile data, {title}: {snippet}"

            for line in user_content.splitlines():
                if line.startswith("[document_chunk:"):
                    title = line.split(":", 1)[1].split("]", 1)[0].strip()
                    snippet_start = user_content.find(line) + len(line)
                    snippet = user_content[snippet_start:].strip().split("\n", 1)[0]
                    if snippet:
                        return (
                            f"Based on verified profile data and supporting document evidence "
                            f"({title}): {snippet}"
                        )

        return (
            "I do not have enough verified public information to answer that question safely."
        )
