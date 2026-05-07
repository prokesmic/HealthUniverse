#!/bin/bash
# Burst-mode runner. Used both for ad-hoc invocation and by the
# launchd plists for Night 2 / Night 3.
#
# Usage:
#   scripts/run_burst.sh 1   # 50 edges,  14d window
#   scripts/run_burst.sh 2   # 100 edges, 30d window
#   scripts/run_burst.sh 3   # 100 edges, 60d window

set -euo pipefail

NIGHT="${1:-1}"
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT"

case "$NIGHT" in
  1) ARGS=(--max-edges 50  --days-back 14 --per-entity 12) ;;
  2) ARGS=(--max-edges 100 --days-back 30 --per-entity 15) ;;
  3) ARGS=(--max-edges 100 --days-back 60 --per-entity 18) ;;
  *) echo "Usage: $0 {1|2|3}"; exit 1 ;;
esac

mkdir -p data/audits
LOG="data/audits/burst-night${NIGHT}-$(date +%Y%m%d-%H%M).log"

echo "[$(date)] burst night ${NIGHT} starting · args=${ARGS[*]}" | tee "$LOG"
echo "[$(date)] log → $LOG"

# Use a smaller, faster model than the daily default.
# gemma4:26b (18 GB) takes ~30-60s per abstract on a Mac mini under
# memory pressure. llama3:8b (4.7 GB) handles structured-JSON
# extraction equally well and is 3-5× faster, which matters when the
# burst processes hundreds of abstracts.
export OLLAMA_MODEL="${OLLAMA_MODEL_BURST:-llama3:8b}"

# Python -u disables stdout/stderr buffering so the log file shows
# progress in real time (the previous run sat silent for an hour).
# caffeinate -i prevents idle sleep while the burst runs.
caffeinate -i "$PROJECT/.venv/bin/python" -u gemma_burst.py "${ARGS[@]}" \
  >> "$LOG" 2>&1 || {
    echo "[$(date)] burst night ${NIGHT} FAILED (exit=$?)" | tee -a "$LOG"
    exit 1
  }

echo "[$(date)] burst night ${NIGHT} complete" | tee -a "$LOG"

# Self-disable launchd plist if we were started by one. Idempotent.
PLIST="$HOME/Library/LaunchAgents/com.healthuniverse.burst-night${NIGHT}.plist"
if [ -f "$PLIST" ]; then
  launchctl bootout "gui/$(id -u)/com.healthuniverse.burst-night${NIGHT}" 2>/dev/null || true
  rm -f "$PLIST"
  echo "[$(date)] launchd plist disabled + removed: $PLIST" | tee -a "$LOG"
fi
