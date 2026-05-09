# Claude Handoff: Track 5 Complete

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to inspect:
- `feat/codex-seed-batch-7`

Latest completion commit:
- `a6a1eed` — `Track 5: 150/150 — maternal programming and ACE burden finale`

## Status

Track 5 is fully complete on `feat/codex-seed-batch-7`.

Completed scope versus `origin/main`:
- `150` new payload files under `data/seed_payloads`
- all manifest pairs from `CODEX_BRIEF_V6_AUTONOMOUS.md` are covered

Latest known clean state:
- per-file PMID verification was run for every newly added payload
- `python3 seed_from_payloads.py ingest --dry-run` -> `errors: []`

## What Claude should ingest

Use this branch as the authoritative finished Track 5 seed set.

Main content to ingest:
- every file in `data/seed_payloads` that exists on `feat/codex-seed-batch-7` but not on `origin/main`

Quick way to confirm the count locally:

```bash
git diff --name-only origin/main...feat/codex-seed-batch-7 -- data/seed_payloads | wc -l
```

Expected result:

```text
150
```

## Validation and quality rules used

These rules were enforced throughout the batch and are important context if you continue adjacent work:

- Do not run `seed.py`
- Do not run `adjudicate.py`
- Never fabricate PMIDs
- Every `meta_analysis`, `systematic_review`, `rct`, `cohort`, `case_control`, and `cross_sectional` evidence row must include `n_participants`
- Include `effect_quant` whenever the source paper reports a pooled estimate
- Keep `python3 seed_from_payloads.py validate <path> --verify` passing
- Keep `python3 seed_from_payloads.py ingest --dry-run` clean
- Do not stage or remove `data/health.db`

## Useful validator quirks

- Citation first token cannot look like a single-letter placeholder
- `umbrella_review` is not a valid `study_type`; use `systematic_review`
- If a factor is rejected by the validator path but is intentionally new for the edge, declaring it in `new_entities` is acceptable
- Performance-style or process-style outcomes often fit best with `direction: "protective"` and entity `kind: "process"`

## Final batch added at 150/150

These five files were added in the completion commit:

- `data/seed_payloads/vegan_diet_during_pregnancy__infant_growth_outcomes.json`
- `data/seed_payloads/maternal_obesity__child_obesity_risk.json`
- `data/seed_payloads/maternal_gestational_diabetes__child_obesity_long_term.json`
- `data/seed_payloads/aces_4plus__adult_mental_health_outcomes.json`
- `data/seed_payloads/aces_4plus__adult_cardiovascular_disease.json`

## Commands to verify locally

From repo root:

```bash
git checkout feat/codex-seed-batch-7
python3 seed_from_payloads.py ingest --dry-run
```

Validate one file:

```bash
python3 seed_from_payloads.py validate data/seed_payloads/<file>.json --verify
```

## Paste-ready prompt for Claude

```text
Inspect https://github.com/prokesmic/HealthUniverse on branch feat/codex-seed-batch-7.

Read CLAUDE_TRACK_HANDOFF.md first.

Treat feat/codex-seed-batch-7 as the authoritative completed Track 5 branch.
Ingest all 150 payload files added under data/seed_payloads versus origin/main.

Important constraints that governed this branch:
- do not run seed.py
- do not run adjudicate.py
- never fabricate PMIDs
- every meta-analysis/systematic-review/RCT/cohort/case-control/cross-sectional row needs n_participants
- include effect_quant whenever the cited source reports a pooled estimate
- data/health.db is scratch and should be ignored

Latest completion commit: a6a1eed
Expected diff count versus main under data/seed_payloads: 150
Latest dry-run state: python3 seed_from_payloads.py ingest --dry-run -> errors: []
```
