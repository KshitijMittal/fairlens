"""G9: time the pipeline on the deployed Space.

Usage: python backend/scripts/bench_host.py https://<space>.hf.space

Calls the Space's /v1/dev/bench twice in one process: the first pass is cold,
the second warm. Pass condition: warm under 20 s, every pass under 55 s.
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
