# Codex brief v6 — autonomous Track 3

> **READ THIS FIRST: This brief is designed to keep you working
> autonomously across stepping pauses. Do not stop after each pause to
> ask for approval. The loop below is your authority. Resume yourself.
> Done = the manifest is empty. Until then, keep going.**

Repo: `https://github.com/prokesmic/HealthUniverse` — branch from `main`.

## What's already done (don't redo)

- Track 1 (densify v1): merged
- Track 2 (densify v2): merged → `feat/codex-densify-batch-2` deleted
- Track 3 (seed batch v5): merged → `feat/codex-seed-batch-5` deleted
- Current corpus state: **905 edges · 3,980 evidence rows · 1,759 PMIDs**

## What you're doing now

Track 4: 150 brand-new PMID-verified factor → outcome pairs across the
five topic areas Codex flagged as under-filled in `CLAUDE_TRACK_HANDOFF.md`:

1. **Hematology / nutrition crossover** (30 pairs)
2. **Gut-brain axis specifics** (30 pairs)
3. **Geriatric polypharmacy** (30 pairs)
4. **Women's reproductive endocrinology beyond menopause** (30 pairs)
5. **Paediatric immunity / early-life programming** (30 pairs)

The full manifest of 150 pairs is **inline below** in the "Manifest"
section. Each pair has a slug stub, an outcome stub, and a one-sentence
research hint. You are responsible for finding the actual PMIDs.

## The autonomous loop — do not stop until manifest is empty

**Branch:** `feat/codex-seed-batch-6`

Repeat this loop without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-6 main` (first run only; `git
   checkout feat/codex-seed-batch-6` thereafter)
2. Pick the next **5** unfinished items from the manifest. An item is
   "finished" if the file `data/seed_payloads/{factor_slug}__{outcome_slug}.json`
   exists on this branch.
3. For each picked item:
   - Search PubMed (E-utilities, the validator's own data source) for
     ≥3 high-quality studies on that factor × outcome
   - Verify the PMID + journal + year on each
   - Write the payload in standard `seed_payload` shape with the keys
     listed in "Required payload shape" below
   - **Include `effect_quant` whenever a meta-analysis or RCT reports a
     pooled estimate.** The UI now leans on this field.
4. Run `python3 seed_from_payloads.py validate --verify` over your
   newly-written files. Fix any failures by replacing the offending
   PMID with a different paper. Keep going until 0 failed.
5. Run `python3 seed_from_payloads.py ingest --dry-run`. If the slug
   resolution fails for any pair, that means a new entity needs to be
   created — add a `new_entities` block to that payload (see existing
   v3/v4 batch payloads for shape).
6. `git add data/seed_payloads/` and commit with this message format:
   ```
   Track 4: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-6`
8. **Open the PR only when N=150** and not before. Until then, keep
   pushing checkpoints to the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

When you wake from a stepping pause and re-read this file, you do
**not** need approval to continue. The loop above is your standing
order. Inspect `git status` on the branch, count finished payloads,
pick up where you left off. The commit message format `{N}/150` makes
your last checkpoint visible.

If you finish the manifest:
- Run a final `--verify validate` over the entire `data/seed_payloads/`
  directory and confirm `0 failed`.
- Open the PR with title `Codex Track 4 — 150 verified pairs across
  5 under-filled topic areas`.
- The PR description must include:
  - Full validator transcript ending `0 failed`.
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows.
  - Topic breakdown: how many pairs in each of the 5 areas.
  - Count of payloads with `effect_quant` populated.

## Required payload shape

```json
{
  "schema_version": 1,
  "edges": [
    {
      "factor_slug":  "iron_deficiency_anemia",
      "outcome_slug": "restless_legs_syndrome",
      "factor_name":  "Iron deficiency anemia",
      "outcome_name": "Restless legs syndrome",
      "factor_kind":  "condition",
      "outcome_kind": "condition",
      "population":   "general adult",
      "direction":    "harmful",          // protective | harmful | u_shaped | mixed | neutral
      "tier":         "B",                // A | B | C | X | D
      "summary":      "180-300 chars …",
      "mechanism":    "Brief plain-English mechanism.",
      "caveats":      "Things to qualify the effect.",
      "effect_size":  "moderate",         // small | moderate | large | trivial | unknown
      "effect_quant": {
        "metric":     "OR",               // RR | HR | OR | SMD | MD
        "value":      2.4,
        "ci_low":     1.8,
        "ci_high":    3.2,
        "comparator": "iron-replete adults",
        "dose_range": null
      },
      "evidence": [
        {
          "citation":      "Allen RP et al 2018 Sleep Med Rev",
          "pmid":          "29886107",
          "doi":           "10.1016/j.smrv.2018.05.001",
          "year":          2018,
          "study_type":    "systematic_review",
          "n_participants": 4500,
          "direction":     "harmful",
          "quality":       "high",
          "notes":         "Pooled across 12 cohorts; OR 2.4 (1.8-3.2)."
        },
        // …≥2 more rows
      ],
      "new_entities": [
        // optional: only when factor_slug or outcome_slug doesn't yet exist
        // see prior batches for shape
      ]
    }
  ]
}
```

## Hard rules — same as all prior tracks

- **Never fabricate PMIDs.** The `--verify` validator hits PubMed and
  rejects unresolvable PMIDs and title mismatches. Anything you can't
  resolve, drop it and pick a different paper.
- Every meta-analysis / SR / RCT / cohort row must include `n_participants`.
- Don't pad with weak rows. Better one strong meta-analysis than three
  cross-sectionals.
- Diversify research groups. If two of your three citations are from
  the same lab, replace one.
- Prioritise post-2018 evidence; older is fine for seminal trials only.
- **Never run `seed.py` or `adjudicate.py`** (those use the paid Claude path).
- Don't modify the schema, the cost cap, or anything in `AGENTS.md` "Avoid".

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

You decide tier based on what the literature actually supports. The
direction listed below is your starting hypothesis; flip it if the
evidence disagrees.

### Block A · Hematology / nutrition crossover (30)

A1. `iron_deficiency_anemia → restless_legs_syndrome` · low ferritin causes RLS · harmful
A2. `iron_supplementation → cognitive_function_iron_deplete` · iron-deplete adults · protective
A3. `low_b12 → cognitive_decline` · in elderly · harmful
A4. `low_folate → neural_tube_defects` · pregnancy · harmful
A5. `high_homocysteine → cvd` · MR studies, mendelian · harmful
A6. `low_ferritin → hair_loss_telogen` · iron-deficient women · harmful
A7. `coffee_with_meal → non_heme_iron_absorption` · blocks iron · harmful
A8. `vitamin_c_with_meal → non_heme_iron_absorption` · enhances iron · protective
A9. `calcium_with_meal → non_heme_iron_absorption` · blocks iron · harmful
A10. `heavy_menstruation → iron_deficiency` · monthly loss · harmful
A11. `vegetarian_diet → b12_deficiency` · plant-only · harmful
A12. `methylfolate → mthfr_677tt_outcomes` · activated folate · protective
A13. `donating_blood → iron_stores` · regular donors · harmful
A14. `donating_blood → cardiovascular_risk` · iron-reduction hypothesis · protective
A15. `hereditary_hemochromatosis → iron_overload` · HFE C282Y homo · harmful
A16. `phlebotomy_therapy → hemochromatosis_outcomes` · standard care · protective
A17. `low_dose_aspirin → gi_bleeding_elderly` · primary prevention · harmful
A18. `proton_pump_inhibitors → b12_deficiency` · long-term use · harmful
A19. `gastric_bypass → b12_deficiency` · post-op · harmful
A20. `gastric_bypass → iron_deficiency` · post-op · harmful
A21. `celiac_disease → iron_deficiency_anemia` · malabsorption · harmful
A22. `inflammatory_bowel_disease → iron_deficiency_anemia` · chronic loss · harmful
A23. `hydroxyurea → sickle_cell_outcomes` · disease-modifying · protective
A24. `iron_supplementation_thalassemia_minor → iron_overload` · contraindicated · harmful
A25. `vitamin_k2 → osteoporosis_postmenopausal` · MK-7 trials · protective
A26. `high_ferritin → insulin_resistance` · iron-overload metabolic · harmful
A27. `polycythemia_vera → stroke_risk` · hyperviscosity · harmful
A28. `lactoferrin_supplementation → iron_status_pregnancy` · alternative to ferrous sulfate · protective
A29. `intravenous_iron → quality_of_life_chronic_anemia` · ESRD/CKD · protective
A30. `vitamin_a_deficiency → iron_status_in_children` · interaction · harmful

### Block B · Gut-brain axis specifics (30)

B1. `multistrain_probiotic → major_depressive_disorder` · MA 2023 · protective
B2. `multistrain_probiotic → generalized_anxiety` · meta · protective
B3. `multistrain_probiotic → ibs_symptoms` · multi-strain · protective
B4. `dietary_fiber → cognitive_function_older` · fiber and brain · protective
B5. `fermented_foods → microbiome_diversity` · Stanford trial · protective
B6. `fecal_microbiota_transplant → recurrent_c_difficile` · gold standard · protective
B7. `fecal_microbiota_transplant → autism_behaviour` · early evidence · u_shaped
B8. `fecal_microbiota_transplant → ibs_global_score` · mixed RCTs · mixed
B9. `early_life_antibiotics → ibd_risk` · cohorts · harmful
B10. `early_life_antibiotics → asthma_risk` · cohorts · harmful
B11. `mediterranean_diet → microbiome_diversity` · longitudinal · protective
B12. `western_diet_pattern → ibd_risk` · cohorts · harmful
B13. `omega3_supplementation → ibd_remission` · maintenance · mixed
B14. `sucralose → glucose_tolerance` · gut microbiome route · harmful
B15. `aspartame → headache_susceptible` · mixed evidence · mixed
B16. `saccharin → glucose_tolerance` · early evidence · harmful
B17. `erythritol → cardiovascular_events` · 2023 paper · harmful
B18. `dietary_polyphenols → microbiome_health` · cocoa/tea/red wine · protective
B19. `inulin_supplementation → satiety` · short-chain fatty acid · protective
B20. `resistant_starch → insulin_sensitivity` · type-2 RS trials · protective
B21. `vagus_nerve_stimulation → treatment_resistant_depression` · device · protective
B22. `small_intestinal_bacterial_overgrowth → ibs_symptoms` · overlap · harmful
B23. `lactobacillus_rhamnosus → ulcerative_colitis_remission` · single-strain · mixed
B24. `bifidobacterium → infant_atopy` · early-life · protective
B25. `lgg_supplementation → atopic_dermatitis_children` · L. rhamnosus GG · protective
B26. `saccharomyces_boulardii → travelers_diarrhea` · prophylaxis · protective
B27. `postbiotics → ibs_global_score` · heat-killed · protective
B28. `bile_acid_sequestrants → gut_motility` · cholestyramine · mixed
B29. `proton_pump_inhibitors → gut_microbiome_dysbiosis` · long-term · harmful
B30. `glutamine_supplementation → intestinal_permeability` · enteral · protective

### Block C · Geriatric polypharmacy (30)

C1. `anticholinergic_burden_score → cognitive_decline` · ACB scale · harmful
C2. `statin_discontinuation_75plus → all_cause_mortality` · primary prevention only · u_shaped
C3. `low_dose_aspirin_75plus_primary_prevention → bleeding_risk` · ASPREE trial · harmful
C4. `z_drugs_zolpidem → fall_risk_elderly` · zolpidem/zopiclone · harmful
C5. `trazodone_low_dose → fall_risk_elderly` · sleep adjunct · harmful
C6. `quetiapine_off_label → qt_prolongation` · low-dose · harmful
C7. `polypharmacy_5plus → hospitalization_risk` · cohort · harmful
C8. `polypharmacy_10plus → fall_risk` · cohort · harmful
C9. `beers_criteria_adherence → adverse_drug_events` · adherence cohorts · protective
C10. `deprescribing_ppis_long_term → outcomes` · STOP-PPI trials · protective
C11. `deprescribing_benzodiazepines_elderly → cognition` · withdrawal trials · protective
C12. `icu_delirium → long_term_cognitive_decline` · BRAIN-ICU · harmful
C13. `dementia_with_antipsychotics → mortality` · black-box warning · harmful
C14. `donepezil → mild_cognitive_impairment` · MCI · mixed
C15. `memantine → moderate_severe_dementia` · NMDA antagonist · protective
C16. `vitamin_d_supplementation_elderly → fall_risk` · meta-analysis 2023 · protective
C17. `statins_long_term → cataract_risk` · MA · harmful
C18. `nitrofurantoin_long_term_elderly → pulmonary_fibrosis` · prophylaxis · harmful
C19. `tamsulosin → fall_risk_men` · alpha-blocker orthostatic · harmful
C20. `beta_blockers_chronic → frailty_progression` · MA · mixed
C21. `intensive_blood_pressure_control_elderly → fall_risk` · SPRINT-MIND · u_shaped
C22. `direct_oral_anticoagulants_falls_paradox → outcomes` · benefit despite falls · protective
C23. `acetylcholinesterase_inhibitors → bradycardia` · adverse · harmful
C24. `tricyclic_antidepressants_elderly → cognitive_function` · anticholinergic · harmful
C25. `ssri_elderly → hyponatremia_risk` · SIADH · harmful
C26. `allopurinol_initiation → kidney_function_decline` · slow titration · protective
C27. `hospital_admission → functional_status_decline` · hospital-associated disability · harmful
C28. `alpha_blockers → orthostatic_hypotension` · class effect · harmful
C29. `loop_diuretics_elderly → electrolyte_disturbance` · long-term · harmful
C30. `frailty_index → icu_mortality` · prognostic · harmful

### Block D · Women's reproductive endocrinology beyond menopause (30)

D1. `pcos → insulin_resistance` · core feature · harmful
D2. `inositol_pcos → insulin_sensitivity_pcos` · myo-inositol trials · protective
D3. `spironolactone_pcos → hirsutism` · anti-androgen · protective
D4. `metformin_pcos → ovulation_rate` · pre-pregnancy · protective
D5. `endometriosis → anti_inflammatory_diet_pain` · DASH-style · protective
D6. `hormonal_iud_endometriosis → pelvic_pain` · LNG-IUS · protective
D7. `combined_oral_contraceptives → ovarian_cancer` · long-term · protective
D8. `combined_oral_contraceptives → breast_cancer_premenopausal` · MA 2023 · harmful
D9. `combined_oral_contraceptives → endometrial_cancer` · long-term · protective
D10. `combined_oral_contraceptives → cervical_cancer` · long-term · harmful
D11. `hrt_timing_hypothesis → cardiovascular_disease` · KEEPS / ELITE · u_shaped
D12. `vaginal_estrogen → recurrent_uti_postmenopausal` · low-dose · protective
D13. `vaginal_estrogen → genitourinary_syndrome` · symptom relief · protective
D14. `dhea_postmenopausal → menopausal_symptoms` · adrenal androgen · mixed
D15. `phytoestrogens_isoflavones → hot_flash_frequency` · soy/red clover MA · mixed
D16. `black_cohosh → hot_flash_frequency` · MA · mixed
D17. `cranberry_extract → uti_recurrence_women` · prophylaxis · protective
D18. `d_mannose → uti_recurrence_women` · vs antibiotic · protective
D19. `hibiscus_tea → blood_pressure_women` · MA · protective
D20. `pregnancy → thyroid_function` · physiologic shift · u_shaped
D21. `postpartum_thyroiditis → long_term_hypothyroidism` · cohort · harmful
D22. `breastfeeding_long_duration → maternal_cardiovascular_disease` · cohorts · protective
D23. `breastfeeding_long_duration → maternal_type_2_diabetes` · cohorts · protective
D24. `breastfeeding_parity_adjusted → ovarian_cancer` · MA · protective
D25. `breastfeeding_long_duration → maternal_breast_cancer` · MA · protective
D26. `hpv_vaccine → cervical_cancer_long_term` · UK 1995-cohort · protective
D27. `hpv_vaccine → oropharyngeal_cancer_men_women` · indirect · protective
D28. `brca_mutation_carriers → prophylactic_mastectomy_outcomes` · MA · protective
D29. `tamoxifen_long_term → endometrial_cancer` · adjuvant · harmful
D30. `aromatase_inhibitors → bone_mineral_density` · post-menopause · harmful

### Block E · Paediatric immunity / early-life programming (30)

E1. `early_peanut_introduction_4_11mo → peanut_allergy` · LEAP · protective
E2. `early_egg_introduction_6mo → egg_allergy` · MA · protective
E3. `vitamin_d_supplementation_children → respiratory_infections` · MA · protective
E4. `vitamin_d_supplementation_children → asthma_exacerbations` · trials · mixed
E5. `cesarean_delivery → atopic_eczema_child` · cohorts · harmful
E6. `daycare_attendance_under_1y → respiratory_infections` · cohorts · harmful
E7. `daycare_attendance_under_1y → asthma_protection_long_term` · biphasic · u_shaped
E8. `early_pet_dog_exposure → atopy_age_5` · cohorts · protective
E9. `farm_environment_exposure → allergic_disease` · Amish vs Hutterite · protective
E10. `antibiotics_under_2y → ibd_risk_long_term` · cohorts · harmful
E11. `antibiotics_under_1y → asthma_risk_long_term` · cohorts · harmful
E12. `antibiotics_under_1y → childhood_obesity_risk` · cohorts · harmful
E13. `maternal_antibiotics_in_pregnancy → child_asthma_risk` · cohorts · harmful
E14. `maternal_smoking_in_pregnancy → child_asthma` · meta · harmful
E15. `maternal_smoking_in_pregnancy → low_birth_weight` · meta · harmful
E16. `maternal_chronic_stress_pregnancy → child_neurodevelopment` · cortisol path · harmful
E17. `maternal_omega3_in_pregnancy → child_cognitive_function` · DHA RCTs · protective
E18. `iron_fortified_formula → infant_cognitive_development` · iron-deficient infants · protective
E19. `vitamin_k_injection_at_birth → hemorrhagic_disease_newborn` · standard care · protective
E20. `hepatitis_b_vaccine_birth → childhood_hepatocellular_carcinoma` · Taiwan cohort · protective
E21. `hpv_vaccine_catch_up → cervical_lesions` · Australia data · protective
E22. `influenza_vaccine_in_pregnancy → neonatal_flu_protection` · cohorts · protective
E23. `probiotics_in_infancy → atopic_dermatitis_2yr` · MA · mixed
E24. `extensively_hydrolyzed_formula → atopic_disease` · GINI cohort · protective
E25. `soy_formula → infant_outcomes` · vs cow's milk · neutral
E26. `vegan_diet_during_pregnancy → infant_growth_outcomes` · cohorts · u_shaped
E27. `maternal_obesity → child_obesity_risk` · cohorts · harmful
E28. `maternal_gestational_diabetes → child_obesity_long_term` · HAPO follow-up · harmful
E29. `aces_4plus → adult_mental_health_outcomes` · CDC-Kaiser · harmful
E30. `aces_4plus → adult_cardiovascular_disease` · cohort meta · harmful

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
At ~15 min of careful research per pair plus 5 min validation overhead,
each checkpoint is ~80 min of work. Don't worry about speed — the
validator catches fabrications, so quality is enforced automatically.

If a pair turns out to have no good evidence (rare), drop it from the
set, leave a comment in your commit message, and move to the next.
You can submit a partial PR if needed — anything ≥120 verified pairs
is a useful merge.

---

## Paste-ready resume prompt

When you wake from a stepping pause and need to continue, the same prompt
should re-engage you on the next batch. Use this as the standing prompt:

```
Continue Track 4 on branch feat/codex-seed-batch-6 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V6_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate.

Track progress via git commit messages of the form 'Track 4: N/150 — topic'. To resume, count payloads on the branch and pick up where you left off.
```
