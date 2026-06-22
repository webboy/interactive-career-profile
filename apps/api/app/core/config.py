from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="Interactive Career Profile", alias="APP_NAME")
    app_url: str = Field(default="http://localhost:9000", alias="APP_URL")
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    mcp_url: str = Field(default="http://mcp:8100", alias="MCP_URL")
    mcp_internal_api_token: str = Field(
        default="change-me-mcp-internal-token",
        alias="MCP_INTERNAL_API_TOKEN",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://redis:6379/0", alias="CELERY_BROKER_URL")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    admin_notification_email: str = Field(
        default="admin@example.com",
        alias="ADMIN_NOTIFICATION_EMAIL",
    )
    smtp_timeout_seconds: int = Field(default=10, alias="SMTP_TIMEOUT_SECONDS")
    database_url: str = Field(
        default="postgresql+psycopg://icp:icp@postgres:5432/icp",
        alias="DATABASE_URL",
    )
    session_secret: str = Field(default="change-me-session-secret", alias="SESSION_SECRET")
    jwt_secret: str = Field(default="change-me-jwt-secret", alias="JWT_SECRET")
    auth_cookie_name: str = Field(default="icp_admin_session", alias="AUTH_COOKIE_NAME")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="AUTH_COOKIE_SAMESITE")
    auth_token_expires_minutes: int = Field(default=60 * 24 * 7, alias="AUTH_TOKEN_EXPIRES_MINUTES")
    default_language: str = Field(default="en", alias="DEFAULT_LANGUAGE")
    supported_languages: str = Field(default="en,de,sr", alias="SUPPORTED_LANGUAGES")

    llm_provider: str | None = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    agent_max_tokens: int = Field(default=1024, alias="AGENT_MAX_TOKENS")
    agent_temperature: float = Field(default=0.2, alias="AGENT_TEMPERATURE")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    aws_region: str | None = Field(default=None, alias="AWS_REGION")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")

    embedding_provider: str | None = Field(default="openai", alias="EMBEDDING_PROVIDER")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    embedding_dimensions: int = Field(default=1536, alias="EMBEDDING_DIMENSIONS")
    retrieval_structured_limit: int = Field(default=10, alias="RETRIEVAL_STRUCTURED_LIMIT")
    retrieval_document_limit: int = Field(default=5, alias="RETRIEVAL_DOCUMENT_LIMIT")
    retrieval_document_score_threshold: float = Field(
        default=0.7,
        alias="RETRIEVAL_DOCUMENT_SCORE_THRESHOLD",
    )

    filesystem_driver: str = Field(default="local", alias="FILESYSTEM_DRIVER")
    local_storage_path: str = Field(default="./storage/uploads", alias="LOCAL_STORAGE_PATH")
    document_upload_max_bytes: int = Field(default=10 * 1024 * 1024, alias="DOCUMENT_UPLOAD_MAX_BYTES")
    document_chunk_size_chars: int = Field(default=1200, alias="DOCUMENT_CHUNK_SIZE_CHARS")
    document_chunk_overlap_chars: int = Field(default=200, alias="DOCUMENT_CHUNK_OVERLAP_CHARS")
    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_region: str | None = Field(default=None, alias="S3_REGION")
    s3_public_url: str | None = Field(default=None, alias="S3_PUBLIC_URL")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str | None = Field(default=None, alias="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(
        default="Interactive Career Profile",
        alias="SMTP_FROM_NAME",
    )
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    enable_demo_seed: bool = Field(default=False, alias="ENABLE_DEMO_SEED")

    port: int = Field(default=8000, alias="PORT")

    @property
    def supported_language_list(self) -> list[str]:
        return [language.strip() for language in self.supported_languages.split(",") if language.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
