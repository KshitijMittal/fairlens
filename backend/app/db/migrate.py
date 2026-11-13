"""Migration runner - applies schema_migrations at startup.

The runner creates its own bookkeeping table (schema_migrations), then
applies any missing migration files in lexical order, one transaction per file.
A changed checksum on an already-applied file is a startup failure.
"""
import hashlib
import logging
import os
from pathlib import Path

import psycopg

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
ADVISORY_LOCK_ID = 4823017


def _checksum(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_schema_migrations_table(conn: psycopg.Connection) -> None:
    conn.execute("""
        create table if not exists schema_migrations (
          version    text primary key,
          checksum   text not null,
          applied_at timestamptz not null default now()
        );
    """)


def _applied_versions(conn: psycopg.Connection) -> dict[str, str]:
    rows = conn.execute("select version, checksum from schema_migrations").fetchall()
    return {version: checksum for version, checksum in rows}


def run_migrations(conn: psycopg.Connection) -> None:
    """Apply any pending migrations. Must be called before the app accepts traffic."""
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"No migration files found in {MIGRATIONS_DIR}")

    # Blocking lock: a second container waits for the first instead of crashing.
    conn.execute("select pg_advisory_lock(%s)", (ADVISORY_LOCK_ID,))
    try:
        _ensure_schema_migrations_table(conn)
        applied = _applied_versions(conn)

        for path in migration_files:
            version = path.stem  # e.g., "0001_users"
            checksum = _checksum(path)

            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"Migration {version} checksum mismatch: "
                        f"database has {applied[version]}, file has {checksum}. "
                        "Editing history is not allowed - restore the original file."
                    )
                continue

            logger.info("Applying migration %s", version)
            with conn.transaction():
                conn.execute(path.read_text(encoding="utf-8"))
                conn.execute(
                    "insert into schema_migrations (version, checksum) values (%s, %s)",
                    (version, checksum),
                )

        logger.info("All %d migrations up to date", len(migration_files))
    finally:
        conn.execute("select pg_advisory_unlock(%s)", (ADVISORY_LOCK_ID,))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL_UNPOOLED or DATABASE_URL is not set")
    with psycopg.connect(url, autocommit=True) as conn:
        run_migrations(conn)


if __name__ == "__main__":
    main()
