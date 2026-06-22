import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_allows_ui_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/api/public/settings",
        headers={
            "Origin": "http://localhost:9000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:9000"
    assert response.headers.get("access-control-allow-credentials") == "true"
