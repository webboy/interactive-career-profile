from pydantic import BaseModel, Field

from app.core.enums import ChatJobStatus


class PublicChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(min_length=1, max_length=255)
    conversation_id: int | None = None
    language: str | None = Field(default=None, max_length=32)


class PublicSourceSummary(BaseModel):
    source_type: str
    title: str


class PublicChatResponse(BaseModel):
    conversation_id: int
    session_id: str
    assistant_message: str
    language: str
    refused: bool
    grounded: bool
    sources: list[PublicSourceSummary] = Field(default_factory=list)


class PublicChatJobCreateResponse(BaseModel):
    job_id: str
    conversation_id: int
    session_id: str
    status: ChatJobStatus


class PublicChatJobStatusResponse(BaseModel):
    job_id: str
    conversation_id: int
    session_id: str
    status: ChatJobStatus
    response: PublicChatResponse | None = None
    error_message: str | None = None


class PublicSettingsResponse(BaseModel):
    app_name: str
    app_url: str
    default_language: str
    supported_languages: list[str]
