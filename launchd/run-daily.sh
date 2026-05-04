#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/logs
echo "=== $(date) start daily ==="
source .venv/bin/activate
python -m ingest.daily --days-back 2 --per-entity 6
python adjudicate.py --pending
python adjudicate.py --run --limit 3
python digest.py --push || true
# Auto-commit any DB changes so Vercel redeploys
if ! git diff --quiet data/healthuniverse.db; then
  git add data/healthuniverse.db
  git commit -m "daily ingest $(date -u +%Y-%m-%dT%H:%MZ)" >/dev/null
  git push -q origin main || echo "push failed (continuing)"
fi
echo "=== $(date) end daily ==="
