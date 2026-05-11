# Claude Handoff: Track 9 Complete

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to inspect:
- `feat/codex-seed-batch-11`

Payload completion commit:
- `9816f5f` - `Track 9: 150/150 — pregnancy and infancy outcomes`

## Status

Track 9 is fully complete on `feat/codex-seed-batch-11`.

Completed scope versus `origin/main`:
- `150` new payload files under `data/seed_payloads`
- all manifest pairs from `CODEX_BRIEF_V11_AUTONOMOUS.md` are covered
- topic split is `30` pairs each for cancer screening, drug specifics, cardiovascular subtypes, sleep apnea subtypes, and endocrine deep dive

Latest known clean state:
- `python3 seed_from_payloads.py validate --verify` -> `1520 ok, 0 failed, 1520 total`
- `python3 seed_from_payloads.py ingest --dry-run` -> `errors: []`

## What Claude should ingest

Use this branch as the authoritative finished Track 9 seed set.

Main content to ingest:
- every file in `data/seed_payloads` that exists on `feat/codex-seed-batch-11` but not on `origin/main`

Quick way to confirm the count locally:

```bash
git diff --name-only origin/main...feat/codex-seed-batch-11 -- data/seed_payloads | wc -l
```

Expected result:

```text
150
```

## Validation and quality rules used

These rules were enforced throughout the batch and still matter if you continue adjacent work:

- Do not run `seed.py`
- Do not run `adjudicate.py`
- Never fabricate PMIDs
- Every `meta_analysis`, `systematic_review`, `rct`, `cohort`, `case_control`, and `cross_sectional` evidence row must include `n_participants`
- Include `effect_quant` whenever the cited source reports a pooled estimate
- Keep `python3 seed_from_payloads.py validate <path> --verify` passing
- Keep `python3 seed_from_payloads.py ingest --dry-run` clean
- Do not stage or remove `data/health.db`

## Track 9 branch summary

- `150` payloads differ versus `origin/main`
- `150` payload edges include an edge-level `effect_quant`
- `0` payload edges use `direction: "contested"` on this branch
- `287` `new_entities` blocks were introduced across the branch

Five random verification rows from the finished branch:

- `light_therapy_advanced_sleep_phase__sleep_timing.json` - `light_therapy_advanced_sleep_phase` -> `sleep_timing` - PMID `15602801` - `2003` - `PalmerCR et al 2003 Behav Sleep Med`
- `orlistat_pcos__metabolic_outcomes.json` - `orlistat_pcos` -> `metabolic_outcomes` - PMID `21484319` - `2011` - `KumarP et al 2011 Reprod Biomed Online`
- `inositol_pcos_ovulation__ovulation_rate.json` - `inositol_pcos_ovulation` -> `ovulation_rate` - PMID `31298405` - `2019` - `NordioM et al 2019 Int J Endocrinol`
- `flexible_sigmoidoscopy__colorectal_cancer_mortality.json` - `flexible_sigmoidoscopy` -> `colorectal_cancer_mortality` - PMID `27133893` - `2016` - `Fitzpatrick-Lewis D et al 2016 Clin Colorectal Cancer`
- `colonoscopy_screening_50_75__colorectal_cancer_mortality.json` - `colonoscopy_screening_50_75` -> `colorectal_cancer_mortality` - PMID `31578199` - `2019` - `Jodal HC et al 2019 BMJ Open`

## Final batch added at 150/150

These five files were added in the completion commit:

- `data/seed_payloads/ssri_during_pregnancy__child_outcomes.json`
- `data/seed_payloads/valproate_during_pregnancy__child_neurodevelopment.json`
- `data/seed_payloads/lithium_during_pregnancy__cardiac_anomaly_offspring.json`
- `data/seed_payloads/lamotrigine_during_pregnancy__child_outcomes.json`
- `data/seed_payloads/acid_suppression_in_infancy__allergy_risk_later.json`

## Commands to verify locally

From repo root:

```bash
git checkout feat/codex-seed-batch-11
python3 seed_from_payloads.py validate --verify
python3 seed_from_payloads.py ingest --dry-run
```

Validate one file:

```bash
python3 seed_from_payloads.py validate data/seed_payloads/<file>.json --verify
```

## Paste-ready prompt for Claude

```text
Inspect https://github.com/prokesmic/HealthUniverse on branch feat/codex-seed-batch-11.

Read CLAUDE_TRACK_HANDOFF.md first.

Treat feat/codex-seed-batch-11 as the authoritative completed Track 9 branch.
Ingest all 150 payload files added under data/seed_payloads versus origin/main.

Important constraints that governed this branch:
- do not run seed.py
- do not run adjudicate.py
- never fabricate PMIDs
- every meta-analysis/systematic-review/RCT/cohort/case-control/cross-sectional row needs n_participants
- include effect_quant whenever the cited source reports a pooled estimate
- data/health.db is scratch and should be ignored

Payload completion commit: 9816f5f
Expected diff count versus main under data/seed_payloads: 150
Latest validator state: python3 seed_from_payloads.py validate --verify -> 1520 ok, 0 failed, 1520 total
Latest dry-run state: python3 seed_from_payloads.py ingest --dry-run -> errors: []
```
