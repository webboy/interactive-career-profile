from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageRole, ToolCallStatus
from app.db.models.conversation import Conversation, Message, ToolCall


async def get_conversation(session: AsyncSession, conversation_id: int) -> Conversation | None:
    result = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()


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
