# Codex brief v7 — autonomous Track 5

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
- **Current corpus: 1,208 edges · 4,892 evidence rows · 2,438 PMIDs · effect_quant 83 %**

## What you're doing now

Track 5: 150 brand-new PMID-verified pairs across **five clinically
high-value areas that are still thin in the graph**:

1. **Mental-health interventions × specific conditions** (30 pairs)
2. **Cardiometabolic medications × outcomes** (30 pairs)
3. **Sleep & circadian interventions × outcomes** (30 pairs)
4. **Vaccines × specific outcomes** (30 pairs)
5. **Longevity / aging interventions × outcomes** (30 pairs)

Manifest is **inline below**.

## The autonomous loop — do not stop until the manifest is empty

**Branch:** `feat/codex-seed-batch-7`

Repeat without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-7 main` (first run only;
   `git checkout feat/codex-seed-batch-7` thereafter).
2. Pick the next **5** unfinished items from the manifest. An item is
   "finished" if `data/seed_payloads/{factor_slug}__{outcome_slug}.json`
   already exists on this branch *or* on `main`. **Skip silently** if
   already present — do not re-research.
3. For each picked item:
   - Search PubMed for ≥3 high-quality studies on that pair
   - Verify each PMID + journal + year via the `--verify` validator
   - Write the payload using the standard `seed_payload` shape (same
     as Track 4 — see CODEX_BRIEF_V6_AUTONOMOUS.md "Required payload
     shape" section if you need a reminder)
   - **Include `effect_quant` whenever the source paper reports a
     pooled estimate.** The UI relies on it.
4. `python3 seed_from_payloads.py validate --verify` over the new
   files. Fix any failures by replacing the offending PMID. Keep going
   until 0 failed.
5. `python3 seed_from_payloads.py ingest --dry-run`. If a slug doesn't
   resolve, add a `new_entities` block to that payload.
6. `git add data/seed_payloads/` and commit with format:
   ```
   Track 5: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-7`.
8. **Open the PR only when N=150.** Until then, push checkpoints to
   the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

After a stepping pause, re-read this file and continue. The standing
order is the loop above. Inspect `git status` on the branch, count
finished payloads, pick up where you left off. Commit messages of
form `Track 5: N/150 — topic` make your last checkpoint visible.

When the manifest is empty:
- Final `--verify validate` run with `0 failed`
- PR title: `Codex Track 5 — 150 verified pairs across 5 high-value clinical areas`
- PR description includes:
  - Full validator transcript ending `0 failed`
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows
  - Topic breakdown: pairs per block
  - Count of payloads with `effect_quant`

## Hard rules (same as every prior track)

- Never fabricate PMIDs (the validator catches it)
- Every meta-analysis / SR / RCT / cohort row must include `n_participants`
- Don't pad with weak rows — one strong meta-analysis > three cross-sectionals
- Diversify research groups
- Prioritise post-2018; older only if seminal
- Never run `seed.py` or `adjudicate.py`
- Don't modify schema, cost cap, or anything in `AGENTS.md` "Avoid"
- One PR per track, branched from `main`

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

Skip silently if a payload file already exists for the pair. Tier is
your decision based on the actual literature; the listed direction is
your starting hypothesis.

### Block A · Mental-health interventions × specific conditions (30)

A1. `cbt_for_insomnia → chronic_insomnia` · MA, gold standard · protective
A2. `cbt_trauma_focused → ptsd` · network MA · protective
A3. `eye_movement_desensitisation_reprocessing → ptsd` · vs trauma-CBT · protective
A4. `behavioural_activation → major_depressive_disorder` · MA · protective
A5. `interpersonal_psychotherapy → major_depressive_disorder` · MA · protective
A6. `mindfulness_based_cognitive_therapy → depression_relapse_prevention` · MA · protective
A7. `dialectical_behaviour_therapy → borderline_personality_disorder_self_harm` · RCTs · protective
A8. `acceptance_commitment_therapy → chronic_pain_function` · MA · protective
A9. `prolonged_exposure_therapy → ptsd` · MA · protective
A10. `cbt_for_chronic_pain → chronic_pain_intensity` · MA · protective
A11. `repetitive_tms → treatment_resistant_depression` · MA · protective
A12. `electroconvulsive_therapy → treatment_resistant_depression` · MA · protective
A13. `iv_ketamine → treatment_resistant_depression` · MA short-term · protective
A14. `intranasal_esketamine → treatment_resistant_depression` · phase-3 RCTs · protective
A15. `psilocybin_assisted_therapy → treatment_resistant_depression` · 2024 trials · protective
A16. `mdma_assisted_therapy → ptsd` · MAPS phase-3 · protective
A17. `ssris → major_depressive_disorder` · network MA · protective
A18. `snris → major_depressive_disorder_severe` · MA · protective
A19. `atypical_antipsychotic_augmentation → trd` · adjunct trials · protective
A20. `lithium → bipolar_mania_acute` · MA · protective
A21. `lithium_maintenance → bipolar_relapse_prevention` · MA · protective
A22. `lamotrigine → bipolar_depression_maintenance` · MA · protective
A23. `valproate → bipolar_mania_acute` · MA · protective
A24. `clozapine → treatment_resistant_schizophrenia` · CATIE-style · protective
A25. `olanzapine → bipolar_mania_acute` · MA · protective
A26. `methylphenidate → adhd_children` · MA · protective
A27. `atomoxetine → adhd_adults` · RCTs · protective
A28. `lisdexamfetamine → adhd_adults` · phase-3 trials · protective
A29. `naltrexone → alcohol_use_disorder` · COMBINE-style MA · protective
A30. `acamprosate → alcohol_use_disorder` · MA · protective

### Block B · Cardiometabolic medications × outcomes (30)

B1. `high_intensity_statins → major_adverse_cardiac_events_high_risk` · MA · protective
B2. `moderate_intensity_statins → mace_low_risk_primary_prevention` · MA · protective
B3. `ezetimibe → ldl_reduction` · IMPROVE-IT-style · protective
B4. `pcsk9_inhibitors → cv_events_high_risk` · FOURIER, ODYSSEY · protective
B5. `icosapent_ethyl → cv_events_residual_risk` · REDUCE-IT · protective
B6. `fenofibrate → triglycerides_metabolic_syndrome` · MA · protective
B7. `sglt2_inhibitors → all_cause_mortality_t2d` · MA · protective
B8. `glp1_agonists → cv_events_t2d` · LEADER/SUSTAIN-style MA · protective
B9. `semaglutide → weight_loss_obesity_no_diabetes` · STEP trials · protective
B10. `tirzepatide → weight_loss` · SURPASS/SURMOUNT · protective
B11. `metformin → all_cause_mortality_t2d` · UKPDS-derived MA · protective
B12. `acarbose → glycaemic_control_t2d` · MA · protective
B13. `spironolactone → heart_failure_mortality` · RALES, EPHESUS · protective
β14. `eplerenone → heart_failure_mortality_post_mi` · EPHESUS · protective
B15. `sacubitril_valsartan → heart_failure_mortality` · PARADIGM-HF · protective
B16. `dapagliflozin → heart_failure_preserved_ef_outcomes` · DELIVER · protective
B17. `empagliflozin → ckd_progression_t2d` · EMPA-KIDNEY · protective
B18. `finerenone → kidney_outcomes_t2d_ckd` · FIDELIO · protective
B19. `continuous_glucose_monitoring → glycaemic_control_t1d` · MA · protective
B20. `continuous_glucose_monitoring → glycaemic_control_t2d_basal_insulin` · MA · protective
B21. `low_carbohydrate_diet → hba1c_t2d` · MA · protective
B22. `time_restricted_eating → weight_loss_overweight` · MA · protective
B23. `mind_diet → cognitive_decline` · cohorts · protective
B24. `plant_based_diet → ldl_cholesterol` · MA · protective
B25. `polypill_cv_prevention → cardiovascular_events_low_resource` · TIPS-3 · protective
B26. `low_dose_aspirin_secondary_prevention → secondary_cv_events` · MA · protective
B27. `apixaban → atrial_fibrillation_stroke_prevention` · ARISTOTLE · protective
B28. `rivaroxaban → vte_secondary_prevention` · EINSTEIN · protective
B29. `clopidogrel → secondary_stroke_prevention` · CAPRIE · protective
B30. `dual_antiplatelet → stent_thrombosis_prevention` · MA · protective

### Block C · Sleep & circadian interventions × outcomes (30)

C1. `cpap_adherent → severe_osa_cv_outcomes` · MA · protective
C2. `mandibular_advancement_device → mild_moderate_osa` · MA · protective
C3. `positional_therapy → positional_osa` · MA · protective
C4. `weight_loss_intervention → osa_severity` · MA · protective
C5. `low_dose_melatonin → jet_lag_recovery` · MA · protective
C6. `low_dose_melatonin → sleep_onset_elderly` · MA · protective
C7. `ramelteon → sleep_onset_latency` · MA · protective
C8. `dual_orexin_antagonists → chronic_insomnia` · MA · protective
C9. `morning_bright_light_therapy → seasonal_affective_disorder` · MA · protective
C10. `morning_bright_light_therapy → delayed_sleep_phase_disorder` · MA · protective
C11. `evening_blue_light_blocking → melatonin_suppression` · RCTs · protective
C12. `evening_screen_use → subjective_sleep_quality` · MA · harmful
C13. `bedroom_temperature_cool → sleep_quality` · MA · protective
C14. `weighted_blanket → chronic_insomnia` · RCTs · protective
C15. `valerian_extract → sleep_quality` · MA · mixed
C16. `magnesium_glycinate → subjective_sleep_quality` · RCTs · mixed
C17. `lavender_aromatherapy → sleep_quality` · MA · protective
C18. `chin_strap_or_mouth_taping → mild_osa_subjective` · trials · mixed
C19. `lateral_sleep_position → osa_severity` · MA · protective
C20. `stimulus_control_therapy → chronic_insomnia` · MA · protective
C21. `sleep_restriction_therapy → chronic_insomnia` · MA · protective
C22. `nicotine_evening → sleep_onset_latency` · MA · harmful
C23. `shift_work_chronic → all_cause_mortality` · MA · harmful
C24. `night_shift_work → breast_cancer_women` · MA · harmful
C25. `chronic_circadian_misalignment → metabolic_syndrome` · MA · harmful
C26. `daytime_nap_under_30min → afternoon_alertness` · MA · protective
C27. `daytime_nap_over_60min → night_insomnia` · cohorts · harmful
C28. `caffeine_more_than_6h_before_bed → sleep_quality` · MA · neutral
C29. `regular_sleep_schedule → cardiometabolic_outcomes` · cohorts · protective
C30. `obstructive_sleep_apnea → atrial_fibrillation_recurrence` · MA · harmful

### Block D · Vaccines × specific outcomes (30)

D1. `influenza_vaccine_elderly → all_cause_mortality_winter` · MA · protective
D2. `influenza_vaccine_elderly → hospitalisation_winter` · MA · protective
D3. `influenza_vaccine_pregnancy → maternal_flu_infection` · MA · protective
D4. `high_dose_flu_vaccine_65plus → laboratory_confirmed_influenza` · MA · protective
D5. `rsv_vaccine_60plus → severe_rsv_disease` · phase-3 trials · protective
D6. `rsv_vaccine_pregnancy → infant_rsv_severe` · MATISSE-style · protective
D7. `recombinant_zoster_vaccine → herpes_zoster` · ZOE trials · protective
D8. `recombinant_zoster_vaccine → postherpetic_neuralgia` · MA · protective
D9. `pneumococcal_pcv13 → invasive_pneumococcal_disease_elderly` · MA · protective
D10. `pneumococcal_ppsv23 → community_acquired_pneumonia_elderly` · MA · mixed
D11. `mrna_covid_boosters → severe_covid_disease_elderly` · MA · protective
D12. `tdap_pregnancy → infant_pertussis` · MA · protective
D13. `mmr_first_dose → measles_in_unvaccinated_communities` · MA · protective
D14. `hpv_vaccine_men → oropharyngeal_cancer` · cohorts · protective
D15. `rotavirus_vaccine → severe_rotaviral_diarrhoea` · MA · protective
D16. `meningococcal_b_vaccine → invasive_meningococcal_b_disease` · MA · protective
D17. `typhoid_vaccine → travel_typhoid_infection` · MA · protective
D18. `yellow_fever_vaccine → yellow_fever_in_endemic_areas` · MA · protective
D19. `hepatitis_a_vaccine → outbreak_hav_in_close_contacts` · MA · protective
D20. `mpox_jynneos_vaccine → mpox_disease` · cohorts · protective
D21. `cholera_oral_vaccine → travel_cholera` · MA · protective
D22. `dengue_vaccine_in_seropositives → severe_dengue` · MA · protective
D23. `malaria_rts_s_vaccine → childhood_clinical_malaria` · phase-3 · protective
D24. `bcg_birth → severe_childhood_tb` · MA · protective
D25. `polio_inactivated_vaccine → paralytic_polio` · MA · protective
D26. `varicella_vaccine_childhood → severe_varicella` · MA · protective
D27. `flu_vaccine_health_workers → workplace_flu_transmission` · cohorts · protective
D28. `tdap_adolescent → pertussis_outbreaks` · MA · protective
D29. `hib_vaccine → invasive_hib_disease` · MA · protective
D30. `combined_dtap_polio_hib → infant_serious_infections` · MA · protective

### Block E · Longevity / aging interventions × outcomes (30)

E1. `caloric_restriction_humans → biomarkers_of_aging` · CALERIE · protective
E2. `metformin_in_non_diabetics → all_cause_mortality` · cohort observational · mixed
E3. `low_dose_rapamycin → biomarkers_of_aging_humans` · early trials · u_shaped
E4. `nicotinamide_riboside → nad_levels_humans` · RCTs · protective
E5. `nicotinamide_mononucleotide → biomarkers_of_aging` · trials · mixed
E6. `resveratrol → cardiovascular_outcomes` · MA · mixed
E7. `spermidine → cognitive_function_elderly` · trials · mixed
E8. `urolithin_a → muscle_function_elderly` · RCT · protective
E9. `low_dose_naltrexone → chronic_pain_outcomes` · trials · mixed
E10. `taurine_supplementation → biomarkers_of_aging` · early trials · u_shaped
E11. `glycine_nac_combined → glutathione_in_aged` · trials · protective
E12. `fisetin → senescent_cells_humans` · phase-2 · u_shaped
E13. `dasatinib_quercetin_senolytic → senescent_cell_burden` · phase-2 · mixed
E14. `bdnf_inducing_exercise → cognitive_aging_decline` · MA · protective
E15. `cold_water_immersion → mood_and_inflammation` · MA · mixed
E16. `frequent_finnish_sauna → all_cause_mortality` · KIHD cohort · protective
E17. `frequent_finnish_sauna → dementia_risk` · KIHD cohort · protective
E18. `zone_2_endurance_training → vo2max_aging` · RCT · protective
E19. `progressive_resistance_training → sarcopenia_elderly` · MA · protective
E20. `protein_intake_elderly → muscle_mass_strength` · MA · protective
E21. `creatine_in_older_adults → muscle_strength` · MA · protective
E22. `hmb_in_older_adults → muscle_mass_during_bedrest` · MA · protective
E23. `omega3_in_older_adults → muscle_function` · MA · mixed
E24. `anti_inflammatory_diet → biological_age` · cohorts · protective
E25. `social_engagement_elderly → all_cause_mortality` · MA · protective
E26. `purpose_in_life → all_cause_mortality` · MA · protective
E27. `forest_bathing → biomarkers_of_inflammation` · trials · protective
E28. `vagal_tone_via_meditation → all_cause_mortality` · cohorts · mixed
E29. `optimism → all_cause_mortality` · MA cohorts · protective
E30. `loneliness_chronic → all_cause_mortality` · MA · harmful

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
Same pace as Track 4: ~80 min per checkpoint of careful work, ~24 hours
of total compute spread across many stepping cycles. The validator
catches fabrications, so quality is enforced automatically.

If a pair has no good evidence (rare), drop it from the set, leave a
note in your commit message, and move on. Submit a partial PR if
needed — anything ≥ 120 verified pairs is a useful merge.

---

## Paste-ready resume prompt

Use this single prompt to start and re-engage Codex on every wake:

```
Continue Track 5 on branch feat/codex-seed-batch-7 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V7_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate.

Track progress via git commit messages of the form 'Track 5: N/150 — topic'. To resume, count payloads on the branch and pick up where you left off.

Skip silently if a payload file for the pair already exists on main or on your branch — do not re-research.
```
