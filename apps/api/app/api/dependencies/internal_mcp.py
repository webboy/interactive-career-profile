from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


async def require_mcp_internal_token(
    x_mcp_internal_token: str = Header(..., alias="X-MCP-Internal-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    if x_mcp_internal_token != settings.mcp_internal_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")
