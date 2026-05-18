# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** 2026-05-18
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** 8 across 5 categories
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


## Oncology  ·  2 candidates
### 1. Datopotamab-deruxtecan extends overall survival in metastatic TNBC

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_dato_dxd_tnbc_os` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-14 (4d ago) |
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

### 2. KRAS-G12D inhibitor MRTX1133: 41% ORR in pancreatic ductal adenocarcinoma

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_kras_g12d_phase1` |
| **Stage** | Phase 1 |
| **Published** | 2026-05-05 (13d ago) |
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


## Cardiovascular  ·  2 candidates
### 3. ACC/AHA add low-dose colchicine 0.5 mg to post-MI guidelines (Class IIa)

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_colchicine_postmi_acc` |
| **Stage** | Guideline |
| **Published** | 2026-05-08 (10d ago) |
| **Strength** | 88% |
| **Source** | [JACC](https://www.jacc.org/doi/10.1016/j.jacc.2026.04.008) |
| **Suggested `factor.slug`** | `colchicine` |
| **Suggested `outcome.slug`** | `post_mi_mace` |

**Summary.** Based on LoDoCo2 + COLCOT pooled data: 31% relative reduction in recurrent MI/stroke/CV-death. Recommended for chronic coronary disease patients without contraindications.

**Why it matters.** Cheap (<$10/mo), oral, evidence-graded — but interacts with statins and many antibiotics. Expect uptake to lag behind the data.

**Seed direction.** Search PubMed for `colchicine post_mi_mace` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_colchicine_postmi_acc"`

---

### 4. Single-dose lerodalcibep silences PCSK9 for 12 months in Phase 2b

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_pcsk9_silencing_long` |
| **Stage** | Phase 2 |
| **Published** | 2026-05-04 (14d ago) |
| **Strength** | 78% |
| **Source** | [The Lancet](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736-26-orion12) |
| **Suggested `factor.slug`** | `lerodalcibep` |
| **Suggested `outcome.slug`** | `ldl_cholesterol` |

**Summary.** ORION-12 — one subcutaneous dose, LDL-C reduction of 51% sustained at week 52. Two doses across 2 years approached PCSK9 mAb efficacy without monthly injections.

**Why it matters.** If durability holds, shifts the cost/adherence math against monthly mAbs (alirocumab, evolocumab). Once-yearly LDL therapy is plausible.

**Seed direction.** Search PubMed for `lerodalcibep ldl_cholesterol` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_pcsk9_silencing_long"`

---


## Metabolic  ·  1 candidate
### 5. Semaglutide 2.4 mg resolves MASH without worsening fibrosis in Phase 3

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_semaglutide_mash_phase3` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-12 (6d ago) |
| **Strength** | 90% |
| **Source** | [NEJM](https://www.nejm.org/doi/10.1056/NEJMoa2607) |
| **Suggested `factor.slug`** | `semaglutide` |
| **Suggested `outcome.slug`** | `mash` |

**Summary.** ESSENCE Part 1 — 72 weeks, 800 patients. MASH resolution 62.9% vs 34.3% placebo; fibrosis improvement 36.8% vs 22.4%. ALT and weight tracked downward together.

**Why it matters.** First GLP-1 with histologic MASH benefit on hard endpoints. Reframes who gets a GLP-1: not just T2D + obesity but anyone with biopsy-proven steatohepatitis.

**Seed direction.** Search PubMed for `semaglutide mash` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_semaglutide_mash_phase3"`

---


## Neuro & Mental Health  ·  2 candidates
### 6. FDA updates lecanemab label: APOE-ε4 homozygotes require MRI at 5, 7, 14

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_lecanemab_apoe4_safety` |
| **Stage** | Approved / Label |
| **Published** | 2026-05-10 (8d ago) |
| **Strength** | 85% |
| **Source** | [FDA Drug Safety](https://www.fda.gov/drugs/drug-safety-and-availability/lecanemab-2026-update) |
| **Suggested `factor.slug`** | `lecanemab` |
| **Suggested `outcome.slug`** | `alzheimers` |

**Summary.** Post-marketing surveillance shows ARIA-E in 32.6% of APOE-ε4/ε4 carriers (vs 5.4% non-carriers). FDA mandates expanded MRI schedule and genotype-aware consent.

**Why it matters.** Effectively a soft contraindication for APOE-ε4/ε4 unless monitoring infrastructure is in place. Pre-treatment APOE testing becomes practical standard.

**Seed direction.** Search PubMed for `lecanemab alzheimers` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_lecanemab_apoe4_safety"`

---

### 7. Psilocybin 25 mg shows durable response in treatment-resistant depression

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_psilocybin_trd_phase3` |
| **Stage** | Phase 3 |
| **Published** | 2026-05-02 (16d ago) |
| **Strength** | 83% |
| **Source** | [NEJM](https://www.nejm.org/doi/10.1056/NEJMoa2026comp005) |
| **Suggested `factor.slug`** | `psilocybin` |
| **Suggested `outcome.slug`** | `treatment_resistant_depression` |

**Summary.** COMP005 Phase 3 — single dose + psychological support. MADRS reduction -12.5 vs -5.4 placebo at week 6; 31% remission vs 14%. Effect persisted to week 12 with no maintenance dose.

**Why it matters.** First Phase 3 win for a classic psychedelic in TRD. Path to FDA decision in 2027. Regulatory model — therapy-bundled REMS — sets precedent.

**Seed direction.** Search PubMed for `psilocybin treatment_resistant_depression` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_psilocybin_trd_phase3"`

---


## Longevity  ·  1 candidate
### 8. Intermittent low-dose rapamycin improves immune function in healthy older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_rapamycin_aging_phase2` |
| **Stage** | Phase 2 |
| **Published** | 2026-05-06 (12d ago) |
| **Strength** | 62% |
| **Source** | [Aging Cell](https://onlinelibrary.wiley.com/doi/10.1111/acel.2026.pearl) |
| **Suggested `factor.slug`** | `rapamycin` |
| **Suggested `outcome.slug`** | `immunosenescence` |

**Summary.** PEARL Phase 2 — 5 mg weekly × 48 weeks in adults 50-85. Improved influenza vaccine response (+22% AB titer), reduced senescent T-cell fraction, no grade ≥3 AEs.

**Why it matters.** First adequately-powered RCT in healthy aging showing both immune and biomarker benefit. Still preliminary — n=120 — but the safety/efficacy signal is real.

**Seed direction.** Search PubMed for `rapamycin immunosenescence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_rapamycin_aging_phase2"`

---

