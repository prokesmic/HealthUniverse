# Codex brief v3 — Health Universe expansion to ~750 edges

> **Builds on v2** (which landed cleanly as PR #3, 250 verified payloads).
> Same JSON schema, same PMID-and-`n_participants` requirement, same
> validator. Different topic coverage.

---

## Repo

https://github.com/prokesmic/HealthUniverse — branch from `main` to a new
`feat/codex-seed-batch-3`. Main currently has 513 edges across 311 entities.

## What changed since v2

- The graph now has 513 edges and embeddings on every entity + edge.
- A **deduper** (`dedupe.py`) auto-merges near-duplicates as they arrive.
  This means **don't re-cover ground v2 already covered** — the deduper
  will fold them anyway, but it's wasted effort.
- The validator (`seed_from_payloads.py validate --verify`) is unchanged
  and still required. Same gates: real PMIDs, `n_participants` for
  quantitative rows, no single-letter author tokens.

## Read these in order

1. `CODEX_BRIEF_500_V2.md` — the JSON schema, validator usage, hard rules
2. This file — for the topic list
3. `AGENTS.md` — repo etiquette, "Avoid" list

## Quality lessons from the v2 review (non-blocking, please address)

The v2 batch passed validation but had two kinds of templated prose. Please
avoid these in v3:

1. **Kitchen-sink mechanism**: don't write *"X may influence Y through
   oxidative damage, inflammatory tone, hormone signaling, bile-acid
   metabolism, and exposure to food-derived carcinogens or protective
   phytochemicals"*. Write the actual mode of action specific to the
   factor — e.g. *"Soy isoflavones bind ERβ preferentially, producing
   weaker estrogenic effects in mammary tissue while modulating SHBG."*

2. **Templated summary skeletons**: don't repeat *"In [population], pooled
   meta-analytic evidence suggest that X tracks with lower/higher risk of
   Y. Most disagreement in the literature is about size, subgroup
   sensitivity, or dose…"* across many edges. Write each summary in its
   own voice, anchored on the strongest piece of evidence. Example:
   *"The 2015 Bagnardi meta-analysis of 5.7M people showed a roughly
   linear ~4% rise in breast cancer risk per 10g/day of alcohol, present
   in both pre- and postmenopausal women. The absolute lifetime increase
   is small at low intakes but the relationship is one of the most
   reproducible in nutritional epidemiology."*

These are quality-of-life issues, not validator-blockers. The repo will
schedule a Gemma "rewrite in plain voice" pass on issues #4 anyway, but
nicer prose now means less rework.

---

## Topic coverage — ~250 new pairs across these areas

Same alphabet style as v2. Aim for 25–30 pairs per area, total ~250.

### A. Drug-condition / drug-drug / drug-nutrient (35 pairs)

Beyond what v2 covered. Examples:
- **GLP-1 agonists** × specific outcomes (cardiovascular events,
  pancreatitis risk, sarcopenia from weight loss, gastroparesis)
- **SGLT2 inhibitors** × CKD, heart failure, ketoacidosis risk
- **Beta blockers** × all-cause mortality after MI vs general use
- **ACE inhibitors / ARBs** × kidney function, cough, angioedema
- **Allopurinol / xanthine-oxidase** × CVD events
- **Bisphosphonates** × osteoporosis vs atypical femur fracture
- **Statins** × diabetes risk (the muscle-symptom controversy)
- **Antihistamines (1st gen)** × dementia risk (anticholinergic)
- **Long-term opioid therapy** × hyperalgesia, hypogonadism, fall risk
- **Methotrexate** × CVD (rheumatoid populations)
- **Levothyroxine** × osteoporosis (over-replacement)
- **Drug-grapefruit interactions** as a single edge per drug class

### B. Occupational + environmental exposures (25 pairs)

- Asbestos × mesothelioma; asbestos × lung cancer (separate)
- Silica dust × silicosis; silica × lupus
- Welding fumes × Parkinson's
- Solvents (benzene, toluene, formaldehyde) × specific cancers
- Diesel exhaust × lung cancer (separate from PM2.5)
- Pesticide spraying occupations × Parkinson's, NHL
- Firefighting × specific cancers
- Lead (occupational vs paint vs water) × cognition, hypertension
- Radon (residential) × lung cancer
- Trichloroethylene × kidney cancer
- Cosmetic talc × ovarian cancer (this is contentious; tier X is fine)
- Hair-dye use × bladder cancer

### C. Gerontology specifics (25 pairs)

- Polypharmacy (≥5 daily meds) × falls, delirium, mortality
- Anticholinergic burden × cognition
- Frailty index × mortality / outcomes
- Sarcopenia × hospitalisation outcomes
- Vitamin D supplementation in adults ≥75 × falls (recent evidence)
- Tai chi × falls
- Balance training × falls
- Hospital-acquired delirium × dementia
- Hearing aid use × cognitive decline rate
- Cataract surgery × dementia
- Social engagement × cognitive reserve
- Loneliness × CVD mortality

### D. Pediatric / developmental (25 pairs)

- ACEs (Adverse Childhood Experiences) total score × adult outcomes
- Maternal smoking in pregnancy × ADHD, asthma, low birth weight
- Maternal alcohol × FASD spectrum
- Lead in childhood × adult cognitive function
- Breastfeeding duration (0/3/6/12 months) × adult outcomes
- Early peanut introduction × peanut allergy (LEAP-style)
- Early cow's milk introduction × T1D risk
- C-section × childhood asthma / obesity
- Antibiotics in first year × IBD, asthma
- Daycare attendance × respiratory infections + immune development
- Pesticide drift × childhood neurodevelopment
- Childhood adiposity rebound timing × adult obesity

### E. Sleep architecture detail (15 pairs)

- Sleep regularity (variability) × mortality (independent of duration)
- REM sleep deprivation × emotional regulation
- Slow-wave sleep × glymphatic clearance / Alzheimer's biomarkers
- Sleep-disordered breathing × stroke (vs general CVD)
- Insomnia (clinical) × suicidality
- Sleep apnea × atrial fibrillation
- CPAP adherence × CV outcomes
- Bedroom CO₂ × sleep quality
- Naps (timing/duration) × cognitive performance vs CV risk

### F. Microbiome strain × condition specificity (20 pairs)

- *L. rhamnosus* GG × antibiotic-associated diarrhea
- *S. boulardii* × C. diff prevention
- *Bifidobacterium longum* 35624 × IBS
- Multi-strain probiotic × atopic dermatitis prevention
- FMT × *C. diff* recurrence
- FMT × IBD
- Akkermansia × metabolic syndrome (early evidence)
- Specific fibres (inulin, GOS, beta-glucan, psyllium, RS3) × specific
  short-chain fatty acid production
- Artificial sweeteners (sucralose, aspartame, sorbitol separately)
  × microbiome composition

### G. Cancer screening + early-detection interventions (15 pairs)

- Colonoscopy × CRC mortality
- FIT (fecal immunochemical) × CRC mortality
- Mammography × breast cancer mortality (with overdiagnosis nuance)
- Low-dose chest CT in heavy smokers × lung cancer mortality
- PSA-based screening × prostate cancer mortality (split evidence)
- HPV self-sampling × cervical cancer mortality
- Lp(a) measurement × CV risk reclassification
- ApoB × MI risk (vs LDL)
- Coronary artery calcium × MI prediction
- Continuous glucose monitoring in T2D × HbA1c

### H. Mental health detail (20 pairs)

- Specific psychotherapy modalities × specific conditions:
  - CBT × anxiety, depression, insomnia, OCD (each separate)
  - EMDR × PTSD
  - DBT × borderline PD, eating disorders
  - IPT × depression
  - ACT × chronic pain
- Psilocybin-assisted therapy × treatment-resistant depression
- Ketamine / esketamine × treatment-resistant depression
- Lithium × suicidality (different tier than for bipolar)
- ECT × treatment-resistant depression
- Light therapy × seasonal depression
- Exercise dose-response × depression severity

### I. Cardiovascular detail beyond the basics (20 pairs)

- Lp(a) × CVD events
- ApoB × MI (head-to-head vs LDL)
- Triglycerides (fasting vs non-fasting) × CVD
- Coronary calcium score × all-cause mortality
- Atrial fibrillation × dementia
- Resting heart rate × mortality (separate from HRV)
- Pulse pressure × mortality
- Orthostatic hypotension × falls + cognitive decline
- Endothelial dysfunction (FMD) × event prediction
- Carotid intima-media thickness × stroke

### J. Endocrine / metabolic detail (20 pairs)

- Hypothyroidism (overt vs subclinical) × CVD, cognition
- Hashimoto's × specific outcomes
- Hyperparathyroidism × kidney stones, osteoporosis
- Vitamin D dose stratification (1000/2000/4000 IU) × outcomes
- HbA1c trajectory × cognitive outcomes
- Insulin resistance markers (HOMA-IR, fasting insulin) × specific cancers
- Metabolic-healthy obesity × outcomes (ongoing controversy)
- Hot-flash severity × CVD risk in postmenopausal women
- Testosterone replacement × CV events (the FDA controversy)
- DHEA × specific outcomes in older adults

### K. Sensory + neurology underrepresented (15 pairs)

- Migraine × CVD, stroke
- Tension headache × specific lifestyle factors
- Tinnitus × specific interventions (tinnitus retraining therapy)
- Vertigo / BPPV × specific exercises
- Restless legs × iron, dopamine
- REM sleep behavior disorder × Parkinson's prediction
- Multiple sclerosis × vitamin D, smoking, EBV
- Trigeminal neuralgia × specific treatments
- Peripheral neuropathy × diabetes control / nutrient deficiencies

### L. Misc + underrepresented (20 pairs)

- Periodontal disease × specific conditions (Alzheimer's, RA, PCOS)
- Gum disease × pregnancy outcomes
- Specific cooking methods × specific outcomes:
  - High-temp cooking (HCAs/PAHs) × specific cancers
  - Boiling vs grilling × cancer markers
- Specific water contaminants:
  - Chlorinated DBPs × bladder cancer
  - Nitrates in water × specific cancers
  - Fluoride dose × outcomes (this needs careful evidence-grading)
- Air pollution component-specific:
  - Black carbon × CVD
  - Ozone × respiratory mortality
  - NO₂ × childhood asthma onset

---

## Submission

```bash
git checkout -b feat/codex-seed-batch-3
# do the work, save payloads under data/seed_payloads/
source .venv/bin/activate
python seed_from_payloads.py validate --verify  # MUST end "0 failed"
python seed_from_payloads.py ingest --dry-run   # confirm slug references resolve
git add data/seed_payloads/
git commit -m "Codex seed batch v3: ~250 pairs across A-L areas"
git push -u origin feat/codex-seed-batch-3
gh pr create --title "Codex seed batch v3 — ~250 pairs"
```

PR description must include:
1. Full `--verify` output ending "0 failed"
2. 5 random `(factor, outcome, PMID, year, journal)` rows
3. Areas covered (which letters from A–L)
4. **A note on prose quality**: pick one summary you wrote and one
   mechanism, paste them in the PR description. The reviewer wants to
   spot-check that you didn't slide back into the v2 templated prose.

---

## After your PR merges

The owner runs `python dedupe.py scan` to catch any near-duplicates
between your batch and existing edges. The deduper auto-folds where
appropriate. You don't need to think about dedup yourself — focus on
quality of each individual payload.
