"""UPDATE is rejected on the four metric tables; DELETE still cascades."""
import uuid

import psycopg
import pytest

from app.db import Repository, get_pool


def test_updates_are_rejected(stored, user_id, db):
    payload = stored("scholarship.csv")
    analysis_id = payload["id"]

    child = {**payload, "id": str(uuid.uuid4())}
    Repository(get_pool()).create_analysis(
        child, user_id, parent_id=uuid.UUID(analysis_id), repair_strategy="reweigh")
    db.execute("insert into analysis_repairs (analysis_id, strategy, summary)"
               " values (%s, 'reweigh', 'summary')", (child["id"],))

    cases = [
        ("update analyses set verdict = 'pass' where id = %s", (analysis_id,), "analyses"),
        ("update analysis_checks set state = 'pass' where analysis_id = %s and check_code = 'C1'",
         (analysis_id,), "analysis_checks"),
        ("update analysis_groups set selection_rate = 0.5 where analysis_id = %s",
         (analysis_id,), "analysis_groups"),
        ("update analysis_repairs set verdict_after = 'pass' where analysis_id = %s",
         (child["id"],), "analysis_repairs"),
    ]
    for sql, params, table in cases:
        with pytest.raises(psycopg.errors.RestrictViolation) as exc:
            db.execute(sql, params)
        assert f"fairlens: {table} is immutable" in str(exc.value)


def test_delete_still_cascades(stored, db):
    payload = stored("scholarship.csv")
    db.execute("delete from analyses where id = %s", (payload["id"],))
    assert db.execute("select count(*) from analysis_checks where analysis_id = %s",
                      (payload["id"],)).fetchone()[0] == 0
    assert db.execute("select count(*) from analysis_groups where analysis_id = %s",
                      (payload["id"],)).fetchone()[0] == 0
