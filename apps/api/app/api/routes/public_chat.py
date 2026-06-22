from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.public import PublicChatRequest, PublicChatResponse
from app.services.agent.graph import run_agent_turn
from app.services.conversations import ConversationSessionMismatchError, resolve_public_conversation_id
from app.services.llm.factory import get_llm_provider
from app.services.public import map_agent_result_to_public_response

router = APIRouter(prefix="/api/public", tags=["public"])


@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(
    payload: PublicChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PublicChatResponse:
    settings = get_settings()
    provider = get_llm_provider(settings)

    try:
        conversation_id = await resolve_public_conversation_id(
            session,
            session_id=payload.session_id,
            conversation_id=payload.conversation_id,
            language=payload.language,
        )
        result = await run_agent_turn(
            session,
            payload.message,
            conversation_id=conversation_id,
            session_id=payload.session_id,
            language=payload.language,
            settings=settings,
            llm_provider=provider,
        )
    except ConversationSessionMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return map_agent_result_to_public_response(result, session_id=payload.session_id)
