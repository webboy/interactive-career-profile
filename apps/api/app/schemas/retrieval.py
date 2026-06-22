from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SourceCategory, UnansweredPromptReason, Visibility


class RetrievedSourceResponse(BaseModel):
    source_type: SourceCategory
    source_id: int
    title: str
    snippet: str
    visibility: Visibility
    score: float | None = None
    was_used: bool
    precedence_rank: int


class RetrievalDebugRequest(BaseModel):
    query: str = Field(min_length=1)
    language: str | None = Field(default=None, max_length=32)
    session_id: str | None = Field(default=None, max_length=255)
    intent_hints: list[str] = Field(default_factory=list)
    structured_limit: int | None = Field(default=None, ge=1, le=100)
    document_limit: int | None = Field(default=None, ge=1, le=100)
    document_score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class RetrievalDebugResponse(BaseModel):
    retrieval_log_id: int
    had_usable_context: bool
    sources: list[RetrievedSourceResponse]
    unanswered_prompt_id: int | None = None


class RetrievalLogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: SourceCategory
    source_id: int
    title: str
    snippet: str
    score: float | None
    visibility: Visibility
    was_used: bool
    precedence_rank: int


class RetrievalLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    language: str | None
    session_id: str | None
    structured_limit: int
    document_limit: int
    document_score_threshold: float
    had_usable_context: bool
    created_at: datetime
    items: list[RetrievalLogItemResponse] = Field(default_factory=list)


class UnansweredPromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    reason: UnansweredPromptReason
    language: str | None
    session_id: str | None
    retrieval_log_id: int | None
    created_at: datetime
