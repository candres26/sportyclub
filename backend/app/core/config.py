from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "local"
    debug: bool = False
    base_domain: str = "lvh.me"
    cors_origins: str = "http://localhost:3000"

    # Confia en la cabecera X-Forwarded-Host para resolver el tenant cuando la
    # API se consume a traves de un proxy (p. ej. el BFF del panel o Caddy).
    trust_forwarded_host: bool = True

    panel_scheme: str = "https"
    panel_port: int | None = None
    invite_accept_path: str = "/accept-invitation"
    password_reset_path: str = "/reset-password"

    postgres_user: str = "sportyclub"
    postgres_password: str = "sportyclub"
    postgres_db: str = "sportyclub"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    app_db_user: str = "app_user"
    app_db_password: str = "app_user"

    # Desactiva el pool de conexiones (util en tests para evitar problemas de
    # conexiones atadas a un event loop concreto).
    db_use_null_pool: bool = False

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    access_token_algorithm: str = "HS256"

    platform_admin_email: str = "admin@sportyclub.app"
    platform_admin_password: str = "change-me-please"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def _database_url(self, user: str, password: str) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def owner_database_url(self) -> str:
        return self._database_url(self.postgres_user, self.postgres_password)

    @property
    def app_database_url(self) -> str:
        return self._database_url(self.app_db_user, self.app_db_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
