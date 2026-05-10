# Codex brief v10 — autonomous Track 8

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
- Track 7 (seed v9 — iatrogenic, biomarkers, pregnancy, mental-health subtypes, exposures): in flight on feat/codex-seed-batch-9
- **Current corpus (pre-Track 7 ingest): 1,551 edges · 5,961 evidence rows · 1,068 entities**

## What you're doing now

Track 8: 150 brand-new PMID-verified pairs across **five blocks that
the corpus is currently nearly empty on** — each one was a deliberate
gap-analysis pick (see "Why this manifest" below):

1. **Recovery & rehabilitation** (30 pairs) — only 1 edge in corpus today
2. **Health behavior change interventions** (30 pairs) — 0 edges today
3. **Dental, vision & hearing health** (30 pairs) — only ~10 edges combined
4. **Functional medicine claims with evidence verdicts** (30 pairs) — high-value for the new /claim-check feature
5. **Pediatric & adolescent** (30 pairs) — 0 ADHD-child edges today

Manifest is **inline below**.

## The autonomous loop — do not stop until the manifest is empty

**Branch:** `feat/codex-seed-batch-10`

Repeat without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-10 main` (first run only;
   `git checkout feat/codex-seed-batch-10` thereafter).
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
     pooled estimate.**
   - **Block D items are deliberately many `contested` or `mixed`.**
     This is correct. The new /claim-check feature on production
     uses these specifically to give honest verdicts on functional
     medicine claims. Don't force "protective" or "harmful" — the
     point is to capture the contested state of the literature.
4. `python3 seed_from_payloads.py validate --verify` over the new
   files. Fix any failures by replacing the offending PMID. Keep going
   until 0 failed.
5. `python3 seed_from_payloads.py ingest --dry-run`. If a slug doesn't
   resolve, add a `new_entities` block to that payload. **Track 8
   will introduce many new outcome entities** (post-surgical
   outcomes, rehab milestones, sensory outcomes) — that's normal.
6. `git add data/seed_payloads/` and commit with format:
   ```
   Track 8: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-10`.
8. **Open the PR only when N=150.** Until then, push checkpoints to
   the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

After a stepping pause, re-read this file and continue. The standing
order is the loop above. Inspect `git status` on the branch, count
finished payloads, pick up where you left off. Commit messages of
form `Track 8: N/150 — topic` make your last checkpoint visible.

When the manifest is empty:
- Final `--verify validate` run with `0 failed`
- PR title: `Codex Track 8 — 150 verified pairs across rehab, behavior change, sensory, functional-medicine claims, paediatric`
- PR description includes:
  - Full validator transcript ending `0 failed`
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows
  - Topic breakdown: pairs per block
  - Count of payloads with `effect_quant`
  - **Count of payloads with `direction: contested`** — Block D is
    designed to land most of these here
  - Count of payloads that introduced `new_entities`

Update `CLAUDE_TRACK_HANDOFF.md` at PR-time to reflect Track 8
completion (replace the Track 7 paragraph; keep the same template).

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

## Track 8 quirks worth remembering

- **Block A (rehab) factors typically encode a population + setting**:
  `cardiac_rehab_post_mi`, `pulmonary_rehab_post_covid`,
  `stroke_rehab_constraint_induced_movement`. Mirror that pattern.
- **Block B (behavior change) factors are intervention names, not
  general behaviors**: `motivational_interviewing`,
  `financial_incentives_smoking_cessation`. These are the actual
  trial arms.
- **Block D contested edges** — for items like `adrenal_fatigue_concept`
  or `coffee_enema_detox`, write the payload as a contested edge
  (`direction: "contested"` or `tier: "X"`) and cite the
  systematic reviews / position statements that conclude the claim
  isn't supported. The /claim-check feature uses these directly.
- **Block E (paediatric) often has new outcome scales** —
  `child_iq`, `bmi_z_score`, `adolescent_mental_health`. Declare
  in `new_entities` as needed.

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

Skip silently if a payload file already exists for the pair. Tier is
your decision based on the literature; the listed direction is your
starting hypothesis.

### Block A · Recovery & rehabilitation (30)

A1. `cardiac_rehabilitation_post_mi → all_cause_mortality_post_mi` · MA · protective
A2. `cardiac_rehab_high_intensity_interval → vo2max_post_mi` · MA · protective
A3. `tele_cardiac_rehab → adherence_outcomes` · MA · protective
A4. `cardiac_rehab_women → adherence` · cohort · mixed
A5. `early_mobilization_post_surgery → length_of_stay` · MA · protective
A6. `eras_protocol_colorectal → post_surgical_outcomes` · MA · protective
A7. `pulmonary_rehab_copd → exercise_capacity` · MA · protective
A8. `pulmonary_rehab_post_covid → dyspnea_long_covid` · trials · mixed
A9. `paced_activity_long_covid → symptom_burden` · trials · mixed
A10. `low_dose_naltrexone_long_covid → symptom_severity` · trials · mixed
A11. `constraint_induced_movement_stroke → upper_limb_function` · MA · protective
A12. `mirror_therapy_stroke → upper_limb_recovery` · MA · protective
A13. `robotic_assisted_stroke_rehab → motor_recovery` · MA · mixed
A14. `transcranial_magnetic_stim_stroke → motor_function` · MA · mixed
A15. `fluoxetine_post_stroke_motor → motor_recovery` · MA · contested
A16. `early_mobilization_post_stroke → outcomes_modified_rankin` · MA · u_shaped
A17. `swallowing_therapy_post_stroke → dysphagia_recovery` · MA · protective
A18. `vestibular_rehabilitation_concussion → symptom_resolution` · MA · protective
A19. `cognitive_rehabilitation_post_concussion → cognitive_outcomes` · MA · mixed
A20. `post_concussion_subsymptom_aerobic → recovery_time` · MA · protective
A21. `peer_support_cancer_survivorship → quality_of_life` · MA · protective
A22. `supervised_exercise_during_chemotherapy → fatigue` · MA · protective
A23. `supervised_exercise_post_chemo_breast → recurrence_risk` · cohort · protective
A24. `pelvic_floor_pt_post_prostatectomy → continence_recovery` · MA · protective
A25. `pelvic_floor_pt_postpartum → urinary_incontinence` · MA · protective
A26. `blood_flow_restriction_rehab_post_acl → quadriceps_strength` · MA · protective
A27. `early_pt_post_acl_repair → return_to_sport` · MA · mixed
A28. `virtual_reality_stroke_rehab → motor_recovery` · MA · mixed
A29. `icu_acquired_weakness_early_mobilization → muscle_preservation` · MA · protective
A30. `community_pulmonary_rehab → copd_readmissions` · MA · protective

### Block B · Health behavior change interventions (30)

B1. `motivational_interviewing → substance_use_reduction` · MA · protective
B2. `motivational_interviewing → medication_adherence` · MA · protective
B3. `cbt_smoking_cessation → quit_rate_long_term` · MA · protective
B4. `financial_incentives_smoking_cessation → quit_rate` · MA · protective
B5. `financial_incentives_weight_loss → weight_loss_outcomes` · MA · mixed
B6. `text_message_intervention → medication_adherence` · MA · protective
B7. `app_based_habit_tracking → adherence_outcomes` · MA · mixed
B8. `peer_support_groups → weight_loss_maintenance` · MA · protective
B9. `social_network_smoking_intervention → quit_rate` · MA · protective
B10. `choice_architecture_defaults → behavior_change` · MA · protective
B11. `implementation_intentions → behavior_completion_rate` · MA · protective
B12. `mindfulness_relapse_prevention → substance_use_recurrence` · MA · mixed
B13. `habit_stacking → exercise_adherence` · trials · mixed
B14. `positive_psychology_intervention → wellbeing_subjective` · MA · protective
B15. `self_monitoring_dietary_intake → weight_loss` · MA · protective
B16. `self_monitoring_blood_glucose_t2d_non_insulin → hba1c` · MA · mixed
B17. `self_monitoring_blood_pressure_home → bp_control` · MA · protective
B18. `accountability_partner → exercise_adherence` · trials · mixed
B19. `nutrition_education_intervention → diet_quality` · MA · mixed
B20. `cooking_classes_intervention → diet_quality` · MA · protective
B21. `transtheoretical_stages_intervention → behavior_change` · MA · mixed
B22. `acceptance_commitment_lifestyle → behavior_outcomes` · MA · protective
B23. `workplace_wellness_program → biometric_outcomes` · MA · mixed
B24. `group_lifestyle_intervention_dpp → t2d_incidence` · MA · protective
B25. `telephone_health_coaching → behavior_outcomes` · MA · protective
B26. `digital_therapeutics_prescribed → outcomes_disease_specific` · MA · mixed
B27. `gamification_health_behavior → engagement_completion` · MA · mixed
B28. `cash_transfers_population_health → mortality` · MA · protective
B29. `community_health_worker_intervention → chronic_disease_outcomes` · MA · protective
B30. `school_based_health_intervention → child_outcomes` · MA · protective

### Block C · Dental, vision & hearing (30)

C1. `periodontal_disease → cardiovascular_disease` · MA · harmful
C2. `periodontal_disease → type_2_diabetes` · MA · harmful
C3. `periodontal_disease → cognitive_decline_dementia` · MA · harmful
C4. `flossing_daily → periodontal_disease_prevention` · MA · protective
C5. `electric_toothbrush_oscillating → plaque_reduction` · MA · protective
C6. `fluoride_toothpaste → caries_prevention` · MA · protective
C7. `fluoridated_drinking_water → caries_prevention_population` · MA · protective
C8. `xylitol_chewing_gum → caries_reduction` · MA · protective
C9. `oil_pulling → plaque_reduction` · MA · mixed
C10. `chlorhexidine_mouthwash → gingivitis` · MA · protective
C11. `tongue_scraping → halitosis_severity` · MA · mixed
C12. `dental_implants_long_term → mastication_quality` · MA · protective
C13. `lutein_zeaxanthin_supplementation → amd_progression` · MA · protective
C14. `omega3_high_dose_amd → amd_progression` · MA · mixed
C15. `omega3_dry_eye → tear_film_quality` · MA · mixed
C16. `outdoor_time_children → myopia_progression` · MA · protective
C17. `low_dose_atropine → childhood_myopia_progression` · MA · protective
C18. `orthokeratology → myopia_progression_children` · MA · protective
C19. `screen_time_children → myopia_incidence` · MA · harmful
C20. `excessive_screen_time → dry_eye_symptoms` · cohort · harmful
C21. `blue_light_filtering_glasses → digital_eye_strain` · MA · mixed
C22. `blue_light_filtering_glasses → sleep_quality` · MA · mixed
C23. `cataract_surgery_early → all_cause_mortality_elderly` · cohort · protective
C24. `hearing_aid_use → cognitive_decline_dementia` · MA · protective
C25. `cochlear_implant_elderly → cognitive_outcomes` · MA · protective
C26. `occupational_noise_above_85db → noise_induced_hearing_loss` · MA · harmful
C27. `recreational_noise_concerts → hearing_loss_risk` · MA · harmful
C28. `tinnitus_cbt → tinnitus_distress` · MA · protective
C29. `ginkgo_biloba_tinnitus → tinnitus_severity` · MA · mixed
C30. `earbud_use_chronic_loud → hearing_loss_adolescent` · cohort · harmful

### Block D · Functional medicine claims with evidence verdicts (30)

D1. `adrenal_fatigue_concept → cortisol_evidence_pattern` · MA · contested
D2. `food_sensitivity_igg_testing → symptom_relief` · MA · contested
D3. `leaky_gut_zonulin_supplements → intestinal_permeability` · trials · mixed
D4. `candida_overgrowth_treatment_systemic → symptom_resolution` · MA · contested
D5. `chelation_iv_edta → cardiovascular_outcomes` · MA · contested
D6. `iv_high_dose_vitamin_c → fatigue_subjective` · trials · mixed
D7. `iv_glutathione → outcomes_humans` · trials · mixed
D8. `infrared_sauna → detoxification_claims` · MA · contested
D9. `coffee_enema → outcomes_humans` · trials · contested
D10. `juice_cleansing_protocols → metabolic_outcomes` · trials · contested
D11. `mthfr_methylfolate_in_non_deficient → outcomes` · MA · mixed
D12. `apoe_e4_diet_tailoring → cognitive_outcomes` · trials · mixed
D13. `pqq_mitochondrial_supplement → outcomes_humans` · trials · mixed
D14. `provoked_urine_heavy_metal_testing → outcomes` · MA · contested
D15. `nutrigenomic_personalized_nutrition → diet_outcomes` · MA · mixed
D16. `consumer_stool_microbiome_test → clinical_outcomes` · MA · contested
D17. `craniosacral_therapy → outcomes` · MA · contested
D18. `acupuncture_chronic_pain → pain_severity` · MA · protective
D19. `acupuncture_ivf → live_birth_rate` · MA · mixed
D20. `acupuncture_migraine_prophylaxis → migraine_frequency` · MA · protective
D21. `homeopathy_meta_evidence → any_outcome` · MA · contested
D22. `structured_water_health_claims → outcomes` · trials · contested
D23. `grounding_earthing → inflammation_markers` · trials · contested
D24. `mouth_taping_sleep → sleep_apnea_outcomes` · trials · mixed
D25. `nasal_breathing_training → exercise_capacity` · trials · mixed
D26. `red_light_panel_at_home → outcomes_skin` · MA · mixed
D27. `cold_thermogenesis → metabolic_outcomes` · MA · mixed
D28. `hyperbaric_oxygen_off_label → various_outcomes` · MA · contested
D29. `ozone_therapy → outcomes_humans` · MA · contested
D30. `bioidentical_hormones_compounded → outcomes_safety` · MA · contested

### Block E · Pediatric & adolescent (30)

E1. `behavior_therapy_preschool_adhd → adhd_severity` · MA · protective
E2. `parent_training_adhd → child_behavior_outcomes` · MA · protective
E3. `methylphenidate_long_term_children → growth_velocity` · MA · harmful
E4. `food_dye_artificial → adhd_symptoms_children` · MA · mixed
E5. `sugar_consumption_acute → behavior_children` · MA · contested
E6. `sleep_extension_adolescent → academic_performance` · trials · protective
E7. `delayed_school_start_times → adolescent_sleep_duration` · MA · protective
E8. `screen_time_above_3h → adolescent_mental_health` · MA · harmful
E9. `social_media_heavy_use → teen_depression` · MA · harmful
E10. `social_media_restriction_intervention → wellbeing` · trials · protective
E11. `green_space_school_proximity → child_cognitive_development` · cohort · protective
E12. `peanut_introduction_4_6mo_high_risk → peanut_allergy_prevention` · MA · protective
E13. `early_egg_introduction → egg_allergy_prevention` · MA · protective
E14. `cesarean_birth → child_atopy_long_term` · MA · harmful
E15. `exclusive_breastfeeding_6mo → child_iq` · MA · protective
E16. `baby_led_weaning → growth_outcomes` · trials · mixed
E17. `school_based_obesity_intervention → bmi_z_score` · MA · protective
E18. `sugar_sweetened_beverage_taxes → consumption_population` · MA · protective
E19. `mediterranean_diet_children → growth_outcomes` · trials · protective
E20. `school_physical_activity_intervention → fitness_children` · MA · protective
E21. `mindfulness_school_intervention → anxiety_children` · MA · mixed
E22. `social_emotional_learning → mental_health_children` · MA · protective
E23. `early_childhood_education_intensive → long_term_outcomes` · MA · protective
E24. `teen_dating_violence_prevention → outcomes` · MA · protective
E25. `school_eating_disorder_prevention → ed_incidence` · MA · mixed
E26. `single_sport_specialization_youth → overuse_injury_risk` · MA · harmful
E27. `youth_strength_training_supervised → injury_outcomes` · MA · protective
E28. `caffeine_adolescent → sleep_anxiety` · MA · harmful
E29. `early_phone_ownership_under_10 → adolescent_mental_health` · cohort · harmful
E30. `helmet_use_youth_sport → concussion_risk` · MA · protective

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
Same pace as Tracks 4–7: ~80 min per checkpoint of careful work,
~24 hours of total compute spread across many stepping cycles.

If a pair has no good evidence (rare), drop it from the set, leave a
note in your commit message, and move on. Submit a partial PR if
needed — anything ≥ 120 verified pairs is a useful merge.

**Expect a high `new_entities` count.** Track 8 introduces many
rehab-population, behavior-change-intervention, and paediatric
outcome entities that don't exist yet. Adding `new_entities` blocks
is normal and expected.

---

## Why this manifest specifically

1. **Block A (rehab)** — the corpus has 1 (one) rehab edge today.
   Recovery is what people actually do AFTER a diagnosis, and a graph
   that's silent on rehab can't serve post-MI, post-stroke, post-cancer,
   long-COVID, or post-surgical users. Cardiac rehab alone has dozens
   of high-quality MAs going back to the 1990s.

2. **Block B (behavior change)** — 0 edges today. We have hundreds of
   "factor X helps outcome Y" edges and nothing on "intervention type
   Z helps the user actually adopt factor X." This is the missing
   middle layer between evidence and outcomes — what coaches actually
   sell.

3. **Block C (dental / vision / hearing)** — ~10 edges combined
   across all three. Periodontal disease alone is causally linked to
   CVD, T2D, and dementia in dozens of MAs; absent. The
   hearing-aid → dementia-prevention edge (ACHIEVE trial 2023) is one
   of the most important findings in geriatric medicine of the past
   five years; absent.

4. **Block D (functional medicine claim verdicts)** — this is the
   ammunition the /claim-check feature needs. Today the feature works
   but it has to lean on Claude's training data because we have no
   corpus rows on "adrenal fatigue", "leaky gut", "chelation IV",
   "homeopathy", etc. After Track 8 it has tier-X / contested edges
   to cite for every common functional-medicine claim.

5. **Block E (paediatric / adolescent)** — 0 ADHD-child edges, 0
   social-media-mental-health edges. The teen mental health crisis is
   real and well-evidenced; we're silent on it. Also the highest-WTP
   coaching segment after biohackers is parents.

---

## Paste-ready resume prompt

Use this single prompt to start and re-engage Codex on every wake:

```
Continue Track 8 on branch feat/codex-seed-batch-10 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V10_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort/case-control row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate.

Track 8 specifics:
- Block A rehab factors encode population + setting (cardiac_rehab_post_mi, stroke_rehab_constraint_induced_movement)
- Block B factors are intervention names (motivational_interviewing, financial_incentives_smoking_cessation)
- Block D is DELIBERATELY many direction:contested or tier:X — capture the contested state of functional medicine claims for the /claim-check feature
- Block E needs new_entities for child/adolescent outcome scales (bmi_z_score, child_iq, adolescent_mental_health)

Track progress via commit messages: 'Track 8: N/150 — topic'.

Skip silently if a payload file for the pair already exists on main or on your branch — do not re-research.
```
