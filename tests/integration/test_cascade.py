"""The ten-zero deletion test: deleting a user leaves no row behind (F9-AC1)."""
import uuid

from app.db import Repository, get_pool


def test_account_deletion_cascades_everywhere(stored, user_id, db):
    repo = Repository(get_pool())
    parent = stored("scholarship.csv")
    parent_id = parent["id"]

    # A repair result is a child analysis of the run it repairs.
    child = {**parent, "id": str(uuid.uuid4())}
    repo.create_analysis(child, user_id, parent_id=uuid.UUID(parent_id),
                         repair_strategy="reweigh")
    child_id = child["id"]

    # One row in every table that hangs off the user or the analysis.
    db.execute("insert into sessions (token_hash, user_id, expires_at)"
               " values ('s1', %s, now() + interval '1 hour')", (user_id,))
    db.execute("insert into auth_tokens (token_hash, user_id, purpose, expires_at)"
               " values ('t1', %s, 'password_reset', now() + interval '1 hour')", (user_id,))
    db.execute("insert into analysis_narratives (analysis_id, kind, body)"
               " values (%s, 'template', 'body')", (parent_id,))
    db.execute("insert into analysis_repairs (analysis_id, strategy, summary)"
               " values (%s, 'reweigh', 'summary')", (child_id,))
    db.execute("insert into chat_messages (analysis_id, role, body)"
               " values (%s, 'user', 'hi')", (parent_id,))
    db.execute("insert into shares (token_hash, analysis_id) values ('share1', %s)", (parent_id,))
    db.execute("insert into llm_cache (key_hash, analysis_id, kind, prompt_version, response)"
               " values ('k1', %s, 'narrative', 'v1', '{}'::jsonb)", (parent_id,))

    # Sanity: the rows exist before the delete, so the assertions below mean something.
    for table in ("analyses", "analysis_checks", "analysis_groups", "analysis_narratives",
                  "analysis_repairs", "chat_messages", "shares", "llm_cache"):
        assert db.execute(f"select count(*) from {table}").fetchone()[0] > 0, table

    db.execute("delete from users where id = %s", (user_id,))

    for table in ("sessions", "auth_tokens", "analyses", "analysis_checks", "analysis_groups",
                  "analysis_narratives", "analysis_repairs", "chat_messages", "shares",
                  "llm_cache"):
        assert db.execute(f"select count(*) from {table}").fetchone()[0] == 0, table
