"""All fourteen migrations apply to an empty Postgres 16, and a second run is a no-op."""
from app.db import _make_unpooled, get_pool
from app.db import migrate

EXPECTED = [
    "0001_users", "0002_sessions", "0003_auth_tokens",
    "0004_analyses", "0005_analysis_checks", "0006_analysis_groups",
    "0007_analysis_narratives", "0008_analysis_repairs",
    "0009_chat_messages", "0010_shares", "0011_rate_limits",
    "0012_llm_cache", "0013_top_level_analyses", "0014_immutability",
]


def test_all_fourteen_are_applied():
    with get_pool().connection() as conn:
        versions = [row["version"] for row in
                    conn.execute("select version from schema_migrations order by version")]
    assert versions == EXPECTED


def test_second_run_is_a_no_op():
    with _make_unpooled() as conn:
        migrate.run_migrations(conn)


def test_checksum_drift_fails_startup(tmp_path, monkeypatch):
    # A temp migrations dir holding one already-applied file, edited.
    drifted = (migrate.MIGRATIONS_DIR / "0001_users.sql").read_text(encoding="utf-8")
    (tmp_path / "0001_users.sql").write_text(drifted + "\n-- edited after apply\n",
                                             encoding="utf-8")
    monkeypatch.setattr(migrate, "MIGRATIONS_DIR", tmp_path)

    with _make_unpooled() as conn:
        try:
            migrate.run_migrations(conn)
        except RuntimeError as exc:
            assert "checksum mismatch" in str(exc)
        else:
            raise AssertionError("a changed migration file must fail startup")
