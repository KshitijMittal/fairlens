#!/bin/sh
# FairLens v2 — Container entrypoint
# Runs migrations under advisory lock, then starts uvicorn

set -e

echo "Starting FairLens v2..."

# Run migrations (the Python runner handles advisory lock and checksums)
python -m app.db.migrate

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 7860 --workers 1