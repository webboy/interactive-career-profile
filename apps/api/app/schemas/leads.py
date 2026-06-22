from pydantic import BaseModel


class ToolCallResponse(BaseModel):
    id: int
    conversation_id: int
    tool_name: str
    status: str
    request_payload: str | None = None
    response_payload: str | None = None
    error_message: str | None = None


class ToolCallsListResponse(BaseModel):
    tool_calls: list[ToolCallResponse]
