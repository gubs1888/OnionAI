"""GET /api/health — status + honest database/demo_mode reporting."""


def test_health_ok(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "onion-quality-ai"
    assert body["database"] == "connected"   # in-memory SQLite is up
    assert body["demo_mode"] is True         # forced for tests


def test_health_reports_disconnect(client):
    # Simulate DB outage: make get_db raise on execute.
    from app.api.deps import get_db

    class BrokenDB:
        def execute(self, *_a, **_k):
            raise RuntimeError("db down")

    app = client.app
    original = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = lambda: iter([BrokenDB()])
    try:
        res = client.get("/api/health")
        body = res.json()
        assert body["database"] == "disconnected"   # never lie
        assert body["status"] == "degraded"
    finally:
        app.dependency_overrides[get_db] = original
