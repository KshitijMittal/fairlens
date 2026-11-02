"""G3 fixture: an exact 60 MiB CSV to push through the rewrite.

Usage: python backend/scripts/make_big_csv.py [path]

shortcut: the file is truncated to the exact byte count, so its last line is
partial. It exists to measure a request body, never to be parsed.
"""
import csv
import os
import sys

TARGET_BYTES = 62_914_560  # 60 MiB, the number G3 asserts


def make_big_csv(path: str, target_bytes: int = TARGET_BYTES) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ["record_id", "outcome", "group"] + [f"col_{i:02d}" for i in range(3, 8)]

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        row = 0
        while f.tell() < target_bytes:
            writer.writerow([row, "yes" if row % 3 == 0 else "no", "group_a" if row % 2 == 0 else "group_b"] + [row % 1000] * 5)
            row += 1
        f.truncate(target_bytes)

    print(f"Created {path}: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "..", "samples", "_gate", "big.csv"
    )
    make_big_csv(os.path.abspath(out))
