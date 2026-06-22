from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.agent import (
    AgentDebugRequest,
    AgentDebugResponse,
    AgentSourceSummary,
    ConversationMessageResponse,
    ConversationMessagesResponse,
)
from app.services.agent.graph import run_agent_turn
from app.services.conversations import get_conversation, list_conversation_messages
from app.services.llm.factory import get_llm_provider

router = APIRouter(prefix="/api/admin", tags=["admin-agent"])


@router.post("/agent/debug", response_model=AgentDebugResponse)
async def admin_debug_agent(
    payload: AgentDebugRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> AgentDebugResponse:
    settings = get_settings()
    provider = get_llm_provider(settings)

    try:
        result = await run_agent_turn(
            session,
            payload.message,
            conversation_id=payload.conversation_id,
            session_id=payload.session_id,
            language=payload.language,
            settings=settings,
            llm_provider=provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AgentDebugResponse(
        conversation_id=result.conversation_id,
        assistant_message=result.assistant_message,
        language=result.language,
        intent=result.intent,
        policy_decision=result.policy_decision,
        retrieval_log_id=result.retrieval_log_id,
        unanswered_prompt_id=result.unanswered_prompt_id,
        sources=[AgentSourceSummary(**source) for source in result.sources],
        grounded=result.grounded,
        refused=result.refused,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def admin_list_conversation_messages(
    conversation_id: int,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> ConversationMessagesResponse:
    conversation = await get_conversation(session, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await list_conversation_messages(session, conversation_id)
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[
            ConversationMessageResponse(
                id=message.id,
                role=message.role.value,
                content=message.content,
            )
            for message in messages
        ],
    )
