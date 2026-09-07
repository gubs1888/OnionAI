"""Batch creation / listing / retrieval + auth login."""

import pytest


def test_login_demo_user(client):
    res = client.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "demo"


def test_login_rejects_bad_password(client):
    res = client.post("/api/auth/login", json={"username": "demo", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_batch_creation(client):
    res = client.post(
        "/api/batches",
        json={"name": "Lot A — Nashik farm", "variety": "Nashik Red", "source": "Lasalgaon"},
    )
    assert res.status_code == 201
    batch = res.json()
    assert batch["batch_code"].startswith("ON-")
    assert batch["status"] == "created"
    assert batch["name"] == "Lot A — Nashik farm"


def test_batch_codes_increment(client):
    a = client.post("/api/batches", json={"name": "B1"}).json()
    b = client.post("/api/batches", json={"name": "B2"}).json()
    assert int(a["batch_code"].split("-")[1]) < int(b["batch_code"].split("-")[1])


def test_batch_list_and_get(client):
    created = client.post("/api/batches", json={"name": "Listed batch"}).json()
    listed = client.get("/api/batches").json()
    assert any(b["batch_code"] == created["batch_code"] for b in listed)

    got = client.get(f"/api/batches/{created['batch_code']}")
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]


def test_batch_get_404_envelope(client):
    res = client.get("/api/batches/DOES-NOT-EXIST")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "BATCH_NOT_FOUND"


@pytest.mark.parametrize("bad", [{"variety": "no name"}, {}])
def test_batch_creation_validation(client, bad):
    res = client.post("/api/batches", json=bad)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
