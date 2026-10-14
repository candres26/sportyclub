import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

TokenType = Literal["access", "refresh"]
TokenScope = Literal["tenant", "platform"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _encode(claims: dict[str, Any]) -> str:
    return jwt.encode(claims, settings.secret_key, algorithm=settings.access_token_algorithm)


def create_access_token(
    subject: str,
    scope: TokenScope,
    tenant_id: str | None = None,
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject,
        "scope": scope,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    if tenant_id is not None:
        claims["tenant_id"] = tenant_id
    return _encode(claims)


def create_refresh_token(
    subject: str,
    scope: TokenScope,
    tenant_id: str | None = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid.uuid4())
    claims: dict[str, Any] = {
        "sub": subject,
        "scope": scope,
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    if tenant_id is not None:
        claims["tenant_id"] = tenant_id
    return _encode(claims), jti, expires_at


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.access_token_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token invalido o expirado") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError("Tipo de token invalido")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
