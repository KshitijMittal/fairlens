"""A stored result and a fresh run serialise identically (S8)."""
import uuid
from pathlib import Path

from app.services import engine

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def test_stored_payload_round_trips_exactly(stored, repo):
    payload = stored("scholarship.csv")
    assert repo.get_analysis(uuid.UUID(payload["id"])) == payload


def test_stored_and_fresh_agree_apart_from_volatile_fields(stored):
    payload = stored("scholarship.csv")
    fresh = engine.run((SAMPLES / "scholarship.csv").read_bytes(), "scholarship.csv")
    fresh["id"] = payload["id"]

    for volatile in ("created_at", "duration_ms"):
        payload.pop(volatile)
        fresh.pop(volatile)

    assert payload == fresh
