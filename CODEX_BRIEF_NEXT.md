# Codex brief: continue corpus growth (next batch)

> Track A (`feat/codex-densify-batch-1`) is merged. Thank you — that landed
> ~1,045 new PMID-verified evidence rows.
>
> This brief outlines two **parallel** continuation tracks. Pick either or
> both; each is its own PR. They do not conflict.

Repo: https://github.com/prokesmic/HealthUniverse — branch from `main`.

Read first:
- `AGENTS.md`
- `CODEX_BRIEF_500_V2.md` — the JSON shape and `--verify` validator (still
  the contract; nothing has changed)
- `CODEX_BRIEF_DENSIFY.md` — densify-mode rules
- `CODEX_BRIEF_V4.md` §A — the v4 topic list (Track 2 source)

---

## Why this exists

Densify v1 promoted ~30 edges and lifted average rows-per-edge from 4.6
to ~6.0. Two natural next pushes:

- **Track 1 — DENSIFY v2**: there are still ~250 thin edges sitting at
  3–4 rows that could promote tier with one more high-quality
  meta-analysis. That's why this is "the next 250", not a repeat of the
  same 350.
- **Track 2 — EXPAND**: produce ~250 new pairs in the v4 topic areas
  that are still uncovered (§A of `CODEX_BRIEF_V4.md`). This is the
  same Track B that was deferred when Track A took priority.

---

## Track 1 — Densify v2 (next 250 thin edges)

### Branch

`feat/codex-densify-batch-2`

### Target list

The repo includes **`docs/densify_targets_v2.json`** — the next 250 edges
ranked by tier-promotion potential, *excluding* anything you already
densified in batch 1 (the validator de-dupes by PMID anyway, but skipping
already-saturated edges saves time).

If `densify_targets_v2.json` doesn't exist when you start, regenerate it
with:

```bash
python -c "
import json, sqlite3
conn = sqlite3.connect('data/healthuniverse.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('''
  SELECT e.id, e.tier, e.direction,
         f.slug AS f_slug, o.slug AS o_slug,
         e.population, COUNT(ev.id) AS n_rows
  FROM edge e
  JOIN entity f ON e.factor_id=f.id
  JOIN entity o ON e.outcome_id=o.id
  LEFT JOIN evidence ev ON ev.edge_id=e.id
  WHERE e.tier IN ('B','C','X')
  GROUP BY e.id
  HAVING n_rows BETWEEN 3 AND 5
  ORDER BY CASE e.tier WHEN 'B' THEN 1 WHEN 'C' THEN 2 ELSE 3 END,
           n_rows ASC,
           e.updated_at DESC
  LIMIT 250
''').fetchall()
print(json.dumps([dict(r) for r in rows], indent=2))" > docs/densify_targets_v2.json
```

Aim for **~5 new evidence rows per edge** (range 3–7). At 250 × 5 = 1,250
new rows.

### Payload format

Identical to densify v1 — see `CODEX_BRIEF_DENSIFY.md`. One file per edge,
named `{factor_slug}__{outcome_slug}__densify_v2.json`:

```json
{
  "schema_version": 1,
  "mode": "densify",
  "edges": [
    {
      "factor_slug":  "factor-slug",
      "outcome_slug": "outcome-slug",
      "population":   "general adult",
      "evidence": [ /* ≥1 PMID-verified rows */ ]
    }
  ]
}
```

### NEW priority field — capture effect size where you can

We're surfacing effect sizes on the UI. If the source paper reports a
clear pooled estimate, please include a structured `effect_quant`:

```json
{
  "citation": "Hu Y et al 2019 J Am Heart Assoc",
  "pmid": "31537432",
  "year": 2019,
  "study_type": "meta_analysis",
  "n_participants": 127477,
  "direction": "protective",
  "quality": "high",
  "effect_quant": {
    "metric": "RR",                    /* RR | HR | OR | SMD | MD */
    "value": 0.95,
    "ci_low": 0.92,
    "ci_high": 0.98,
    "comparator": "placebo",
    "dose_range": "1–4 g/day EPA+DHA"  /* optional, free-text */
  },
  "notes": "Pooled 13 RCTs; ω-3 reduced MI by 8% and total CHD by 5%."
}
```

`effect_quant` is **optional** and gracefully skipped if the paper is
mechanistic / case-report / animal. The validator does not require it.
But for any meta-analysis or RCT you cite, including it is high-value.

### Quality bar

Same as v1:
- No fabricated PMIDs (validator hits PubMed and rejects)
- No padding with weak rows
- Diversify research groups
- Prioritise post-2018 unless it's a seminal trial
- Single strong meta-analysis > three weak cross-sectionals

### Submission

```bash
git checkout -b feat/codex-densify-batch-2
./setup.sh && source .venv/bin/activate
python seed_from_payloads.py validate --verify   # MUST end "0 failed"
python seed_from_payloads.py ingest --dry-run    # confirm slugs resolve
git add data/seed_payloads/
git commit -m "Densify v2: next 250 thin edges with PMID-verified evidence"
git push -u origin feat/codex-densify-batch-2
gh pr create --title "Densify v2 — ≈1,250 new PMID-verified rows on next 250 thin edges"
```

PR description must include:
- Full `--verify` transcript ending "0 failed"
- 5 random `(edge_id, factor, outcome, new_PMID, year, journal)` rows
- A breakdown: edges densified, rows added, edges that should re-tier
- (NEW) How many of your rows include `effect_quant`

---

## Track 2 — Expand: 250 new pairs in v4 topic areas

### Branch

`feat/codex-seed-batch-5`

### Scope

Same as `CODEX_BRIEF_V4.md` §A — produce ~250 new payloads in `replace`
mode (default; what v2/v3/v4 used) covering the 11 v4 topic areas:

1. Sports & performance nutrition (25)
2. Occupational medicine (25)
3. Gut-brain axis specifics (25)
4. Paediatric immunology + early-life programming (20)
5. Geriatric polypharmacy (20)
6. Dermatology (20)
7. Women's reproductive endocrinology beyond menopause (15)
8. Ophthalmology beyond AMD/cataracts (15)
9. Hematology / nutrition crossover (15)
10. Specific cancer prevention through diet (15)
11. Misc + underrepresented (15)

Each pair = ≥3 PMID-verified evidence rows. Same v2 schema, no `mode`
field (or `"mode": "replace"` explicitly).

### Same NEW priority — effect_quant

Whenever the cited paper reports a clear effect size, include the
`effect_quant` block (see Track 1 above). Especially valuable on RCTs
and meta-analyses.

### Quality bar / submission

Identical to v4. PR title:
`Codex seed batch v5 — 250 pairs in v4 topic areas`

---

## Hard rules — same as always

- Never fabricate PMIDs (the `--verify` check catches it)
- Never call our paid Claude paths (`seed.py`, `adjudicate.py`)
- Never modify schema, the cost cap, or anything in the `AGENTS.md`
  "Avoid" list
- One PR per track, branched from `main`
- Don't merge — PRs go to the owner

---

## Suggested order

1. **Track 1 first** (densify v2) — same JSON shape, deepest leverage on
   tier promotions
2. **Track 2 second** (expand) — broadens coverage but adds dependency
   on the v4 topic-area research

Either order is fine. Both are independent PRs.

---

## What "good" looks like

Best case across both tracks:
- ~1,250 new evidence rows from Track 1
- ~1,500 new rows from Track 2 (250 × 6 avg)
- **Total: roughly +2,750 evidence rows on top of today's ~4,500.**
- ~20–40 tier promotions
- Hundreds of edges with structured `effect_quant` so the UI can show
  "−25% RR (0.71–0.79)" instead of just "Beneficial"

Honest expectation: real PMID research is ~15–25 minutes per row of
careful work. Quality bar > count.
