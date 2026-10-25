import os

# --- Configuracion de entorno para tests (antes de importar la app) -------- #
# Host, puerto y credenciales de la BD salen del .env (o de los valores por
# defecto de Settings), igual que en desarrollo. El nombre de la BD se fuerza
# siempre: los tests vacian tablas y nunca deben tocar la BD de desarrollo.
os.environ["POSTGRES_DB"] = "sportyclub_test"
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789abcdef")
os.environ.setdefault("BASE_DOMAIN", "lvh.me")
os.environ.setdefault("PANEL_SCHEME", "http")
os.environ.setdefault("PANEL_PORT", "3000")
os.environ.setdefault("DB_USE_NULL_POOL", "true")
os.environ.setdefault("TRUST_FORWARDED_HOST", "true")
os.environ.setdefault("PLATFORM_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("PLATFORM_ADMIN_PASSWORD", "adminpass123")

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from alembic.config import Config as AlembicConfig
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from app.core.config import settings
from app.core.rate_limit import login_failures, password_reset_requests
from app.main import app

BASE_DIR = Path(__file__).resolve().parent.parent

_owner_engine = create_async_engine(settings.owner_database_url, poolclass=NullPool)
_owner_session_factory = async_sessionmaker(_owner_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    cfg = AlembicConfig(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    try:
        command.upgrade(cfg, "head")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"No se pudo preparar la base de datos de tests: {exc}")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _seed(_apply_migrations) -> None:
    from app.bootstrap import bootstrap

    await bootstrap()


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(_seed) -> None:
    async with _owner_session_factory() as session, session.begin():
        await session.execute(
            text("TRUNCATE tenants, platform_refresh_tokens CASCADE")
        )
        await session.execute(
            text("DELETE FROM platform_admins WHERE email <> :email"),
            {"email": settings.platform_admin_email.lower().strip()},
        )
    login_failures.clear()
    password_reset_requests.clear()
    yield


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def mailbox(monkeypatch) -> list[dict]:
    sent: list[dict] = []

    def _invite(to: str, club_name: str, invite_url: str) -> None:
        sent.append({"type": "invitation", "to": to, "club_name": club_name, "url": invite_url})

    def _reset(to: str, reset_url: str) -> None:
        sent.append({"type": "reset", "to": to, "url": reset_url})

    import app.modules.auth.router as auth_router
    import app.modules.clubs.router as clubs_router
    import app.modules.invitations.router as invitations_router

    monkeypatch.setattr(clubs_router, "send_invitation_email", _invite)
    monkeypatch.setattr(invitations_router, "send_invitation_email", _invite)
    monkeypatch.setattr(auth_router, "send_password_reset_email", _reset)
    return sent


@pytest_asyncio.fixture
async def platform_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/platform/auth/login",
        json={
            "email": settings.platform_admin_email,
            "password": settings.platform_admin_password,
        },
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def tenant_headers(slug: str) -> dict[str, str]:
    return {"host": f"{slug}.{settings.base_domain}"}


def auth_headers(club: dict, token: str | None = None) -> dict[str, str]:
    token = token or club["access_token"]
    return {**club["headers"], "Authorization": f"Bearer {token}"}


async def _token_from_mailbox(mailbox: list[dict], email: str) -> str:
    for message in mailbox:
        if message["to"] == email:
            query = parse_qs(urlparse(message["url"]).query)
            return query["token"][0]
    raise AssertionError(f"No se encontro correo para {email}")


@pytest_asyncio.fixture
async def club_factory(client: AsyncClient, platform_headers, mailbox):
    async def _create(slug: str, name: str = "Club", owner_email: str | None = None):
        owner_email = owner_email or f"owner-{slug}@example.com"
        resp = await client.post(
            "/api/v1/platform/clubs",
            json={"name": name, "slug": slug, "owner_email": owner_email},
            headers=platform_headers,
        )
        assert resp.status_code == 201, resp.text
        tenant = resp.json()
        token = await _token_from_mailbox(mailbox, owner_email)
        headers = tenant_headers(slug)
        accept = await client.post(
            "/api/v1/auth/accept-invitation",
            json={"token": token, "full_name": "Owner", "password": "password123"},
            headers=headers,
        )
        assert accept.status_code == 200, accept.text
        return {
            "slug": slug,
            "tenant": tenant,
            "owner_email": owner_email,
            "headers": headers,
            "access_token": accept.json()["access_token"],
            "refresh_token": accept.json()["refresh_token"],
        }

    return _create
