"""Auth, reset and upload-wall integration tests over real HTTP (F8, F2-AC6)."""
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.security import hash_token, new_auth_token
from app.db import Repository, get_pool

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


@pytest.fixture(scope="module")
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def repo():
    return Repository(get_pool())


def _signup(client: TestClient, password: str = "Correct-horse-1") -> dict:
    email = f"{uuid.uuid4().hex}@example.com"
    res = client.post("/v1/auth/signup",
                      json={"email": email, "password": password, "display_name": "Test"})
    assert res.status_code == 201, res.text
    return {"email": email, "password": password, **res.json()}


def test_signup_creates_session_and_me_works(client):
    me = _signup(client)

    res = client.get("/v1/me")
    assert res.status_code == 200
    assert res.json() == {"id": me["id"], "email": me["email"], "display_name": "Test"}


def test_duplicate_signup_is_409(client):
    me = _signup(client)
    res = client.post("/v1/auth/signup",
                      json={"email": me["email"], "password": "Correct-horse-1"})
    assert res.status_code == 409


def test_login_names_the_reason(client):
    """v3.3: a missing account and a wrong password are different answers, so a
    visitor knows whether to sign up. The reset endpoint still stays uniform."""
    me = _signup(client)
    missing = client.post("/v1/auth/login",
                          json={"email": "nobody@example.com", "password": "wrong-password-1"})
    wrong = client.post("/v1/auth/login",
                        json={"email": me["email"], "password": "wrong-password-1"})
    assert missing.status_code == 404
    assert "No account" in missing.json()["detail"]
    assert wrong.status_code == 401
    assert "Incorrect password" in wrong.json()["detail"]


def test_logout_clears_the_session(client):
    me = _signup(client)
    assert client.post("/v1/auth/logout").status_code == 204
    assert client.get("/v1/me").status_code == 401

    assert client.post("/v1/auth/login",
                       json={"email": me["email"], "password": me["password"]}).status_code == 200
    assert client.get("/v1/me").status_code == 200


def test_reset_response_is_uniform(client):
    me = _signup(client)
    real = client.post("/v1/auth/reset/request", json={"email": me["email"]})
    missing = client.post("/v1/auth/reset/request", json={"email": "nobody@example.com"})

    assert real.status_code == missing.status_code == 202
    assert real.json() == missing.json()


def test_reset_token_is_single_use_and_ends_sessions(client, repo):
    me = _signup(client)
    token = new_auth_token()
    repo.create_auth_token(hash_token(token), uuid.UUID(me["id"]), "password_reset",
                           datetime.now(timezone.utc) + timedelta(minutes=30))

    res = client.post("/v1/auth/reset/confirm",
                      json={"token": token, "password": "A-new-password-1"})
    assert res.status_code == 200

    assert client.get("/v1/me").status_code == 401

    again = client.post("/v1/auth/reset/confirm",
                        json={"token": token, "password": "Another-password-1"})
    assert again.status_code == 400

    assert client.post("/v1/auth/login",
                       json={"email": me["email"], "password": me["password"]}).status_code == 401
    assert client.post("/v1/auth/login",
                       json={"email": me["email"], "password": "A-new-password-1"}).status_code == 200


def test_expired_reset_token_is_refused(client, repo):
    me = _signup(client)
    token = new_auth_token()
    token_hash = hash_token(token)
    repo.create_auth_token(token_hash, uuid.UUID(me["id"]), "password_reset",
                           datetime.now(timezone.utc) + timedelta(minutes=30))
    with get_pool().connection() as conn:
        # Move creation and expiry into the past consistently, so only expiry is the reason.
        conn.execute("update users set password_changed_at = now() - interval '61 minutes'"
                     " where id = %s", (me["id"],))
        conn.execute("update auth_tokens set created_at = now() - interval '60 minutes',"
                     " expires_at = now() - interval '30 minutes' where token_hash = %s",
                     (token_hash,))

    res = client.post("/v1/auth/reset/confirm",
                      json={"token": token, "password": "A-new-password-1"})
    assert res.status_code == 400


def test_reset_token_issued_before_a_password_change_is_dead(client, repo):
    me = _signup(client)
    token = new_auth_token()
    repo.create_auth_token(hash_token(token), uuid.UUID(me["id"]), "password_reset",
                           datetime.now(timezone.utc) + timedelta(minutes=30))
    repo.set_password(uuid.UUID(me["id"]), "irrelevant-hash")

    res = client.post("/v1/auth/reset/confirm",
                      json={"token": token, "password": "A-new-password-1"})
    assert res.status_code == 400


@pytest.fixture
def anonymous_client():
    from app.main import app

    return TestClient(app)


def test_providers_reports_google_flag(anonymous_client):
    res = anonymous_client.get("/v1/auth/providers")
    assert res.status_code == 200
    assert res.json() == {"google": False}


def test_unauthenticated_upload_is_401(anonymous_client):
    data = (SAMPLES / "scholarship.csv").read_bytes()
    res = anonymous_client.post(
        "/v1/analyses",
        files={"file": ("scholarship.csv", data, "text/csv")},
        data={"confirmations": json.dumps(
            {"outcome": "awarded", "positive": "yes", "group": "region"})},
    )
    assert res.status_code == 401


def test_inspect_run_stream_and_owned_read(client):
    _signup(client)
    data = (SAMPLES / "scholarship.csv").read_bytes()

    inspected = client.post("/v1/analyses/inspect",
                            files={"file": ("scholarship.csv", data, "text/csv")})
    assert inspected.status_code == 200, inspected.text
    card = inspected.json()["card"]
    confirmations = {"outcome": card["outcome"]["column"],
                     "positive": card["outcome"]["positive_value"],
                     "group": card["groups"]["column"]}

    with client.stream(
        "POST", "/v1/analyses",
        files={"file": ("scholarship.csv", data, "text/csv")},
        data={"confirmations": json.dumps(confirmations)},
    ) as res:
        assert res.status_code == 200, res.read()
        frames = [json.loads(line) for line in res.iter_lines() if line]

    events = [frame["event"] for frame in frames]
    assert events[-1] == "result"
    stages = [frame["stage"] for frame in frames if frame["event"] == "stage"]
    assert stages == ["parsing", "cleaning", "training", "measuring", "influence", "saving"]

    payload = frames[-1]["payload"]
    assert payload["confirmation"]["outcome"]["positive_value"] == confirmations["positive"]

    stored = client.get(f"/v1/analyses/{payload['id']}")
    assert stored.status_code == 200
    assert stored.json()["id"] == payload["id"]

    listed = client.get("/v1/analyses")
    assert listed.status_code == 200
    assert payload["id"] in {row["id"] for row in listed.json()["analyses"]}

    other = TestClient(client.app)
    _signup(other)
    assert other.get(f"/v1/analyses/{payload['id']}").status_code == 404

def test_unknown_analysis_id_is_404(client):
    _signup(client)
    assert client.get("/v1/analyses/not-a-uuid").status_code == 404
    assert client.get(f"/v1/analyses/{uuid.uuid4()}").status_code == 404
