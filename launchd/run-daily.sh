#!/usr/bin/env bash
# Daily Health Universe pipeline. Runs at 05:15 via launchd.
# - Gemma extracts claims from new abstracts (free, local)
# - Adjudicates queued tier-A/B promotions with Claude (cap-aware)
# - Generates digest + push
# - Publishes the slim web DB (scripts/build_web_db.py) so Vercel redeploys
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

  # The working DB stays local; Vercel gets the slim web copy. The build
  # also guards size (ntfy warning from 60 MB, no push from 90 MB).
  echo "--- web DB ---"
  TO 300 python scripts/build_web_db.py; WEB_RC=$?
  if [ "$WEB_RC" -ne 0 ]; then
    echo "web DB not published (exit $WEB_RC), push skipped"
  elif ! git diff --quiet data/healthuniverse.web.db; then
    git add data/healthuniverse.web.db
    git commit -m "daily ingest $(date -u +%Y-%m-%dT%H:%MZ)" >/dev/null
    if ! TO 60 git push -q origin main; then
      echo "push failed"
      python scripts/build_web_db.py --alert "run-daily.sh: git push failed, live site not updated. See $LOG"
    fi
  else
    echo "no DB changes to push"
  fi

  echo "=== $(date) end daily ==="
} >> "$LOG" 2>&1
