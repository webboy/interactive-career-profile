"""Internal FastMCP server with HTTP tool bridge for API integration."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP

API_URL = os.environ.get("API_URL", "http://api:8000").rstrip("/")
MCP_INTERNAL_API_TOKEN = os.environ.get(
    "MCP_INTERNAL_API_TOKEN",
    "change-me-mcp-internal-token",
)
PORT = int(os.environ.get("PORT", "8100"))

mcp = FastMCP("icp-internal")


async def _call_api(method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"X-MCP-Internal-Token": MCP_INTERNAL_API_TOKEN}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            f"{API_URL}{path}",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool
async def request_meeting(
    requester_name: str,
    requester_email: str,
    organization: str = "",
    message: str = "",
    preferred_times: str = "",
) -> dict[str, Any]:
    payload = {
        "requester_name": requester_name,
        "requester_email": requester_email,
        "organization": organization or None,
        "message": message or None,
        "preferred_times": preferred_times or None,
    }
    return await _call_api("POST", "/api/internal/mcp/meeting-requests", payload)


@mcp.tool
async def send_follow_up_question(requester_email: str, question: str) -> dict[str, Any]:
    return await _call_api(
        "POST",
        "/api/internal/mcp/follow-up-requests",
        {"requester_email": requester_email, "question": question},
    )


@mcp.tool
async def submit_job_description(
    requester_email: str,
    job_description: str,
    company: str = "",
    role_title: str = "",
) -> dict[str, Any]:
    payload = {
        "requester_email": requester_email,
        "job_description": job_description,
        "company": company or None,
        "role_title": role_title or None,
    }
    return await _call_api("POST", "/api/internal/mcp/job-submissions", payload)


@mcp.tool
async def recommend_cv_profile(query: str, intent_hints: list[str] | None = None) -> dict[str, Any]:
    return await _call_api(
        "POST",
        "/api/internal/mcp/recommend-profile",
        {"query": query, "intent_hints": intent_hints or []},
    )


@mcp.tool
async def get_skill_evidence(query: str, intent_hints: list[str] | None = None) -> dict[str, Any]:
    return await _call_api(
        "POST",
        "/api/internal/mcp/skill-evidence",
        {"query": query, "intent_hints": intent_hints or []},
    )


@mcp.tool
async def get_project_case_study(query: str, intent_hints: list[str] | None = None) -> dict[str, Any]:
    return await _call_api(
        "POST",
        "/api/internal/mcp/project-case-study",
        {"query": query, "intent_hints": intent_hints or []},
    )


TOOL_ROUTES: dict[str, tuple[str, str]] = {
    "request_meeting": ("POST", "/api/internal/mcp/meeting-requests"),
    "send_follow_up_question": ("POST", "/api/internal/mcp/follow-up-requests"),
    "submit_job_description": ("POST", "/api/internal/mcp/job-submissions"),
    "recommend_cv_profile": ("POST", "/api/internal/mcp/recommend-profile"),
    "get_skill_evidence": ("POST", "/api/internal/mcp/skill-evidence"),
    "get_project_case_study": ("POST", "/api/internal/mcp/project-case-study"),
}


def create_app() -> FastAPI:
    app = FastAPI(title="ICP Internal MCP")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "mcp"}

    @app.post("/tools/{tool_name}")
    async def invoke_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        route = TOOL_ROUTES.get(tool_name)
        if route is None:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

        method, path = route
        try:
            result = await _call_api(method, path, arguments)
            return {"success": True, "result": result}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    app.mount("/mcp", mcp.http_app())
    return app


def main() -> None:
    app = create_app()
    print(f"ICP internal MCP listening on {PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
