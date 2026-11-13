"""Database repository — typed wrappers around the named queries.

Each method corresponds to one or more named SQL files and returns
plain Python types (dict, list, None). No ORM, no query building.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from psycopg.types.json import Jsonb

from app.db import queries as q


class Repository:
    """Database repository with one method per query file."""

    def __init__(self, pool) -> None:
        self._pool = pool

    # --- User & Auth ---

    def create_user(
        self,
        email: str,
        password_hash: str | None,
        google_sub: str | None,
        display_name: str | None,
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("users_insert"),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "google_sub": google_sub,
                    "display_name": display_name,
                },
            )
            return cur.fetchone()

    def get_user_by_email(self, email: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("users_by_email"),
                {"email": email},
            )
            return cur.fetchone()

    def get_user_by_google_sub(self, google_sub: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("users_by_google_sub"),
                {"google_sub": google_sub},
            )
            return cur.fetchone()

    def set_password(self, user_id: uuid.UUID, password_hash: str) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("users_set_password"),
                {"user_id": str(user_id), "password_hash": password_hash},
            )
            return cur.fetchone()

    # --- Sessions ---

    def create_session(
        self,
        token_hash: str,
        user_id: uuid.UUID,
        expires_at: datetime,
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("sessions_insert"),
                {
                    "token_hash": token_hash,
                    "user_id": str(user_id),
                    "expires_at": expires_at,
                },
            )
            return cur.fetchone()

    def get_session(self, token_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("sessions_by_hash"),
                {"token_hash": token_hash},
            )
            return cur.fetchone()

    def delete_session(self, token_hash: str) -> None:
        with self._pool.connection() as conn:
            conn.execute(q.get_query("sessions_delete"), {"token_hash": token_hash})

    def delete_all_sessions_for_user(self, user_id: uuid.UUID) -> None:
        with self._pool.connection() as conn:
            conn.execute(q.get_query("sessions_delete_all_for_user"), {"user_id": str(user_id)})

    # --- Auth tokens ---

    def create_auth_token(
        self,
        token_hash: str,
        user_id: uuid.UUID,
        purpose: str,
        expires_at: datetime,
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("auth_tokens_insert"),
                {
                    "token_hash": token_hash,
                    "user_id": str(user_id),
                    "purpose": purpose,
                    "expires_at": expires_at,
                },
            )
            return cur.fetchone()

    def consume_auth_token(self, token_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("auth_tokens_consume"),
                {"token_hash": token_hash},
            )
            return cur.fetchone()

    # --- Analyses ---

    def create_analysis(
        self,
        payload: dict,
        user_id: uuid.UUID,
        parent_id: uuid.UUID | None = None,
        repair_strategy: str | None = None,
    ) -> dict:
        """Insert the analysis, its checks and its groups in one transaction.

        The engine payload is stored whole in `analyses.result`; the columns and
        the two child tables are the queryable projection of the same payload.
        """
        dataset = payload["dataset"]
        confirmation = payload["confirmation"]
        column_types = {e["column"]: "categorical" for e in payload["encoding"]["categorical"]}
        column_types |= {e["column"]: "numeric" for e in payload["encoding"]["numeric"]}

        params = {
            "id": payload["id"],
            "user_id": str(user_id),
            "parent_id": str(parent_id) if parent_id else None,
            "repair_strategy": repair_strategy,
            "dataset_name": dataset["name"],
            "source_sha256": dataset["sha256"],
            "is_sample": dataset["is_sample"],
            "sample_slug": (dataset["sample"] or {}).get("slug"),
            "row_count": dataset["rows"],
            "column_count": dataset["columns"],
            "columns": Jsonb([{"name": name, "inferred_type": column_types.get(name, "unknown")}
                              for name in dataset["column_names"]]),
            "outcome_column": confirmation["outcome"]["column"],
            "positive_value": confirmation["outcome"]["positive_value"],
            "group_column": confirmation["groups"]["column"],
            "group_count": len(confirmation["groups"]["values"]),
            "age_banding": confirmation["age_banding"]["applied"],
            "sampling": Jsonb(payload["sampling"]) if payload["sampling"] else None,
            "thresholds": Jsonb(payload["thresholds"]),
            "model_card": Jsonb(payload["model_card"]),
            "encoding": Jsonb(payload["encoding"]),
            "proxies": Jsonb(payload["proxies"]),
            "result": Jsonb(payload),
            "verdict": payload["verdict"],
            "deciding_checks": payload["deciding_checks"],
            "seed": payload["seed"],
            "engine_version": payload["engine_version"],
            "duration_ms": payload["duration_ms"],
        }

        with self._pool.connection() as conn, conn.transaction():
            conn.execute(q.get_query("analyses_insert"), params)

            for check in payload["checks"]:
                low, high = check["interval"] or (None, None)
                conn.execute(q.get_query("checks_insert"), {
                    "analysis_id": payload["id"],
                    "check_code": check["code"],
                    "state": check["state"],
                    "value": check["value"],
                    "ci_low": low,
                    "ci_high": high,
                    "threshold": Jsonb(check["threshold"]),
                    "reason": check["reason"],
                })

            for scope, rows in payload["groups"].items():
                for row in rows:
                    low, high = row["interval"] or (None, None)
                    conn.execute(q.get_query("groups_insert"), {
                        "analysis_id": payload["id"],
                        "scope": scope,
                        "group_label": row["label"],
                        "n": row["n"],
                        "positives": row["positives"],
                        "selection_rate": row["selection_rate"],
                        "rate_ci_low": low,
                        "rate_ci_high": high,
                        "tpr": row["tpr"],
                        "fpr": row["fpr"],
                        "accuracy": row["accuracy"],
                    })

        return payload

    def get_analysis(self, analysis_id: uuid.UUID) -> dict | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                q.get_query("analyses_by_id"),
                {"id": str(analysis_id)},
            ).fetchone()
        return row["result"] if row else None

    def get_analysis_by_share_token(self, token_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("analyses_by_share_token"),
                {"token_hash": token_hash},
            )
            return cur.fetchone()

    def list_analyses(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("analyses_for_user"),
                {"user_id": str(user_id), "limit": limit, "offset": offset},
            )
            return cur.fetchall()

    def delete_analysis(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                q.get_query("analyses_delete"),
                {"id": str(analysis_id), "user_id": str(user_id)},
            )

    # --- Checks & Groups ---

    def get_checks(self, analysis_id: uuid.UUID) -> list[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("checks_by_analysis"),
                {"analysis_id": str(analysis_id)},
            )
            return cur.fetchall()

    def get_groups(self, analysis_id: uuid.UUID) -> list[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("groups_by_analysis"),
                {"analysis_id": str(analysis_id)},
            )
            return cur.fetchall()

    # --- Narratives ---

    def insert_narrative(
        self,
        analysis_id: uuid.UUID,
        kind: str,
        body: str,
        provider: str | None,
        model_name: str | None,
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("narrative_insert"),
                {
                    "analysis_id": str(analysis_id),
                    "kind": kind,
                    "body": body,
                    "provider": provider,
                    "model_name": model_name,
                },
            )
            return cur.fetchone()

    def get_narrative(self, analysis_id: uuid.UUID) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("narrative_by_analysis"),
                {"analysis_id": str(analysis_id)},
            )
            return cur.fetchone()

    # --- Repairs ---

    def replace_repairs(self, analysis_id: uuid.UUID, repairs: list[dict]) -> list[dict]:
        """
        Replace all repairs for an analysis in one transaction.
        Returns the inserted repairs.
        """
        with self._pool.connection() as conn:
            with conn.transaction():
                conn.execute(
                    q.get_query("repairs_delete"),
                    {"analysis_id": str(analysis_id)},
                )
                results = []
                for r in repairs:
                    cur = conn.execute(
                        q.get_query("repairs_insert"),
                        {**r, "analysis_id": str(analysis_id)},
                    )
                    results.append(cur.fetchone())
                return results

    def get_repairs(self, analysis_id: uuid.UUID) -> list[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("repairs_by_analysis"),
                {"analysis_id": str(analysis_id)},
            )
            return cur.fetchall()

    # --- Chat ---

    def insert_chat_message(
        self,
        analysis_id: uuid.UUID,
        role: str,
        body: str,
        citations: list[dict],
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("chat_insert"),
                {
                    "analysis_id": str(analysis_id),
                    "role": role,
                    "body": body,
                    "citations": json.dumps(citations),
                },
            )
            return cur.fetchone()

    def get_chat_messages(self, analysis_id: uuid.UUID) -> list[dict]:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("chat_by_analysis"),
                {"analysis_id": str(analysis_id)},
            )
            return cur.fetchall()

    # --- Shares ---

    def create_share(self, token_hash: str, analysis_id: uuid.UUID) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("shares_insert"),
                {"token_hash": token_hash, "analysis_id": str(analysis_id)},
            )
            return cur.fetchone()

    def get_share(self, token_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("shares_by_hash"),
                {"token_hash": token_hash},
            )
            return cur.fetchone()

    def delete_share(self, token_hash: str) -> None:
        with self._pool.connection() as conn:
            conn.execute(q.get_query("shares_delete"), {"token_hash": token_hash})

    def touch_share(self, token_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("shares_touch"),
                {"token_hash": token_hash},
            )
            return cur.fetchone()

    # --- Rate Limits ---

    def hit_rate_limit(self, bucket: str, identifier: str) -> int:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("rate_limit_hit"),
                {"bucket": bucket, "identifier": identifier},
            )
            return cur.fetchone()["count"]

    def sweep_rate_limits(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(q.get_query("rate_limits_sweep"))

    # --- LLM Cache ---

    def get_llm_cache(self, key_hash: str) -> dict | None:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("llm_cache_get"),
                {"key_hash": key_hash},
            )
            return cur.fetchone()

    def put_llm_cache(
        self,
        key_hash: str,
        analysis_id: uuid.UUID | None,
        kind: str,
        prompt_version: str,
        response: dict,
    ) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("llm_cache_put"),
                {
                    "key_hash": key_hash,
                    "analysis_id": str(analysis_id) if analysis_id else None,
                    "kind": kind,
                    "prompt_version": prompt_version,
                    "response": json.dumps(response),
                },
            )
            return cur.fetchone()

    # --- Account ---

    def get_account_export_counts(self, user_id: uuid.UUID) -> dict:
        with self._pool.connection() as conn:
            cur = conn.execute(
                q.get_query("account_export_counts"),
                {"user_id": str(user_id)},
            )
            return cur.fetchone()

    # --- Rate limit sweep (called on startup and login) ---
    def sweep_expired(self) -> None:
        with self._pool.connection() as conn:
            conn.execute(q.get_query("sessions_delete_expired"))
            conn.execute(q.get_query("rate_limits_sweep"))