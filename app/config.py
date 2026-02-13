from typing import Literal
from urllib.parse import quote

from pydantic import PostgresDsn, SecretStr, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.types import StorageType


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=True,
    )

    APP_NAME: str = "entitycore"
    APP_VERSION: str | None = None
    APP_DEBUG: bool = False
    APP_DISABLE_AUTH: bool = False

    COMMIT_SHA: str | None = None

    ENVIRONMENT: str | None = None
    ROOT_PATH: str = ""
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ORIGIN_REGEX: str | None = None

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    LOG_SERIALIZE: bool = True
    LOG_BACKTRACE: bool = False
    LOG_DIAGNOSE: bool = False
    LOG_ENQUEUE: bool = False
    LOG_CATCH: bool = True
    LOG_STANDARD_LOGGER: dict[str, str] = {"root": "INFO"}

    KEYCLOAK_URL: str = "https://staging.cell-a.openbraininstitute.org/auth/realms/SBO"
    AUTH_CACHE_MAXSIZE: int = 128  # items
    AUTH_CACHE_MAX_TTL: int = 300  # seconds
    AUTH_CACHE_INFO: bool = False

    S3_PRESIGNED_URL_NETLOC: str | None = None  # to override the presigned url hostname and port
    S3_MULTIPART_THRESHOLD: int = 5 * 1024**2  # bytes  # TODO: decide an appropriate value
    S3_PRESIGNED_URL_EXPIRATION: int = 600  # seconds  # TODO: decide an appropriate value

    API_ASSET_POST_MAX_SIZE: int = 150 * 1024**2  # bytes  # TODO: decide an appropriate value

    DB_ENGINE: str = "postgresql+psycopg2"
    DB_USER: str = "entitycore"
    DB_PASS: str = "entitycore"  # noqa: S105
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "entitycore"
    DB_URI: str = ""

    DB_POOL_SIZE: int = 30
    DB_POOL_PRE_PING: bool = False
    DB_MAX_OVERFLOW: int = 0

    OPENAI_API_KEY: SecretStr | None = None

    @field_validator("DB_URI", mode="before")
    @classmethod
    def build_db_uri(cls, v: str, info: ValidationInfo) -> str:
        """Return the configured db uri, or build it from the parameters."""
        if v:
            dsn = PostgresDsn(v)
        else:
            dsn = PostgresDsn.build(
                scheme=info.data["DB_ENGINE"],
                username=quote(info.data["DB_USER"]),
                password=quote(info.data["DB_PASS"]),
                host=info.data["DB_HOST"],
                port=info.data["DB_PORT"],
                path=info.data["DB_NAME"],
            )
        return dsn.unicode_string()


class AWSS3InternalConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="aws_s3_internal_",
    )
    type: Literal[StorageType.aws_s3_internal] = StorageType.aws_s3_internal
    bucket: str = "entitycore-data-dev"
    region: str = "us-east-1"
    is_open: bool = False


class AWSS3OpenConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="aws_s3_open_",
    )
    type: Literal[StorageType.aws_s3_open] = StorageType.aws_s3_open
    bucket: str = "openbluebrain"
    region: str = "us-west-2"
    is_open: bool = True


StorageUnion = AWSS3InternalConfig | AWSS3OpenConfig


settings = Settings()
storages: dict[StorageType, StorageUnion] = {
    StorageType.aws_s3_internal: AWSS3InternalConfig(),
    StorageType.aws_s3_open: AWSS3OpenConfig(),
}
