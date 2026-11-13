"""An anonymous sample run writes no rows, is readable by id, and 404s after expiry."""
from fastapi.testclient import TestClient

from app.core import result_cache
from app.main import app
from app.db import get_pool


def test_anonymous_run_is_cached_and_writes_nothing():
    with TestClient(app) as client:
        run = client.post("/v1/dev/sample/scholarship").json()
        assert run["verdict"] == "pass"

        assert client.get("/v1/health").json()["database"] is True
        assert client.get(f"/v1/analyses/{run['id']}").status_code == 200
        assert client.get("/v1/analyses/not-a-uuid").status_code == 404

    with get_pool().connection() as conn:
        row = conn.execute("select count(*) as n from analyses where id = %s", (run["id"],))
        assert row.fetchone()["n"] == 0


def test_expired_run_404s(monkeypatch):
    with TestClient(app) as client:
        run = client.post("/v1/dev/sample/scholarship").json()
        monkeypatch.setattr(result_cache, "TTL_SECONDS", -1)
        assert client.get(f"/v1/analyses/{run['id']}").status_code == 404
