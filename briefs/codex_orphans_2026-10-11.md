# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** 2026-10-11
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** 59 across 6 categories
**Strength threshold:** ≥ 0.7

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


## Oncology  ·  10 candidates
### 1. Combination therapy extends survival in EGFR lung cancer by over 10 months

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_036069b76d4e1788` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-08 (33d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852633) |
| **Suggested `factor.slug`** | `osimertinib_plus_platinum_pemetrexed` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** A phase 3 trial showed adding chemotherapy to targeted therapy increased median survival from 37.6 to 47.5 months. The combination reduced death risk by 23% compared to targeted therapy alone.

**Why it matters.** If you or a loved one has EGFR-mutated lung cancer, discuss combination therapy with your doctor as a first-line treatment option.

**Seed direction.** Search PubMed for `osimertinib_plus_platinum_pemetrexed overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_036069b76d4e1788"`

---

### 2. New drug combo approved for advanced HER2-positive breast cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_54e28f36524fc62b` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (3d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-tucatinib-trastuzumab-and-pertuzumab-maintenance-treatment-her2-positive-breast-cancer) |
| **Suggested `factor.slug`** | `tucatinib_trastuzumab_pertuzumab_combo` |
| **Suggested `outcome.slug`** | `her2_positive_breast_cancer_maintenance` |

**Summary.** The FDA has approved a new combination therapy for adults with advanced HER2-positive breast cancer. It is used after initial treatment to help maintain control of the disease.

**Why it matters.** This approval offers a new maintenance option for patients with advanced HER2-positive breast cancer, potentially extending time without disease progression.

**Seed direction.** Search PubMed for `tucatinib_trastuzumab_pertuzumab_combo her2_positive_breast_cancer_maintenance` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_54e28f36524fc62b"`

---

### 3. New drug approved for rare blood disorder causing excess red blood cells

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c647df2d84a6abc2` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-09 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-drug-its-kind-polycythemia-vera-rare-blood-disorder) |
| **Suggested `factor.slug`** | `rusfertide` |
| **Suggested `outcome.slug`** | `polycythemia_vera` |

**Summary.** The FDA has approved rusfertide for adults with polycythemia vera, a rare blood disorder that causes the body to produce too many red blood cells. This is the first drug of its kind approved for this condition.

**Why it matters.** People with polycythemia vera should talk to their doctor about this new treatment option.

**Seed direction.** Search PubMed for `rusfertide polycythemia_vera` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_c647df2d84a6abc2"`

---

### 4. New treatment approved for early-stage colon cancer with specific genetic marker

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5f7c11942825c50a` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-09 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-atezolizumab-combination-chemotherapy-stage-iii-mismatch-repair-deficient-colon-cancer) |
| **Suggested `factor.slug`** | `chemo_immunotherapy_combo` |
| **Suggested `outcome.slug`** | `colon_cancer_recurrence` |

**Summary.** The FDA has approved a combination of chemotherapy and immunotherapy for adults and children with Stage III colon cancer that has a specific genetic defect. This treatment is intended to reduce the risk of cancer returning after surgery.

**Why it matters.** If you or a loved one has this type of colon cancer, ask your doctor if this new option is right for you.

**Seed direction.** Search PubMed for `chemo_immunotherapy_combo colon_cancer_recurrence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_5f7c11942825c50a"`

---

### 5. New drug approved for advanced pancreatic cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_fb068eb5540424c0` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-09 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-class-targeted-therapy-metastatic-pancreatic-cancer) |
| **Suggested `factor.slug`** | `ras_inhibitor` |
| **Suggested `outcome.slug`** | `metastatic_pancreatic_cancer` |

**Summary.** The FDA has approved a new targeted therapy for metastatic pancreatic cancer. It is the first of its kind to treat the most common form of this aggressive disease.

**Why it matters.** Patients with advanced pancreatic cancer now have a new treatment option approved ahead of schedule.

**Seed direction.** Search PubMed for `ras_inhibitor metastatic_pancreatic_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_fb068eb5540424c0"`

---

### 6. Removing fallopian tubes during routine surgery may lower ovarian cancer risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_62e029ea6fac2440` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (89d ago) |
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

### 7. FDA approves first new sunscreen ingredient in 30 years

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0c157ee7cbf678cc` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (82d ago) |
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

### 8. New treatment approved for advanced breast cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_df5771162bf505a7` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (3d ago) |
| **Strength** | 90% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-grants-accelerated-approval-new-breast-cancer-treatment) |
| **Suggested `factor.slug`** | `new_breast_cancer_treatment` |
| **Suggested `outcome.slug`** | `advanced_breast_cancer` |

**Summary.** The FDA has granted accelerated approval to a new treatment for adult patients with advanced breast cancer. This expands available options for patients who need new therapies.

**Why it matters.** Patients with advanced breast cancer now have access to a newly approved treatment option.

**Seed direction.** Search PubMed for `new_breast_cancer_treatment advanced_breast_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_df5771162bf505a7"`

---

### 9. New algorithm safely rules out blood clots in cancer patients, avoiding CT scans

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_39fdd03b34d86bf2` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-25 (47d ago) |
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

### 10. New guideline adds blood test option for colorectal cancer screening

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e5887844999f1e27` |
| **Stage** | Guideline |
| **Published** | 2026-09-08 (33d ago) |
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


## Cardiovascular  ·  9 candidates
### 11. Nicotine vapes may help more people quit smoking than patches or gum

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6268e1fd1a60452c` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854234) |
| **Suggested `factor.slug`** | `nicotine_vapes` |
| **Suggested `outcome.slug`** | `smoking_cessation` |

**Summary.** People were more likely to quit smoking using nicotine vapes compared to traditional nicotine replacement therapies like patches or gum. The updated Cochrane review found a significant difference in success rates.

**Why it matters.** If you're trying to quit smoking, nicotine vapes may offer a more effective option than gum or patches.

**Seed direction.** Search PubMed for `nicotine_vapes smoking_cessation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6268e1fd1a60452c"`

---

### 12. First heart valve designed to grow with children gets FDA approval

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e2b180179d60aa40` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-07 (4d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-heart-valve-designed-grow-children) |
| **Suggested `factor.slug`** | `size_adjustable_heart_valve` |
| **Suggested `outcome.slug`** | `congenital_pulmonary_valve_disease` |

**Summary.** The Autus Size-Adjustable Valve is approved for pediatric patients with congenital pulmonary valve disease. It is the first surgically implanted heart valve designed to grow with children.

**Why it matters.** Children with this condition may avoid repeated surgeries as the valve can adapt to their growth.

**Seed direction.** Search PubMed for `size_adjustable_heart_valve congenital_pulmonary_valve_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_e2b180179d60aa40"`

---

### 13. Major heart groups agree on a single definition for heart failure

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb5e3b6d8c3e1b49` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (61d ago) |
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

### 14. Updated Heart Disease Guidelines for Older Adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_99b0c6b66be5ad72` |
| **Stage** | Guideline |
| **Published** | 2026-09-22 (19d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853628) |
| **Suggested `factor.slug`** | `age_inclusive_care` |
| **Suggested `outcome.slug`** | `cardiovascular_disease` |

**Summary.** The American College of Cardiology released new guidelines for heart disease care in older adults. These emphasize age-specific treatment adjustments for better outcomes.

**Why it matters.** Older adults with heart disease should ask their doctor about age-appropriate care plans, as new guidelines now standardize personalized treatment approaches.

**Seed direction.** Search PubMed for `age_inclusive_care cardiovascular_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_99b0c6b66be5ad72"`

---

### 15. Microplastics Found in Blood of Heart Attack Patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8b0f91e34d087299` |
| **Stage** | Preclinical |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854235) |
| **Suggested `factor.slug`** | `microplastics` |
| **Suggested `outcome.slug`** | `myocardial_infarction` |

**Summary.** More microplastics and nanoplastics were detected in the coronary blood of patients having heart attacks compared to healthy individuals or those with chronic heart conditions.

**Why it matters.** This suggests environmental pollutants may play a role in heart disease—consider reducing plastic use to protect heart health.

**Seed direction.** Search PubMed for `microplastics myocardial_infarction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_8b0f91e34d087299"`

---

### 16. Pre-op iron reduces blood needs and improves recovery after heart surgery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_26eed9a442dc0494` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-24 (48d ago) |
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

### 17. IV iron before heart surgery reduces blood transfusions and improves 90-day recovery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b07cf4e81bd58d81` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-26 (46d ago) |
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

### 18. Nearly 80% of young adults with metabolic syndrome show early artery damage

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_98d9e89377de3985` |
| **Stage** | research |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854233) |
| **Suggested `factor.slug`** | `ckm_syndrome` |
| **Suggested `outcome.slug`** | `artery_damage` |

**Summary.** A study found that nearly 80% of young adults with cardiovascular-kidney-metabolic (CKM) syndrome had early signs of artery damage. This condition is linked to worse cardiovascular health.

**Why it matters.** Young adults with metabolic issues should get heart health checked early to prevent future problems.

**Seed direction.** Search PubMed for `ckm_syndrome artery_damage` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_98d9e89377de3985"`

---

### 19. IV iron before heart surgery reduces need for blood transfusions by 7%

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f8bbb8f9c34029d8` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-22 (50d ago) |
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


## Metabolic  ·  10 candidates
### 20. FDA approves first oral drug to lower LDL cholesterol

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a3bf5bc02049572f` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (47d ago) |
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

### 21. First gene therapy approved for children with Sanfilippo syndrome

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f1c1f2dc90e24b4d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (3d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-gene-therapy-pediatric-patients-sanfilippo-syndrome-type) |
| **Suggested `factor.slug`** | `gene_therapy` |
| **Suggested `outcome.slug`** | `sanfilippo_syndrome_type_a` |

**Summary.** The FDA has approved the first gene therapy for children with Sanfilippo syndrome type A, a rare inherited metabolic disorder. This treatment offers a new option for a condition that previously had no approved therapy.

**Why it matters.** Families of children with this rare disease now have access to a treatment that may slow progression and improve quality of life.

**Seed direction.** Search PubMed for `gene_therapy sanfilippo_syndrome_type_a` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_f1c1f2dc90e24b4d"`

---

### 22. New wearable tracks blood sugar and ketones continuously

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0e91983ca274d562` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-10 (1d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-authorizes-first-wearable-device-continuously-monitors-both-ketone-levels-and-blood-sugar) |
| **Suggested `factor.slug`** | `libre_duo_10_day_monitor` |
| **Suggested `outcome.slug`** | `diabetes_management` |

**Summary.** The Libre Duo 10 Day system is approved for people aged 2 and older with diabetes. It provides continuous monitoring of both glucose and ketone levels.

**Why it matters.** People with diabetes can now track two key health markers in real time with a single wearable device.

**Seed direction.** Search PubMed for `libre_duo_10_day_monitor diabetes_management` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_0e91983ca274d562"`

---

### 23. First OTC glucose monitor approved for children with diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3a1173badb98dc91` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (82d ago) |
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

### 24. AI-Powered Eye Scan Improves Diabetes Vision Screening Accuracy

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0a2c6d6f6e7a8c8b` |
| **Stage** | Phase 3 |
| **Published** | 2026-07-21 (82d ago) |
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

### 25. First Drug Approved to Lower Pancreatitis Risk in Severe High Triglycerides

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_66ec86d216139ace` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-11 (61d ago) |
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

### 26. FDA approves gene therapy for children 2+ with sickle cell disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ab673401325c68f1` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-18 (54d ago) |
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

### 27. New Guidelines Standardize Diagnosis and Treatment for Heart-Kidney-Metabolic Condition

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_9da7dbf213dfafac` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (61d ago) |
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

### 28. Bone health: 600 METs-min/week of walking/jogging, plus falls risk assessment.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7878d119f83dc7e0` |
| **Stage** | Guideline |
| **Published** | 2026-09-10 (31d ago) |
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

### 29. Some diabetes drugs may better protect kidneys for people with protein in urine

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4fe1552550fa8fe8` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-18 (23d ago) |
| **Strength** | 80% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100574/rr-0) |
| **Suggested `factor.slug`** | `glp1_sgl2_drugs` |
| **Suggested `outcome.slug`** | `kidney_decline` |

**Summary.** Patients with protein in urine had a 3.2% kidney decline risk with newer diabetes drugs versus 5.4% with older drugs over five years. Without protein in urine, risks were similar (2.4% vs 2.1%).

**Why it matters.** Ask your doctor if protein in your urine means you should consider certain diabetes medications for better kidney protection.

**Seed direction.** Search PubMed for `glp1_sgl2_drugs kidney_decline` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_4fe1552550fa8fe8"`

---


## Neuro & Mental Health  ·  19 candidates
### 30. FDA Approves New ADHD Medication

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_33b0fdb6f0ab7d0b` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (33d ago) |
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

### 31. FDA approves first drug for Alexander disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4d237501fc6e4ed3` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (3d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-drug-treat-alexander-disease) |
| **Suggested `factor.slug`** | `zanvastro` |
| **Suggested `outcome.slug`** | `alexander_disease` |

**Summary.** The FDA has approved a new injection for treating Alexander disease in both children and adults. This is the first approved treatment for this rare neurological condition.

**Why it matters.** People with Alexander disease now have their first approved treatment option, offering new hope for managing the disease.

**Seed direction.** Search PubMed for `zanvastro alexander_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_4d237501fc6e4ed3"`

---

### 32. FDA approves new drug for agitation in Alzheimer's dementia patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4f487e92268d5f9a` |
| **Stage** | Approved / Label |
| **Published** | 2026-06-16 (117d ago) |
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

### 33. FDA approves second over-the-counter naloxone nasal spray for opioid overdose

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_47a96cc94db33c7c` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-28 (75d ago) |
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

### 34. Blood thinner more effective than standard drug for migraines linked to heart hole

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cd80dcb8bd64e525` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-06 (66d ago) |
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

### 35. FDA approves home start for Alzheimer's antibody treatment

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7e72d1fb17965942` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (47d ago) |
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

### 36. 988 Lifeline linked to 11% drop in youth suicide deaths, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3fbb4c6d2d44e3b8` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-22 (19d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852956) |
| **Suggested `factor.slug`** | `988_lifeline` |
| **Suggested `outcome.slug`** | `suicide_mortality` |

**Summary.** A study found 11% fewer adolescent and young adult suicide deaths after 988 Lifeline launch. This equals 4,372 fewer deaths than expected.

**Why it matters.** Call or text 988 if you or someone you know is in crisis—this national service is linked to a significant reduction in youth suicides.

**Seed direction.** Search PubMed for `988_lifeline suicide_mortality` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_3fbb4c6d2d44e3b8"`

---

### 37. Early-life sugar limits may lower dementia risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2001ce500f754062` |
| **Stage** | observational |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854232) |
| **Suggested `factor.slug`** | `early_life_sugar_intake` |
| **Suggested `outcome.slug`** | `dementia` |

**Summary.** People who had limited sugar intake in their first 1000 days of life showed better brain health and lower dementia risk later in life. The study analyzed data from a large cohort over decades.

**Why it matters.** Limiting sugar in early childhood may support long-term brain health and reduce dementia risk.

**Seed direction.** Search PubMed for `early_life_sugar_intake dementia` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_2001ce500f754062"`

---

### 38. Optogenetics helps some people see again after retinitis pigmentosa

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2e6814462d8b83c9` |
| **Stage** | Phase 1 |
| **Published** | 2026-10-07 (4d ago) |
| **Strength** | 85% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/07/optogenetics-restores-some-vision-retinitis-pigmentosa/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `optogenetics` |
| **Suggested `outcome.slug`** | `retinitis_pigmentosa` |

**Summary.** In a small trial, about half of patients regained photosensitivity. The treatment uses light-sensitive proteins to restore some vision.

**Why it matters.** This early research offers hope for people with inherited vision loss, showing that restoring sight may be possible.

**Seed direction.** Search PubMed for `optogenetics retinitis_pigmentosa` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_2e6814462d8b83c9"`

---

### 39. Post-surgery confusion linked to future memory problems in older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_06582a505e001bb7` |
| **Stage** | other |
| **Published** | 2026-07-14 (89d ago) |
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

### 40. Ebola survivors may face long-term neurological issues, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_51281ffea9235180` |
| **Stage** | other |
| **Published** | 2026-07-21 (82d ago) |
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

### 41. Web tool helps patients stay on antidepressants longer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_82c82aa9bbec1885` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-04 (68d ago) |
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

### 42. Pregnant women using acetaminophen not linked to autism or ADHD in children

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c3b2819380c42865` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (68d ago) |
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

### 43. Mechanical clot removal improves recovery for stroke patients with medium or distal artery blockages.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6fe724c3027f0767` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (40d ago) |
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

### 44. Endovascular treatment for large stroke improves 1-year recovery compared to standard care.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_aa3d028565d9c70c` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (40d ago) |
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

### 45. Blood test may predict Alzheimer's-related cognitive decline risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_995ae1d23488274d` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-15 (26d ago) |
| **Strength** | 80% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2851721) |
| **Suggested `factor.slug`** | `blood_biomarkers` |
| **Suggested `outcome.slug`** | `cognitive_impairment` |

**Summary.** A blood test for Alzheimer's biomarkers accurately predicts cognitive impairment risk. This could enable earlier diagnosis and treatment with new therapies.

**Why it matters.** Ask your doctor about blood-based Alzheimer's risk testing if you're concerned about cognitive changes.

**Seed direction.** Search PubMed for `blood_biomarkers cognitive_impairment` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_995ae1d23488274d"`

---

### 46. New injection therapy shows safety in early glaucoma trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b54c506d5e304338` |
| **Stage** | Phase 1 |
| **Published** | 2026-10-09 (2d ago) |
| **Strength** | 75% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/09/biotech-news-life-biosciences-share-glaucoma-cellular-reprogramming-drug-update/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `cellular_reprogramming` |
| **Suggested `outcome.slug`** | `glaucoma` |

**Summary.** Three patients with glaucoma received a single injection of an experimental therapy. No serious side effects were reported.

**Why it matters.** This early trial suggests a potential new treatment path for glaucoma with a single injection and no major safety concerns.

**Seed direction.** Search PubMed for `cellular_reprogramming glaucoma` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_b54c506d5e304338"`

---

### 47. Thrombectomy for Stroke Clots in Smaller Arteries Improves Outcomes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_95c15f102f5df3fe` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (40d ago) |
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

### 48. New noninvasive scan finds clot source in stroke patients, improving treatment decisions

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8e723f61a7b0f64d` |
| **Stage** | Phase 2 |
| **Published** | 2026-09-01 (40d ago) |
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


## Longevity  ·  1 candidate
### 49. Better physical fitness linked to longer life in older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7dab82bbd86ef7bb` |
| **Stage** | research |
| **Published** | 2026-09-22 (19d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853630) |
| **Suggested `factor.slug`** | `physical_fitness` |
| **Suggested `outcome.slug`** | `all_cause_mortality` |

**Summary.** Older adults with higher physical fitness had lower risk of death from any cause. The study tracked health outcomes over time.

**Why it matters.** Staying physically active may help you live longer, even as you age.

**Seed direction.** Search PubMed for `physical_fitness all_cause_mortality` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_7dab82bbd86ef7bb"`

---


## Other  ·  10 candidates
### 50. FDA approves first robotic device for blood draws in adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_68d956358a305371` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853910) |
| **Suggested `factor.slug`** | `robotic_blood_draw_device` |
| **Suggested `outcome.slug`** | `blood_draw_accuracy` |

**Summary.** The FDA has authorized the first stand-alone robotic device for drawing blood from adults in outpatient settings. It is designed to improve consistency and reduce human error in blood collection.

**Why it matters.** This technology could make blood tests faster and more reliable for patients and clinics.

**Seed direction.** Search PubMed for `robotic_blood_draw_device blood_draw_accuracy` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_68d956358a305371"`

---

### 51. FDA approves first oral drug for adult dermatomyositis

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_39a328133dbdf7ed` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-09 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-oral-drug-indicated-treat-dermatomyositis-adults) |
| **Suggested `factor.slug`** | `brepocitinib` |
| **Suggested `outcome.slug`** | `dermatomyositis` |

**Summary.** The FDA has approved brepocitinib tablets for treating dermatomyositis in adults. This is the first oral medication approved specifically for this condition.

**Why it matters.** People with dermatomyositis now have a new, convenient treatment option approved by the FDA.

**Seed direction.** Search PubMed for `brepocitinib dermatomyositis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_39a328133dbdf7ed"`

---

### 52. ACOG releases 2026 maternal immunization schedule, differing from CDC recommendations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_da2120b27bcd3d2b` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (89d ago) |
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

### 53. FDA approves first oral antibiotic for serious urinary tract infections

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_bb11334112b54274` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (68d ago) |
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

### 54. FDA approves first mRNA flu vaccine, offering new protection against influenza

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c4b63497f5702144` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (33d ago) |
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

### 55. FDA approves first freeze-dried plasma product for U.S. use

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6e04af7812b96e19` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-15 (26d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853282) |
| **Suggested `factor.slug`** | `freeze_dried_plasma` |
| **Suggested `outcome.slug`** | `blood_transfusion` |

**Summary.** The FDA approved the first freeze-dried plasma product in the U.S. This product can be stored at room temperature and reconstituted quickly for emergency use.

**Why it matters.** This means plasma can now be transported without refrigeration, improving emergency care access in remote areas and during disasters.

**Seed direction.** Search PubMed for `freeze_dried_plasma blood_transfusion` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6e04af7812b96e19"`

---

### 56. New drug approved for stubborn herpes sores in immune-compromised adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_498b479f8003cd85` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-10 (1d ago) |
| **Strength** | 90% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/news-events-human-drugs/fda-approves-drug-treat-lesions-caused-herpes-simplex-virus) |
| **Suggested `factor.slug`** | `pritelivir` |
| **Suggested `outcome.slug`** | `herpes_simplex_lesions` |

**Summary.** The FDA has approved a new drug for adults with weakened immune systems who have not responded to other treatments for herpes simplex virus skin and mucosal lesions. It is intended for patients who continue to have sores despite prior therapy.

**Why it matters.** If you or someone you know has persistent herpes sores and a weakened immune system, this approval offers a new treatment option.

**Seed direction.** Search PubMed for `pritelivir herpes_simplex_lesions` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_498b479f8003cd85"`

---

### 57. Writing style may affect how patients are responded to

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_01baa2a6eb915a69` |
| **Stage** | research |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854231) |
| **Suggested `factor.slug`** | `writing_style` |
| **Suggested `outcome.slug`** | `patient_message_response_disparity` |

**Summary.** A study found that bias in writing style explained nearly half of the differences in care team responses to patient messages from marginalized groups.

**Why it matters.** Healthcare providers should review their message tone to ensure equitable patient communication.

**Seed direction.** Search PubMed for `writing_style patient_message_response_disparity` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_01baa2a6eb915a69"`

---

### 58. Tick bites may raise risk of blood transfusion reactions

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8bf01ac45f6cff82` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-06 (5d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854230) |
| **Suggested `factor.slug`** | `alpha_gal_syndrome` |
| **Suggested `outcome.slug`** | `transfusion_reaction` |

**Summary.** People with alpha-gal syndrome, caused by tick bites, may have allergic reactions to blood transfusions. This may be due to immune antibodies reacting with certain blood components.

**Why it matters.** If you have a red meat allergy from a tick bite, tell your doctor before a blood transfusion.

**Seed direction.** Search PubMed for `alpha_gal_syndrome transfusion_reaction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_8bf01ac45f6cff82"`

---

### 59. FDA approves first generic single-dose flu treatment, increasing affordability

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6385c93e7b351a52` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (68d ago) |
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

