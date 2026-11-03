"""Short-lived in-process cache for anonymous sample runs (plan P2, F9-AC5).

Single worker, 50-entry cap, 30-minute TTL. Never hardened beyond this.
"""
import threading
import time
from collections import OrderedDict

CAP = 50
TTL_SECONDS = 30 * 60

_lock = threading.Lock()
_store: "OrderedDict[str, tuple[float, dict]]" = OrderedDict()


def put(run_id: str, payload: dict) -> None:
    with _lock:
        _store[run_id] = (time.time(), payload)
        _store.move_to_end(run_id)
        while len(_store) > CAP:
            _store.popitem(last=False)


def get(run_id: str) -> dict | None:
    with _lock:
        entry = _store.get(run_id)
        if entry is None:
            return None
        stored_at, payload = entry
        if time.time() - stored_at > TTL_SECONDS:
            del _store[run_id]
            return None
        _store.move_to_end(run_id)
        return payload
