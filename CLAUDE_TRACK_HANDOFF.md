# Claude Handoff: Track 7 Content Complete, Final Verify Blocked by PubMed Flakiness

Repo: `https://github.com/prokesmic/HealthUniverse`

Primary branch to inspect:
- `feat/codex-seed-batch-9`

Latest branch head for this handoff:
- `content-complete through Track 7: 150/150`

## Status

Track 7's manifest from `CODEX_BRIEF_V9_AUTONOMOUS.md` is now fully covered on this branch:
- all `150/150` manifest pairs have payload files
- the final five items are:
  - `occupational_radiation_low_dose -> cancer_lifetime`
  - `occupational_chronic_noise_above_80db -> hypertension`
  - `occupational_sedentary_long_chronic -> cardiovascular_outcomes`
  - `commute_long_above_60min -> mental_health_subjective`
  - `green_space_residential -> all_cause_mortality`

However, the branch is **not yet PR-ready** because full-branch `--verify` is being blocked by intermittent PubMed / E-utilities failures:
- individual validation of the final five files succeeds
- direct `curl` lookups to the PMIDs succeed
- full or repeated `python3 seed_from_payloads.py --verify validate` runs intermittently return:
  - `PMID ... did not resolve on PubMed`
  - `[pubmed lookup] Expecting value: line 1 column 1 (char 0)`

That looks like transient remote lookup instability or rate limiting, not fabricated PMIDs.

## Current branch history

Recent checkpoints before the final content-complete batch:
- `cb41068` — `Track 7: 140/150 — phthalates, pesticides, diesel, silica, and asbestos exposures`
- `9f6637c` — `Track 7: 135/150 — lead, mercury, cadmium, and BPA metabolic harms`
- `1c4c052` — `Track 7: 130/150 — wildfire smoke, biomass, mold, VOCs, and arsenic cardiovascular harms`

## Final five payload files

These are the files Claude should inspect first:
- `data/seed_payloads/occupational_radiation_low_dose__cancer_lifetime.json`
- `data/seed_payloads/occupational_chronic_noise_above_80db__hypertension.json`
- `data/seed_payloads/occupational_sedentary_long_chronic__cardiovascular_outcomes.json`
- `data/seed_payloads/commute_long_above_60min__mental_health_subjective.json`
- `data/seed_payloads/green_space_residential__all_cause_mortality.json`

## What passed locally

The final five files each passed `--verify` individually at least once.

Representative successful file-level verifies:

```bash
python3 seed_from_payloads.py --verify validate data/seed_payloads/occupational_radiation_low_dose__cancer_lifetime.json
python3 seed_from_payloads.py --verify validate data/seed_payloads/occupational_chronic_noise_above_80db__hypertension.json
python3 seed_from_payloads.py --verify validate data/seed_payloads/occupational_sedentary_long_chronic__cardiovascular_outcomes.json
python3 seed_from_payloads.py --verify validate data/seed_payloads/commute_long_above_60min__mental_health_subjective.json
python3 seed_from_payloads.py --verify validate data/seed_payloads/green_space_residential__all_cause_mortality.json
```

What did **not** pass reliably:

```bash
python3 seed_from_payloads.py --verify validate
```

because PubMed resolution intermittently fails across known-good PMIDs in many older files as well, not only in the final five.

## Suggested next step for Claude

1. Check out `feat/codex-seed-batch-9`.
2. Re-run:

```bash
python3 seed_from_payloads.py --verify validate
python3 seed_from_payloads.py ingest --dry-run
```

3. If full verify passes cleanly:
   - keep branch as the authoritative completed Track 7 branch
   - open the PR into `main`
4. If full verify still fails with transient PubMed resolution errors:
   - do **not** rewrite good payloads just because lookup flaked
   - spot-check the failing PMIDs directly with `curl -ks` against PubMed E-utilities
   - retry the full verify later rather than degrading the evidence set

## Hard rules preserved on this branch

- do not run `seed.py`
- do not run `adjudicate.py`
- never fabricate PMIDs
- every `meta_analysis`, `systematic_review`, `rct`, `cohort`, `case_control`, and `cross_sectional` row needs `n_participants`
- include `effect_quant` whenever the source reports a pooled estimate
- use threshold-encoded exposure slugs where the brief calls for them

## Paste-ready prompt for Claude

```text
Repo: https://github.com/prokesmic/HealthUniverse
Branch: feat/codex-seed-batch-9

Read CLAUDE_TRACK_HANDOFF.md first.

Track 7 is content-complete at 150/150 on this branch.
Do not restart the manifest or recreate payloads.

Your job is to treat feat/codex-seed-batch-9 as the authoritative Track 7 branch, re-run:
python3 seed_from_payloads.py --verify validate
python3 seed_from_payloads.py ingest --dry-run

If the full verify passes, proceed with PR prep.
If it fails only because PubMed lookups intermittently return empty/invalid responses, do not rewrite valid payloads blindly. Spot-check failing PMIDs directly and retry later.
```
