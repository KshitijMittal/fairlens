"""G2 (retired): the mail probe recorded on 2026-11-01. Kept as evidence only.

The M0 probe app and its /v1/dev/mail-probe endpoint were replaced in M1, so this
no longer runs against the deployed Space.

Usage: python backend/scripts/mail_probe.py https://<space>.hf.space you@example.com

Needed PROBE_TOKEN and BREVO_API_KEY/BREVO_SENDER set as Space secrets.
Spaces block every port except 80, 443 and 8080, so SMTP is not an option.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from dotenv import dotenv_values


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python backend/scripts/mail_probe.py <space-url> <recipient>")
        return 2
    url, recipient = sys.argv[1].rstrip("/"), sys.argv[2]
    env = dotenv_values(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    token = env.get("PROBE_TOKEN")
    if not token:
        print("ERROR: PROBE_TOKEN missing from .env")
        return 1

    req = urllib.request.Request(
        f"{url}/v1/dev/mail-probe?to={urllib.parse.quote(recipient)}",
        data=b"",
        headers={"x-probe-token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            print(json.load(resp))
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        print(f"FAILED: HTTP {exc.code}: {body}")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
