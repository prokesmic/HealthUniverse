# Claude Handoff: Track 8 Complete

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to inspect:
- `feat/codex-seed-batch-10`

Latest completion commit:
- `57328fc` — `Track 8: 150/150 — specialization, youth strength, caffeine, phone ownership, and helmets`

## Status

Track 8 is fully complete on `feat/codex-seed-batch-10`.

Completed scope versus `origin/main`:
- `150` new payload files under `data/seed_payloads`
- all `150/150` manifest pairs from `CODEX_BRIEF_V10_AUTONOMOUS.md` are covered
- topic coverage is balanced at `30` pairs each across blocks `A` through `E`

Latest known clean state:
- file-level `python3 seed_from_payloads.py validate <new-file>.json --verify` passed throughout the final batch
- `python3 seed_from_payloads.py ingest --dry-run` -> `errors: []`

## What Claude should ingest

Use this branch as the authoritative finished Track 8 seed set.

Main content to ingest:
- every file in `data/seed_payloads` that exists on `feat/codex-seed-batch-10` but not on `origin/main`

Quick way to confirm the count locally:

```bash
git diff --name-only origin/main...feat/codex-seed-batch-10 -- data/seed_payloads | wc -l
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
- Keep `python3 seed_from_payloads.py ingest --dry-run` clean
- File-level PubMed verification was used for new payloads during the final completion run
- Do not stage or remove `data/health.db`

## Useful validator quirks

- Citation first token cannot look like a single-letter placeholder
- `umbrella_review` is not a valid `study_type`; use `systematic_review`
- New entities must be declared locally when the edge references a slug that has not been introduced yet
- The validator requires at least `3` evidence rows per edge in these payloads

## Final batch added at 150/150

These five files were added in the completion commit:

- `data/seed_payloads/single_sport_specialization_youth__overuse_injury_risk.json`
- `data/seed_payloads/youth_strength_training_supervised__injury_outcomes.json`
- `data/seed_payloads/caffeine_adolescent__sleep_anxiety.json`
- `data/seed_payloads/early_phone_ownership_under_10__adolescent_mental_health.json`
- `data/seed_payloads/helmet_use_youth_sport__concussion_risk.json`

## Commands to verify locally

From repo root:

```bash
git checkout feat/codex-seed-batch-10
python3 seed_from_payloads.py ingest --dry-run
```

Validate one file:

```bash
python3 seed_from_payloads.py validate data/seed_payloads/<file>.json --verify
```

## Paste-ready prompt for Claude

```text
Inspect https://github.com/prokesmic/HealthUniverse on branch feat/codex-seed-batch-10.

Read CLAUDE_TRACK_HANDOFF.md first.

Treat feat/codex-seed-batch-10 as the authoritative completed Track 8 branch.
Ingest all 150 payload files added under data/seed_payloads versus origin/main.

Important constraints that governed this branch:
- do not run seed.py
- do not run adjudicate.py
- never fabricate PMIDs
- every meta-analysis/systematic-review/RCT/cohort/case-control/cross-sectional row needs n_participants
- include effect_quant whenever the cited source reports a pooled estimate
- data/health.db is scratch and should be ignored

Latest completion commit: 57328fc
Expected diff count versus main under data/seed_payloads: 150
Latest dry-run state: python3 seed_from_payloads.py ingest --dry-run -> errors: []
```
