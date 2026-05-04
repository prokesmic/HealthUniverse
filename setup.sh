#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env -- edit it to set ANTHROPIC_API_KEY"
fi

python db.py
python sources.py
python topics.py

echo
echo "Setup complete. Next:"
echo "  1) edit .env and set ANTHROPIC_API_KEY"
echo "  2) test one pair:  source .venv/bin/activate && python seed.py --pair magnesium,sleep_quality --dry-run"
