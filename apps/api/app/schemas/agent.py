from pydantic import BaseModel, Field

from app.core.enums import AgentIntent, PolicyDecision


class AgentDebugRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None
    session_id: str | None = Field(default=None, max_length=255)
    language: str | None = Field(default=None, max_length=32)


class AgentSourceSummary(BaseModel):
    source_type: str
    title: str
    was_used: bool


class AgentDebugResponse(BaseModel):
    conversation_id: int
    assistant_message: str
    language: str
    intent: AgentIntent
    policy_decision: PolicyDecision
    retrieval_log_id: int | None = None
    unanswered_prompt_id: int | None = None
    sources: list[AgentSourceSummary] = Field(default_factory=list)
    grounded: bool
    refused: bool


class ConversationMessageResponse(BaseModel):
    id: int
    role: str
    content: str


class ConversationMessagesResponse(BaseModel):
    conversation_id: int
    messages: list[ConversationMessageResponse]
