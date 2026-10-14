from tests.conftest import auth_headers


async def test_platform_login(client):
    from app.core.config import settings

    resp = await client.post(
        "/api/v1/platform/auth/login",
        json={
            "email": settings.platform_admin_email,
            "password": settings.platform_admin_password,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_platform_login_wrong_password(client):
    from app.core.config import settings

    resp = await client.post(
        "/api/v1/platform/auth/login",
        json={"email": settings.platform_admin_email, "password": "nope"},
    )
    assert resp.status_code == 401


async def test_create_club_and_list(client, platform_headers):
    create = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Club Norte", "slug": "club-norte"},
        headers=platform_headers,
    )
    assert create.status_code == 201, create.text
    assert create.json()["slug"] == "club-norte"

    listing = await client.get("/api/v1/platform/clubs", headers=platform_headers)
    assert listing.status_code == 200
    slugs = {tenant["slug"] for tenant in listing.json()}
    assert "club-norte" in slugs


async def test_duplicate_slug_conflict(client, platform_headers):
    payload = {"name": "Club Duplicado", "slug": "club-dup"}
    first = await client.post("/api/v1/platform/clubs", json=payload, headers=platform_headers)
    assert first.status_code == 201

    second = await client.post("/api/v1/platform/clubs", json=payload, headers=platform_headers)
    assert second.status_code == 409


async def test_invalid_slug_rejected(client, platform_headers):
    resp = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Malo", "slug": "www"},
        headers=platform_headers,
    )
    assert resp.status_code == 422


async def test_club_token_cannot_access_platform(client, club_factory):
    club = await club_factory("plat-a")
    resp = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Hack", "slug": "hack"},
        headers=auth_headers(club),
    )
    assert resp.status_code == 401
