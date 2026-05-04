# Codex brief — Health Universe seed expansion to 500

> **Scope:** ~250 new `(factor → outcome)` deep-research payloads.
> **Output:** JSON files in `data/seed_payloads/`, validated by
> `seed_from_payloads.py`. **Do NOT call our Anthropic API.**
> **PR target:** new branch `feat/codex-seed-batch-1`, PR into `main`.

---

## What you are doing

Producing structured, evidence-graded research summaries for ~250 specific
health relationships, in a strict JSON schema this repo will ingest into its
SQLite knowledge graph. Each summary is the equivalent of one Cochrane-style
mini-review: tier (A–D/X), direction (protective/harmful/etc.), 4–10 cited
studies weighted by quality, plain-English summary + mechanism + caveats.

You will use **your own** LLM/tools (web browsing, your model's medical
knowledge) to do the research. You will **not** touch this repo's Claude
budget. Output goes into JSON files we ingest.

---

## Hard rules — non-negotiable

1. **Never fabricate citations.** Only include studies you have located or
   are confident exist (specific authors, year, journal, approximate n).
   When uncertain, omit the row rather than invent details. The validator
   does not catch fabrication — the project owner will spot-check randomly
   and reject the whole PR if any cited study is invented.
2. **Weigh evidence by quality.** Meta-analyses & large RCTs > cohort >
   small RCT > observational > mechanistic / animal. Tier rubric below.
3. **Avoid hype.** When evidence is weak or split, write it that way (tier
   C/D/X). When mainstream wisdom contradicts the evidence, follow the
   evidence.
4. **Default to the most boring claim.** If something looks too good
   (turmeric cures cancer, etc.), it almost certainly doesn't.
5. **Use existing entity slugs** from `topics.py` whenever possible. Add
   new entities only when truly missing. Provide them via `new_entities`.
6. **Do not run our Claude calls** (`seed.py`, `adjudicate.py`). Do not
   modify `claude_client.py`, `db.py`, the schema, the cost ledger, or the
   AGENTS.md "Avoid" list.

---

## What to deliver

A directory `data/seed_payloads/` containing one JSON file per `(factor,
outcome)` pair you research, named:

    {factor_slug}__{outcome_slug}.json

Example: `coffee__parkinsons.json`. Use double underscore between slugs.

Each file has this exact shape:

```json
{
  "schema_version": 1,
  "new_entities": [
    {
      "slug": "blue_light_evening",
      "name": "Evening blue light",
      "kind": "environmental",
      "aliases": ["evening screen blue light"],
      "description": "Blue-wavelength light exposure within 2h of sleep"
    }
  ],
  "edges": [
    {
      "factor_slug":  "<existing or new entity slug>",
      "outcome_slug": "<existing or new entity slug>",
      "direction":    "protective" | "harmful" | "neutral" | "u_shaped" | "mixed",
      "tier":         "A" | "B" | "C" | "D" | "X",
      "effect_size":  "trivial" | "small" | "moderate" | "large" | "unknown",
      "effect_quant": "<quantitative effect with CI if known, else short qualitative line>",
      "population":   "general adult" | "<more specific scope>",
      "mechanism":    "<one short paragraph, plain English>",
      "summary":      "<2-4 sentences, card body for non-expert reader>",
      "caveats":      "<key cautions, dose ranges, contraindications, ~2 sentences>",
      "evidence": [
        {
          "citation":      "<authors year journal short>",
          "year":          2024,
          "study_type":    "meta_analysis"|"systematic_review"|"rct"|"cohort"|"case_control"|"cross_sectional"|"mechanistic"|"animal"|"case_report"|"expert_opinion",
          "n_participants": 1234,
          "direction":     "protective"|"harmful"|"neutral"|"u_shaped"|"mixed",
          "quality":       "high"|"moderate"|"low"|"very_low",
          "notes":         "<one short sentence>"
        }
      ]
    }
  ]
}
```

Most files will have `new_entities: []` (or the field can be omitted) and
`edges: [<one edge>]`. Use multiple `edges` per file only when convenient
(e.g. dose-response variants of the same pair).

### Required fields per edge

`factor_slug`, `outcome_slug`, `direction`, `tier`, `summary` (≥80 chars),
`mechanism` (≥60 chars), `evidence` (≥3 rows). Validator enforces this.

### Tier rubric (apply conservatively)

- **A** = ≥2 high-quality meta-analyses *or* large RCTs, consistent
  direction, mechanism known.
- **B** = multiple cohorts + plausible mechanism, minor conflicts.
- **C** = early RCTs / strong observational, mechanism plausible.
- **D** = mechanistic / animal / single small study only.
- **X** = evidence genuinely split between directions.

Aim for **4–10 evidence rows per edge.** Three is the validator minimum.
More than ten is noise.

---

## Validation — run this before opening the PR

```bash
cd HealthUniverse
./setup.sh                  # creates .venv, installs deps
source .venv/bin/activate
python seed_from_payloads.py validate
```

The validator checks: schema_version, slug existence (against `entity`
table or your `new_entities`), tier/direction enums, study-type enums,
≥3 evidence rows, summary/mechanism length floors. Fix everything until
validation prints `0 failed`.

You can also do a dry-run import to check DB compatibility:

```bash
python seed_from_payloads.py ingest --dry-run
```

The owner will run the actual `ingest` command after PR review.

---

## Topic coverage — the 250 pairs

The repo currently has ~190 pairs queued/done. To reach 500, we need ~310.
You produce **~250 of them.** The remaining ~60 the owner reserves for
future work.

Cover these areas, distributed roughly as indicated. Use existing slugs
where possible; declare new entities only when missing.

### A. Cardiometabolic detail (40 pairs)
Dose-response and population-stratified variants. Examples:
- `coffee` × `cvd`: low (1–2 cups/day) vs moderate (3–4) vs heavy (5+)
  populations (`coffee_low`, `coffee_moderate`, `coffee_heavy`)
- `omega3` × `cvd` stratified by baseline triglycerides
- `walking_daily` × `cvd` at 4k vs 7k vs 10k+ steps
- `vitamin_d` × `cvd` stratified by baseline 25-OH-D level
- Mediterranean / DASH / vegetarian diet patterns × cvd, hypertension, t2d
- Saturated fat, monounsaturated fat, polyunsaturated fat × CVD
- Specific micronutrients: potassium, calcium, sodium × hypertension

### B. Cancer detail (35 pairs)
- Alcohol dose-response × breast cancer (`alcohol_low`, `alcohol_moderate`,
  `alcohol_heavy`)
- Aspirin (low-dose) × colorectal cancer
- Specific food groups × specific cancers (cruciferous × bladder, allium ×
  stomach, soy × breast cancer in pre/post-menopausal women)
- Hormone therapy × breast / endometrial cancer
- Sun exposure × melanoma × non-melanoma skin cancer (likely opposite signs)
- HPV vaccination × cervical cancer
- Aflatoxin / mycotoxin × hepatocellular carcinoma

### C. Brain & mood detail (30 pairs)
- Specific exercise modalities × cognitive decline (HIIT, dance, tai chi)
- Bilingualism / cognitive engagement × dementia
- Antidepressants (general) × depression remission rates
- Cognitive behavioural therapy × depression / anxiety
- Specific micronutrient deficiencies × cognitive function (B12, folate,
  iron, iodine)
- Air pollution components (PM2.5 vs NO2 vs ozone) × dementia separately
- Hearing-aid use × dementia

### D. Sleep, circadian, light (20 pairs)
- Caffeine timing × sleep quality
- Alcohol × sleep architecture (REM suppression specifically)
- Bedroom temperature × sleep quality
- Shift work × cardiovascular / metabolic / cancer risk separately
- Melatonin × sleep onset latency vs sleep maintenance
- CPAP × sleep apnea outcomes

### E. Microbiome, gut, immune (25 pairs)
- Specific fibers (inulin, beta-glucan, resistant starch, psyllium) ×
  microbiome composition
- Specific fermented foods × microbiome diversity
- Antibiotic exposure × IBD / asthma / obesity later in life
- Vaginal vs C-section birth × childhood microbiome
- Probiotic strains × specific GI conditions (e.g. *L. rhamnosus* GG ×
  antibiotic-associated diarrhea)
- Specific prebiotics × IBS

### F. Drug-nutrient interactions (15 pairs)
These are critical and underdone in the existing graph. Each is one edge.
- Statins × CoQ10 depletion
- Metformin × B12 deficiency
- PPIs × magnesium / B12 / bone density
- Diuretics × potassium / magnesium
- Oral contraceptives × folate / B6
- SSRIs × bone density
- Long-term glucocorticoids × bone density / muscle
- Levothyroxine × calcium / iron timing

### G. Environmental & toxicants (25 pairs)
- Phthalates × endocrine outcomes
- Heavy metals (lead, mercury, arsenic, cadmium) × cognition / kidney
- Pesticides (organophosphates, glyphosate where evidence exists) ×
  neurodegeneration
- Drinking water nitrates × specific cancers
- BPA × childhood neurodevelopment
- Indoor air quality / mold × respiratory outcomes

### H. Gene-factor interactions (15 pairs)
Use `gene` kind for new entities like `apoe4`, `mthfr_c677t`, `fto_aa`.
- ApoE4 × saturated fat × Alzheimer's
- ApoE4 × omega-3 × Alzheimer's
- MTHFR × folate × homocysteine / NTD risk
- FTO × physical activity × obesity
- Lactase persistence × dairy × cardiovascular outcomes

### I. Pediatrics expansion (15 pairs)
- Sugar in infancy × obesity later
- Antibiotics in first year × obesity / asthma / IBD
- Vitamin D in infancy × allergic disease
- Iron in infancy × neurodevelopment
- Pesticide exposure in pregnancy × childhood neurodevelopment
- Maternal diet during pregnancy × child obesity / allergy

### J. Aging / longevity / sarcopenia (15 pairs)
- Protein intake (g/kg/day) × sarcopenia in older adults at multiple doses
- Leucine / HMB × muscle protein synthesis
- Caloric restriction (modest, sustained) × all-cause mortality
- Time-restricted eating × specific outcomes (separate from existing rows)
- Senolytic agents × outcomes (mostly tier D, that's fine)
- VO2 max trajectory × all-cause mortality

### K. Misc / underrepresented (15 pairs)
- Dental health (periodontal disease) × CVD / Alzheimer's
- Hearing loss × dementia
- Vision loss × falls / cognitive function
- Posture / kyphosis × all-cause mortality
- Grip strength × all-cause mortality
- Resting heart rate × all-cause mortality

---

## How to do the research efficiently

For each pair:

1. Look up the most recent meta-analysis or Cochrane review. If one exists
   from the last 5 years, lean on its summary.
2. Find 2–4 large supporting studies (RCTs / cohort studies).
3. Note any high-quality contradicting studies.
4. Decide tier conservatively per the rubric.
5. Write summary in plain English, 2–4 sentences. No "may help with..."
   weasel words; pick a direction or use `mixed`.
6. Write mechanism in 1 short paragraph. Don't overstate certainty.
7. Write caveats: dose, who shouldn't, common side effects.
8. Save the JSON. Validate.

Aim for **20–30 minutes per pair** when starting; faster as you find your
rhythm. **Quality > speed.** A bad payload is worse than no payload.

---

## PR submission

```bash
git checkout -b feat/codex-seed-batch-1
git add data/seed_payloads/
python seed_from_payloads.py validate    # must print "0 failed"
git commit -m "Codex seed batch 1: <N> pairs across <areas>"
git push -u origin feat/codex-seed-batch-1
gh pr create --title "Codex seed batch 1 — N pairs" --body "..."
```

PR description must include:
- Number of pairs in this batch
- Areas covered (A/B/C/... letters from the topic list)
- Sample of 3 random citations the reviewer can spot-check
- Output of `python seed_from_payloads.py validate` (must show all OK)

---

## What you will NOT do

- ❌ Run `python seed.py` or `python adjudicate.py` (those use the owner's
  Claude key)
- ❌ Modify `claude_client.py`, `db.py`, `schema.sql`, `cost_ledger`,
  `seed.py`, `adjudicate.py`, `ingest/*`, `digest.py`, `profile.py`,
  the LaunchAgent plist, or `web/static/style.css` color tokens
- ❌ Add new dependencies to `requirements.txt` without an issue first
- ❌ Push to `main` directly (PR only)
- ❌ Submit edges with `<3` evidence rows or fabricated citations

---

## Why this is structured this way

The owner is paying for Anthropic API only for one-off seed research and
tier-A/B adjudication, and is using local Gemma for the daily ingest loop.
Asking you to run separate Claude calls would either burn the owner's
budget or require sharing API keys. JSON payloads are a clean handoff: you
do the research with whatever tools you have, the owner ingests with a
deterministic script, both sides have something to verify against.

The schema is exactly what `seed.py`'s prompt produces, so payloads from
this batch are indistinguishable from the owner's seed batch once
ingested. The only marker we keep is `edge_history.actor='codex_payload'`
for audit.
