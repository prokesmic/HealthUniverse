#!/usr/bin/env python3
"""Generate a Codex/Claude seeding brief from the breakthroughs orphan queue.

Writes a timestamped markdown file under `briefs/`. Designed to run after
`scripts/breakthroughs_daily.py` so each day's fresh orphans become a batch
of seed instructions Codex can pick up.

Usage:
  python scripts/orphans_to_brief.py
  python scripts/orphans_to_brief.py --min-strength 0.7
  python scripts/orphans_to_brief.py --stdout         # dump to stdout instead
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.orphan_brief import build_brief, write_brief   # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-strength", type=float, default=0.6,
                    help="reject orphans below this strength (default 0.6)")
    ap.add_argument("--stdout", action="store_true",
                    help="print to stdout instead of writing to briefs/")
    args = ap.parse_args(argv)

    if args.stdout:
        md, _ = build_brief(min_strength=args.min_strength)
        sys.stdout.write(md)
        return 0

    out = write_brief(min_strength=args.min_strength)
    md, meta = build_brief(min_strength=args.min_strength)
    print(f"→ wrote {out}  ({meta['n']} candidates across {len(meta['categories'])} categories)")
    for c in meta["categories"]:
        print(f"    • {c['slug']}: {c['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
