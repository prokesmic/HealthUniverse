# Codex brief: massively densify the evidence corpus

> **Two parallel tracks. Pick either or both. Each is its own PR.**
>
> Track A — **DENSIFY**: add 3–5 more PMID-verified evidence rows to ~350
> existing edges that are currently thin. Goal: +1,500 evidence rows.
>
> Track B — **EXPAND**: produce another ~250 new pairs from the v4 topic
> areas that are still uncovered (sports, occupational, paeds immunity,
> geriatric polypharmacy, dermatology, women's repro endo, ophthalmology,
> hematology, cancer prevention, misc — see `CODEX_BRIEF_V4.md` §A).

Repo: https://github.com/prokesmic/HealthUniverse — branch from `main`.

Read first:
- `AGENTS.md`
- `CODEX_BRIEF_500_V2.md` — the JSON shape and `--verify` validator (still
  the contract)
- `CODEX_BRIEF_V4.md` §A — the v4 topic list

---

## Why this exists

Right now we have **~764 edges** with **~3,500 evidence rows** = an
average of ~4.6 rows per edge. Many tier-B and tier-C edges sit at 3
rows. With 4–6 more high-quality citations each, several would promote
to tier-A; many tier-Cs would promote to tier-B.

We've added a **densify mode** to the existing payload validator and
ingester that:

- Lets you submit additional evidence rows to an existing edge **without**
  overwriting its summary, mechanism, caveats, tier, or direction.
- Auto-dedupes incoming evidence by PMID — if you submit a PMID we already
  have, it's silently skipped.
- Drops the "≥3 evidence rows" minimum and the summary/mechanism length
  floors (they're not needed when only adding rows).

You opt in via `"mode": "densify"` at the top level of any payload file.

---

## Track A — Densify ~350 thin edges

### Branch

`feat/codex-densify-batch-1`

### Target list

The repo includes **`docs/densify_targets.json`** — the 350 edges
currently most worth densifying, ranked by tier (A first, then B, then X,
then C). Each entry has `id`, `tier`, `direction`, `f_slug`, `o_slug`,
`population`, and current `n_rows`.

```json
[
  { "id": 12, "tier": "B", "direction": "mixed",
    "f_slug": "omega3", "o_slug": "cvd",
    "population": "general adult", "n_rows": 6 },
  ...
]
```

Aim for **~5 new evidence rows per edge** (range 3–7 depending on what
exists in the literature). At 350 × 5 = 1,750 new rows.

### Payload format (densify)

One file per edge, named `{factor_slug}__{outcome_slug}__densify.json` to
distinguish from v2/v3/v4 batches:

```json
{
  "schema_version": 1,
  "mode": "densify",
  "edges": [
    {
      "factor_slug":  "omega3",
      "outcome_slug": "cvd",
      "population":   "general adult",
      "evidence": [
        {
          "citation":      "Hu Y et al 2019 J Am Heart Assoc",
          "pmid":          "31537432",
          "doi":           "10.1161/JAHA.119.013543",
          "year":          2019,
          "study_type":    "meta_analysis",
          "n_participants": 127477,
          "direction":     "protective",
          "quality":       "high",
          "notes":         "Pooled 13 RCTs; ω-3 reduced MI by 8% and total CHD by 5% with dose-response."
        }
      ]
    }
  ]
}
```

### What's required per evidence row

Same as v2/v3/v4 — every stat-quantitative row (`meta_analysis`,
`systematic_review`, `rct`, `cohort`, `case_control`, `cross_sectional`)
must include a real PMID and `n_participants`. Mechanistic / animal /
case_report / expert_opinion don't need PMIDs but still need real refs.

### What's NOT required in densify mode

- `direction`, `tier`, `summary`, `mechanism`, `caveats`, `effect_size`,
  `effect_quant` are all ignored if you include them. We don't touch
  what's already on the edge.
- The "≥3 evidence rows per file" floor is dropped — you can submit a
  single strong meta-analysis if that's the most useful addition.

### Quality bar

- **Don't fabricate PMIDs.** The validator hits PubMed and rejects
  unresolvable PMIDs and title mismatches. Same as v2/v3.
- **Don't pad with low-quality rows.** A single new tier-A meta-analysis
  is worth more than three weak cross-sectionals.
- **Diversify research groups.** If we already have 3 papers from one lab
  on an edge, add rows from different labs.
- **Recency matters.** Prioritise post-2018 evidence; older studies are
  fine if they're seminal.

### Submission

```bash
git checkout -b feat/codex-densify-batch-1
./setup.sh
source .venv/bin/activate
python seed_from_payloads.py validate --verify   # MUST end "0 failed"
python seed_from_payloads.py ingest --dry-run    # confirms slugs resolve
git add data/seed_payloads/
git commit -m "Densify ~350 thin edges with PMID-verified evidence"
git push -u origin feat/codex-densify-batch-1
gh pr create --title "Densify ~350 thin edges (≈1,500 new evidence rows)"
```

PR description must include:
- Full `--verify` transcript ending "0 failed"
- 5 random `(edge_id, factor, outcome, new_PMID, year, journal)` rows
- A breakdown: how many edges densified, total new rows added, edges that
  could likely promote tier (your judgement; the owner re-tiers).

---

## Track B — Expand: 250 more new pairs from v4 topics

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

Same `validate --verify` gate. PR title:
`Codex seed batch v5 — 250 pairs in v4 topic areas`.

---

## What the validator now accepts

| Field | Replace mode | Densify mode |
|---|---|---|
| `mode` | omit (default) | required `"densify"` |
| Edge `direction`, `tier`, `summary`, `mechanism` | required | ignored |
| Evidence min rows | ≥3 | ≥1 |
| `pmid` on stat-quantitative rows | required | required |
| `n_participants` on stat-quantitative rows | required | required |
| `new_entities` block | allowed | rejected |
| Existing edge | created or updated | must exist |

Both modes coexist in the same `data/seed_payloads/` directory.

---

## Hard rules — same as v2

- Never fabricate PMIDs (the `--verify` check catches it)
- Never call our paid Claude paths (`seed.py`, `adjudicate.py`)
- Never modify schema, the cost cap, or anything in the `AGENTS.md`
  "Avoid" list
- One PR per track, branched from `main`, never push to `main` directly
- Don't merge

---

## Suggested order

1. **Track A first** (densify) — bigger immediate quality lift, no new
   topics to research, same JSON shape you already know
2. **Track B second** (expand) — broadens coverage but adds dependency
   on the v4 topic-area research

Both can land in either order. Both should be separate PRs.

---

## What "massive" looks like

Best case across both tracks:
- ~1,750 new evidence rows from densify (Track A)
- ~1,500 new evidence rows from 250 new pairs × 6 rows avg (Track B)
- **Total: roughly +3,250 evidence rows on top of today's ~3,500.**
- ~30–60 tier promotions from densified edges crossing thresholds (tier A
  needs ≥2 high-quality meta-analyses + score ≥12)

Honest expectation: real PMID research is ~15–25 minutes per row of
careful work. Don't promise a timeline you can't keep — the quality bar
is more important than the count.
