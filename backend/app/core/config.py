from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_ENVIRONMENTS = {"local", "test"}
DEFAULT_SECRET_KEY = "change-me-in-production"
DEFAULT_PLATFORM_ADMIN_PASSWORD = "change-me-please"
MIN_SECRET_KEY_LENGTH = 32


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
    # Activalo solo si la API no es accesible directamente desde internet.
    trust_forwarded_host: bool = False

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

    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    access_token_algorithm: str = "HS256"

    platform_admin_email: str = "admin@sportyclub.app"
    platform_admin_password: str = DEFAULT_PLATFORM_ADMIN_PASSWORD

    @property
    def is_dev(self) -> bool:
        return self.environment.lower() in DEV_ENVIRONMENTS

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        if self.is_dev:
            return self
        problems: list[str] = []
        if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
            problems.append(
                f"SECRET_KEY debe ser un secreto aleatorio de al menos {MIN_SECRET_KEY_LENGTH} "
                "caracteres"
            )
        if self.platform_admin_password == DEFAULT_PLATFORM_ADMIN_PASSWORD:
            problems.append("PLATFORM_ADMIN_PASSWORD no puede ser el valor por defecto")
        if self.postgres_password == "sportyclub":
            problems.append("POSTGRES_PASSWORD no puede ser el valor por defecto")
        if self.app_db_password == "app_user":
            problems.append("APP_DB_PASSWORD no puede ser el valor por defecto")
        if problems:
            raise ValueError(
                f"Configuracion insegura para ENVIRONMENT={self.environment}: "
                + "; ".join(problems)
            )
        return self

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
