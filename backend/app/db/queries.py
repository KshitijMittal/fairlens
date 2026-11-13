"""Database query loader and repository.

Loads all named SQL files from backend/app/db/queries/ at import time.
Provides a simple typed wrapper around psycopg connections.
"""
from pathlib import Path
from typing import Any

import psycopg

QUERIES_DIR = Path(__file__).resolve().parent / "queries"

_QUERIES: dict[str, str] = {}

for path in QUERIES_DIR.glob("*.sql"):
    _QUERIES[path.stem] = path.read_text(encoding="utf-8")


def get_query(name: str) -> str:
    """Get a query by its filename (without .sql extension)."""
    if name not in _QUERIES:
        raise KeyError(f"Query '{name}' not found. Available: {sorted(_QUERIES.keys())}")
    return _QUERIES[name]