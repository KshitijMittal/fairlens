"""Engine constants: one place for thresholds, echoed with every result (PRD 8.6)."""

ENGINE_VERSION = "2.0.0"

THRESHOLDS = {
    "parity": {"pass_at": 0.90, "warn_at": 0.80},
    "amplification": {"warn_at": 0.05, "fail_at": 0.15},
    "equal_opportunity": {"pass_at": 0.05, "fail_at": 0.15},
    "bootstrap": {"resamples": 1000, "confidence": 0.95, "max_half_width": 0.10},
    "min_group_rows": 30,
    "sample_adequacy": {"min_group_rows": 100, "max_rate_half_width": 0.05},
}

BOOTSTRAP_RESAMPLES = THRESHOLDS["bootstrap"]["resamples"]
BOOTSTRAP_CONFIDENCE = THRESHOLDS["bootstrap"]["confidence"]
RATIO_MAX_HALF_WIDTH = THRESHOLDS["bootstrap"]["max_half_width"]
MIN_GROUP_ROWS = THRESHOLDS["min_group_rows"]
C5_MIN_GROUP_ROWS = THRESHOLDS["sample_adequacy"]["min_group_rows"]
C5_MAX_RATE_HALF_WIDTH = THRESHOLDS["sample_adequacy"]["max_rate_half_width"]

FOLDS = 5
POSITIVE_RATE_THRESHOLD = 0.5
SAMPLING_THRESHOLD = 50_000


def derive_seed(file_bytes: bytes, confirmations: dict) -> int:
    import hashlib
    import json

    canonical = json.dumps(confirmations, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(file_bytes + canonical.encode()).digest()
    return int.from_bytes(digest[:4], "big")
