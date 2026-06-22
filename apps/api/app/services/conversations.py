from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageRole, ToolCallStatus
from app.db.models.conversation import Conversation, Message, ToolCall


async def get_conversation(session: AsyncSession, conversation_id: int) -> Conversation | None:
    result = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()


async def get_latest_conversation_for_session(
    session: AsyncSession,
    session_id: str,
) -> Conversation | None:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


class ConversationSessionMismatchError(ValueError):
    """Raised when a conversation does not belong to the supplied public session."""


async def resolve_public_conversation_id(
    session: AsyncSession,
    *,
    session_id: str,
    conversation_id: int | None = None,
    language: str | None = None,
) -> int:
    if conversation_id is not None:
        conversation = await get_conversation(session, conversation_id)
        if conversation is None:
            raise ValueError("Conversation not found")
        if conversation.session_id != session_id:
            raise ConversationSessionMismatchError("Conversation does not belong to session")
        return conversation.id

    latest = await get_latest_conversation_for_session(session, session_id)
    if latest is not None:
        return latest.id

    conversation = await create_conversation(
        session,
        session_id=session_id,
        language=language,
    )
    return conversation.id


async def list_conversation_messages(session: AsyncSession, conversation_id: int) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(result.scalars().all())


async def create_conversation(
    session: AsyncSession,
    *,
    session_id: str | None = None,
    language: str | None = None,
) -> Conversation:
    conversation = Conversation(session_id=session_id, language=language)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def add_message(
    session: AsyncSession,
    conversation: Conversation,
    *,
    role: MessageRole,
    content: str,
) -> Message:
    message = Message(conversation_id=conversation.id, role=role, content=content)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def record_tool_call(
    session: AsyncSession,
    conversation: Conversation,
    *,
    tool_name: str,
    status: ToolCallStatus = ToolCallStatus.PENDING,
    request_payload: str | None = None,
    response_payload: str | None = None,
    error_message: str | None = None,
) -> ToolCall:
    tool_call = ToolCall(
        conversation_id=conversation.id,
        tool_name=tool_name,
        status=status,
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=error_message,
    )
    session.add(tool_call)
    await session.commit()
    await session.refresh(tool_call)
    return tool_call
