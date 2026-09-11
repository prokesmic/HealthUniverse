# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** 2026-09-11
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** 36 across 5 categories
**Strength threshold:** ≥ 0.6

## How to use

Each block below is a single edge to seed. For each one:

1. **Research the factor → outcome relationship** using PubMed + the linked
   source. Don't trust the headline — pull the underlying study/trial.
2. **Grade the evidence tier** per our methodology (A=meta-analysis or
   multiple RCTs converging, B=single registrational RCT or strong cohort,
   C=Phase 1/2 or emerging, D=limited/preclinical-only, X=contested).
3. **Write the edge payload** in the standard seed schema (factor entity,
   outcome entity, edge object with direction/tier/summary/effect_size,
   and ≥3 evidence rows with PMIDs).
4. **Match the existing entity slugs** if the factor or outcome already
   exists; only mint a new entity if there's no match.
5. **Include the breakthrough id** in the edge's `provenance` field so we
   can close the loop: `provenance: { "breakthrough_id": "br_..." }`

Acceptance criteria:
- ≥ 3 PMID-verified evidence rows per edge.
- Tier rationale documented in the edge `tier_reason` field.
- Direction is one of: protective / harmful / mixed / u_shaped / neutral.
- Effect size is one of: small / moderate / large / trivial / unknown.
- If the source readout is a single trial, prefer tier B with a note that
  replication is pending; do not over-grade.

---


## Oncology  ·  5 candidates
### 1. Datopotamab-deruxtecan extends overall survival in metastatic TNBC

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_dato_dxd_tnbc_os` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-14 (120d ago) |
| **Strength** | 92% |
| **Source** | [ASCO 2026](https://ascopubs.org/doi/10.1200/JCO.2026.40.tropion_breast02) |
| **Suggested `factor.slug`** | `datopotamab_deruxtecan` |
| **Suggested `outcome.slug`** | `triple_negative_breast_cancer` |

**Summary.** TROPION-Breast02 randomised 540 patients with previously-treated triple-negative breast cancer. Median OS 18.4 mo vs 14.0 mo with chemo (HR 0.71, 95% CI 0.55-0.92).

**Why it matters.** First TROP2-ADC to clear an OS benefit in TNBC. Likely registrational; expect filing inside 12 months.

**Seed direction.** Search PubMed for `datopotamab_deruxtecan triple_negative_breast_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_dato_dxd_tnbc_os"`

---

### 2. Removing fallopian tubes during routine surgery may lower ovarian cancer risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_62e029ea6fac2440` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (59d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2850113) |
| **Suggested `factor.slug`** | `opportunistic_salpingectomy` |
| **Suggested `outcome.slug`** | `tubo_ovarian_carcinoma` |

**Summary.** The European Society of Gynaecological Oncology recommends removing fallopian tubes during other gynecological surgeries to prevent ovarian cancer. This safe approach is now widely supported.

**Why it matters.** Women having routine gynecological surgery should discuss removing fallopian tubes with their doctor to reduce ovarian cancer risk.

**Seed direction.** Search PubMed for `opportunistic_salpingectomy tubo_ovarian_carcinoma` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_62e029ea6fac2440"`

---

### 3. FDA approves first new sunscreen ingredient in 30 years

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0c157ee7cbf678cc` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (52d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851030) |
| **Suggested `factor.slug`** | `bemotrizinol` |
| **Suggested `outcome.slug`** | `skin_cancer_prevention` |

**Summary.** The FDA approved bemotrizinol as the first new active sunscreen ingredient in over 30 years. This expands options for sun protection products available to consumers.

**Why it matters.** Check sunscreen labels for bemotrizinol to access the first new active ingredient approved in over 30 years for sun protection.

**Seed direction.** Search PubMed for `bemotrizinol skin_cancer_prevention` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_0c157ee7cbf678cc"`

---

### 4. New algorithm safely rules out blood clots in cancer patients, avoiding CT scans

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_39fdd03b34d86bf2` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-25 (17d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851621) |
| **Suggested `factor.slug`** | `years_algorithm` |
| **Suggested `outcome.slug`** | `pulmonary_embolism` |

**Summary.** A new diagnostic algorithm for blood clots in cancer patients was as safe and efficient as standard CT scans in a large trial. It reduced the need for CT scans, avoiding radiation and contrast exposure.

**Why it matters.** Cancer patients may now avoid unnecessary CT scans for blood clot diagnosis, reducing radiation exposure and contrast use.

**Seed direction.** Search PubMed for `years_algorithm pulmonary_embolism` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_39fdd03b34d86bf2"`

---

### 5. New guideline adds blood test option for colorectal cancer screening

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e5887844999f1e27` |
| **Stage** | Guideline |
| **Published** | 2026-09-08 (3d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853040) |
| **Suggested `factor.slug`** | `blood_test` |
| **Suggested `outcome.slug`** | `colorectal_cancer` |

**Summary.** The American Cancer Society now includes a blood test as a screening choice for colorectal cancer. This expands options beyond colonoscopy and stool tests.

**Why it matters.** Ask your doctor if a blood test is a good screening option for you—it's less invasive than colonoscopy and may increase screening rates.

**Seed direction.** Search PubMed for `blood_test colorectal_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_e5887844999f1e27"`

---


## Cardiovascular  ·  5 candidates
### 6. Major heart groups agree on a single definition for heart failure

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb5e3b6d8c3e1b49` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (31d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851950) |
| **Suggested `factor.slug`** | `universal_definition` |
| **Suggested `outcome.slug`** | `heart_failure` |

**Summary.** Four leading heart organizations established a universal definition for heart failure. This standardizes diagnosis and treatment globally.

**Why it matters.** Understand that heart failure is now defined consistently worldwide, improving diagnosis and care for millions of patients.

**Seed direction.** Search PubMed for `universal_definition heart_failure` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_cb5e3b6d8c3e1b49"`

---

### 7. Memory Changes May Predict Heart Events 8 Years Early

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e6dece34f86e5874` |
| **Stage** | other |
| **Published** | 2026-06-09 (94d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2849296) |
| **Suggested `factor.slug`** | `cognitive_decline` |
| **Suggested `outcome.slug`** | `cardiovascular_events` |

**Summary.** Cognitive decline in older adults may precede cardiovascular events by up to 8 years. This could enable earlier detection of heart risks.

**Why it matters.** Older adults noticing memory changes should discuss them with their doctor as they may signal future heart risks.

**Seed direction.** Search PubMed for `cognitive_decline cardiovascular_events` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_e6dece34f86e5874"`

---

### 8. Pre-op iron reduces blood needs and improves recovery after heart surgery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_26eed9a442dc0494` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-24 (18d ago) |
| **Strength** | 85% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100407/rr-5) |
| **Suggested `factor.slug`** | `intravenous_iron` |
| **Suggested `outcome.slug`** | `blood_transfusion` |

**Summary.** For heart surgery patients with anemia, a single 1000 mg iron dose cut blood transfusions from 68.2% to 61.1%. It also increased days alive and at home at 90 days.

**Why it matters.** If you're having heart surgery with anemia, ask your doctor about pre-surgery iron to reduce blood transfusions and speed recovery.

**Seed direction.** Search PubMed for `intravenous_iron blood_transfusion` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_26eed9a442dc0494"`

---

### 9. IV iron before heart surgery reduces blood transfusions and improves 90-day recovery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b07cf4e81bd58d81` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-26 (16d ago) |
| **Strength** | 85% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100407/rr-7) |
| **Suggested `factor.slug`** | `intravenous_iron` |
| **Suggested `outcome.slug`** | `recovery_90d` |

**Summary.** A trial of 955 heart surgery patients found IV iron reduced blood transfusions. It also improved 90-day recovery rates, meaning more time alive and out of hospital.

**Why it matters.** Ask your cardiac surgeon if IV iron before surgery could reduce your blood transfusion needs and speed up recovery.

**Seed direction.** Search PubMed for `intravenous_iron recovery_90d` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_b07cf4e81bd58d81"`

---

### 10. IV iron before heart surgery reduces need for blood transfusions by 7%

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f8bbb8f9c34029d8` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-22 (20d ago) |
| **Strength** | 80% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100407/rr-4) |
| **Suggested `factor.slug`** | `iv_iron` |
| **Suggested `outcome.slug`** | `transfusion_reduction` |

**Summary.** IV iron before heart surgery reduced blood transfusion rates from 68.2% to 61.1%. This represents a 7.1% absolute risk reduction.

**Why it matters.** If you're having heart surgery and have anemia, ask your doctor if IV iron could lower your risk of needing a blood transfusion.

**Seed direction.** Search PubMed for `iv_iron transfusion_reduction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_f8bbb8f9c34029d8"`

---


## Metabolic  ·  7 candidates
### 11. FDA approves first oral drug to lower LDL cholesterol

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a3bf5bc02049572f` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (17d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852500) |
| **Suggested `factor.slug`** | `oral_pcsk9_inhibitor` |
| **Suggested `outcome.slug`** | `ldl_reduction` |

**Summary.** The FDA approved the first oral medication targeting LDL cholesterol reduction. Previously, such treatments required injections.

**Why it matters.** Ask your doctor if this oral option could improve your cholesterol management plan.

**Seed direction.** Search PubMed for `oral_pcsk9_inhibitor ldl_reduction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_a3bf5bc02049572f"`

---

### 12. First OTC glucose monitor approved for children with diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3a1173badb98dc91` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (52d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851034) |
| **Suggested `factor.slug`** | `continuous_glucose_monitor` |
| **Suggested `outcome.slug`** | `diabetes` |

**Summary.** The FDA approved the first over-the-counter continuous glucose monitor for children. This device allows blood sugar monitoring without a prescription.

**Why it matters.** Parents can now buy a glucose monitor for their child without a prescription, making diabetes management easier at home.

**Seed direction.** Search PubMed for `continuous_glucose_monitor diabetes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_3a1173badb98dc91"`

---

### 13. AI-Powered Eye Scan Improves Diabetes Vision Screening Accuracy

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0a2c6d6f6e7a8c8b` |
| **Stage** | Phase 3 |
| **Published** | 2026-07-21 (52d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2850451) |
| **Suggested `factor.slug`** | `ai_oct` |
| **Suggested `outcome.slug`** | `diabetic_macular_edema` |

**Summary.** An AI-enhanced eye scan system improved detection of diabetic eye disease in a clinical trial. It showed better diagnostic accuracy and reduced unnecessary referrals compared to standard screening.

**Why it matters.** If you have diabetes, ask your doctor about AI-enhanced eye screenings for early detection of vision-threatening complications.

**Seed direction.** Search PubMed for `ai_oct diabetic_macular_edema` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_0a2c6d6f6e7a8c8b"`

---

### 14. First Drug Approved to Lower Pancreatitis Risk in Severe High Triglycerides

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_66ec86d216139ace` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-11 (31d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851947) |
| **Suggested `factor.slug`** | `hypertriglyceridemia_drug` |
| **Suggested `outcome.slug`** | `acute_pancreatitis` |

**Summary.** The FDA approved a new treatment for severe high triglycerides. It is the first drug shown to lower acute pancreatitis risk.

**Why it matters.** If you have severe high triglycerides, ask your doctor about this treatment to help prevent pancreatitis.

**Seed direction.** Search PubMed for `hypertriglyceridemia_drug acute_pancreatitis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_66ec86d216139ace"`

---

### 15. FDA approves gene therapy for children 2+ with sickle cell disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ab673401325c68f1` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-18 (24d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852255) |
| **Suggested `factor.slug`** | `gene_therapy` |
| **Suggested `outcome.slug`** | `sickle_cell_disease` |

**Summary.** The FDA approved a gene therapy for children aged 2 and older with sickle cell disease who experience frequent pain crises or require regular blood transfusions. This treatment addresses the genetic cause of the condition.

**Why it matters.** Parents of children with sickle cell disease should ask their doctors about this new treatment option for managing severe symptoms.

**Seed direction.** Search PubMed for `gene_therapy sickle_cell_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_ab673401325c68f1"`

---

### 16. New Guidelines Standardize Diagnosis and Treatment for Heart-Kidney-Metabolic Condition

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_9da7dbf213dfafac` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (31d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851943) |
| **Suggested `factor.slug`** | `ckm_guideline` |
| **Suggested `outcome.slug`** | `ckm_syndrome` |

**Summary.** The guidelines provide unified methods for diagnosing and staging cardiovascular-kidney-metabolic syndrome. Updated treatment recommendations aim to improve care for millions affected by this interconnected condition.

**Why it matters.** Ask your doctor how these new standards may impact your care plan for heart, kidney, and metabolic health.

**Seed direction.** Search PubMed for `ckm_guideline ckm_syndrome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_9da7dbf213dfafac"`

---

### 17. Bone health: 600 METs-min/week of walking/jogging, plus falls risk assessment.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7878d119f83dc7e0` |
| **Stage** | Guideline |
| **Published** | 2026-09-10 (1d ago) |
| **Strength** | 80% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100561/rr) |
| **Suggested `factor.slug`** | `walking_jogging` |
| **Suggested `outcome.slug`** | `bone_density` |

**Summary.** Aim for 600 METs-min/week of brisk walking or jogging to boost bone density. Assess falls risk alongside exercise to prevent fractures.

**Why it matters.** To protect your bones, do 600 METs-min/week of walking/jogging and talk to your doctor about fall prevention.

**Seed direction.** Search PubMed for `walking_jogging bone_density` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_7878d119f83dc7e0"`

---


## Neuro & Mental Health  ·  14 candidates
### 18. FDA Approves New ADHD Medication

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_33b0fdb6f0ab7d0b` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (3d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853045) |
| **Suggested `factor.slug`** | `new_adhd_medication` |
| **Suggested `outcome.slug`** | `adhd` |

**Summary.** The FDA approved a new medication for ADHD treatment. This provides an additional option for patients who may not respond to existing therapies.

**Why it matters.** Patients with ADHD should discuss this new treatment option with their healthcare provider to determine if it's appropriate for their needs.

**Seed direction.** Search PubMed for `new_adhd_medication adhd` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_33b0fdb6f0ab7d0b"`

---

### 19. FDA approves new drug for agitation in Alzheimer's dementia patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4f487e92268d5f9a` |
| **Stage** | Approved / Label |
| **Published** | 2026-06-16 (87d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2849527) |
| **Suggested `factor.slug`** | `dementia_agitation_drug` |
| **Suggested `outcome.slug`** | `dementia_agitation` |

**Summary.** The FDA approved a new medication to treat agitation in Alzheimer's dementia. This provides a new treatment option for a common and distressing symptom.

**Why it matters.** Families and caregivers of Alzheimer's patients now have a new treatment option for managing agitation, improving daily care and quality of life.

**Seed direction.** Search PubMed for `dementia_agitation_drug dementia_agitation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_4f487e92268d5f9a"`

---

### 20. FDA approves second over-the-counter naloxone nasal spray for opioid overdose

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_47a96cc94db33c7c` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-28 (45d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851467) |
| **Suggested `factor.slug`** | `naloxone_nasal_spray` |
| **Suggested `outcome.slug`** | `opioid_overdose` |

**Summary.** The FDA approved a second over-the-counter naloxone nasal spray for opioid overdose emergencies. This increases access to life-saving treatment without requiring a prescription.

**Why it matters.** Know naloxone is now available in two over-the-counter nasal spray forms, making it easier to keep at home for opioid overdose emergencies.

**Seed direction.** Search PubMed for `naloxone_nasal_spray opioid_overdose` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_47a96cc94db33c7c"`

---

### 21. Blood thinner more effective than standard drug for migraines linked to heart hole

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cd80dcb8bd64e525` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-06 (36d ago) |
| **Strength** | 90% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100103/rr-2) |
| **Suggested `factor.slug`** | `blood_thinner` |
| **Suggested `outcome.slug`** | `migraine_prevention` |

**Summary.** A blood thinner reduced migraine frequency more than standard treatment in people with a heart hole (PFO). 78% of patients on the blood thinner had fewer migraines versus 62% on standard drug, a 16% absolute improvement.

**Why it matters.** If you have migraines and a heart hole (PFO), ask your doctor if a blood thinner might be a better option than standard migraine medication.

**Seed direction.** Search PubMed for `blood_thinner migraine_prevention` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_cd80dcb8bd64e525"`

---

### 22. FDA approves home start for Alzheimer's antibody treatment

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7e72d1fb17965942` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (17d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852497) |
| **Suggested `factor.slug`** | `lecanemab` |
| **Suggested `outcome.slug`** | `alzheimers` |

**Summary.** The FDA approved a new subcutaneous starting dose for lecanemab, allowing patients to begin Alzheimer's treatment at home. This eliminates the need for an initial clinic visit.

**Why it matters.** Alzheimer's patients can now start treatment at home, reducing travel burden for early therapy initiation.

**Seed direction.** Search PubMed for `lecanemab alzheimers` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_7e72d1fb17965942"`

---

### 23. Virtual neurology visits as effective as in-person for first-time patient evaluations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_efba2df41cc84c9f` |
| **Stage** | Phase 3 |
| **Published** | 2026-06-02 (101d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2849012) |
| **Suggested `factor.slug`** | `virtual_neurology_visits` |
| **Suggested `outcome.slug`** | `care_equivalence` |

**Summary.** Virtual neurology visits showed no significant difference in outcomes compared to in-person visits for initial patient evaluations. Patient satisfaction rates were comparable between both methods.

**Why it matters.** Ask your doctor about virtual options for your first neurology appointment to reduce travel time without compromising care quality.

**Seed direction.** Search PubMed for `virtual_neurology_visits care_equivalence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_efba2df41cc84c9f"`

---

### 24. Post-surgery confusion linked to future memory problems in older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_06582a505e001bb7` |
| **Stage** | other |
| **Published** | 2026-07-14 (59d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2850666) |
| **Suggested `factor.slug`** | `postoperative_delirium` |
| **Suggested `outcome.slug`** | `long_term_cognitive_decline` |

**Summary.** Older adults who experience delirium after surgery are twice as likely to develop long-term cognitive decline. This risk remains even after accounting for other health conditions.

**Why it matters.** If you or a loved one has surgery, ask your doctor about monitoring for postoperative confusion to address potential cognitive decline early.

**Seed direction.** Search PubMed for `postoperative_delirium long_term_cognitive_decline` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_06582a505e001bb7"`

---

### 25. Ebola survivors may face long-term neurological issues, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_51281ffea9235180` |
| **Stage** | other |
| **Published** | 2026-07-21 (52d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851032) |
| **Suggested `factor.slug`** | `ebola_virus` |
| **Suggested `outcome.slug`** | `neurological_complications` |

**Summary.** A study found Ebola survivors often develop persistent neurological problems. These include memory loss and movement disorders lasting years.

**Why it matters.** If you or someone you know survived Ebola, discuss long-term neurological monitoring with a healthcare provider.

**Seed direction.** Search PubMed for `ebola_virus neurological_complications` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_51281ffea9235180"`

---

### 26. Web tool helps patients stay on antidepressants longer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_82c82aa9bbec1885` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-04 (38d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2850824) |
| **Suggested `factor.slug`** | `decision_support_tool` |
| **Suggested `outcome.slug`** | `antidepressant_discontinuation` |

**Summary.** Patients using a web-based decision-support tool were less likely to stop antidepressants early at 8 weeks.
This reduced discontinuation compared to standard care without the tool.

**Why it matters.** Ask your doctor if a decision-support tool can help you stay on antidepressants longer for better depression management.

**Seed direction.** Search PubMed for `decision_support_tool antidepressant_discontinuation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_82c82aa9bbec1885"`

---

### 27. Pregnant women using acetaminophen not linked to autism or ADHD in children

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c3b2819380c42865` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (38d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851690) |
| **Suggested `factor.slug`** | `acetaminophen` |
| **Suggested `outcome.slug`** | `autism_adhd` |

**Summary.** A large study found no association between acetaminophen use during pregnancy and autism or ADHD in offspring. This confirms existing evidence on the safety of common pain relief during pregnancy.

**Why it matters.** Pregnant people can safely use acetaminophen for pain relief as directed, without fearing autism or ADHD risks in children.

**Seed direction.** Search PubMed for `acetaminophen autism_adhd` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_c3b2819380c42865"`

---

### 28. Mechanical clot removal improves recovery for stroke patients with medium or distal artery blockages.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6fe724c3027f0767` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (10d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851951) |
| **Suggested `factor.slug`** | `mechanical_thrombectomy` |
| **Suggested `outcome.slug`** | `functional_independence` |

**Summary.** Mechanical thrombectomy plus standard care improved recovery rates for stroke patients with medium or distal artery blockages. A higher percentage achieved functional independence at 90 days compared to standard care alone.

**Why it matters.** If you or someone you know has a stroke with a medium or distal artery blockage, ask your doctor about mechanical thrombectomy as part of treatment.

**Seed direction.** Search PubMed for `mechanical_thrombectomy functional_independence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_6fe724c3027f0767"`

---

### 29. Endovascular treatment for large stroke improves 1-year recovery compared to standard care.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_aa3d028565d9c70c` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (10d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852448) |
| **Suggested `factor.slug`** | `endovascular_thrombectomy` |
| **Suggested `outcome.slug`** | `functional_outcome` |

**Summary.** Patients with large stroke treated with endovascular thrombectomy had better one-year functional outcomes and survival rates than medical management alone. The benefit was significant for both measures.

**Why it matters.** If you or a loved one has a large stroke, ask your doctor if endovascular treatment is appropriate for improved long-term recovery.

**Seed direction.** Search PubMed for `endovascular_thrombectomy functional_outcome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_aa3d028565d9c70c"`

---

### 30. Thrombectomy for Stroke Clots in Smaller Arteries Improves Outcomes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_95c15f102f5df3fe` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (10d ago) |
| **Strength** | 70% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851954) |
| **Suggested `factor.slug`** | `mechanical_thrombectomy` |
| **Suggested `outcome.slug`** | `ischemic_stroke` |

**Summary.** Adding mechanical thrombectomy to standard care improved functional recovery in stroke patients with medium or distal artery blockages. 60% of thrombectomy patients had good outcomes versus 40% with standard care alone.

**Why it matters.** If you or someone you know has a stroke with a clot in a smaller artery, ask if mechanical thrombectomy is an option to improve recovery chances.

**Seed direction.** Search PubMed for `mechanical_thrombectomy ischemic_stroke` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_95c15f102f5df3fe"`

---

### 31. New noninvasive scan finds clot source in stroke patients, improving treatment decisions

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8e723f61a7b0f64d` |
| **Stage** | Phase 2 |
| **Published** | 2026-09-01 (10d ago) |
| **Strength** | 70% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42677492/?utm_source=Chrome&utm_medium=rss&utm_campaign=None&utm_content=0147763&fc=None&ff=20260907003013&v=2.20.1) |
| **Suggested `factor.slug`** | `noninvasive_thrombus_imaging` |
| **Suggested `outcome.slug`** | `ischemic_stroke` |

**Summary.** Noninvasive imaging directly identifies blood clots in stroke patients. It frequently reveals the clot's origin, enabling more precise treatment planning.

**Why it matters.** This test could lead to faster, more targeted stroke treatment in the future, improving recovery chances for patients.

**Seed direction.** Search PubMed for `noninvasive_thrombus_imaging ischemic_stroke` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_8e723f61a7b0f64d"`

---


## Other  ·  5 candidates
### 32. WHO prequalifies first malaria treatment for infants under six months

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2fc6c3b9b1918bf9` |
| **Stage** | Approved / Label |
| **Published** | 2026-06-09 (94d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2849301) |
| **Suggested `factor.slug`** | `infant_malaria_treatment` |
| **Suggested `outcome.slug`** | `malaria` |

**Summary.** WHO prequalified a new malaria treatment designed for infants under six months. This is the first such treatment approved for this age group.

**Why it matters.** Parents in malaria areas should seek immediate care for infants with fever, as a new infant-specific treatment is now available through health programs.

**Seed direction.** Search PubMed for `infant_malaria_treatment malaria` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_2fc6c3b9b1918bf9"`

---

### 33. ACOG releases 2026 maternal immunization schedule, differing from CDC recommendations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_da2120b27bcd3d2b` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (59d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2850667) |
| **Suggested `factor.slug`** | `maternal_vaccination` |
| **Suggested `outcome.slug`** | `maternal_infection_prevention` |

**Summary.** ACOG issued its first formal maternal vaccine schedule for 2026 that does not align with CDC guidelines. This marks a significant shift in obstetric care recommendations.

**Why it matters.** Pregnant individuals should discuss vaccination plans with their OB/GYN, as ACOG's new schedule may change which vaccines are recommended during pregnancy.

**Seed direction.** Search PubMed for `maternal_vaccination maternal_infection_prevention` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_da2120b27bcd3d2b"`

---

### 34. FDA approves first oral antibiotic for serious urinary tract infections

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_bb11334112b54274` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (38d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851693) |
| **Suggested `factor.slug`** | `oral_carbapenem` |
| **Suggested `outcome.slug`** | `complicated_utis` |

**Summary.** The FDA approved the first oral carbapenem antibiotic for complicated urinary tract infections. This offers a convenient alternative to IV therapy for patients.

**Why it matters.** Ask your doctor about this oral option for complicated UTIs to potentially avoid IV antibiotics and hospital visits.

**Seed direction.** Search PubMed for `oral_carbapenem complicated_utis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_bb11334112b54274"`

---

### 35. FDA approves first mRNA flu vaccine, offering new protection against influenza

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c4b63497f5702144` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (3d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853094) |
| **Suggested `factor.slug`** | `mRNA_flu_vaccine` |
| **Suggested `outcome.slug`** | `influenza` |

**Summary.** The first mRNA-based flu vaccine received FDA approval. It uses technology proven in successful COVID-19 vaccines.

**Why it matters.** Ask your doctor about the new mRNA flu vaccine when it becomes available this fall for better seasonal protection.

**Seed direction.** Search PubMed for `mRNA_flu_vaccine influenza` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_c4b63497f5702144"`

---

### 36. FDA approves first generic single-dose flu treatment, increasing affordability

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6385c93e7b351a52` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (38d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851691) |
| **Suggested `factor.slug`** | `generic_flu_treatment` |
| **Suggested `outcome.slug`** | `influenza` |

**Summary.** The FDA approved the first generic version of a single-dose influenza treatment. This will expand access and reduce costs for patients.

**Why it matters.** Ask your doctor about this affordable flu treatment option for faster symptom relief during flu season.

**Seed direction.** Search PubMed for `generic_flu_treatment influenza` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6385c93e7b351a52"`

---

