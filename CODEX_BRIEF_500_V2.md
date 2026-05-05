# Codex brief v2 — Health Universe seed expansion (250 pairs, **PMIDs required**)

> **This supersedes `CODEX_BRIEF_500.md`.** v1 was rejected because evidence
> rows had abbreviated single-letter "authors", `n_participants: null`
> everywhere, and citations that didn't match the edge topic. We learned
> the hard way that the v1 validator only checked structure. **The v2
> validator checks PubMed.** Ungrounded payloads will fail before review.

---

## What changed vs v1

1. **Every evidence row of a stat-quantitative study type** (`meta_analysis`,
   `systematic_review`, `rct`, `cohort`, `case_control`, `cross_sectional`)
   **must include a `pmid` (PubMed ID).** No PMID → validator rejects.
2. **Every PMID is resolved against PubMed.** The paper must exist and its
   real title must fuzzy-match what you wrote in `notes` or `citation`.
3. **Citations must start with a real first-author surname** (≥3 chars).
   "M 2026 Sleep Med" is rejected. "Mah J 2021 BMC Complement Med Ther" is
   accepted.
4. **`n_participants` is required** for the same stat-quantitative types.
   Use the largest reported total n (sum across pooled studies for
   meta-analyses; total enrolled for RCTs/cohorts).

These four checks make fabrication impossible — you must find real papers.

---

## Repo

https://github.com/prokesmic/HealthUniverse — branch from `main`, NOT from
`feat/codex-seed-batch-1` (that branch will be closed without merge).

---

## What you produce — exact JSON shape

One `.json` file per edge in `data/seed_payloads/`, named
`{factor_slug}__{outcome_slug}.json`:

```json
{
  "schema_version": 1,
  "new_entities": [
    {
      "slug":        "alcohol_low",
      "name":        "Low alcohol intake (<7 drinks/week)",
      "kind":        "behavior",
      "aliases":     ["light drinking"],
      "description": "≤7 standard drinks per week"
    }
  ],
  "edges": [
    {
      "factor_slug":  "alcohol_low",
      "outcome_slug": "breast_cancer",
      "direction":    "harmful",
      "tier":         "B",
      "effect_size":  "small",
      "effect_quant": "RR ~1.04 per 10g/day vs none",
      "population":   "premenopausal and postmenopausal women",
      "mechanism":    "Ethanol is metabolised to acetaldehyde, a class-1 carcinogen, and elevates circulating estradiol, both implicated in breast carcinogenesis.",
      "summary":      "Even light drinking (<7 drinks/week) is associated with a small but consistent rise in breast cancer risk in pooled cohort and meta-analyses, with the effect roughly linear in dose. The signal is strongest for ER+ tumors and present in both pre- and postmenopausal women.",
      "caveats":      "Absolute lifetime risk increase is small at low intakes; tradeoffs vs cardiovascular benefits at the same dose are contested.",
      "evidence": [
        {
          "citation":      "Bagnardi V et al 2015 Br J Cancer",
          "pmid":          "25422909",
          "doi":           "10.1038/bjc.2014.579",
          "year":          2015,
          "study_type":    "meta_analysis",
          "n_participants": 5780000,
          "direction":     "harmful",
          "quality":       "high",
          "notes":         "Alcohol consumption and site-specific cancer risk: a comprehensive dose-response meta-analysis."
        }
      ]
    }
  ]
}
```

### Required fields (validator enforces all of these)

| Field | Rule |
|---|---|
| `schema_version` | must be `1` |
| `factor_slug`, `outcome_slug` | must exist in `entity` table OR be declared in `new_entities` |
| `direction` | one of `protective` `harmful` `neutral` `u_shaped` `mixed` |
| `tier` | one of `A` `B` `C` `D` `X` |
| `summary` | ≥80 chars, plain English, 2–4 sentences |
| `mechanism` | ≥60 chars, **specific** to the factor — no kitchen-sink lists |
| `evidence` | ≥3 rows |
| Each evidence row | must have `citation`, `study_type`, `quality`, `notes` |
| Stat-quantitative rows (`meta_analysis`/`systematic_review`/`rct`/`cohort`/`case_control`/`cross_sectional`) | **must additionally have `pmid` and `n_participants`** |
| `citation` | must start with a real surname (≥3 chars), not initials |
| `pmid` | must resolve on PubMed |
| `notes` or `citation` | must fuzzy-match the actual PubMed title (≥65% word overlap) |

---

## Pair coverage — same as v1 (250 pairs across areas A–K)

The pair list and area distribution from `CODEX_BRIEF_500.md` (sections
A–K) is unchanged. Use the same filenames you used in v1; you can
copy-paste filenames from your previous branch as a starting checklist.

If a pair turned out to have weak evidence, downgrade tier to D or X.
**Do not skip pairs** — every pair in the v1 brief should appear, even if
the answer is "evidence too thin to call".

---

## How to find real PMIDs

PubMed E-utilities are free, no key needed. From a browser or `curl`:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=magnesium+sleep+meta-analysis&retmode=json&retmax=10
```

Returns a list of PMIDs. Then esummary to confirm title:

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=33865376&retmode=json
```

Use those PMIDs and titles directly in your payloads. **Do not invent
PMIDs.** The validator hits PubMed for every PMID you submit; mismatches
fail the build.

For non-PubMed sources (Cochrane, Europe PMC), include the DOI in `doi`
and skip the PMID — the validator only requires PMID for stat-quantitative
study types whose primary index is PubMed. Mechanistic / animal /
case_report / expert_opinion rows do **not** need PMIDs (but real
citations are still expected).

---

## Validation — required before opening PR

```bash
git checkout -b feat/codex-seed-batch-2
./setup.sh                                          # one-time
source .venv/bin/activate

# Fast structural validation (offline)
python seed_from_payloads.py validate

# Full citation verification (calls PubMed; takes ~10 minutes for 250 files)
python seed_from_payloads.py validate --verify
```

Both must print `0 failed`. If `--verify` finds any PMID that doesn't
resolve or any title that doesn't match, fix the affected payloads and
re-run.

```bash
python seed_from_payloads.py ingest --dry-run
git add data/seed_payloads/
git commit -m "Codex seed batch v2: 250 pairs with verified PMIDs"
git push -u origin feat/codex-seed-batch-2
gh pr create --title "Codex seed batch v2 — 250 pairs"
```

In the PR description, paste:

1. The full `--verify` output (must end in "0 failed")
2. 5 random `(factor, outcome, PMID, year, journal)` rows from your output
3. A note on which areas (A–K from `CODEX_BRIEF_500.md`) you covered

---

## Quality bar — what makes a "good" payload

Beyond what the validator catches, the human reviewer checks:

- **Mechanism is specific.** "Methylmercury crosses the placenta and BBB,
  binds selenocysteine in selenoproteins, and induces neuronal oxidative
  damage." → good. "may influence X through oxidative stress, endocrine
  disruption, neurotoxicity, chronic inflammation, or cumulative organ
  burden" → rejected as kitchen-sink filler.
- **Summary is non-templated.** No "X looks Y for Z in [population], with
  the strongest signal around …" boilerplate across many edges.
- **Citations match the edge topic.** Don't cite a paper about ischemic
  heart disease as evidence for an all-cause mortality edge unless the
  paper actually reports all-cause mortality.
- **Tier is conservative.** A is rare. Default to B/C unless ≥2 high-
  quality meta-analyses agree.
- **Multiple cited papers should be from different research groups.**
  Don't stack 3 citations from the same lab.

---

## Hard rules — non-negotiable

- ❌ Never fabricate PMIDs. The validator will catch you immediately.
- ❌ Never invent citations. If you can't find ≥3 real papers for a pair,
  drop the tier to D and use mechanistic + expert_opinion rows (which
  don't need PMIDs but do need real refs).
- ❌ Never call the project's Anthropic API. `seed.py`, `adjudicate.py`,
  `claude_client.py` are off-limits.
- ❌ Never push directly to `main`. PR only.
- ❌ Never modify `db.py`, `schema.sql`, the cost ledger, the launchd
  scripts, or anything in the AGENTS.md "Avoid" list.
- ✅ Single underscore in entity slugs (`alcohol_low`); double underscore
  in filenames (`alcohol_low__breast_cancer.json`).
- ✅ When uncertain, drop the row rather than guess.

---

## Why this is structured this way

The v1 batch was rejected because validator checked structure but not
truthfulness. We've now closed that gap. The v2 validator's PMID round-
trip is roughly the gold standard for "this citation is real" — a
researcher manually checking would do the same lookup. By moving the
check into automation, we let you iterate fast: fail-fast feedback when a
citation doesn't resolve, no human-in-the-loop until the PR opens.
