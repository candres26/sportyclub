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


async def test_create_club_returns_invite_url(client, platform_headers):
    resp = await client.post(
        "/api/v1/platform/clubs",
        json={
            "name": "Club Invita",
            "slug": "club-invita",
            "owner_email": "dueno@example.com",
        },
        headers=platform_headers,
    )
    assert resp.status_code == 201, resp.text
    invite_url = resp.json()["invite_url"]
    assert invite_url is not None
    assert "club-invita" in invite_url
    assert "token=" in invite_url


async def test_create_club_without_owner_has_no_invite_url(client, platform_headers):
    resp = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Sin Dueno", "slug": "sin-dueno"},
        headers=platform_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["invite_url"] is None


async def test_platform_admins_lifecycle(client, platform_headers):
    create = await client.post(
        "/api/v1/platform/admins",
        json={
            "email": "ops@example.com",
            "full_name": "Ops Admin",
            "password": "supersecret123",
        },
        headers=platform_headers,
    )
    assert create.status_code == 201, create.text
    admin_id = create.json()["id"]
    assert create.json()["email"] == "ops@example.com"

    listing = await client.get("/api/v1/platform/admins", headers=platform_headers)
    assert listing.status_code == 200
    emails = {admin["email"] for admin in listing.json()}
    assert "ops@example.com" in emails

    deactivate = await client.patch(
        f"/api/v1/platform/admins/{admin_id}",
        json={"is_active": False},
        headers=platform_headers,
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False


async def test_duplicate_platform_admin_conflict(client, platform_headers):
    payload = {
        "email": "dup@example.com",
        "full_name": "Dup",
        "password": "supersecret123",
    }
    first = await client.post(
        "/api/v1/platform/admins", json=payload, headers=platform_headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/platform/admins", json=payload, headers=platform_headers
    )
    assert second.status_code == 409


async def test_cannot_deactivate_last_active_admin(client, platform_headers):
    from app.core.config import settings

    listing = await client.get("/api/v1/platform/admins", headers=platform_headers)
    bootstrap = next(
        admin
        for admin in listing.json()
        if admin["email"] == settings.platform_admin_email.lower().strip()
    )
    resp = await client.patch(
        f"/api/v1/platform/admins/{bootstrap['id']}",
        json={"is_active": False},
        headers=platform_headers,
    )
    assert resp.status_code == 400
