"""Vercel serverless entrypoint. Vercel detects `app` in api/*.py.
SQLite is read-only on Vercel runtime — that's expected. Seeding and
ingestion run locally; commit the updated DB to redeploy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from web.app import app  # noqa: F401, E402
