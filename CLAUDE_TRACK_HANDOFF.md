# Claude Handoff: HealthUniverse Research Continuation

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to continue:
- `feat/codex-seed-batch-5`

Also relevant completed branch:
- `feat/codex-densify-batch-2`

## What is already done

### Track 1: Densify batch 2
- Branch: `feat/codex-densify-batch-2`
- Status: fully completed and pushed
- Scope completed:
  - `250` `__densify_v2.json` files
  - `750` new evidence rows
  - `55` rows with `effect_quant`
- Latest known clean state:
  - `python3 seed_from_payloads.py --verify validate` -> `1098 ok, 0 failed, 1098 total`
  - `python3 seed_from_payloads.py ingest --dry-run` -> clean

### Track 2: Seed batch 5
- Branch: `feat/codex-seed-batch-5`
- Status: in progress, pushed, validator-clean
- Latest pushed commit: `100f51c`
- Current scope completed versus `origin/main`:
  - `123` new payload files under `data/seed_payloads`
  - latest full validation:
    - `python3 seed_from_payloads.py --verify validate` -> `970 ok, 0 failed, 970 total`
    - `python3 seed_from_payloads.py ingest --dry-run` -> `errors: []`

## Hard rules

- Do not run `seed.py`
- Do not run `adjudicate.py`
- Do not fabricate PMIDs
- Keep `python3 seed_from_payloads.py --verify validate` at `0 failed`
- Keep `python3 seed_from_payloads.py ingest --dry-run` clean
- Do not open the PR until Track 2 is actually complete
- Do not weaken the quality bar to hit the target count

## What was added in the most recent batch

These 7 files were just added and pushed in commit `100f51c`:

- `data/seed_payloads/hairdresser__bladder_cancer.json`
- `data/seed_payloads/polypharmacy__frailty.json`
- `data/seed_payloads/probiotics__anxiety.json`
- `data/seed_payloads/nicotinamide_oral__non_melanoma_skin_cancer.json`
- `data/seed_payloads/spironolactone_oral__acne_vulgaris.json`
- `data/seed_payloads/occupational_noise__hypertension.json`
- `data/seed_payloads/pcos__preeclampsia.json`

## Current completion state for Track 2

- Approximate original target: `250` new pairs
- Actually completed so far: `123` payload files vs `origin/main`
- Track 2 is materially advanced but still incomplete

## Best next areas to continue

The most underfilled remaining categories are:

1. Hematology / nutrition crossover
2. Gut-brain axis specifics
3. Geriatric polypharmacy beyond the current benzodiazepine/polypharmacy set
4. Women’s reproductive endocrinology beyond menopause
5. Paediatric immunity / early-life programming depth

## Good next candidate edges

These were identified as promising continuation directions:

- `pcos__gestational_diabetes`
- `endometriosis__ovarian_cancer`
- `hairdresser__bladder_cancer` is already done; do not recreate
- `occupational_noise__hypertension` is already done; do not recreate
- `polypharmacy__frailty` is already done; do not recreate
- `probiotics__anxiety` is already done; do not recreate
- `nicotinamide_oral__non_melanoma_skin_cancer` is already done; do not recreate
- `spironolactone_oral__acne_vulgaris` is already done; do not recreate
- `pcos__preeclampsia` is already done; do not recreate

## Validator quirks to respect

- Citation first token cannot look like a single-letter placeholder.
  - Bad example: `de Vries MJ ...`
  - Safe workaround if needed: `deVries MJ ...`
- `umbrella_review` is not a valid `study_type`
  - Map to `systematic_review`
- If a factor acts as the factor in a new edge but is not accepted from the DB alone by the validator path, declaring it in `new_entities` is acceptable and already used on branch
- Performance-style outcomes on this branch often use:
  - `direction: "protective"`
  - entity `kind: "process"`

## Commands to resume safely

From repo root:

```bash
git checkout feat/codex-seed-batch-5
python3 seed_from_payloads.py --verify validate
python3 seed_from_payloads.py ingest --dry-run
```

Validate a single file:

```bash
python3 seed_from_payloads.py --verify validate data/seed_payloads/<file>.json
```

## Suggested operating mode

Work in batches of a few new payloads at a time:

1. Research real PMIDs
2. Add payloads
3. Validate each new file individually
4. Run full-branch `--verify validate`
5. Run `ingest --dry-run`
6. Commit and push the clean checkpoint

## Paste-ready prompt for Claude

```text
Continue Track 2 on branch feat/codex-seed-batch-5 in https://github.com/prokesmic/HealthUniverse.

Read CLAUDE_TRACK_HANDOFF.md first.

Your job is to continue the in-progress Track 2 seed expansion until it is fully complete.

Requirements:
- do not run seed.py
- do not run adjudicate.py
- never fabricate PMIDs
- keep python3 seed_from_payloads.py --verify validate at 0 failed
- keep python3 seed_from_payloads.py ingest --dry-run clean
- commit and push validator-clean checkpoints as you go
- do not open the PR until the full Track 2 brief is actually complete

Current known state:
- branch feat/codex-seed-batch-5
- latest pushed commit 100f51c
- 123 payload files added vs origin/main
- latest full validation: 970 ok, 0 failed, 970 total

Focus next on the most underfilled areas:
- hematology / nutrition crossover
- gut-brain axis specifics
- geriatric polypharmacy
- women’s reproductive endocrinology beyond menopause
- paediatric immunity / early-life programming
```
