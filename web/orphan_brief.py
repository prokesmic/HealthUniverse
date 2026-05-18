"""Turn the orphan-breakthroughs queue into a Codex/Claude seeding brief.

The breakthroughs feed surfaces clinical readouts and guideline shifts faster
than our human-curated corpus can absorb them. Orphans — items that didn't
match a corpus edge by (factor_slug, outcome_slug) lookup — are exactly the
gaps to close. This module turns that queue into a structured markdown brief
Codex (or Claude) can act on.

Design intent:
  • One file per run — versioned by ISO date, lands in `briefs/`.
  • Grouped by category so a batch run can ship by topic.
  • Each orphan becomes a self-contained "seed instruction" with the factor,
    outcome, source URL, plausible PMID hint, and a starter direction.
  • Recalls are excluded (they're not edges — they're safety events).
  • Anything already-matched on re-check is skipped so reruns are idempotent.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from web import breakthroughs as bx

ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = ROOT / "briefs"


# ─── Filtering ─────────────────────────────────────────────────────

def candidate_orphans(min_strength: float = 0.6) -> list[dict]:
    """Orphans worth seeding. Excludes recalls (not edges) and low-strength.
    Re-checks corpus on read so freshly-seeded edges drop out automatically."""
    out: list[dict] = []
    for o in bx.orphans():
        if o.get("stage") == "recall":
            continue
        if float(o.get("strength", 0)) < min_strength:
            continue
        if not o.get("factor_slug") or not o.get("outcome_slug"):
            continue
        # Live re-check — corpus may have grown since the feed last ran.
        if bx.match_corpus(o.get("factor_slug"), o.get("outcome_slug")):
            continue
        out.append(o)
    # Highest strength + freshest first
    out.sort(key=lambda r: (-float(r.get("strength", 0)), r.get("published_at", "")), reverse=False)
    out.sort(key=lambda r: (-float(r.get("strength", 0)), r.get("published_at", "")))
    return out


def _by_category(orphans: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for o in orphans:
        groups.setdefault(o.get("category", "other"), []).append(o)
    # Order by feed taxonomy
    return {c: groups[c] for c in bx.CATEGORY_ORDER if c in groups}


# ─── Markdown generation ───────────────────────────────────────────

_HEADER = """# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** {generated}
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** {n_total} across {n_cats} categories
**Strength threshold:** ≥ {min_strength}

## How to use

Each block below is a single edge to seed. For each one:

1. **Research the factor → outcome relationship** using PubMed + the linked
   source. Don't trust the headline — pull the underlying study/trial.
2. **Grade the evidence tier** per our methodology (A=meta-analysis or
   multiple RCTs converging, B=single registrational RCT or strong cohort,
   C=Phase 1/2 or emerging, D=limited/preclinical-only, X=contested).
3. **Write the edge payload** in the standard seed schema (factor entity,
   outcome entity, edge object with direction/tier/summary/effect_size,
   and ≥3 evidence rows with PMIDs).
4. **Match the existing entity slugs** if the factor or outcome already
   exists; only mint a new entity if there's no match.
5. **Include the breakthrough id** in the edge's `provenance` field so we
   can close the loop: `provenance: {{ "breakthrough_id": "br_..." }}`

Acceptance criteria:
- ≥ 3 PMID-verified evidence rows per edge.
- Tier rationale documented in the edge `tier_reason` field.
- Direction is one of: protective / harmful / mixed / u_shaped / neutral.
- Effect size is one of: small / moderate / large / trivial / unknown.
- If the source readout is a single trial, prefer tier B with a note that
  replication is pending; do not over-grade.

---

"""

_CATEGORY_HEADER = "\n## {label}  ·  {n} candidate{s}\n"

_ORPHAN_TMPL = """### {n}. {headline}

| Field | Value |
|---|---|
| **Breakthrough ID** | `{id}` |
| **Stage** | {stage_label} |
| **Published** | {published} ({days}d ago) |
| **Strength** | {strength_pct}% |
| **Source** | [{source_name}]({source_url}) |
| **Suggested `factor.slug`** | `{factor_slug}` |
| **Suggested `outcome.slug`** | `{outcome_slug}` |

**Summary.** {summary}

{why_block}**Seed direction.** Search PubMed for `{factor_slug} {outcome_slug}` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. {trial_hint}

**Provenance tag.** `provenance.breakthrough_id = "{id}"`

---

"""


def build_brief(min_strength: float = 0.6) -> tuple[str, dict]:
    """Generate the brief markdown. Returns (markdown, meta)."""
    orphans = candidate_orphans(min_strength=min_strength)
    groups = _by_category(orphans)

    md = _HEADER.format(
        generated=date.today().isoformat(),
        n_total=len(orphans),
        n_cats=len(groups),
        min_strength=min_strength,
    )

    if not orphans:
        md += "\n_No orphans above threshold. Corpus is current._\n"
        return md, {"n": 0, "categories": []}

    n = 0
    for cat, rows in groups.items():
        md += _CATEGORY_HEADER.format(
            label=bx.CATEGORY_LABEL.get(cat, cat),
            n=len(rows),
            s="" if len(rows) == 1 else "s",
        )
        for o in rows:
            n += 1
            why_block = ""
            if o.get("why_it_matters"):
                why_block = f"**Why it matters.** {o['why_it_matters']}\n\n"
            trial_hint = ""
            if o.get("stage") in ("phase3", "phase2"):
                trial_hint = "Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions."
            elif o.get("stage") == "guideline":
                trial_hint = "Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials."
            elif o.get("stage") == "approved":
                trial_hint = "Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data."
            md += _ORPHAN_TMPL.format(
                n=n,
                headline=o.get("headline", "—"),
                id=o.get("id", ""),
                stage_label=bx.STAGE_LABEL.get(o.get("stage", ""), o.get("stage", "")),
                published=o.get("published_at", ""),
                days=bx.days_ago(o.get("published_at", "")),
                strength_pct=int(round(float(o.get("strength", 0)) * 100)),
                source_name=o.get("source_name", ""),
                source_url=o.get("source_url", ""),
                factor_slug=o.get("factor_slug", ""),
                outcome_slug=o.get("outcome_slug", ""),
                summary=o.get("summary", ""),
                why_block=why_block,
                trial_hint=trial_hint,
            )

    meta = {
        "n": len(orphans),
        "categories": [{"slug": c, "n": len(r)} for c, r in groups.items()],
        "generated_at": date.today().isoformat(),
    }
    return md, meta


def write_brief(min_strength: float = 0.6) -> Path:
    md, meta = build_brief(min_strength=min_strength)
    BRIEFS_DIR.mkdir(exist_ok=True)
    out = BRIEFS_DIR / f"codex_orphans_{date.today().isoformat()}.md"
    out.write_text(md)
    return out
