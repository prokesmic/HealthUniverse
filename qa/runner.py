"""QA orchestrator.

Usage:
  python qa/runner.py                       # all personas, all scenarios, all reviewers
  python qa/runner.py --persona P1_biohacker --scenarios stack_brief,claim_check
  python qa/runner.py --reviewers medical,evidence

Output: qa/reports/<DATE>.md with severity-tiered findings.

Cost:
  ~ N_personas × N_scenarios × N_reviewers Claude calls.
  At default (5 × 8 × 5 = 200 calls × ~$0.005 = $1) per full sweep.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from qa.reviewers import REVIEWERS, review                      # noqa: E402
from qa.scenarios import SCENARIOS                              # noqa: E402
from fastapi.testclient import TestClient                       # noqa: E402


def load_personas() -> list[dict]:
    p = ROOT / "qa" / "personas.json"
    return json.loads(p.read_text())["personas"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--persona", default="all",
                    help='Comma-list of persona IDs or "all" (default).')
    ap.add_argument("--scenarios", default="all",
                    help='Comma-list of scenario names or "all".')
    ap.add_argument("--reviewers", default="all",
                    help='Comma-list of reviewer names or "all".')
    ap.add_argument("--limit-personas", type=int, default=0,
                    help="Cap the number of personas (for cost control).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Run scenarios but skip reviewer Claude calls.")
    args = ap.parse_args()

    personas = load_personas()
    if args.persona != "all":
        wanted = set(args.persona.split(","))
        personas = [p for p in personas if p["id"] in wanted]
    if args.limit_personas:
        personas = personas[:args.limit_personas]
    scenarios = list(SCENARIOS.keys()) if args.scenarios == "all" \
                else [s.strip() for s in args.scenarios.split(",")]
    reviewers = list(REVIEWERS.keys()) if args.reviewers == "all" \
                else [r.strip() for r in args.reviewers.split(",")]

    print(f"[qa] personas={len(personas)} scenarios={len(scenarios)} reviewers={len(reviewers)} dry_run={args.dry_run}")

    # Boot the app once and reuse the client.
    from web.app import app                                     # noqa: E402
    client = TestClient(app)

    all_findings: list[dict] = []
    transcript_count = 0
    review_count = 0
    t0 = time.time()

    for persona in personas:
        for scenario_name in scenarios:
            fn = SCENARIOS.get(scenario_name)
            if not fn:
                print(f"  ! unknown scenario {scenario_name}")
                continue
            print(f"[run] {persona['id']:<35} × {scenario_name:<18}", end=" ", flush=True)
            try:
                events = fn(persona, client)
                transcript_count += 1
            except Exception as exc:
                print(f"SCENARIO_FAILED: {exc}")
                all_findings.append({
                    "severity": "P0", "category": "technical",
                    "reviewer": "harness",
                    "persona": persona["id"], "scenario": scenario_name,
                    "headline": "scenario raised an exception",
                    "evidence": str(exc)[:300],
                    "suggestion": "Investigate the failing endpoint or test driver.",
                })
                continue
            print(f"({len(events)} events)", end=" ", flush=True)

            if args.dry_run:
                print()
                continue

            for reviewer_name in reviewers:
                try:
                    fs = review(reviewer_name, persona, scenario_name, events)
                    review_count += 1
                    if fs:
                        all_findings.extend(fs)
                except Exception as exc:
                    print(f"\n  ! reviewer {reviewer_name} failed: {exc}")
            print(f"-> {len([f for f in all_findings if f['persona']==persona['id'] and f['scenario']==scenario_name])} findings")

    dt = time.time() - t0
    print(f"\n[qa] done in {dt:.1f}s · transcripts={transcript_count} reviews={review_count} findings={len(all_findings)}")

    write_report(personas, scenarios, reviewers, all_findings, dt)


def write_report(personas: list[dict], scenarios: list[str], reviewers: list[str],
                 findings: list[dict], elapsed_s: float) -> None:
    out_dir = ROOT / "qa" / "reports"
    out_dir.mkdir(exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = out_dir / f"{date}.md"

    by_sev = defaultdict(list)
    for f in findings:
        by_sev[f.get("severity", "P3")].append(f)

    sev_counts = Counter(f.get("severity", "P3") for f in findings)
    cat_counts = Counter(f.get("category", "?") for f in findings)
    rev_counts = Counter(f.get("reviewer", "?") for f in findings)
    pers_counts = Counter(f.get("persona", "?") for f in findings)

    lines = []
    lines.append(f"# Health Universe — QA sweep")
    lines.append(f"_Generated {datetime.now().isoformat(timespec='minutes')} · "
                 f"elapsed {elapsed_s:.0f}s_\n")
    lines.append(f"**Coverage:** {len(personas)} personas × {len(scenarios)} scenarios "
                 f"× {len(reviewers)} reviewers = {len(personas)*len(scenarios)*len(reviewers)} review passes.\n")
    lines.append(f"**Total findings:** {len(findings)}\n")

    lines.append("## By severity")
    for sev in ("P0", "P1", "P2", "P3"):
        lines.append(f"- **{sev}**: {sev_counts.get(sev, 0)}")
    lines.append("")

    lines.append("## By category")
    for cat, n in cat_counts.most_common():
        lines.append(f"- **{cat}**: {n}")
    lines.append("")

    lines.append("## By reviewer")
    for rev, n in rev_counts.most_common():
        lines.append(f"- **{rev}**: {n}")
    lines.append("")

    lines.append("## By persona (highest-volume issues hit which personas)")
    for p, n in pers_counts.most_common():
        lines.append(f"- **{p}**: {n}")
    lines.append("")

    for sev in ("P0", "P1", "P2", "P3"):
        bucket = by_sev.get(sev, [])
        if not bucket: continue
        lines.append(f"\n---\n## {sev} — {len(bucket)} finding{'s' if len(bucket)!=1 else ''}\n")
        for f in bucket:
            lines.append(f"### `{f.get('persona')}` · `{f.get('scenario')}` · `{f.get('reviewer')}`")
            lines.append(f"**{f.get('headline','(no headline)')}**\n")
            ev = (f.get('evidence') or "").replace("\n", " ")[:400]
            lines.append(f"_Evidence:_ {ev}\n")
            lines.append(f"_Suggested fix:_ {f.get('suggestion','(no suggestion)')}\n")

    if not findings:
        lines.append("\n_No findings. Either everything is great, or the reviewers were too lenient — re-run with broader scope._\n")

    path.write_text("\n".join(lines))
    print(f"[qa] report → {path}")
    # Also write a machine-readable JSON copy alongside.
    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "elapsed_seconds": elapsed_s,
        "findings": findings,
    }, indent=2))


if __name__ == "__main__":
    main()
