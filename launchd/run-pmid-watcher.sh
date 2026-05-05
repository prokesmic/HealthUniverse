#!/usr/bin/env bash
# Weekly PMID retraction watcher. Runs via launchd on Sunday 04:30.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/logs
LOG="data/logs/pmid-watcher-$(date +%Y%m%d).log"

{
  echo "=== $(date) start pmid watcher ==="
  source .venv/bin/activate
  export PYTHONUNBUFFERED=1
  python pmid_watcher.py --push
  echo "=== $(date) end pmid watcher ==="
} >> "$LOG" 2>&1
