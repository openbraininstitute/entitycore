from pydantic import PostgresDsn, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    ENVIRONMENT: str | None = None
    ROOT_PATH: str = ""

    DB_ENGINE: str = "postgresql"
    DB_USER: str = "test_db"
    DB_PASS: str = "test_db"
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "test_db"
    DB_URI: str = ""

    DB_POOL_SIZE: int = 30
    DB_POOL_PRE_PING: bool = True
    DB_MAX_OVERFLOW: int = 0

    @field_validator("DB_URI", mode="before")
    @classmethod
    def build_db_uri(cls, v: str, info: ValidationInfo) -> str:
        """Return the configured db uri, or build it from the parameters."""
        if v:
            dsn = PostgresDsn(v)
        else:
            dsn = PostgresDsn.build(
                scheme=info.data["DB_ENGINE"],
                username=info.data["DB_USER"],
                password=info.data["DB_PASS"],
                host=info.data["DB_HOST"],
                port=info.data["DB_PORT"],
                path=info.data["DB_NAME"],
            )
        return dsn.unicode_string()


settings = Settings()
