# Codex brief v9 — autonomous Track 7

> **READ THIS FIRST: This brief keeps you working autonomously across
> stepping pauses. Do not stop after each pause to ask for approval.
> The loop below is your authority. Resume yourself. Done = the
> manifest is empty. Until then, keep going.**

Repo: `https://github.com/prokesmic/HealthUniverse` — branch from `main`.

## What's already done (don't redo)

- Track A (densify v1): merged
- Track 1 (densify v2): merged
- Track 2 (seed v5 — coffee × cancer, occupational, sports, benzos, breastfeeding): merged
- Track 4 (seed v6 — hematology, gut-brain, geriatric, women's repro, paediatric): merged
- Track 5 (seed v7 — mental-health, cardiometabolic meds, sleep, vaccines, longevity): merged
- Track 6 (seed v8 — athletic perf, cognitive nootropics, hormonal, gut strains, skin/hair): merged
- **Current corpus: 1,551 edges · 5,961 evidence rows · 1,068 entities · 83.2% audited**

## What you're doing now

Track 7: 150 brand-new PMID-verified pairs across **five clinical-depth
blocks that the corpus is currently thin on but that pay off directly
in the user-facing pre-visit checkup, advanced-biomarker tracking,
and the underserved pregnancy / mental-health-subtype / environmental
segments**:

1. **Iatrogenic effects: common drugs × specific adverse outcomes** (30 pairs)
2. **Advanced biomarkers × outcomes** (30 pairs)
3. **Pregnancy / fertility / pre-conception** (30 pairs)
4. **Mental health subtypes beyond depression** (30 pairs)
5. **Environmental & occupational exposures (emerging)** (30 pairs)

Manifest is **inline below**.

## The autonomous loop — do not stop until the manifest is empty

**Branch:** `feat/codex-seed-batch-9`

Repeat without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-9 main` (first run only;
   `git checkout feat/codex-seed-batch-9` thereafter).
2. Pick the next **5** unfinished items from the manifest. An item is
   "finished" if `data/seed_payloads/{factor_slug}__{outcome_slug}.json`
   already exists on this branch *or* on `main`. **Skip silently** if
   already present — do not re-research.
3. For each picked item:
   - Search PubMed for ≥3 high-quality studies on that pair
   - Verify each PMID + journal + year via the `--verify` validator
   - Write the payload using the standard `seed_payload` shape (mirror
     any payload already on `main` for the exact JSON skeleton)
   - **Include `effect_quant` whenever the source paper reports a
     pooled estimate.** Lab/biomarker thresholds where applicable.
   - **Use `direction: "harmful"` on Block A iatrogenic edges.** They
     describe a drug causing an adverse outcome. The user-facing UI
     uses this to surface them in the Hard-avoid / Biomarkers-to-monitor
     buckets on /my-plan.
   - **Use `direction: "mixed"` or `"u_shaped"` honestly** for IVF /
     fertility / supplement-fertility pairs; literature is genuinely
     noisy and the skeptic-mode briefs need real contested edges.
4. `python3 seed_from_payloads.py validate --verify` over the new
   files. Fix any failures by replacing the offending PMID. Keep going
   until 0 failed.
5. `python3 seed_from_payloads.py ingest --dry-run`. If a slug doesn't
   resolve, add a `new_entities` block to that payload. **Track 7 is
   expected to introduce many new biomarker / exposure / drug-class
   entities** — that's normal.
6. `git add data/seed_payloads/` and commit with format:
   ```
   Track 7: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-9`.
8. **Open the PR only when N=150.** Until then, push checkpoints to
   the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

After a stepping pause, re-read this file and continue. The standing
order is the loop above. Inspect `git status` on the branch, count
finished payloads, pick up where you left off. Commit messages of
form `Track 7: N/150 — topic` make your last checkpoint visible.

When the manifest is empty:
- Final `--verify validate` run with `0 failed`
- PR title: `Codex Track 7 — 150 verified pairs across clinical depth, biomarkers, pregnancy, mental-health subtypes, and exposures`
- PR description includes:
  - Full validator transcript ending `0 failed`
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows
  - Topic breakdown: pairs per block
  - Count of payloads with `effect_quant`
  - Count of payloads with `direction: harmful` (expect block A to be
    almost entirely harmful; Block C will skew mixed)
  - Count of payloads that introduced `new_entities`

Update `CLAUDE_TRACK_HANDOFF.md` at PR-time to reflect Track 7
completion (replace the Track 6 paragraph; keep the same template).

## Hard rules (same as every prior track)

- Never fabricate PMIDs (Claude's nightly semantic verifier on main
  flags mismatches)
- Every meta-analysis / SR / RCT / cohort / case-control / cross-sectional
  row must include `n_participants`
- Don't pad with weak rows — one strong meta-analysis > three cross-sectionals
- Diversify research groups
- Prioritise post-2018; older only if seminal (e.g. landmark RCTs)
- Never run `seed.py` or `adjudicate.py`
- Don't modify schema, cost cap, or anything in `AGENTS.md` "Avoid"
- Don't stage or remove `data/health.db`
- One PR per track, branched from `main`

## Track 7 quirks worth remembering

- **Block A (iatrogenic) factors are drug names + dose modifier**, e.g.
  `statins_high_dose`, `ppis_long_term`, `nsaids_chronic`. If the dose
  modifier doesn't apply (a single-dose drug), use plain class slug.
- **Block B (biomarkers) factors should encode a threshold** when the
  literature uses one — e.g. `lpa_high_above_125nmol`,
  `coronary_artery_calcium_zero`, `hba1c_5_7_to_6_4`. The Stack Brief
  uses these threshold-encoded slugs to match user lab values.
- **Block C (pregnancy) often needs new outcome slugs** — paternal /
  preconception / IVF outcomes are not yet entities. Declare them.
- **Block E (exposures) often has complex thresholds** — e.g.
  `pfas_high_serum` is "above the population median in NHANES" or
  "above 1 ng/mL", which the source paper will define. Use the
  paper's definition; document in `description`.

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

Skip silently if a payload file already exists for the pair. Tier is
your decision based on the literature; the listed direction is your
starting hypothesis — flip if the evidence says so.

### Block A · Iatrogenic effects: common drugs × adverse outcomes (30)

A1. `statins_high_dose → rhabdomyolysis_risk` · MA dose-response · harmful
A2. `statins_long_term → new_onset_diabetes_risk` · MA · harmful
A3. `statins_high_dose → muscle_pain_complaints` · MA · harmful
A4. `metformin_long_term → b12_deficiency_clinical` · MA · harmful
A5. `ppis_long_term → b12_deficiency_clinical` · MA · harmful
A6. `ppis_long_term → magnesium_deficiency_clinical` · MA · harmful
A7. `ppis_long_term → bone_fracture_risk` · MA · harmful
A8. `ssris_long_term → sexual_dysfunction_persistent` · MA · harmful
A9. `ssris_chronic → bleeding_risk_anticoagulated` · MA · harmful
A10. `snris_long_term → blood_pressure_elevation` · MA · harmful
A11. `nsaids_chronic → gi_bleeding_risk` · MA dose-response · harmful
A12. `nsaids_chronic → renal_function_decline` · MA · harmful
A13. `nsaids_chronic → cardiovascular_events` · MA · harmful
A14. `acetaminophen_chronic_high_dose → liver_enzyme_elevation` · cohort · harmful
A15. `opioids_long_term → tolerance_dependence` · MA · harmful
A16. `opioids_long_term → constipation_chronic` · MA · harmful
A17. `benzodiazepines_long_term → cognitive_decline_elderly` · MA · harmful
A18. `anticholinergic_burden_chronic → dementia_risk` · MA · harmful
A19. `corticosteroids_systemic_chronic → bone_density_loss` · MA · harmful
A20. `corticosteroids_systemic_chronic → hyperglycemia_chronic` · MA · harmful
A21. `fluoroquinolones → tendon_rupture_risk` · MA · harmful
A22. `fluoroquinolones → aortic_aneurysm_risk` · cohort · harmful
A23. `iron_supplementation_high_dose → gi_distress` · MA · harmful
A24. `calcium_supplementation_high_dose → vascular_calcification` · MA · harmful
A25. `calcium_with_vitamin_d_high_dose → kidney_stone_risk` · MA · harmful
A26. `vitamin_a_high_dose → liver_toxicity` · cohort · harmful
A27. `vitamin_e_high_dose → all_cause_mortality_excess` · MA · u_shaped
A28. `vitamin_b6_high_dose → peripheral_neuropathy` · cohort · harmful
A29. `selenium_high_dose → t2d_risk` · MA · u_shaped
A30. `niacin_extended_release → liver_function_disturbance` · MA · harmful

### Block B · Advanced biomarkers × outcomes (30)

B1. `vo2max_low → all_cause_mortality` · MA · harmful
B2. `vo2max_high → coronary_disease_progression` · cohort · protective
B3. `grip_strength_low → all_cause_mortality_elderly` · MA · harmful
B4. `grip_strength_low → cardiovascular_events` · MA · harmful
B5. `coronary_artery_calcium_high → mace_10yr` · MA · harmful
B6. `coronary_artery_calcium_zero → mace_low_risk` · cohort · protective
B7. `arterial_stiffness_pwv_high → cv_events` · MA · harmful
B8. `lpa_high_above_125nmol → mace_lifetime` · MA · harmful
B9. `ldl_p_high_discordant → atherosclerosis_progression` · cohort · harmful
B10. `apob_to_apoa1_ratio_high → mace_risk` · MA · harmful
B11. `homocysteine_high_above_15 → stroke_risk` · MA · harmful
B12. `ferritin_low_below_30 → restless_legs_syndrome` · MA · harmful
B13. `ferritin_high_above_300 → metabolic_syndrome` · cohort · harmful
B14. `hba1c_prediabetes_5_7_to_6_4 → cv_mortality` · MA · harmful
B15. `fasting_insulin_high_above_15 → cardiometabolic_outcomes` · MA · harmful
B16. `omega3_index_low_below_4 → cv_mortality` · MA · harmful
B17. `omega3_index_high_above_8 → cardiovascular_events` · cohort · protective
B18. `hs_crp_high_above_3 → cv_events` · MA · harmful
B19. `heart_rate_variability_low → cardiac_arrhythmia_risk` · MA · harmful
B20. `resting_heart_rate_high_above_80 → all_cause_mortality` · MA · harmful
B21. `sleep_efficiency_low → cardiometabolic_outcomes` · MA · harmful
B22. `rem_sleep_short → cognitive_decline` · MA · harmful
B23. `slow_wave_sleep_short → memory_consolidation` · MA · harmful
B24. `visceral_adipose_tissue_high → mace_risk` · MA · harmful
B25. `lean_body_mass_high_elderly → frailty_protection` · MA · protective
B26. `waist_to_hip_ratio_high → cv_events_independent_of_bmi` · MA · harmful
B27. `telomere_length_short → all_cause_mortality` · MA · harmful
B28. `epigenetic_age_acceleration_grimage → all_cause_mortality` · MA · harmful
B29. `visceral_fat_high → cognitive_decline` · cohort · harmful
B30. `anaerobic_threshold_high → endurance_outcomes` · MA · protective

### Block C · Pregnancy / fertility / pre-conception (30)

C1. `preconception_folate_supplementation → ntd_prevention` · MA · protective
C2. `preconception_iodine_repletion → child_neurodevelopment` · MA · protective
C3. `paternal_smoking_preconception → sperm_dna_fragmentation` · MA · harmful
C4. `paternal_age_above_45 → autism_risk_offspring` · MA · harmful
C5. `paternal_obesity → sperm_concentration` · MA · harmful
C6. `paternal_alcohol_preconception → live_birth_rate_ivf` · cohort · harmful
C7. `paternal_diet_mediterranean → sperm_quality` · cohort · protective
C8. `paternal_zinc_repletion → sperm_motility` · MA · mixed
C9. `paternal_selenium_repletion → fertility_outcomes` · MA · mixed
C10. `paternal_l_carnitine → sperm_motility` · MA · mixed
C11. `heat_exposure_men_chronic → sperm_concentration` · MA · harmful
C12. `cycling_heavy_men → sperm_concentration` · cohort · harmful
C13. `ivf_acupuncture → live_birth_rate` · MA · mixed
C14. `ivf_dhea_supplementation_dor → live_birth_rate_diminished_reserve` · MA · mixed
C15. `ivf_coq10_supplementation → oocyte_quality` · trials · mixed
C16. `ivf_melatonin_supplementation → oocyte_quality` · MA · mixed
C17. `ivf_omega3_supplementation → live_birth_rate` · MA · mixed
C18. `low_dose_aspirin_recurrent_miscarriage → live_birth_rate` · MA · mixed
C19. `progesterone_luteal_support_ivf → live_birth_rate` · MA · protective
C20. `metformin_pcos_during_pregnancy → live_birth_rate` · MA · mixed
C21. `letrozole_anovulatory_pcos → live_birth_rate` · MA · protective
C22. `clomiphene_anovulatory → live_birth_rate` · MA · protective
C23. `maternal_chronic_stress_pregnancy → preterm_birth` · MA · harmful
C24. `maternal_air_pollution_pm2_5_pregnancy → preterm_birth` · MA · harmful
C25. `maternal_dha_supplementation_pregnancy → preterm_birth_prevention` · MA · protective
C26. `maternal_choline_pregnancy → child_cognitive_development` · MA · protective
C27. `maternal_caffeine_high_pregnancy → fetal_growth_restriction` · MA · harmful
C28. `gestational_weight_gain_low → small_for_gestational_age` · MA · harmful
C29. `gestational_weight_gain_high → child_obesity_long_term` · MA · harmful
C30. `breastfeeding_short_duration → maternal_t2d_risk` · MA · harmful

### Block D · Mental health subtypes beyond depression (30)

D1. `cbt_for_generalized_anxiety_disorder → gad_severity` · MA · protective
D2. `cbt_for_panic_disorder → panic_attack_frequency` · MA · protective
D3. `cbt_for_social_anxiety_disorder → social_anxiety_severity` · MA · protective
D4. `exposure_response_prevention → ocd_severity` · MA · protective
D5. `dialectical_behaviour_therapy → self_harm_frequency` · MA · protective
D6. `ssris_high_dose → ocd_severity` · MA · protective
D7. `clomipramine → ocd_severity_treatment_resistant` · MA · protective
D8. `deep_brain_stimulation_treatment_resistant_ocd → ocd_severity` · MA · protective
D9. `cbt_insomnia_chronic → insomnia_severity_index` · MA · protective
D10. `emdr → complex_ptsd_severity` · MA · protective
D11. `prolonged_exposure_therapy → ptsd_severity` · MA · protective
D12. `neurofeedback_for_adhd_children → adhd_symptom_severity` · MA · mixed
D13. `methylphenidate_extended_release_adults → adhd_adult_severity` · MA · protective
D14. `atomoxetine_adults → adhd_adult_severity` · MA · protective
D15. `cbt_for_eating_disorders_bulimia → bulimia_remission` · MA · protective
D16. `family_based_therapy_anorexia → weight_restoration` · MA · protective
D17. `clozapine_treatment_resistant_schizophrenia → relapse_prevention` · MA · protective
D18. `ssris_long_term → discontinuation_syndrome_risk` · MA · harmful
D19. `mindfulness_based_anxiety → trait_anxiety` · MA · mixed
D20. `internet_cbt_self_directed → depression_severity` · MA · protective
D21. `internet_cbt_self_directed → anxiety_severity` · MA · protective
D22. `transcranial_dcs → treatment_resistant_depression` · MA · mixed
D23. `transcranial_dcs → ocd_severity` · MA · mixed
D24. `ketogenic_diet_therapeutic → bipolar_mood_stabilization` · trials · mixed
D25. `low_carb_diet → mood_subjective` · trials · mixed
D26. `psychobiotic_probiotic → depression_severity` · MA · mixed
D27. `psychobiotic_probiotic → anxiety_severity` · MA · mixed
D28. `saffron_extract → adhd_children` · trials · mixed
D29. `inositol_high_dose → ocd_severity` · MA · mixed
D30. `n_acetylcysteine → ocd_severity` · MA · mixed

### Block E · Environmental & occupational exposures (30)

E1. `pfas_high_serum → thyroid_dysfunction` · MA · harmful
E2. `pfas_high_serum → kidney_function_decline` · cohort · harmful
E3. `pfas_high_serum → ldl_elevation` · MA · harmful
E4. `pfas_high_serum → hepatic_steatosis` · cohort · harmful
E5. `microplastics_blood_detected → vascular_inflammation_markers` · trials · mixed
E6. `light_at_night_chronic → metabolic_syndrome` · MA · harmful
E7. `light_at_night_chronic → breast_cancer_risk` · MA · harmful
E8. `street_light_outdoor_exposure → sleep_efficiency` · cohort · harmful
E9. `organophosphate_pesticides → child_neurodevelopment` · MA · harmful
E10. `wildfire_smoke_pm2_5 → cv_events` · cohort · harmful
E11. `wildfire_smoke_pm2_5 → respiratory_hospitalisation` · MA · harmful
E12. `household_air_pollution_biomass → copd_risk` · MA · harmful
E13. `mold_exposure_chronic → respiratory_symptoms_severity` · MA · harmful
E14. `indoor_voc_high → asthma_exacerbation` · MA · harmful
E15. `arsenic_drinking_water → cardiovascular_disease` · MA · harmful
E16. `lead_exposure_low_level → adult_hypertension` · MA · harmful
E17. `lead_exposure_low_level → cognitive_decline_elderly` · MA · harmful
E18. `mercury_fish_consumption → fetal_neurodevelopment` · MA · u_shaped
E19. `cadmium_chronic_exposure → kidney_function_decline` · MA · harmful
E20. `bpa_urine_high → metabolic_outcomes` · MA · mixed
E21. `phthalates_urine_high → reproductive_outcomes_men` · MA · harmful
E22. `occupational_pesticide_exposure → parkinsons_risk` · MA · harmful
E23. `occupational_diesel_exhaust_chronic → lung_cancer` · MA · harmful
E24. `occupational_silica_dust_chronic → silicosis_risk` · MA · harmful
E25. `occupational_asbestos_low_dose → mesothelioma_lifetime` · MA · harmful
E26. `occupational_radiation_low_dose → cancer_lifetime` · MA · harmful
E27. `occupational_chronic_noise_above_80db → hypertension` · MA · harmful
E28. `occupational_sedentary_long_chronic → cardiovascular_outcomes` · MA · harmful
E29. `commute_long_above_60min → mental_health_subjective` · cohort · harmful
E30. `green_space_residential → all_cause_mortality` · MA · protective

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
Same pace as Tracks 4–6: ~80 min per checkpoint of careful work,
~24 hours of total compute spread across many stepping cycles. The
validator catches fabrications, so quality is enforced automatically.

If a pair has no good evidence (rare), drop it from the set, leave a
note in your commit message, and move on. Submit a partial PR if
needed — anything ≥ 120 verified pairs is a useful merge.

**Expect a high `new_entities` count.** Track 7 introduces many
biomarker-with-threshold and exposure-with-dose entities that don't
exist yet. Adding `new_entities` blocks is normal and expected — just
keep the names canonical and reusable.

---

## Why this manifest specifically

1. **Block A (iatrogenic)** turns the corpus into an honest broker
   on common medications. Today the graph has lots of "X drug protects
   against Y outcome"; it's thinner on "X drug, taken long enough,
   causes Z." That's exactly what users want when they ask "what are
   the long-term costs of this drug?" — and what the pre-visit checkup
   page surfaces as "questions to ask your prescriber."

2. **Block B (biomarkers)** populates the per-lab evidence overlay on
   `/me/data` with tier-A reference points. Today a user adds a
   coronary calcium score and gets a thin response; after Track 7,
   the response is anchored in 3+ specific edges with effect sizes.

3. **Block C (pregnancy / fertility)** is the most underserved
   segment in the corpus. Track 5 covered some maternal programming;
   pre-conception, paternal factors, and IVF specifically were
   essentially blank. That market is willing to pay (Function Health
   sells a fertility panel for $499).

4. **Block D (mental health subtypes)** extends Track 5's depression-
   heavy mental-health work to the conditions that actually drive
   chronic morbidity in 18–35 year-olds: anxiety subtypes, OCD,
   adult ADHD, eating disorders. Each maps directly to factors people
   put in their Stack Brief.

5. **Block E (environmental exposures)** captures emerging public
   concern (PFAS, microplastics, light pollution, wildfire smoke)
   with strong recent literature. Differentiates us from products
   that only cover lifestyle/supplement factors.

---

## Paste-ready resume prompt

Use this single prompt to start and re-engage Codex on every wake:

```
Continue Track 7 on branch feat/codex-seed-batch-9 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V9_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort/case-control row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate.

Track 7 specifics:
- Block A iatrogenic edges should mostly be direction:harmful
- Block B biomarker factors should encode thresholds in the slug (e.g. lpa_high_above_125nmol)
- Block C will need many new_entities for paternal / preconception / IVF outcomes
- Block D may need new_entities for specific mental health outcome scales
- Block E often needs threshold-encoded exposure entities

Track progress via commit messages: 'Track 7: N/150 — topic'.

Skip silently if a payload file for the pair already exists on main or on your branch — do not re-research.
```
