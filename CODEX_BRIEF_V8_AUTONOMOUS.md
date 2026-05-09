# Codex brief v8 — autonomous Track 6

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
- Track 5 (seed v7 — mental-health, cardiometabolic meds, sleep & circadian, vaccines, longevity): merged
- **Current corpus: 1,401 edges · 5,509 evidence rows · ~3,400 PMIDs**

## What you're doing now

Track 6: 150 brand-new PMID-verified pairs across **five highly-searched
biohacker / coach / consumer topic blocks that the corpus is currently
thin on**. These are the topics paying users (Stack Brief subscribers,
nutritionist coaches, supplement-heavy users) actually paste in:

1. **Athletic performance & body composition** (30 pairs)
2. **Cognitive & nootropic compounds** (30 pairs)
3. **Hormonal optimization & endocrine** (30 pairs)
4. **Specific gut / microbiome strains × outcomes** (30 pairs)
5. **Skin / hair / aesthetic interventions** (30 pairs)

Manifest is **inline below**.

## The autonomous loop — do not stop until the manifest is empty

**Branch:** `feat/codex-seed-batch-8`

Repeat without pausing for approval:

1. `git checkout -b feat/codex-seed-batch-8 main` (first run only;
   `git checkout feat/codex-seed-batch-8` thereafter).
2. Pick the next **5** unfinished items from the manifest. An item is
   "finished" if `data/seed_payloads/{factor_slug}__{outcome_slug}.json`
   already exists on this branch *or* on `main`. **Skip silently** if
   already present — do not re-research.
3. For each picked item:
   - Search PubMed for ≥3 high-quality studies on that pair
   - Verify each PMID + journal + year via the `--verify` validator
   - Write the payload using the standard `seed_payload` shape (same
     as Track 5 — see CODEX_BRIEF_V7_AUTONOMOUS.md "Required payload
     shape" section if you need a reminder, or mirror any payload from
     `data/seed_payloads/` on main)
   - **Include `effect_quant` whenever the source paper reports a
     pooled estimate.** The Stack Brief UI relies on it.
   - **Use `direction: "mixed"` or `"u_shaped"` honestly** when the
     literature is genuinely contested. The skeptic-mode view on
     /stack ranks contested edges highest, so a wrong "protective"
     classification gets caught quickly.
4. `python3 seed_from_payloads.py validate --verify` over the new
   files. Fix any failures by replacing the offending PMID. Keep going
   until 0 failed.
5. `python3 seed_from_payloads.py ingest --dry-run`. If a slug doesn't
   resolve, add a `new_entities` block to that payload.
6. `git add data/seed_payloads/` and commit with format:
   ```
   Track 6: {N}/150 — {short topic summary}
   ```
7. `git push origin feat/codex-seed-batch-8`.
8. **Open the PR only when N=150.** Until then, push checkpoints to
   the branch.
9. Repeat from step 2.

## Resume strategy across stepping pauses

After a stepping pause, re-read this file and continue. The standing
order is the loop above. Inspect `git status` on the branch, count
finished payloads, pick up where you left off. Commit messages of
form `Track 6: N/150 — topic` make your last checkpoint visible.

When the manifest is empty:
- Final `--verify validate` run with `0 failed`
- PR title: `Codex Track 6 — 150 verified pairs across 5 high-traffic consumer topics`
- PR description includes:
  - Full validator transcript ending `0 failed`
  - 5 random `(edge_id, factor, outcome, PMID, year, journal)` rows
  - Topic breakdown: pairs per block
  - Count of payloads with `effect_quant`
  - Count of payloads with `direction: mixed` or `u_shaped` (we're
    explicitly *expecting* a higher share than prior tracks here —
    nootropics + supplements have noisier literature)

Update `CLAUDE_TRACK_HANDOFF.md` at PR-time to reflect Track 6
completion (replace the Track 5 paragraph; keep the same template).

## Hard rules (same as every prior track)

- Never fabricate PMIDs (the verifier flags it; Claude's semantic
  audit on main runs nightly and catches mismatches)
- Every meta-analysis / SR / RCT / cohort / case-control / cross-sectional
  row must include `n_participants`
- Don't pad with weak rows — one strong meta-analysis > three cross-sectionals
- Diversify research groups
- Prioritise post-2018; older only if seminal (CALERIE, REDUCE-IT, etc.)
- Never run `seed.py` or `adjudicate.py`
- Don't modify schema, cost cap, or anything in `AGENTS.md` "Avoid"
- Don't stage or remove `data/health.db`
- One PR per track, branched from `main`

## Validator quirks worth remembering

- Citation first token cannot look like a single-letter placeholder
- `umbrella_review` is not a valid `study_type`; use `systematic_review`
- If a factor is rejected by the validator path but is intentionally
  new for the edge, declaring it in `new_entities` is acceptable
- Performance / process outcomes often fit best with `direction: "protective"`
  and entity `kind: "process"`

---

## Manifest — 150 pairs

Format: `factor_slug → outcome_slug · research hint · expected direction`

Skip silently if a payload file already exists for the pair. Tier is
your decision based on the actual literature; the listed direction is
your starting hypothesis — flip to `mixed` / `u_shaped` / `harmful`
if the evidence says so.

### Block A · Athletic performance & body composition (30)

A1. `creatine_monohydrate → strength_gains_resistance_training` · MA · protective
A2. `creatine_monohydrate → muscle_mass_gains_resistance_training` · MA · protective
A3. `creatine_monohydrate → high_intensity_sprint_performance` · MA · protective
A4. `creatine_monohydrate → cognitive_performance_under_sleep_deprivation` · RCTs · protective
A5. `beta_alanine → muscular_endurance_1to4_minutes` · MA · protective
A6. `caffeine_pre_exercise → endurance_performance_trained` · MA · protective
A7. `caffeine_pre_exercise → strength_one_rep_max` · MA · mixed
A8. `sodium_bicarbonate → high_intensity_anaerobic_performance` · MA · protective
A9. `nitrate_beetroot_juice → endurance_time_to_exhaustion` · MA · protective
A10. `citrulline_malate → resistance_training_volume` · MA · mixed
A11. `branched_chain_amino_acids → muscle_soreness_dom` · MA · mixed
A12. `essential_amino_acids → muscle_protein_synthesis_post_exercise` · RCTs · protective
A13. `whey_protein_post_workout → muscle_protein_synthesis` · RCTs · protective
A14. `casein_protein_pre_sleep → overnight_muscle_protein_synthesis` · RCTs · protective
A15. `pre_workout_carbohydrate_30g → endurance_performance` · MA · protective
A16. `glycogen_supercompensation → marathon_finish_time` · MA · protective
A17. `cherry_juice_tart → muscle_recovery_dom` · MA · protective
A18. `curcumin_with_piperine → exercise_induced_inflammation` · MA · protective
A19. `omega3_high_dose → exercise_induced_muscle_damage` · MA · mixed
A20. `cold_water_immersion_post_strength → muscle_hypertrophy` · MA · harmful
A21. `cold_water_immersion_post_endurance → recovery_perceived` · MA · protective
A22. `compression_garments_post_exercise → recovery_markers` · MA · mixed
A23. `foam_rolling_post_exercise → range_of_motion_acute` · MA · protective
A24. `static_stretching_pre_exercise → power_output_acute` · MA · harmful
A25. `dynamic_warmup → injury_prevention_team_sports` · MA · protective
A26. `progressive_overload_training → strength_long_term` · MA · protective
A27. `high_volume_training_split → muscle_hypertrophy` · MA · mixed
A28. `low_load_blood_flow_restriction → muscle_hypertrophy_rehab` · MA · protective
A29. `eccentric_emphasised_training → tendon_stiffness_athletes` · MA · protective
A30. `polarised_endurance_training_distribution → vo2max` · MA · protective

### Block B · Cognitive & nootropic compounds (30)

B1. `caffeine_l_theanine_combo → sustained_attention` · MA · protective
B2. `l_theanine_alone → anxiety_acute_subjective` · MA · protective
B3. `caffeine_acute → reaction_time` · MA · protective
B4. `alpha_gpc → power_output_anaerobic` · RCTs · mixed
B5. `citicoline → memory_age_related_decline` · MA · protective
B6. `bacopa_monnieri → memory_in_healthy_adults` · MA · protective
B7. `bacopa_monnieri → anxiety_subjective` · MA · mixed
B8. `lion_s_mane_hericium → cognitive_function_mild_impairment` · RCTs · mixed
B9. `panax_ginseng → fatigue_subjective` · MA · mixed
B10. `american_ginseng → working_memory_acute` · RCTs · mixed
B11. `rhodiola_rosea → mental_fatigue` · MA · mixed
B12. `ashwagandha → perceived_stress_subjective` · MA · protective
B13. `ashwagandha → cortisol_morning` · RCTs · mixed
B14. `phosphatidylserine → cognition_age_related_decline` · MA · mixed
B15. `phosphatidylserine → exercise_induced_cortisol` · RCTs · mixed
B16. `acetyl_l_carnitine → mild_cognitive_impairment` · MA · mixed
B17. `nicotine_gum_acute → working_memory` · RCTs · mixed
B18. `modafinil_off_label → sustained_attention_healthy` · MA · protective
B19. `methylene_blue_low_dose → cognition_humans` · early trials · mixed
B20. `pterostilbene → metabolic_markers_humans` · trials · mixed
B21. `huperzine_a → memory_alzheimer_disease` · MA · mixed
B22. `vinpocetine → cognitive_function_vascular` · MA · mixed
B23. `ginkgo_biloba_240mg → cognitive_decline_dementia_prevention` · MA · mixed
B24. `epa_high_dose → depression_severity_in_mdd` · MA · protective
B25. `dha_high_dose → cognitive_function_age_related` · MA · mixed
B26. `creatine_in_vegetarians → cognitive_function` · RCTs · protective
B27. `cocoa_flavanols_high_dose → cognitive_function_aged` · MA · protective
B28. `green_tea_extract → working_memory_acute` · RCTs · mixed
B29. `saffron_extract → mild_to_moderate_depression` · MA · protective
B30. `s_adenosyl_methionine_same → depressive_symptoms` · MA · mixed

### Block C · Hormonal optimization & endocrine (30)

C1. `testosterone_replacement_hypogonadal → libido_recovery` · MA · protective
C2. `testosterone_replacement_hypogonadal → erectile_function` · MA · protective
C3. `testosterone_replacement_hypogonadal → bone_mineral_density` · MA · protective
C4. `testosterone_replacement_hypogonadal → cardiovascular_safety` · TRAVERSE-style · mixed
C5. `clomiphene_citrate_men → secondary_hypogonadism` · RCTs · protective
C6. `enclomiphene_men → testosterone_recovery` · phase-3 · protective
C7. `hcg_men_on_trt → testicular_volume_preservation` · trials · protective
C8. `aromatase_inhibitor_men → estradiol_management_on_trt` · trials · mixed
C9. `dhea_supplementation_men → testosterone_or_libido` · MA · mixed
C10. `dhea_supplementation_postmenopausal → libido` · MA · mixed
C11. `boron_supplementation → free_testosterone` · trials · mixed
C12. `zinc_repletion_in_deficient → testosterone` · MA · mixed
C13. `magnesium_supplementation → testosterone_in_deficient` · trials · mixed
C14. `tongkat_ali_eurycoma → testosterone_men` · MA · mixed
C15. `fadogia_agrestis → testosterone_humans` · trials · mixed
C16. `vitamin_d_repletion → testosterone_in_deficient_men` · MA · mixed
C17. `body_recomposition_weight_loss → testosterone_in_obese_men` · MA · protective
C18. `chronic_endurance_overtraining → testosterone_men` · cohorts · harmful
C19. `chronic_alcohol_high → testosterone_men` · MA · harmful
C20. `chronic_sleep_restriction → testosterone_morning` · trials · harmful
C21. `chronic_stress_cortisol → testosterone_men` · cohorts · harmful
C22. `endocrine_disrupting_phthalates → testosterone_men` · MA · harmful
C23. `levothyroxine → quality_of_life_subclinical_hypothyroid` · MA · mixed
C24. `liothyronine_t3_addition → quality_of_life_hypothyroid_on_t4` · MA · mixed
C25. `selenium_supplementation → thyroid_autoantibodies_hashimoto` · MA · mixed
C26. `iodine_excess → autoimmune_thyroid_susceptible` · cohorts · harmful
C27. `progesterone_micronised_oral → menopausal_sleep` · RCTs · protective
C28. `transdermal_estradiol → vasomotor_symptoms` · MA · protective
C29. `inositol_myo_d_chiro → ovulation_pcos` · MA · protective
C30. `letrozole_anovulatory → live_birth_pcos` · MA · protective

### Block D · Specific gut / microbiome strains × outcomes (30)

D1. `lactobacillus_rhamnosus_gg → antibiotic_associated_diarrhoea_children` · MA · protective
D2. `lactobacillus_plantarum_299v → ibs_global_severity` · MA · mixed
D3. `bifidobacterium_longum_1714 → stress_perceived_anxiety` · RCTs · mixed
D4. `lactobacillus_helveticus_r0052_bifido_longum_r0175 → mood_psychological_distress` · RCTs · mixed
D5. `saccharomyces_boulardii → c_difficile_recurrence_prevention` · MA · protective
D6. `vsl3_high_dose_probiotic_blend → ulcerative_colitis_remission` · MA · protective
D7. `bifidobacterium_infantis → ibs_d_predominant_symptoms` · MA · mixed
D8. `lactobacillus_reuteri_dsm17938 → infant_colic` · MA · protective
D9. `lactobacillus_reuteri_breastfed → maternal_iron_status` · trials · mixed
D10. `prebiotic_inulin_long_chain → bifidobacterium_abundance` · MA · protective
D11. `prebiotic_galactooligosaccharides → travelers_diarrhoea` · trials · mixed
D12. `partially_hydrolysed_guar_fibre → constipation_chronic` · MA · protective
D13. `psyllium_husk → ldl_cholesterol` · MA · protective
D14. `psyllium_husk → ibs_constipation_predominant` · MA · protective
D15. `peppermint_oil_enteric_coated → ibs_global_symptoms` · MA · protective
D16. `enteric_curcumin → ulcerative_colitis_maintenance` · MA · mixed
D17. `boswellia_serrata → ulcerative_colitis_remission` · trials · mixed
D18. `slippery_elm_marshmallow_root → reflux_symptoms` · trials · mixed
D19. `dgl_licorice → reflux_symptoms` · trials · mixed
D20. `zinc_carnosine → gastric_ulcer_h_pylori_eradication` · MA · protective
D21. `low_fodmap_diet_short_term → ibs_global_symptoms` · MA · protective
D22. `low_fodmap_diet_long_term → microbiome_diversity` · cohorts · harmful
D23. `gluten_free_in_non_celiac → gi_symptoms_self_reported` · RCTs · mixed
D24. `dairy_elimination → eczema_severity_children` · MA · mixed
D25. `kefir_regular_intake → gut_microbiome_diversity` · trials · protective
D26. `kombucha_regular_intake → metabolic_markers_humans` · trials · mixed
D27. `apple_cider_vinegar → postprandial_glycaemia` · trials · mixed
D28. `digestive_enzymes_pancreatic → bloating_chronic_dyspepsia` · trials · mixed
D29. `betaine_hcl_supplementation → hypochlorhydria_symptoms` · trials · mixed
D30. `intestinal_alkaline_phosphatase_oral → endotoxaemia` · early trials · mixed

### Block E · Skin / hair / aesthetic interventions (30)

E1. `hydrolysed_collagen_peptides → skin_elasticity_clinical` · MA · protective
E2. `hydrolysed_collagen_peptides → skin_hydration_clinical` · MA · protective
E3. `hydrolysed_collagen_peptides → nail_brittleness` · trials · mixed
E4. `hydrolysed_collagen_peptides → joint_pain_osteoarthritis` · MA · mixed
E5. `topical_retinol_long_term → photoaging_clinical_grading` · MA · protective
E6. `topical_tretinoin → photoaging_clinical_grading` · MA · protective
E7. `topical_niacinamide_5pct → fine_lines_clinical` · RCTs · protective
E8. `topical_vitamin_c_15pct → photoaging_clinical_grading` · RCTs · protective
E9. `topical_hyaluronic_acid → skin_hydration_acute` · RCTs · protective
E10. `topical_alpha_hydroxy_acids → skin_texture_clinical` · MA · protective
E11. `topical_salicylic_acid → mild_acne_clinical` · MA · protective
E12. `topical_benzoyl_peroxide → moderate_acne_clinical` · MA · protective
E13. `topical_adapalene_0_1pct → moderate_acne_clinical` · MA · protective
E14. `oral_isotretinoin → severe_nodulocystic_acne` · MA · protective
E15. `spironolactone_low_dose_women → adult_female_acne` · MA · protective
E16. `combined_oral_contraceptives_anti_androgenic → moderate_acne_women` · MA · protective
E17. `topical_minoxidil_5pct → androgenetic_alopecia_men` · MA · protective
E18. `topical_minoxidil_5pct → androgenetic_alopecia_women` · MA · protective
E19. `oral_finasteride_men → androgenetic_alopecia_men` · MA · protective
E20. `oral_finasteride_men → sexual_side_effects_persistent` · cohorts · harmful
E21. `oral_dutasteride_men → androgenetic_alopecia_men` · MA · protective
E22. `low_level_red_light_therapy → androgenetic_alopecia` · MA · mixed
E23. `microneedling_scalp → androgenetic_alopecia` · trials · mixed
E24. `topical_rosemary_oil → androgenetic_alopecia` · trials · mixed
E25. `oral_biotin_high_dose → hair_growth_in_non_deficient` · MA · neutral
E26. `oral_marine_collagen_with_vitamins → hair_density_in_thinning_women` · trials · mixed
E27. `topical_caffeine → hair_shaft_thickness` · trials · mixed
E28. `daily_sunscreen_spf30_plus → photoaging_long_term` · MA · protective
E29. `daily_sunscreen_spf30_plus → cutaneous_squamous_cell_carcinoma` · MA · protective
E30. `chronic_uv_exposure → melanoma_risk_intermittent` · MA · harmful

---

## Suggested cadence

Five payloads per checkpoint × 30 checkpoints = full 150-pair manifest.
Same pace as Track 5: ~80 min per checkpoint of careful work, ~24 hours
of total compute spread across many stepping cycles. The validator
catches fabrications, so quality is enforced automatically.

If a pair has no good evidence (rare), drop it from the set, leave a
note in your commit message, and move on. Submit a partial PR if
needed — anything ≥ 120 verified pairs is a useful merge.

**Expect higher `mixed` / `u_shaped` rates than prior tracks**:
nootropics, supplement-heavy, and skin-care literature is genuinely
noisier. That's a feature, not a bug — Stack Brief skeptic mode
ranks contested edges first. Don't force "protective" if the MA
says CI crosses 1.

---

## Why this manifest specifically

These 150 pairs map to the exact factor names that paying users paste
into the Stack Brief: creatine, magnesium, omega-3, ashwagandha,
collagen, retinol, finasteride, lion's mane, etc. Today the corpus
returns "no match" or sparse coverage for many of them. After Track 6,
a typical biohacker stack-brief should have ≥ 80 % matched factors
with at least one tier-A or tier-B edge each. That's the threshold at
which Pro pricing converts.

---

## Paste-ready resume prompt

Use this single prompt to start and re-engage Codex on every wake:

```
Continue Track 6 on branch feat/codex-seed-batch-8 in https://github.com/prokesmic/HealthUniverse.

Read CODEX_BRIEF_V8_AUTONOMOUS.md first. The manifest of 150 pairs is inline there.

Your standing job: pick the next 5 unfinished items from the manifest, research them, write PMID-verified payloads, validate, commit, push. Repeat until the full 150 are merged. Do NOT stop or wait for approval between checkpoints — the brief itself is your authority.

Hard rules: never fabricate PMIDs, never run seed.py or adjudicate.py, every meta-analysis/SR/RCT/cohort/case-control row needs n_participants, include effect_quant whenever the source paper reports a pooled estimate. Use direction "mixed" or "u_shaped" honestly when the literature is contested — don't force protective.

Track progress via git commit messages of the form 'Track 6: N/150 — topic'. To resume, count payloads on the branch and pick up where you left off.

Skip silently if a payload file for the pair already exists on main or on your branch — do not re-research.
```
