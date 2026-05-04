#!/usr/bin/env bash
# Daily Health Universe pipeline. Runs at 05:15 via launchd.
# - Gemma extracts claims from new abstracts (free, local)
# - Adjudicates queued tier-A/B promotions with Claude (cap-aware)
# - Generates digest + push
# - Commits DB changes so Vercel redeploys
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/logs
LOG=data/logs/daily-$(date +%Y%m%d).log

{
  echo "=== $(date) start daily ==="
  source .venv/bin/activate

  # Unbuffered Python so log streams in real time.
  export PYTHONUNBUFFERED=1

  # Cap each step's wall time so a single hang can't eat the whole day.
  # macOS gtimeout via Homebrew if available, else perl fallback.
  if command -v gtimeout >/dev/null 2>&1; then
    TO() { gtimeout --kill-after=15 "$@"; }
  else
    TO() { perl -e 'alarm shift; exec @ARGV' "$@"; }
  fi

  echo "--- ingest.daily ---"
  TO 1800 python -m ingest.daily --days-back 2 --per-entity 3 || echo "ingest exited $?"

  echo "--- adjudicate (pending) ---"
  TO 60 python adjudicate.py --pending || true

  echo "--- adjudicate (run) ---"
  TO 600 python adjudicate.py --run --limit 3 || echo "adjudicate exited $?"

  echo "--- digest ---"
  TO 60 python digest.py --push || echo "digest exited $?"

  if ! git diff --quiet data/healthuniverse.db; then
    git add data/healthuniverse.db
    git commit -m "daily ingest $(date -u +%Y-%m-%dT%H:%MZ)" >/dev/null
    TO 60 git push -q origin main || echo "push failed (continuing)"
  else
    echo "no DB changes to push"
  fi

  echo "=== $(date) end daily ==="
} >> "$LOG" 2>&1
