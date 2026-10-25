from datetime import date

from tests.conftest import auth_headers
from tests.test_rbac import _invite_and_login


async def _create_person(client, club, **fields) -> dict:
    payload = {"first_name": "Ana", "last_name": "Perez", **fields}
    resp = await client.post("/api/v1/people", json=payload, headers=auth_headers(club))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _metrics_by_name(client, club) -> dict[str, dict]:
    resp = await client.get("/api/v1/metrics", headers=auth_headers(club))
    assert resp.status_code == 200, resp.text
    return {m["name"]: m for m in resp.json()}


# --------------------------------------------------------------------------- #
# Alta del club
# --------------------------------------------------------------------------- #
async def test_new_club_gets_discipline_and_default_metrics(client, platform_headers, mailbox):
    from tests.conftest import _token_from_mailbox, tenant_headers

    resp = await client.post(
        "/api/v1/platform/clubs",
        json={"name": "Boxeo Norte", "slug": "boxeo-norte", "owner_email": "d@x.com",
              "sport": "Boxeo"},
        headers=platform_headers,
    )
    assert resp.status_code == 201, resp.text
    token = await _token_from_mailbox(mailbox, "d@x.com")
    accept = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": token, "full_name": "Dueno", "password": "password123"},
        headers=tenant_headers("boxeo-norte"),
    )
    club = {"headers": tenant_headers("boxeo-norte"), "access_token": accept.json()["access_token"]}

    disciplines = await client.get("/api/v1/disciplines", headers=auth_headers(club))
    assert [d["name"] for d in disciplines.json()] == ["Boxeo"]
    assert set(await _metrics_by_name(client, club)) == {"Estatura", "Peso", "Alcance"}


# --------------------------------------------------------------------------- #
# Personas
# --------------------------------------------------------------------------- #
async def test_person_crud_and_search(client, club_factory):
    club = await club_factory("ppl-crud")
    person = await _create_person(
        client, club, document_type="TI", document_number="1001", birth_date="2012-03-10",
        email="ANA@Example.com", phone="",
    )
    assert person["email"] == "ana@example.com"
    assert person["phone"] is None
    assert person["age"] is not None and person["age"] >= 12

    await _create_person(client, club, first_name="Luis", last_name="Gomez")

    search = await client.get("/api/v1/people?q=ana per", headers=auth_headers(club))
    assert search.status_code == 200
    assert [p["id"] for p in search.json()["items"]] == [person["id"]]
    by_doc = await client.get("/api/v1/people?q=1001", headers=auth_headers(club))
    assert by_doc.json()["total"] == 1

    update = await client.patch(
        f"/api/v1/people/{person['id']}",
        json={"phone": "3001234567", "document_number": None},
        headers=auth_headers(club),
    )
    assert update.status_code == 200, update.text
    assert update.json()["phone"] == "3001234567"
    assert update.json()["document_number"] is None

    blank_name = await client.patch(
        f"/api/v1/people/{person['id']}", json={"first_name": None}, headers=auth_headers(club)
    )
    assert blank_name.status_code == 400

    delete = await client.delete(f"/api/v1/people/{person['id']}", headers=auth_headers(club))
    assert delete.status_code == 204
    gone = await client.get(f"/api/v1/people/{person['id']}", headers=auth_headers(club))
    assert gone.status_code == 404


async def test_document_unique_per_club(client, club_factory):
    club_a = await club_factory("ppl-doc-a")
    club_b = await club_factory("ppl-doc-b")
    await _create_person(client, club_a, document_number="555")

    dup = await client.post(
        "/api/v1/people",
        json={"first_name": "Otra", "last_name": "Persona", "document_number": "555"},
        headers=auth_headers(club_a),
    )
    assert dup.status_code == 409

    # El mismo documento puede existir en otro club.
    await _create_person(client, club_b, document_number="555")


async def test_people_are_isolated_between_clubs(client, club_factory):
    club_a = await club_factory("ppl-iso-a")
    club_b = await club_factory("ppl-iso-b")
    person_a = await _create_person(client, club_a)

    listing_b = await client.get("/api/v1/people", headers=auth_headers(club_b))
    assert listing_b.json()["total"] == 0
    direct = await client.get(f"/api/v1/people/{person_a['id']}", headers=auth_headers(club_b))
    assert direct.status_code == 404


# --------------------------------------------------------------------------- #
# Acudientes
# --------------------------------------------------------------------------- #
async def test_parent_with_two_children_who_also_trains(client, club_factory):
    club = await club_factory("ppl-family")
    parent = await _create_person(client, club, first_name="Carlos", last_name="Ruiz")
    kid1 = await _create_person(client, club, first_name="Sofia", last_name="Ruiz")
    kid2 = await _create_person(client, club, first_name="Mateo", last_name="Ruiz")

    for kid in (kid1, kid2):
        link = await client.post(
            f"/api/v1/people/{kid['id']}/guardians",
            json={"guardian_id": parent["id"], "relation": "padre"},
            headers=auth_headers(club),
        )
        assert link.status_code == 201, link.text

    dependents = await client.get(
        f"/api/v1/people/{parent['id']}/dependents", headers=auth_headers(club)
    )
    assert {d["person"]["first_name"] for d in dependents.json()} == {"Sofia", "Mateo"}

    guardians = await client.get(
        f"/api/v1/people/{kid1['id']}/guardians", headers=auth_headers(club)
    )
    assert [(g["relation"], g["person"]["id"]) for g in guardians.json()] == [
        ("padre", parent["id"])
    ]

    # El padre tambien es deportista: tiene su propia ficha tecnica.
    metrics = await _metrics_by_name(client, club)
    own = await client.post(
        f"/api/v1/people/{parent['id']}/measurements",
        json={"metric_id": metrics["Peso"]["id"], "value": "82.5", "measured_at": "2026-10-01"},
        headers=auth_headers(club),
    )
    assert own.status_code == 201, own.text

    duplicate = await client.post(
        f"/api/v1/people/{kid1['id']}/guardians",
        json={"guardian_id": parent["id"], "relation": "padre"},
        headers=auth_headers(club),
    )
    assert duplicate.status_code == 409

    unlink = await client.delete(
        f"/api/v1/people/{kid1['id']}/guardians/{parent['id']}", headers=auth_headers(club)
    )
    assert unlink.status_code == 204


async def test_person_cannot_be_own_guardian(client, club_factory):
    club = await club_factory("ppl-self")
    person = await _create_person(client, club)
    resp = await client.post(
        f"/api/v1/people/{person['id']}/guardians",
        json={"guardian_id": person["id"], "relation": "padre"},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


async def test_guardian_from_other_club_is_rejected(client, club_factory):
    club_a = await club_factory("ppl-gx-a")
    club_b = await club_factory("ppl-gx-b")
    kid_a = await _create_person(client, club_a)
    parent_b = await _create_person(client, club_b)
    resp = await client.post(
        f"/api/v1/people/{kid_a['id']}/guardians",
        json={"guardian_id": parent_b["id"], "relation": "madre"},
        headers=auth_headers(club_a),
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Ficha tecnica
# --------------------------------------------------------------------------- #
async def test_profile_and_measurement_history(client, club_factory):
    club = await club_factory("ppl-sheet")
    athlete = await _create_person(client, club)

    empty = await client.get(f"/api/v1/people/{athlete['id']}/profile", headers=auth_headers(club))
    assert empty.status_code == 200
    assert empty.json()["blood_type"] is None

    saved = await client.put(
        f"/api/v1/people/{athlete['id']}/profile",
        json={"blood_type": "O+", "dominant_side": "zurdo", "allergies": ""},
        headers=auth_headers(club),
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["blood_type"] == "O+"
    assert saved.json()["allergies"] is None

    metrics = await _metrics_by_name(client, club)
    for value, day in (("140", "2026-01-15"), ("146.5", "2026-07-15"), ("143", "2026-04-15")):
        resp = await client.post(
            f"/api/v1/people/{athlete['id']}/measurements",
            json={"metric_id": metrics["Estatura"]["id"], "value": value, "measured_at": day},
            headers=auth_headers(club),
        )
        assert resp.status_code == 201, resp.text

    history = await client.get(
        f"/api/v1/people/{athlete['id']}/measurements?metric_id={metrics['Estatura']['id']}",
        headers=auth_headers(club),
    )
    assert [m["measured_at"] for m in history.json()] == [
        "2026-07-15",
        "2026-04-15",
        "2026-01-15",
    ]
    assert history.json()[0]["unit"] == "cm"
    assert history.json()[0]["value"] == "146.50"

    negative = await client.post(
        f"/api/v1/people/{athlete['id']}/measurements",
        json={"metric_id": metrics["Peso"]["id"], "value": "-1", "measured_at": "2026-01-01"},
        headers=auth_headers(club),
    )
    assert negative.status_code == 422


async def test_inactive_metric_rejects_new_measurements(client, club_factory):
    club = await club_factory("ppl-inactive")
    athlete = await _create_person(client, club)
    metrics = await _metrics_by_name(client, club)
    deactivate = await client.patch(
        f"/api/v1/metrics/{metrics['Alcance']['id']}",
        json={"is_active": False},
        headers=auth_headers(club),
    )
    assert deactivate.status_code == 200
    resp = await client.post(
        f"/api/v1/people/{athlete['id']}/measurements",
        json={"metric_id": metrics["Alcance"]["id"], "value": "170",
              "measured_at": date.today().isoformat()},
        headers=auth_headers(club),
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Permisos por rol
# --------------------------------------------------------------------------- #
async def test_coach_can_read_and_measure_but_not_create(client, club_factory, mailbox):
    club = await club_factory("ppl-coach")
    athlete = await _create_person(client, club)
    coach = await _invite_and_login(client, club, mailbox, "coach@example.com", "coach")

    listing = await client.get("/api/v1/people", headers=auth_headers(coach))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    metrics = await _metrics_by_name(client, coach)
    measure = await client.post(
        f"/api/v1/people/{athlete['id']}/measurements",
        json={"metric_id": metrics["Peso"]["id"], "value": "40", "measured_at": "2026-10-01"},
        headers=auth_headers(coach),
    )
    assert measure.status_code == 201

    create = await client.post(
        "/api/v1/people",
        json={"first_name": "No", "last_name": "Permitido"},
        headers=auth_headers(coach),
    )
    assert create.status_code == 403

    new_metric = await client.post(
        "/api/v1/metrics", json={"name": "Envergadura", "unit": "cm"}, headers=auth_headers(coach)
    )
    assert new_metric.status_code == 403


async def test_member_cannot_see_people(client, club_factory, mailbox):
    club = await club_factory("ppl-member")
    member = await _invite_and_login(client, club, mailbox, "socio@example.com", "member")
    resp = await client.get("/api/v1/people", headers=auth_headers(member))
    assert resp.status_code == 403
