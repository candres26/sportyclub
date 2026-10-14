from tests.conftest import auth_headers


async def test_users_are_isolated_between_clubs(client, club_factory):
    club_a = await club_factory("iso-a")
    club_b = await club_factory("iso-b")

    resp_a = await client.get("/api/v1/users", headers=auth_headers(club_a))
    assert resp_a.status_code == 200, resp_a.text
    emails_a = {user["email"] for user in resp_a.json()}
    assert club_a["owner_email"] in emails_a
    assert club_b["owner_email"] not in emails_a

    resp_b = await client.get("/api/v1/users", headers=auth_headers(club_b))
    emails_b = {user["email"] for user in resp_b.json()}
    assert club_b["owner_email"] in emails_b
    assert club_a["owner_email"] not in emails_b


async def test_user_of_other_club_is_not_visible(client, club_factory):
    club_a = await club_factory("iso-c")
    club_b = await club_factory("iso-d")

    me_a = await client.get("/api/v1/auth/me", headers=auth_headers(club_a))
    user_a_id = me_a.json()["id"]

    # El usuario de A no existe en el contexto de B
    resp = await client.get(f"/api/v1/users/{user_a_id}", headers=auth_headers(club_b))
    assert resp.status_code == 404


async def test_roles_are_isolated_between_clubs(client, club_factory):
    club_a = await club_factory("iso-e")
    club_b = await club_factory("iso-f")

    roles_a = await client.get("/api/v1/roles", headers=auth_headers(club_a))
    roles_b = await client.get("/api/v1/roles", headers=auth_headers(club_b))

    ids_a = {role["id"] for role in roles_a.json()}
    ids_b = {role["id"] for role in roles_b.json()}
    assert ids_a.isdisjoint(ids_b)
    assert {"admin", "staff", "member"} == {r["name"] for r in roles_a.json()}
