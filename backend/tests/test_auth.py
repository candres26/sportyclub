from tests.conftest import auth_headers, tenant_headers


async def test_login_and_me(client, club_factory):
    club = await club_factory("auth-club")

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "password123"},
        headers=club["headers"],
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={**club["headers"], "Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == club["owner_email"]
    assert body["tenant"]["slug"] == "auth-club"
    assert "admin" in body["roles"]


async def test_login_wrong_password(client, club_factory):
    club = await club_factory("auth-club2")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "wrong-password"},
        headers=club["headers"],
    )
    assert resp.status_code == 401


async def test_refresh_rotation_and_reuse_detection(client, club_factory):
    club = await club_factory("auth-club3")
    old_refresh = club["refresh_token"]

    first = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
        headers=club["headers"],
    )
    assert first.status_code == 200, first.text
    assert first.json()["refresh_token"] != old_refresh

    reuse = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
        headers=club["headers"],
    )
    assert reuse.status_code == 401


async def test_logout_revokes_refresh(client, club_factory):
    club = await club_factory("auth-club4")
    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": club["refresh_token"]},
        headers=club["headers"],
    )
    assert logout.status_code == 204

    after = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": club["refresh_token"]},
        headers=club["headers"],
    )
    assert after.status_code == 401


async def test_password_reset_flow(client, club_factory, mailbox):
    club = await club_factory("auth-club5")

    forgot = await client.post(
        "/api/v1/auth/password/forgot",
        json={"email": club["owner_email"]},
        headers=club["headers"],
    )
    assert forgot.status_code == 202

    reset_message = next(
        m for m in mailbox if m["type"] == "reset" and m["to"] == club["owner_email"]
    )
    from urllib.parse import parse_qs, urlparse

    token = parse_qs(urlparse(reset_message["url"]).query)["token"][0]

    reset = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "password": "new-password123"},
        headers=club["headers"],
    )
    assert reset.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "password123"},
        headers=club["headers"],
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "new-password123"},
        headers=club["headers"],
    )
    assert new_login.status_code == 200


async def test_accept_invitation_invalid_token(client, club_factory):
    club = await club_factory("auth-club6")
    resp = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": "invalid", "full_name": "X", "password": "password123"},
        headers=club["headers"],
    )
    assert resp.status_code == 400


async def test_token_of_other_club_is_rejected(client, club_factory):
    club_a = await club_factory("auth-a")
    club_b = await club_factory("auth-b")

    resp = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers(club_a),  # token de A, subdominio de A... probemos en B
    )
    assert resp.status_code == 200

    # Token de A usado contra el subdominio de B
    auth = f"Bearer {club_a['access_token']}"
    cross = await client.get(
        "/api/v1/auth/me",
        headers={**tenant_headers(club_b["slug"]), "Authorization": auth},
    )
    assert cross.status_code == 401


async def test_tenant_resolved_from_forwarded_host(client, club_factory):
    club = await club_factory("fwd-a")

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": club["owner_email"], "password": "password123"},
        headers={"x-forwarded-host": "fwd-a.lvh.me"},
    )
    assert resp.status_code == 200, resp.text
