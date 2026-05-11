# Codex brief v11 — autonomous Track 9

> **READ THIS FIRST: This brief keeps you working autonomously across
> stepping pauses. Do not stop after each pause to ask for approval.
> The loop below is your authority. Resume yourself. Done = the
> manifest is empty. Until then, keep going.**

Repo: `https://github.com/prokesmic/HealthUniverse` — branch from `main`.

## What's already done (don't redo)

- Track A (densify v1): merged
- Track 1 (densify v2): merged
- Track 2 (seed v5): merged
- Track 4 (seed v6 — hematology, gut-brain, geriatric, women's repro, paediatric): merged
- Track 5 (seed v7 — mental-health, cardiometabolic, sleep, vaccines, longevity): merged
- Track 6 (seed v8 — athletic, nootropics, hormonal, gut strains, skin/hair): merged
- Track 7 (seed v9 — iatrogenic, biomarkers, pregnancy, mental-health subtypes, exposures): merged
- Track 8 (seed v10 — rehab, behavior change, sensory health, FM claim verdicts, paediatric): merged
- **Current corpus: 1,851 edges · 6,868 evidence rows · 1,540 entities · 85.4% audited**

## What you're doing now

Track 9: 150 brand-new PMID-verified pairs across **five clinical-depth
blocks the corpus is still mostly silent on** (gap-analysis confirmed:
e.g. zero edges on `hfpef`, `aortic_stenosis`, `pad`, `hypoglossal_nerve_stim`,
`rem_behavior_disorder`, `graves_disease`, `t1d_islet` as of today):

1. **Cancer screening & surveillance** (30 pairs)
2. **Drug-specific risk/benefit deepening** (30 pairs)
3. **Cardiovascular subtypes — HFpEF, AF, AS, PAD, lipid escalation** (30 pairs)
4. **Sleep apnea phenotypes & sleep disorder subtypes** (30 pairs)
5. **Endocrine deep dive — thyroid optimization, T1D, adrenal, PCOS, Cushings** (30 pairs)

Manifest is **inline below**.

## The autonomous loop — do not stop until the manifest is empty

**Branch:** `feat/codex-seed-batch-11`

Repeat without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-11 main` (first run only;
   `git checkout feat/codex-seed-batch-11` thereafter).
2. Pick the next **5** unfinished items from the manifest. Skip
   silently if a payload file already exists for the pair.
3. For each picked item:
   - Search PubMed for ≥3 high-quality studies on that pair
   - Verify each PMID + journal + year via the `--verify` validator
   - Write the payload using the standard `seed_payload` shape
   - **Include `effect_quant` whenever the source paper reports a
     pooled estimate.**
   - **Block A (cancer screening) often has contested edges** —
     PSA routine, mammography 40-49, ovarian general-pop screening,
     dermatology full-body, MCED blood tests. Use
     `direction: contested` honestly where the evidence is split.
   - **Block B (drug specifics) factors encode the WHOLE situation**:
     `levothyroxine_with_ppi`, `ssri_with_tramadol`,
     `metoclopramide_chronic`. The factor slug captures both the
     drug and the modifier; outcome is the specific adverse / wanted
     effect.
4. `python3 seed_from_payloads.py validate --verify`. Fix failures.
5. `python3 seed_from_payloads.py ingest --dry-run`. Add `new_entities`
   blocks where needed — Track 9 introduces many drug-class +
   modifier entities, HF phenotype entities, OSA-subtype entities.
6. `git add data/seed_payloads/` and commit with format:
   ```
   Track 9: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-11`.
8. **Open the PR only when N=150.** Until then, push checkpoints to
   the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

After a stepping pause, re-read this file and continue. Inspect
`git status` on the branch, count finished payloads, pick up where
you left off. Commit messages of form `Track 9: N/150 — topic` make
your last checkpoint visible.

When the manifest is empty:
- Final `--verify validate` run with `0 failed`
- PR title: `Codex Track 9 — 150 verified pairs across cancer screening, drug specifics, CV subtypes, OSA, endocrine`
- PR description includes:
  - Full validator transcript ending `0 failed`
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows
  - Topic breakdown: pairs per block
  - Count of payloads with `effect_quant`
  - Count of payloads with `direction: contested` (expect Block A
    and Block B to land most of these)
  - Count of payloads that introduced `new_entities`

Update `CLAUDE_TRACK_HANDOFF.md` at PR-time to reflect Track 9
completion.

## Hard rules (same as every prior track)

- Never fabricate PMIDs (the nightly semantic verifier on main
  flags mismatches; Codex's own efetch fallback added in Track 8
  resolves esummary misses)
- Every meta-analysis / SR / RCT / cohort / case-control / cross-sectional
  row must include `n_participants`
- Don't pad with weak rows — one strong MA > three cross-sectionals
- Diversify research groups
- Prioritise post-2018; older only if seminal (NLST, NELSON, IMPROVE-IT,
  PARADIGM-HF, PARTNER 3, etc.)
- Never run `seed.py` or `adjudicate.py`
- Don't modify schema, cost cap, or anything in `AGENTS.md` "Avoid"
- Don't stage or remove `data/health.db`
- One PR per track, branched from `main`

## Track 9 quirks worth remembering

- **Block A trials to cite by name**: NLST + NELSON (lung), CNBSS
  (mammography 40-49), Welch & Mandelblatt analyses (mammography
  benefit estimates), CAP / PROBASE (PSA), USPSTF position
  statements on each.
- **Block B factors are dose/context-encoded** — `metformin_with_iv_contrast`,
  `oral_contraceptive_with_rifampin`. Not generic drug names.
- **Block C frequently needs trial names in `notes`** — DELIVER,
  EMPEROR-Preserved, PARAGON, PARTNER 3, EAST-AFNET 4, COLCOT,
  LoDoCo2, CLEAR Outcomes, DAPA-CKD, PATHWAY-2, SUMMIT,
  STEP-HFpEF, SCOT-HEART. Make the trial visible in
  `effect_quant`.
- **Block D OSA-specific landmark trials**: STAR (hypoglossal),
  SAVE (CPAP for CV), SERVE-HF (CSA in HF — caution; harmful
  for adaptive servo-ventilation in HFrEF).
- **Block E** introduces a clean separation: real adrenal
  insufficiency (Addison's, secondary, Cushing's) vs "adrenal
  fatigue" (which Track 8 already classified as contested).

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

### Block A · Cancer screening & surveillance (30)

A1. `mammography_biennial_50_74 → breast_cancer_mortality_reduction` · MA · protective
A2. `mammography_annual_40_49 → breast_cancer_mortality_reduction` · MA · contested
A3. `tomosynthesis_3d_mammography → breast_cancer_detection_rate` · MA · protective
A4. `mri_screening_dense_breast → cancer_detection_rate` · MA · protective
A5. `colonoscopy_screening_50_75 → colorectal_cancer_mortality` · MA · protective
A6. `fit_test_annual → colorectal_cancer_mortality` · MA · protective
A7. `cologuard_stool_dna_test → colorectal_cancer_detection` · MA · mixed
A8. `flexible_sigmoidoscopy → colorectal_cancer_mortality` · MA · protective
A9. `colonoscopy_interval_after_negative_10yr → cancer_incidence` · MA · protective
A10. `ldct_lung_screening_high_risk → lung_cancer_mortality` · MA · protective
A11. `ldct_lung_screening_population_low_risk → outcomes` · MA · contested
A12. `low_dose_aspirin_colorectal_chemo → cancer_incidence` · MA · u_shaped
A13. `tamoxifen_high_risk_breast → breast_cancer_incidence` · MA · protective
A14. `raloxifene_high_risk_breast → breast_cancer_incidence` · MA · protective
A15. `brca_prophylactic_mastectomy → breast_cancer_incidence` · MA · protective
A16. `brca_prophylactic_oophorectomy → ovarian_cancer_mortality` · MA · protective
A17. `hpv_dna_self_test_cervical → cervical_cancer_detection` · MA · protective
A18. `psa_screening_routine_men_55_69 → prostate_cancer_mortality` · MA · contested
A19. `mri_first_prostate_pathway → diagnostic_outcomes` · MA · protective
A20. `dermatology_full_body_skin_exam → melanoma_mortality` · MA · contested
A21. `self_skin_examination_monthly → melanoma_early_detection` · MA · mixed
A22. `multi_cancer_early_detection_blood → cancer_detection` · trials · mixed
A23. `galleri_cfdna_assay → cancer_detection_outcomes` · trials · mixed
A24. `testicular_self_exam → testicular_cancer_outcomes` · MA · contested
A25. `ovarian_screening_general_pop → ovarian_cancer_mortality` · MA · contested
A26. `ca125_high_risk_women → ovarian_cancer_detection` · MA · mixed
A27. `polyp_size_threshold_management → colorectal_cancer_outcomes` · MA · mixed
A28. `helicobacter_pylori_eradication → gastric_cancer_prevention` · MA · protective
A29. `transient_elastography_screening_hcc_high_risk → cancer_detection` · MA · mixed
A30. `endoscopic_surveillance_barrett_esophagus → adenocarcinoma_mortality` · MA · mixed

### Block B · Drug-specific risk/benefit deepening (30)

B1. `levothyroxine_morning_fasting → tsh_optimization` · MA · protective
B2. `levothyroxine_evening_dosing → tsh_optimization` · trials · mixed
B3. `levothyroxine_with_calcium → tsh_absorption` · trials · harmful
B4. `levothyroxine_with_coffee → tsh_absorption` · trials · harmful
B5. `levothyroxine_with_ppi → tsh_absorption` · MA · harmful
B6. `warfarin_after_leafy_green_intake_change → inr_variability` · cohort · harmful
B7. `metoclopramide_chronic → tardive_dyskinesia` · MA · harmful
B8. `methotrexate_without_folic_acid → mucositis_alopecia` · MA · harmful
B9. `methotrexate_with_folic_acid → adverse_events_reduction` · MA · protective
B10. `lithium_with_nsaids → lithium_toxicity_risk` · MA · harmful
B11. `ssri_with_tramadol → serotonin_syndrome_risk` · MA · harmful
B12. `ssri_with_st_johns_wort → serotonin_syndrome_risk` · MA · harmful
B13. `clopidogrel_with_ppi → cardiovascular_events_excess` · MA · contested
B14. `cyp3a4_strong_inhibitor_with_statin → rhabdomyolysis_risk` · MA · harmful
B15. `grapefruit_with_calcium_channel_blocker → hypotension_risk` · cohort · harmful
B16. `oral_contraceptive_with_broad_spectrum_antibiotic → contraceptive_failure` · MA · contested
B17. `oral_contraceptive_with_rifampin → contraceptive_failure` · MA · harmful
B18. `tetracycline_with_dairy → absorption_reduction` · MA · harmful
B19. `fluoroquinolone_with_iron_calcium → absorption_reduction` · MA · harmful
B20. `metformin_with_iv_contrast → contrast_nephropathy_risk` · MA · contested
B21. `ssri_during_pregnancy → child_outcomes` · MA · mixed
B22. `valproate_during_pregnancy → child_neurodevelopment` · MA · harmful
B23. `lithium_during_pregnancy → cardiac_anomaly_offspring` · MA · harmful
B24. `lamotrigine_during_pregnancy → child_outcomes` · MA · mixed
B25. `acid_suppression_in_infancy → allergy_risk_later` · cohort · harmful
B26. `opioids_during_breastfeeding → infant_outcomes` · MA · harmful
B27. `donepezil_rapid_dose_escalation → adverse_events` · MA · harmful
B28. `statin_intolerance_alternate_day → ldl_reduction` · trials · mixed
B29. `gabapentinoids_long_term → cognitive_outcomes_elderly` · MA · harmful
B30. `triptans_chronic_overuse → medication_overuse_headache` · MA · harmful

### Block C · Cardiovascular subtypes (30)

C1. `sglt2_inhibitor_hfpef → hf_hospitalization` · MA · protective
C2. `arni_sacubitril_valsartan_hfref → mortality` · MA · protective
C3. `mra_spironolactone_hfref → mortality` · MA · protective
C4. `icd_hfref_primary_prevention → sudden_cardiac_death` · MA · protective
C5. `crt_d_hfref_wide_qrs → mortality` · MA · protective
C6. `catheter_ablation_persistent_af → recurrence` · MA · protective
C7. `early_rhythm_control_af → cv_outcomes` · MA · protective
C8. `dronedarone_persistent_af → outcomes` · MA · contested
C9. `tavi_severe_aortic_stenosis_low_risk → mortality` · MA · protective
C10. `statin_aortic_stenosis_progression → progression_rate` · MA · contested
C11. `atorvastatin_high_dose_pad → cv_events_pad` · MA · protective
C12. `cilostazol_pad → claudication_distance` · MA · protective
C13. `supervised_exercise_therapy_pad → walking_distance` · MA · protective
C14. `ezetimibe_post_acs → mace` · MA · protective
C15. `pcsk9_inhibitor_post_acs → mace` · MA · protective
C16. `inclisiran_long_term → ldl_reduction` · trials · protective
C17. `bempedoic_acid_statin_intolerant → mace` · MA · protective
C18. `colchicine_low_dose_post_mi → recurrent_cv_events` · MA · protective
C19. `dapagliflozin_ckd_non_diabetic → kidney_outcomes` · MA · protective
C20. `spironolactone_resistant_hypertension → bp_outcomes` · MA · protective
C21. `renal_denervation_resistant_htn → bp_outcomes` · MA · mixed
C22. `left_atrial_appendage_occlusion_af → stroke_outcomes` · MA · protective
C23. `tirzepatide_hfpef_obesity → outcomes` · trials · protective
C24. `semaglutide_hfpef_obesity → outcomes` · MA · protective
C25. `lipoprotein_apheresis_extreme_lpa → cv_outcomes` · cohort · protective
C26. `coronary_ct_angiography_chest_pain → diagnostic_outcomes` · MA · protective
C27. `nstemi_invasive_strategy → mace` · MA · protective
C28. `stable_cad_invasive_vs_optimal_medical → outcomes` · MA · contested
C29. `endovascular_therapy_acute_large_vessel_stroke → mortality_disability` · MA · protective
C30. `dual_antiplatelet_post_pci_duration → bleeding_vs_ischemia` · MA · u_shaped

### Block D · Sleep apnea & sleep disorder subtypes (30)

D1. `cpap_severe_osa → cardiovascular_outcomes` · MA · contested
D2. `cpap_severe_osa → daytime_sleepiness` · MA · protective
D3. `cpap_severe_osa → resistant_hypertension` · MA · protective
D4. `cpap_osa → glycemic_control_t2d` · MA · mixed
D5. `cpap_mild_osa → quality_of_life` · MA · mixed
D6. `weight_loss_10pct_osa → ahi_reduction` · MA · protective
D7. `tongue_strengthening_myofunctional → ahi_reduction` · MA · mixed
D8. `uvulopalatopharyngoplasty → osa_severity` · MA · mixed
D9. `hypoglossal_nerve_stimulation_osa → ahi_reduction` · MA · protective
D10. `maxillomandibular_advancement_osa → ahi_reduction` · MA · protective
D11. `positional_therapy_supine_predominant_osa → ahi` · MA · protective
D12. `mandibular_advancement_device_mild_moderate → ahi` · MA · protective
D13. `home_sleep_apnea_test → diagnosis_accuracy` · MA · protective
D14. `wearable_oximetry_osa_screening → diagnosis` · MA · mixed
D15. `pediatric_adenotonsillectomy_osa → outcomes` · MA · protective
D16. `adaptive_servo_ventilation_csa_hfref → mortality` · MA · harmful
D17. `acetazolamide_csa → ahi` · MA · mixed
D18. `modafinil_narcolepsy_type_1 → wakefulness` · MA · protective
D19. `sodium_oxybate_narcolepsy → cataplexy` · MA · protective
D20. `solriamfetol_narcolepsy → wakefulness` · MA · protective
D21. `pitolisant_narcolepsy → daytime_sleepiness` · MA · protective
D22. `ropinirole_rls → severity` · MA · protective
D23. `gabapentin_enacarbil_rls → severity` · MA · protective
D24. `iron_repletion_rls_ferritin_low → severity` · MA · protective
D25. `melatonin_rem_behavior_disorder → episodes` · MA · protective
D26. `clonazepam_rem_behavior_disorder → episodes` · MA · protective
D27. `shift_work_disorder_modafinil → wakefulness` · MA · protective
D28. `dual_orexin_antagonist_chronic_insomnia → sleep_onset` · MA · protective
D29. `doxepin_low_dose_insomnia → sleep_maintenance` · MA · protective
D30. `light_therapy_advanced_sleep_phase → sleep_timing` · MA · protective

### Block E · Endocrine deep dive (30)

E1. `levothyroxine_subclinical_hypothyroid_tsh_4_to_10 → cv_outcomes` · MA · contested
E2. `levothyroxine_subclinical_hypothyroid_elderly → quality_of_life` · MA · mixed
E3. `liothyronine_addition_hypothyroid → wellbeing` · MA · contested
E4. `desiccated_thyroid_extract → wellbeing` · trials · mixed
E5. `selenium_hashimoto → tpoab_levels` · MA · mixed
E6. `iodine_excess_in_iodine_replete → autoimmune_thyroid_risk` · cohort · harmful
E7. `low_iodine_pregnancy → child_neurodevelopment` · MA · harmful
E8. `graves_disease_thyroidectomy → outcomes` · MA · protective
E9. `graves_disease_radioactive_iodine → graves_orbitopathy` · MA · harmful
E10. `graves_disease_antithyroid_long_term → relapse` · MA · mixed
E11. `carbimazole_pregnancy → congenital_anomaly_risk` · MA · harmful
E12. `cinacalcet_secondary_hyperparathyroidism → outcomes` · MA · protective
E13. `inositol_pcos_ovulation → ovulation_rate` · MA · protective
E14. `spironolactone_pcos_hirsutism → outcomes` · MA · protective
E15. `semaglutide_pcos → outcomes` · trials · protective
E16. `orlistat_pcos → metabolic_outcomes` · MA · mixed
E17. `cgm_t2d_no_insulin → hba1c` · MA · mixed
E18. `closed_loop_t1d → time_in_range` · MA · protective
E19. `islet_transplant_t1d → insulin_independence` · MA · mixed
E20. `teplizumab_t1d_at_risk → onset_delay` · trials · protective
E21. `hydrocortisone_chronic_addisons → quality_of_life` · MA · mixed
E22. `fludrocortisone_chronic_addisons → bp_outcomes` · MA · protective
E23. `dhea_addisons_women → quality_of_life` · MA · mixed
E24. `pasireotide_cushings_disease → cortisol` · MA · protective
E25. `metyrapone_cushings → cortisol` · MA · protective
E26. `osilodrostat_cushings → cortisol` · trials · protective
E27. `growth_hormone_adult_deficiency → quality_of_life` · MA · mixed
E28. `bromocriptine_macroprolactinoma → tumor_reduction` · MA · protective
E29. `cabergoline_prolactinoma → outcomes` · MA · protective
E30. `kisspeptin_hypogonadotropic → testosterone_recovery` · trials · mixed

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
Same pace as Tracks 4–8: ~80 min per checkpoint of careful work,
~24 hours of total compute spread across many stepping cycles.

If a pair has no good evidence (rare), drop it from the set, leave a
note in your commit message, and move on. Submit a partial PR if
needed — anything ≥ 120 verified pairs is a useful merge.

**Expect a high `new_entities` count.** Track 9 introduces many
HF-phenotype, OSA-subtype, drug-class-with-modifier, and rare-
endocrine-disease entities not yet in the graph.

---

## Why this manifest specifically

1. **Block A (cancer screening)** — every adult navigates these
   decisions. Today the corpus has 2 mammography edges and 2
   colonoscopy edges. The pre-visit checkup page can't currently
   surface "the case for / against screening X" because the corpus
   doesn't carry it. After Track 9, that's solved across breast,
   colorectal, lung, prostate, cervix, ovarian, skin, gastric, and
   liver cancer screening.

2. **Block B (drug specifics)** — the corpus already has many
   "drug class → outcome" edges from Track 5/7. What's missing is
   the *contextual* edges: levothyroxine taken after coffee
   (absorbed less), warfarin with leafy-green diet change (INR
   destabilises), methotrexate without folate (mucositis), SSRI +
   tramadol (serotonin syndrome). These are the practical questions
   patients have AT THE PHARMACY counter.

3. **Block C (CV subtypes)** — the corpus has CVD-as-monolithic.
   But cardiology has split into HFpEF vs HFrEF, AF management
   pathways, PAD as its own disease, lipid escalation (PCSK9 →
   inclisiran → bempedoic), aortic stenosis trajectory. Each
   pathway has a recent landmark trial. After Track 9, the
   recommendation engine has these phenotype-specific edges.

4. **Block D (OSA/sleep disorder subtypes)** — OSA affects ~30%
   of adults and is dramatically undertreated. Today the corpus
   has CPAP (general) and weight-loss (general) only. After Track
   9: hypoglossal-nerve-stim (Inspire), positional therapy, MAD,
   maxillomandibular advancement, narcolepsy types, RLS subtype
   management, REM-behavior-disorder management.

5. **Block E (endocrine deep dive)** — distinguishes REAL adrenal
   insufficiency (Addison's, Cushing's) from "adrenal fatigue"
   (Track 8 already covered as contested). Also fills in
   thyroid optimization questions (LT4 timing, T3 augmentation,
   subclinical hypothyroid treatment threshold) that patients
   most often ask about.

---

## Paste-ready resume prompt

```
Continue Track 9 on branch feat/codex-seed-batch-11 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V11_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort/case-control row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate.

Track 9 specifics:
- Block A cancer screening: many honest contested edges (PSA routine, mammography 40-49, dermatology full-body, MCED, ovarian general-pop)
- Block B drug specifics encode the WHOLE situation in the factor slug (levothyroxine_with_ppi, ssri_with_tramadol)
- Block C trial names belong in effect_quant (DELIVER, EMPEROR-Preserved, PARTNER 3, EAST-AFNET 4, CLEAR Outcomes, COLCOT, etc.)
- Block D SERVE-HF: adaptive servo-ventilation in CSA + HFrEF is HARMFUL (mortality increase)
- Block E distinguishes real adrenal insufficiency from the "adrenal fatigue" classified contested in Track 8

Track progress via commit messages: 'Track 9: N/150 — topic'.

Skip silently if a payload file for the pair already exists on main or on your branch — do not re-research.
```
