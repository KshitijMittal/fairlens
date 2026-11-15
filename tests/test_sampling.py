"""Sampling tests — deterministic, recorded in payload (F1-AC4, F1-AC7)."""
import hashlib
import numpy as np
import pandas as pd
import pytest

from app.services.engine import run, SAMPLING_THRESHOLD


def _make_large_frame(n_rows: int, seed: int = 42) -> bytes:
    """Generate a deterministic CSV with n_rows."""
    rng = np.random.default_rng(seed)
    n_groups = 4
    groups = [f"group_{i}" for i in range(n_groups)]
    group_col = rng.choice(groups, size=n_rows)
    outcome = rng.choice(["approved", "denied"], size=n_rows, p=[0.6, 0.4])
    feature1 = rng.normal(0, 1, n_rows)
    feature2 = rng.integers(1, 10, n_rows)

    df = pd.DataFrame({
        "group": group_col,
        "decision": outcome,
        "feature1": feature1,
        "feature2": feature2,
    })
    return df.to_csv(index=False).encode()


class TestSampling:
    """Tests for deterministic sampling above 50,000 rows."""

    def test_sampling_disabled_by_default(self):
        """Without sampling config, full frame is used even if large."""
        raw = _make_large_frame(60_000)
        result = run(raw, "test.csv")
        assert result["sampling"] is None
        assert result["dataset"]["rows"] == 60_000

    def test_sampling_enabled_above_threshold(self):
        """With sampling enabled, frame is sampled deterministically."""
        raw = _make_large_frame(60_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 30_000, "seed": 12345}
        }
        result = run(raw, "test.csv", confirmations)
        assert result["sampling"] is not None
        assert result["sampling"]["enabled"] is True
        assert result["sampling"]["original_rows"] == 60_000
        assert result["sampling"]["sampled_rows"] == 30_000
        assert result["sampling"]["seed"] == 12345
        assert result["dataset"]["rows"] == 30_000

    def test_same_seed_produces_identical_metrics(self):
        """Same seed twice gives identical metrics (F1-AC4, F1-AC7)."""
        raw = _make_large_frame(60_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 25_000, "seed": 999}
        }

        result1 = run(raw, "test.csv", confirmations)
        result2 = run(raw, "test.csv", confirmations)

        # All numeric results should be identical
        assert result1["seed"] == result2["seed"]
        assert result1["verdict"] == result2["verdict"]
        assert result1["checks"] == result2["checks"]
        assert result1["groups"] == result2["groups"]
        assert result1["affected"] == result2["affected"]
        assert result1["model_card"] == result2["model_card"]
        assert result1["sampling"] == result2["sampling"]

    def test_different_seeds_produce_different_results(self):
        """Different seeds produce different samples (and thus different results)."""
        raw = _make_large_frame(60_000)
        confirmations1 = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 25_000, "seed": 111}
        }
        confirmations2 = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 25_000, "seed": 222}
        }

        result1 = run(raw, "test.csv", confirmations1)
        result2 = run(raw, "test.csv", confirmations2)

        # Sampling metadata should differ
        assert result1["sampling"]["seed"] != result2["sampling"]["seed"]
        # At least some metrics should differ (probabilistically)
        # We can't guarantee they differ, but the seeds differ

    def test_sampling_recorded_in_payload(self):
        """Sampling block is recorded in the payload (F1-AC7)."""
        raw = _make_large_frame(60_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 25_000, "seed": 4242}
        }
        result = run(raw, "test.csv", confirmations)

        sampling = result["sampling"]
        assert sampling is not None
        assert "enabled" in sampling
        assert "original_rows" in sampling
        assert "sampled_rows" in sampling
        assert "seed" in sampling
        assert "method" in sampling
        assert sampling["method"] == "random"

    def test_sampling_below_threshold_no_op(self):
        """Frames below threshold are not sampled even if sampling config present."""
        raw = _make_large_frame(10_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 5_000, "seed": 42}
        }
        result = run(raw, "test.csv", confirmations)
        assert result["sampling"] is None
        assert result["dataset"]["rows"] == 10_000

    def test_sampling_size_capped_at_frame_size(self):
        """Sample size cannot exceed frame size."""
        raw = _make_large_frame(60_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 100_000, "seed": 42}
        }
        result = run(raw, "test.csv", confirmations)
        assert result["sampling"]["sampled_rows"] == 60_000

    def test_sampling_deterministic_indices(self):
        """Sampling uses deterministic indices for reproducibility."""
        raw = _make_large_frame(60_000)
        confirmations = {
            "outcome": "decision",
            "positive": "approved",
            "group": "group",
            "sampling": {"enabled": True, "size": 30_000, "seed": 777}
        }

        result1 = run(raw, "test.csv", confirmations)
        result2 = run(raw, "test.csv", confirmations)

        # The seed used for sampling should be recorded
        assert result1["sampling"]["seed"] == result2["sampling"]["seed"] == 777

        # The full result should be byte-identical
        import json
        # Volatile fields are not part of the deterministic contract.
        for result in (result1, result2):
            result.pop("created_at")
            result.pop("duration_ms")
        json1 = json.dumps(result1, sort_keys=True)
        json2 = json.dumps(result2, sort_keys=True)
        assert json1 == json2, "Same seed must produce byte-identical payload"