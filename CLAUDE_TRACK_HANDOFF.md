# Claude Handoff: Track 6 Complete

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to inspect:
- `feat/codex-seed-batch-8`

Latest completion commit:
- `25b2b57` — `Track 6: 150/150 — reflux, hair, gut-barrier, and evidence-gap finale`

## Status

Track 6 is fully complete on `feat/codex-seed-batch-8`.

Completed scope versus `origin/main`:
- `150` new payload files under `data/seed_payloads`
- all `150/150` manifest pairs from `CODEX_BRIEF_V8_AUTONOMOUS.md` are covered
- topic coverage is balanced at `30` pairs each across blocks `A` through `E`

Latest known clean state:
- `python3 seed_from_payloads.py --verify validate` -> `1520 ok, 0 failed, 1520 total`
- `python3 seed_from_payloads.py ingest --dry-run` -> `errors: []`

## What Claude should ingest

Use this branch as the authoritative finished Track 6 seed set.

Main content to ingest:
- every file in `data/seed_payloads` that exists on `feat/codex-seed-batch-8` but not on `origin/main`

Quick way to confirm the count locally:

```bash
git diff --name-only origin/main...feat/codex-seed-batch-8 -- data/seed_payloads | wc -l
```

Expected result:

```text
150
```

## Validation and quality rules used

These rules were enforced throughout the batch and remain important if you continue adjacent work:

- Do not run `seed.py`
- Do not run `adjudicate.py`
- Never fabricate PMIDs
- Every `meta_analysis`, `systematic_review`, `rct`, `cohort`, `case_control`, and `cross_sectional` evidence row includes `n_participants`
- Include `effect_quant` whenever the source paper reports a pooled estimate
- Keep `python3 seed_from_payloads.py --verify validate` passing
- Keep `python3 seed_from_payloads.py ingest --dry-run` clean
- Do not stage or remove `data/health.db`

## Useful validator quirks

- Citation first token cannot look like a single-letter placeholder
- `umbrella_review` is not a valid `study_type`; use `systematic_review`
- If a factor is rejected by the validator path but is intentionally new for the edge, declaring it in `new_entities` is acceptable
- Performance-style or process-style outcomes often fit best with `direction: "protective"` and entity `kind: "process"`

## Final batch added at 150/150

These ten files were added in the completion commit:

- `data/seed_payloads/betaine_hcl_supplementation__hypochlorhydria_symptoms.json`
- `data/seed_payloads/dairy_elimination__eczema_severity_children.json`
- `data/seed_payloads/dgl_licorice__reflux_symptoms.json`
- `data/seed_payloads/digestive_enzymes_pancreatic__bloating_chronic_dyspepsia.json`
- `data/seed_payloads/fadogia_agrestis__testosterone_humans.json`
- `data/seed_payloads/intestinal_alkaline_phosphatase_oral__endotoxaemia.json`
- `data/seed_payloads/lactobacillus_reuteri_breastfed__maternal_iron_status.json`
- `data/seed_payloads/oral_marine_collagen_with_vitamins__hair_density_in_thinning_women.json`
- `data/seed_payloads/slippery_elm_marshmallow_root__reflux_symptoms.json`
- `data/seed_payloads/topical_caffeine__hair_shaft_thickness.json`

## Commands to verify locally

From repo root:

```bash
git checkout feat/codex-seed-batch-8
python3 seed_from_payloads.py --verify validate
python3 seed_from_payloads.py ingest --dry-run
```

Validate one file:

```bash
python3 seed_from_payloads.py --verify validate data/seed_payloads/<file>.json
```

## Paste-ready prompt for Claude

```text
Inspect https://github.com/prokesmic/HealthUniverse on branch feat/codex-seed-batch-8.

Read CLAUDE_TRACK_HANDOFF.md first.

Treat feat/codex-seed-batch-8 as the authoritative completed Track 6 branch.
Ingest all 150 payload files added under data/seed_payloads versus origin/main.

Important constraints that governed this branch:
- do not run seed.py
- do not run adjudicate.py
- never fabricate PMIDs
- every meta-analysis/systematic-review/RCT/cohort/case-control/cross-sectional row needs n_participants
- include effect_quant whenever the cited source reports a pooled estimate
- data/health.db is scratch and should be ignored

Latest completion commit: 25b2b57
Expected diff count versus main under data/seed_payloads: 150
Latest validator state: python3 seed_from_payloads.py --verify validate -> 1520 ok, 0 failed, 1520 total
Latest dry-run state: python3 seed_from_payloads.py ingest --dry-run -> errors: []
```
