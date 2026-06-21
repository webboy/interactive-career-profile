import pytest
from httpx import AsyncClient

from app.core.security import hash_password, verify_password
from app.core.version import API_VERSION
from app.db.models.setting import Setting
from tests.conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD


@pytest.mark.asyncio
async def test_health_returns_ok_with_version(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "api"
    assert payload["version"] == API_VERSION
    assert payload["database"] == "connected"


def test_password_hashing_and_verification() -> None:
    password = "secure-password"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


@pytest.mark.asyncio
async def test_login_success_sets_cookie_and_me_works(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == TEST_ADMIN_EMAIL
    assert "icp_admin_session" in response.cookies

    me_response = await client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == TEST_ADMIN_EMAIL


@pytest.mark.asyncio
async def test_login_failure_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": "wrong-password"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_session(client: AsyncClient) -> None:
    login_response = await client.post(
        "/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    assert login_response.status_code == 200

    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    me_response = await client.get("/api/auth/me")
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_settings_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/admin/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_settings_redact_secret_values(auth_client: AsyncClient, db_session) -> None:
    db_session.add(
        Setting(
            key="openai_api_key",
            value="super-secret-key",
            is_secret=True,
        )
    )
    await db_session.commit()

    response = await auth_client.get("/api/admin/settings")
    assert response.status_code == 200

    payload = response.json()
    secret_setting = next(item for item in payload if item["key"] == "openai_api_key")
    assert secret_setting["value"] == "***REDACTED***"
    assert secret_setting["is_secret"] is True


@pytest.mark.asyncio
async def test_public_legal_pages_are_readable(client: AsyncClient) -> None:
    privacy_response = await client.get("/api/public/privacy")
    terms_response = await client.get("/api/public/terms")

    assert privacy_response.status_code == 200
    assert terms_response.status_code == 200
    assert privacy_response.json()["slug"] == "privacy"
    assert terms_response.json()["slug"] == "terms"


@pytest.mark.asyncio
async def test_admin_can_update_legal_page(auth_client: AsyncClient) -> None:
    response = await auth_client.put(
        "/api/admin/legal-pages/privacy",
        json={
            "title": "Updated Privacy Policy",
            "content": "Updated privacy content",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Updated Privacy Policy"
    assert payload["content"] == "Updated privacy content"

    public_response = await auth_client.get("/api/public/privacy")
    assert public_response.json()["content"] == "Updated privacy content"
