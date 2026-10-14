from urllib.parse import parse_qs, urlparse

from tests.conftest import auth_headers, tenant_headers


async def _invite_and_login(client, club, mailbox, email: str, role_name: str) -> dict:
    roles = await client.get("/api/v1/roles", headers=auth_headers(club))
    role = next(r for r in roles.json() if r["name"] == role_name)

    invite = await client.post(
        "/api/v1/invitations",
        json={"email": email, "role_id": role["id"]},
        headers=auth_headers(club),
    )
    assert invite.status_code == 201, invite.text

    message = next(m for m in mailbox if m["to"] == email)
    token = parse_qs(urlparse(message["url"]).query)["token"][0]

    accept = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": token, "full_name": "Invited", "password": "password123"},
        headers=club["headers"],
    )
    assert accept.status_code == 200, accept.text
    return {
        **club,
        "email": email,
        "access_token": accept.json()["access_token"],
    }


async def test_admin_can_create_role(client, club_factory):
    club = await club_factory("rbac-a")
    resp = await client.post(
        "/api/v1/roles",
        json={"name": "entrenador", "description": "Entrenador", "permissions": ["users:read"]},
        headers=auth_headers(club),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["permissions"] == ["users:read"]


async def test_unknown_permission_is_rejected(client, club_factory):
    club = await club_factory("rbac-b")
    resp = await client.post(
        "/api/v1/roles",
        json={"name": "raro", "permissions": ["no:existe"]},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


async def test_member_cannot_list_users(client, club_factory, mailbox):
    club = await club_factory("rbac-c")
    member = await _invite_and_login(client, club, mailbox, "member@example.com", "member")

    forbidden = await client.get("/api/v1/users", headers=auth_headers(member))
    assert forbidden.status_code == 403

    allowed = await client.get("/api/v1/auth/me", headers=auth_headers(member))
    assert allowed.status_code == 200
    assert allowed.json()["roles"] == ["member"]


async def test_unauthenticated_requests_are_rejected(client, club_factory):
    await club_factory("rbac-d")
    resp = await client.get("/api/v1/users", headers=tenant_headers("rbac-d"))
    assert resp.status_code == 401


async def test_invitation_and_audit_log(client, club_factory, mailbox):
    club = await club_factory("rbac-e")
    await _invite_and_login(client, club, mailbox, "someone@example.com", "staff")

    logs = await client.get("/api/v1/audit-logs", headers=auth_headers(club))
    assert logs.status_code == 200, logs.text
    actions = {entry["action"] for entry in logs.json()["items"]}
    assert "invitation.create" in actions
