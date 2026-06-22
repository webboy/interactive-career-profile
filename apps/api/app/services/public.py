from app.schemas.public import PublicChatResponse, PublicSourceSummary
from app.services.agent.graph import AgentTurnResult


def map_agent_result_to_public_response(
    result: AgentTurnResult,
    *,
    session_id: str,
) -> PublicChatResponse:
    return PublicChatResponse(
        conversation_id=result.conversation_id,
        session_id=session_id,
        assistant_message=result.assistant_message,
        language=result.language,
        refused=result.refused,
        grounded=result.grounded,
        sources=[
            PublicSourceSummary(
                source_type=str(source["source_type"]),
                title=str(source["title"]),
            )
            for source in result.sources
        ],
    )
