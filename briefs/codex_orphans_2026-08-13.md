# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** 2026-08-13
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** 28 across 6 categories
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


## Oncology  ·  4 candidates
### 1. Datopotamab-deruxtecan extends overall survival in metastatic TNBC

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_dato_dxd_tnbc_os` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-14 (91d ago) |
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
| **Published** | 2026-07-14 (30d ago) |
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
| **Published** | 2026-07-21 (23d ago) |
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

### 4. KRAS-G12D inhibitor MRTX1133: 41% ORR in pancreatic ductal adenocarcinoma

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_kras_g12d_phase1` |
| **Stage** | Phase 1 |
| **Published** | 2026-05-05 (100d ago) |
| **Strength** | 71% |
| **Source** | [Nature Medicine](https://www.nature.com/articles/s41591-026-mrtx1133) |
| **Suggested `factor.slug`** | `mrtx1133` |
| **Suggested `outcome.slug`** | `pancreatic_cancer` |

**Summary.** First-in-human Phase 1, n=78, heavily pre-treated PDAC. Objective response 41%, disease control 71%. Median PFS 7.4 months — unprecedented in this setting.

**Why it matters.** KRAS-G12D drives ~40% of pancreatic cancers. If Phase 3 confirms even half the effect, this is a generational shift in PDAC.

**Seed direction.** Search PubMed for `mrtx1133 pancreatic_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_kras_g12d_phase1"`

---


## Cardiovascular  ·  4 candidates
### 5. Major heart groups agree on a single definition for heart failure

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb5e3b6d8c3e1b49` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (2d ago) |
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

### 6. Low-dose colchicine cuts repeat heart attacks by 31% — now in cardiology guidelines

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_colchicine_postmi_acc` |
| **Stage** | Guideline |
| **Published** | 2026-05-08 (97d ago) |
| **Strength** | 88% |
| **Source** | [JACC](https://www.jacc.org/doi/10.1016/j.jacc.2026.04.008) |
| **Suggested `factor.slug`** | `colchicine` |
| **Suggested `outcome.slug`** | `post_mi_mace` |

**Summary.** Combining two large trials, a cheap, century-old anti-inflammatory pill (0.5 mg of colchicine daily) reduced repeat heart attacks, strokes, and cardiovascular death by nearly a third in people who already have heart disease. Major cardiology groups have added it to standard care.

**Why it matters.** If you've had a heart attack or have known coronary disease, this is a $10/month addition that's now backed by guidelines. Ask your cardiologist whether it fits your medications.

**Seed direction.** Search PubMed for `colchicine post_mi_mace` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_colchicine_postmi_acc"`

---

### 7. Memory Changes May Predict Heart Events 8 Years Early

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e6dece34f86e5874` |
| **Stage** | other |
| **Published** | 2026-06-09 (65d ago) |
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

### 8. One injection a year cut bad cholesterol roughly in half — for the whole year

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_pcsk9_silencing_long` |
| **Stage** | Phase 2 |
| **Published** | 2026-05-04 (101d ago) |
| **Strength** | 78% |
| **Source** | [The Lancet](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736-26-orion12) |
| **Suggested `factor.slug`** | `lerodalcibep` |
| **Suggested `outcome.slug`** | `ldl_cholesterol` |

**Summary.** A new gene-silencing therapy delivered as a single shot dropped LDL ('bad') cholesterol by 51% and held that drop steady for 12 months, in a 400-person Phase 2 trial. Two doses across two years matched what monthly cholesterol injections do today.

**Why it matters.** If approved, this turns cholesterol control from a daily pill or monthly injection into a once-yearly visit — far easier to stick with.

**Seed direction.** Search PubMed for `lerodalcibep ldl_cholesterol` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_pcsk9_silencing_long"`

---


## Metabolic  ·  5 candidates
### 9. Ozempic-class drug improves fatty liver disease in nearly two-thirds of patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_semaglutide_mash_phase3` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-12 (93d ago) |
| **Strength** | 90% |
| **Source** | [NEJM](https://www.nejm.org/doi/10.1056/NEJMoa2607) |
| **Suggested `factor.slug`** | `semaglutide` |
| **Suggested `outcome.slug`** | `mash` |

**Summary.** In an 800-person trial running 18 months, weekly semaglutide (the active ingredient in Ozempic and Wegovy) cleared fatty-liver inflammation in 63% of people vs 34% on placebo. Liver scarring also improved, and weight came down alongside.

**Why it matters.** Fatty liver disease affects roughly one in four adults and had almost no medical treatment. Now there's one that also helps with weight.

**Seed direction.** Search PubMed for `semaglutide mash` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_semaglutide_mash_phase3"`

---

### 10. First OTC glucose monitor approved for children with diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3a1173badb98dc91` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (23d ago) |
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

### 11. AI-Powered Eye Scan Improves Diabetes Vision Screening Accuracy

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0a2c6d6f6e7a8c8b` |
| **Stage** | Phase 3 |
| **Published** | 2026-07-21 (23d ago) |
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

### 12. First Drug Approved to Lower Pancreatitis Risk in Severe High Triglycerides

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_66ec86d216139ace` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-11 (2d ago) |
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

### 13. New Guidelines Standardize Diagnosis and Treatment for Heart-Kidney-Metabolic Condition

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_9da7dbf213dfafac` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (2d ago) |
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


## Neuro & Mental Health  ·  10 candidates
### 14. FDA approves new drug for agitation in Alzheimer's dementia patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4f487e92268d5f9a` |
| **Stage** | Approved / Label |
| **Published** | 2026-06-16 (58d ago) |
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

### 15. FDA approves second over-the-counter naloxone nasal spray for opioid overdose

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_47a96cc94db33c7c` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-28 (16d ago) |
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

### 16. Blood thinner more effective than standard drug for migraines linked to heart hole

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cd80dcb8bd64e525` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-06 (7d ago) |
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

### 17. FDA tightens monitoring for new Alzheimer's drug in people with a high-risk gene

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_lecanemab_apoe4_safety` |
| **Stage** | Approved / Label |
| **Published** | 2026-05-10 (95d ago) |
| **Strength** | 85% |
| **Source** | [FDA](https://www.fda.gov/drugs/drug-safety-and-availability/lecanemab-2026-update) |
| **Suggested `factor.slug`** | `lecanemab` |
| **Suggested `outcome.slug`** | `alzheimers` |

**Summary.** Real-world data on lecanemab (a new Alzheimer's-disease drug) showed brain swelling in about 1 in 3 patients who carry two copies of the APOE-ε4 gene, vs about 1 in 20 of those without it. The FDA now requires more frequent MRIs and gene-aware consent.

**Why it matters.** If you or a family member is considering lecanemab, a simple APOE genetic test now meaningfully changes the risk conversation with your doctor.

**Seed direction.** Search PubMed for `lecanemab alzheimers` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_lecanemab_apoe4_safety"`

---

### 18. Virtual neurology visits as effective as in-person for first-time patient evaluations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_efba2df41cc84c9f` |
| **Stage** | Phase 3 |
| **Published** | 2026-06-02 (72d ago) |
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

### 19. Single psilocybin session helps depression that didn't respond to standard drugs

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_psilocybin_trd_phase3` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-02 (103d ago) |
| **Strength** | 83% |
| **Source** | [NEJM](https://www.nejm.org/doi/10.1056/NEJMoa2026comp005) |
| **Suggested `factor.slug`** | `psilocybin` |
| **Suggested `outcome.slug`** | `treatment_resistant_depression` |

**Summary.** In a 300-person Phase 3 trial in treatment-resistant depression, one 25 mg dose of psilocybin (with psychological support) brought 31% of patients into remission at 6 weeks, vs 14% on placebo. The effect held through week 12 with no additional doses.

**Why it matters.** For people whose depression hasn't responded to two or more standard antidepressants, this is the first Phase 3 win for a psychedelic. FDA decision expected 2027.

**Seed direction.** Search PubMed for `psilocybin treatment_resistant_depression` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_psilocybin_trd_phase3"`

---

### 20. Post-surgery confusion linked to future memory problems in older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_06582a505e001bb7` |
| **Stage** | other |
| **Published** | 2026-07-14 (30d ago) |
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

### 21. Ebola survivors may face long-term neurological issues, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_51281ffea9235180` |
| **Stage** | other |
| **Published** | 2026-07-21 (23d ago) |
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

### 22. Web tool helps patients stay on antidepressants longer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_82c82aa9bbec1885` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-04 (9d ago) |
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

### 23. Pregnant women using acetaminophen not linked to autism or ADHD in children

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c3b2819380c42865` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (9d ago) |
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


## Longevity  ·  1 candidate
### 24. Low-dose rapamycin once a week improved immune response in healthy older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_rapamycin_aging_phase2` |
| **Stage** | Phase 2 |
| **Published** | 2026-05-06 (99d ago) |
| **Strength** | 62% |
| **Source** | [Aging Cell](https://onlinelibrary.wiley.com/doi/10.1111/acel.2026.pearl) |
| **Suggested `factor.slug`** | `rapamycin` |
| **Suggested `outcome.slug`** | `immunosenescence` |

**Summary.** In 120 healthy adults aged 50-85, 5 mg of rapamycin once a week for 11 months raised flu-vaccine antibody response by 22% and reduced markers of immune aging. No serious side effects.

**Why it matters.** First well-run trial in healthy aging to show an immune benefit. Still early — the question now is whether the same protocol affects real-world infection or hospitalisation rates.

**Seed direction.** Search PubMed for `rapamycin immunosenescence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_rapamycin_aging_phase2"`

---


## Other  ·  4 candidates
### 25. WHO prequalifies first malaria treatment for infants under six months

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2fc6c3b9b1918bf9` |
| **Stage** | Approved / Label |
| **Published** | 2026-06-09 (65d ago) |
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

### 26. ACOG releases 2026 maternal immunization schedule, differing from CDC recommendations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_da2120b27bcd3d2b` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (30d ago) |
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

### 27. FDA approves first oral antibiotic for serious urinary tract infections

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_bb11334112b54274` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (9d ago) |
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

### 28. FDA approves first generic single-dose flu treatment, increasing affordability

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6385c93e7b351a52` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (9d ago) |
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

