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
    database_url: str = Field(
        default="postgresql+psycopg://icp:icp@postgres:5432/icp",
        alias="DATABASE_URL",
    )
    session_secret: str = Field(default="change-me-session-secret", alias="SESSION_SECRET")
    jwt_secret: str = Field(default="change-me-jwt-secret", alias="JWT_SECRET")
    default_language: str = Field(default="en", alias="DEFAULT_LANGUAGE")
    supported_languages: str = Field(default="en,de,sr", alias="SUPPORTED_LANGUAGES")

    llm_provider: str | None = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str | None = Field(default=None, alias="OPENAI_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    aws_region: str | None = Field(default=None, alias="AWS_REGION")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")

    embedding_provider: str | None = Field(default="openai", alias="EMBEDDING_PROVIDER")
    openai_embedding_model: str | None = Field(default=None, alias="OPENAI_EMBEDDING_MODEL")

    filesystem_driver: str = Field(default="local", alias="FILESYSTEM_DRIVER")
    local_storage_path: str = Field(default="./storage/uploads", alias="LOCAL_STORAGE_PATH")
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
