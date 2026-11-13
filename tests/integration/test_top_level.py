"""A repair child analysis does not appear in the history view."""
import uuid

from app.db import Repository, get_pool


def test_child_is_absent_from_top_level(stored, user_id, db):
    parent = stored("scholarship.csv")
    child = {**parent, "id": str(uuid.uuid4())}
    Repository(get_pool()).create_analysis(
        child, user_id, parent_id=uuid.UUID(parent["id"]), repair_strategy="reweigh")

    assert db.execute("select count(*) from top_level_analyses where id = %s",
                      (parent["id"],)).fetchone()[0] == 1
    assert db.execute("select count(*) from top_level_analyses where id = %s",
                      (child["id"],)).fetchone()[0] == 0
