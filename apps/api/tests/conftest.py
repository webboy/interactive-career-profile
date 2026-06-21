import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.core.version import API_VERSION, API_VERSION_KEY
from app.db.base import Base
from app.db.models.legal_page import LegalPage
from app.db.models.setting import Setting
from app.db.models.system_metadata import SystemMetadata
from app.db.models.user import User
from app.db.session import get_db_session
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "test-password-123"


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            SystemMetadata.__table__.insert().values(
                key=API_VERSION_KEY,
                value=API_VERSION,
            )
        )
        await connection.execute(
            LegalPage.__table__.insert(),
            [
                {
                    "slug": "privacy",
                    "title": "Privacy Policy",
                    "content": "Privacy placeholder",
                },
                {
                    "slug": "terms",
                    "title": "Terms of Use",
                    "content": "Terms placeholder",
                },
            ],
        )
        await connection.execute(
            User.__table__.insert().values(
                email=TEST_ADMIN_EMAIL,
                password_hash=hash_password(TEST_ADMIN_PASSWORD),
                is_active=True,
            )
        )

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine) -> AsyncClient:
    app = create_app()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    response = await client.post(
        "/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return client
