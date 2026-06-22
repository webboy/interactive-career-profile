import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import ToolCallStatus
from app.services.conversations import get_conversation, record_tool_call

TOOL_ROUTE_MAP: dict[str, tuple[str, str]] = {
    "request_meeting": ("POST", "/api/internal/mcp/meeting-requests"),
    "send_follow_up_question": ("POST", "/api/internal/mcp/follow-up-requests"),
    "submit_job_description": ("POST", "/api/internal/mcp/job-submissions"),
    "recommend_cv_profile": ("POST", "/api/internal/mcp/recommend-profile"),
    "get_skill_evidence": ("POST", "/api/internal/mcp/skill-evidence"),
    "get_project_case_study": ("POST", "/api/internal/mcp/project-case-study"),
}


class McpTransport(Protocol):
    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class McpToolCallResult:
    tool_name: str
    success: bool
    payload: dict[str, Any] | None
    error_message: str | None = None


class HttpMcpTransport:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.mcp_url.rstrip('/')}/tools/{tool_name}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=arguments)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("success", False):
                raise RuntimeError(payload.get("error", "MCP tool call failed"))
            return payload.get("result", {})


class InternalApiMcpTransport:
    """Direct internal API transport for tests and local fallbacks."""

    def __init__(self, settings: Settings | None = None, app=None) -> None:
        self.settings = settings or get_settings()
        self.app = app

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        route = TOOL_ROUTE_MAP.get(tool_name)
        if route is None:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        method, path = route
        headers = {"X-MCP-Internal-Token": self.settings.mcp_internal_api_token}
        if self.app is not None:
            transport = ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                response = await client.request(method, path, json=arguments, headers=headers)
                response.raise_for_status()
                return response.json()

        url = f"{self.settings.api_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, json=arguments, headers=headers)
            response.raise_for_status()
            return response.json()


class ApiMcpClient:
    def __init__(
        self,
        settings: Settings | None = None,
        transport: McpTransport | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.transport = transport or HttpMcpTransport(self.settings)

    async def call_tool(
        self,
        session: AsyncSession,
        *,
        conversation_id: int,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> McpToolCallResult:
        conversation = await get_conversation(session, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")

        request_summary = json.dumps({"tool": tool_name, "arguments": arguments})
        tool_call = await record_tool_call(
            session,
            conversation,
            tool_name=tool_name,
            status=ToolCallStatus.PENDING,
            request_payload=request_summary,
        )

        try:
            payload = await self.transport.invoke_tool(tool_name, arguments)
            response_summary = json.dumps(payload)
            tool_call.status = ToolCallStatus.SUCCESS
            tool_call.response_payload = response_summary
            await session.commit()
            await session.refresh(tool_call)
            return McpToolCallResult(
                tool_name=tool_name,
                success=True,
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            tool_call.status = ToolCallStatus.FAILED
            tool_call.error_message = str(exc)
            await session.commit()
            await session.refresh(tool_call)
            return McpToolCallResult(
                tool_name=tool_name,
                success=False,
                payload=None,
                error_message=str(exc),
            )


_default_client: ApiMcpClient | None = None


def get_mcp_client(settings: Settings | None = None) -> ApiMcpClient:
    global _default_client
    if _default_client is None:
        _default_client = ApiMcpClient(settings=settings)
    return _default_client


def set_mcp_client(client: ApiMcpClient | None) -> None:
    global _default_client
    _default_client = client
