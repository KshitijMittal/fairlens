"""Integration test setup: one disposable Postgres, migrated from empty once.

TEST_DATABASE_URL must point at a throwaway database: the session fixture drops
the whole `public` schema before migrating.
"""
import os
import uuid
from pathlib import Path

import psycopg
import pytest

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://fairlens:fairlens@localhost:5433/fairlens"
)

# Set before importing app modules: they read the environment at import time.
os.environ["DATABASE_URL"] = TEST_URL
os.environ["DATABASE_URL_UNPOOLED"] = TEST_URL
os.environ["ENV"] = "test"

from app.services import engine  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


@pytest.fixture(scope="session", autouse=True)
def _database():
    from app.db import close_pool, init_db

    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        conn.execute("drop schema public cascade; create schema public;")
    init_db()

    yield

    close_pool()


@pytest.fixture
def db():
    with psycopg.connect(TEST_URL, autocommit=True) as conn:
        yield conn


@pytest.fixture
def repo():
    from app.db import Repository, get_pool

    return Repository(get_pool())


@pytest.fixture
def user_id(db):
    row = db.execute(
        "insert into users (email, password_hash) values (%s, %s) returning id",
        (f"{uuid.uuid4()}@example.test", "x"),
    ).fetchone()
    return row[0]


@pytest.fixture
def stored(repo, user_id):
    """Store a bundled sample and return the exact payload that was saved."""
    def _store(filename: str, **kwargs) -> dict:
        payload = engine.run((SAMPLES / filename).read_bytes(), filename)
        payload["id"] = str(uuid.uuid4())
        repo.create_analysis(payload, user_id, **kwargs)
        return payload

    return _store
