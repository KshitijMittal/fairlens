"""G9 (retired): the host benchmark recorded on 2026-11-01. Kept as evidence only.

The M0 probe app and its /v1/dev/bench endpoint were replaced in M1, so this no
longer runs against the deployed Space.

Usage: python backend/scripts/bench_host.py https://<space>.hf.space

Called /v1/dev/bench twice in one process: the first pass cold, the second warm.
"""
import json
import sys
import urllib.request


def call(url: str) -> dict:
    with urllib.request.urlopen(f"{url.rstrip('/')}/v1/dev/bench", timeout=300) as resp:
        return json.load(resp)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python backend/scripts/bench_host.py <space-url>")
        return 2
    url = sys.argv[1]

    cold = call(url)
    warm = call(url)
    print(json.dumps({"cold": cold, "warm": warm}, indent=2))

    failed = warm["seconds"] > 20 or cold["seconds"] > 55 or warm["seconds"] > 55
    print("PASS" if not failed else "FAIL: over budget")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
