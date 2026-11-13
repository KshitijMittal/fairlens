"""Database module - connection pool, migrations, and repository."""
import os

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.db.migrate import run_migrations


def _make_pool() -> ConnectionPool:
    """Create a pooled connection pool for the app."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    return ConnectionPool(
        conninfo=db_url,
        min_size=1,
        max_size=4,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=False,
    )


def _make_unpooled() -> psycopg.Connection:
    """Create an unpooled connection for migrations.

    Tuple rows: the migration runner indexes columns positionally.
    """
    db_url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL_UNPOOLED or DATABASE_URL is not set")

    return psycopg.connect(db_url, autocommit=True)


# Module-level pool (created on demand, opened by get_pool)
pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global pool
    if pool is None:
        pool = _make_pool()
        pool.open()
    return pool


def close_pool() -> None:
    global pool
    if pool is not None:
        pool.close()
        pool = None


def init_db() -> None:
    """Run migrations and open the pool. Called at app startup."""
    with _make_unpooled() as conn:
        run_migrations(conn)

    get_pool()


# Re-export for convenience
from app.db.repository import Repository  # noqa: E402
from app.db.queries import get_query  # noqa: E402

__all__ = [
    "pool",
    "get_pool",
    "close_pool",
    "init_db",
    "Repository",
    "get_query",
]
