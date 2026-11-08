# Codex / Claude — Breakthroughs → Corpus seeding brief

**Generated:** 2026-11-08
**Source:** `data/breakthroughs.json` orphan queue (post-live-rematch)
**Total candidates:** 163 across 5 categories
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


## Oncology  ·  57 candidates
### 1. Combination therapy extends survival in EGFR lung cancer by over 10 months

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_036069b76d4e1788` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-08 (61d ago) |
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
| **Published** | 2026-10-08 (31d ago) |
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
| **Published** | 2026-10-09 (30d ago) |
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
| **Published** | 2026-10-09 (30d ago) |
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
| **Published** | 2026-10-09 (30d ago) |
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

### 6. New drug approved for advanced pancreatic cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_197794650cda0485` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854429) |
| **Suggested `factor.slug`** | `new_pancreatic_cancer_drug` |
| **Suggested `outcome.slug`** | `metastatic_pancreatic_cancer` |

**Summary.** The FDA has approved a first-in-class therapy for metastatic pancreatic cancer. This marks the first new treatment option in years for this aggressive disease.

**Why it matters.** Patients with advanced pancreatic cancer now have a new treatment option approved by the FDA.

**Seed direction.** Search PubMed for `new_pancreatic_cancer_drug metastatic_pancreatic_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_197794650cda0485"`

---

### 7. FDA Approves First Treatment for Advanced Bladder Cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5b1c7b88ed5b24a9` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-15 (24d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-treatment-certain-people-bcg-unresponsive-bladder-cancer) |
| **Suggested `factor.slug`** | `bcg_unresponsive_bladder_cancer_treatment` |
| **Suggested `outcome.slug`** | `bladder_cancer_response` |

**Summary.** The FDA has approved a new treatment for adults with certain types of bladder cancer that no longer respond to BCG therapy. This approval marks the first option for this specific group of patients.

**Why it matters.** People with advanced bladder cancer that doesn’t respond to standard therapy now have a new treatment option.

**Seed direction.** Search PubMed for `bcg_unresponsive_bladder_cancer_treatment bladder_cancer_response` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_5b1c7b88ed5b24a9"`

---

### 8. New treatment approved for aggressive bladder cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b8a7c0e2049d627e` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-15 (24d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-expanded-indication-nogapendekin-alfa-inbakicept-pmln-bcg-unresponsive-non-muscle) |
| **Suggested `factor.slug`** | `nogapendekin_alfa_inbakicept` |
| **Suggested `outcome.slug`** | `bladder_cancer_progression` |

**Summary.** The FDA has approved a new treatment for adults with BCG-unresponsive non-muscle invasive bladder cancer. It is used in combination with BCG to help prevent cancer progression.

**Why it matters.** If you or a loved one has this type of bladder cancer, this approval offers a new treatment option after BCG failure.

**Seed direction.** Search PubMed for `nogapendekin_alfa_inbakicept bladder_cancer_progression` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_b8a7c0e2049d627e"`

---

### 9. New drug recommended for approval in Europe for pancreatic cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_adc710a9c539df29` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-16 (23d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/16/biotech-news-revmed-pancreatic-cancer-drug-nears-european-approval/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `pancreatic_cancer_drug` |
| **Suggested `outcome.slug`** | `pancreatic_cancer` |

**Summary.** European regulators have recommended approval for a new pancreatic cancer drug following FDA approval. The recommendation marks a key step toward wider availability in Europe.

**Why it matters.** This could mean faster access to a new treatment option for patients with advanced pancreatic cancer in Europe.

**Seed direction.** Search PubMed for `pancreatic_cancer_drug pancreatic_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_adc710a9c539df29"`

---

### 10. New cancer drug gets full FDA approval after proven benefit

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cc3ab2f08f1d152f` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-18 (21d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/verified-clinical-benefit-cancer-accelerated-approvals) |
| **Suggested `factor.slug`** | `cancer_drug` |
| **Suggested `outcome.slug`** | `cancer_outcome` |

**Summary.** Several cancer drugs previously granted accelerated approval have now received full FDA approval after postmarketing trials confirmed their clinical benefit. These approvals apply to specific blood and solid tumor cancers.

**Why it matters.** Patients and doctors can now rely on these treatments as proven options for certain cancers.

**Seed direction.** Search PubMed for `cancer_drug cancer_outcome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_cc3ab2f08f1d152f"`

---

### 11. New immunotherapy may let some rectal cancer patients skip chemo, radiation, and surgery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_154f8e2b8fa04d0d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-immunotherapy-may-allow-certain-patients-rectal-cancer-avoid-chemotherapy-radiation-and) |
| **Suggested `factor.slug`** | `dostarlimab` |
| **Suggested `outcome.slug`** | `rectal_cancer` |

**Summary.** The FDA approved a new use of immunotherapy for certain patients with locally advanced rectal cancer. This treatment may allow some to avoid chemotherapy, radiation, and surgery.

**Why it matters.** If you or a loved one has rectal cancer, ask your doctor if you might be eligible for this treatment option.

**Seed direction.** Search PubMed for `dostarlimab rectal_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_154f8e2b8fa04d0d"`

---

### 12. New drug gets FDA approval for advanced rectal cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2ae03698430d7f2f` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-dostarlimab-locally-advanced-rectal-cancer) |
| **Suggested `factor.slug`** | `dostarlimab` |
| **Suggested `outcome.slug`** | `rectal_cancer` |

**Summary.** The FDA has granted accelerated approval to a new drug for locally advanced rectal cancer. This approval is based on tumor response rates observed in clinical trials.

**Why it matters.** People with this type of rectal cancer now have a new treatment option approved by the FDA.

**Seed direction.** Search PubMed for `dostarlimab rectal_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_2ae03698430d7f2f"`

---

### 13. FDA approves new drug for lung cancer with RET gene change

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f980e8e8bd67b97b` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-21 (18d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/drug-approvals-and-databases/fda-approves-pralsetinib-non-small-cell-lung-cancer-ret-gene-fusions) |
| **Suggested `factor.slug`** | `pralsetinib` |
| **Suggested `outcome.slug`** | `non_small_cell_lung_cancer_ret_fusion` |

**Summary.** The FDA has approved pralsetinib for non-small cell lung cancer patients with RET gene fusions. This approval is based on clinical trial results showing significant tumor response in this specific genetic subgroup.

**Why it matters.** If you or a loved one has lung cancer with a RET gene fusion, this drug may be a treatment option worth discussing with your doctor.

**Seed direction.** Search PubMed for `pralsetinib non_small_cell_lung_cancer_ret_fusion` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_f980e8e8bd67b97b"`

---

### 14. New melanoma vaccine cuts recurrence risk by 42%

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a97e596b2014a1c8` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-22 (17d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/22/esmo-moderna-merck-cancer-vaccine-intismeran-data-released/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `mRNA_cancer_vaccine` |
| **Suggested `outcome.slug`** | `melanoma_recurrence` |

**Summary.** A personalized mRNA cancer vaccine reduced the risk of melanoma returning by 42% compared to standard treatment. The results came from a large clinical trial in patients with high-risk melanoma.

**Why it matters.** This vaccine may help prevent melanoma from coming back after surgery—talk to your doctor about new treatment options.

**Seed direction.** Search PubMed for `mRNA_cancer_vaccine melanoma_recurrence` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_a97e596b2014a1c8"`

---

### 15. New approval for cancer treatment in high-TMB tumors

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6bcb430c57ae9162` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-23 (16d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-traditional-approval-pembrolizumab-or-pembrolizumab-and-berahyaluronidase-alfa-pmph) |
| **Suggested `factor.slug`** | `pembrolizumab` |
| **Suggested `outcome.slug`** | `tmb_h_cancer` |

**Summary.** The FDA has granted traditional approval for a treatment in patients with unresectable or metastatic solid tumors that have high tumor mutational burden. The approval includes a new indication based on updated clinical data.

**Why it matters.** Patients with certain advanced cancers may now have access to a new treatment option backed by FDA approval.

**Seed direction.** Search PubMed for `pembrolizumab tmb_h_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6bcb430c57ae9162"`

---

### 16. New lung cancer treatment cuts death risk by more than half

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b6b219dca86cf5bb` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-24 (15d ago) |
| **Strength** | 95% |
| **Source** | [Endpoints News](https://endpoints.news/esmo26-amgens-imdelltra-regimen-more-than-halves-risk-of-death-in-phase-3-lung-cancer-trial/) |
| **Suggested `factor.slug`** | `imdeltra_plus_imfinzi` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** In a phase 3 trial, adding a new drug to standard treatment reduced the risk of death by 58% in certain small cell lung cancer patients. The results were compared to standard treatment alone.

**Why it matters.** People with certain lung cancers may now have a significantly better chance of survival with this new combination therapy.

**Seed direction.** Search PubMed for `imdeltra_plus_imfinzi overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_b6b219dca86cf5bb"`

---

### 17. New drug added to prostate cancer treatment reduces spread risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_34487fe908d304a2` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-24 (15d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42921729/) |
| **Suggested `factor.slug`** | `enzalutamide` |
| **Suggested `outcome.slug`** | `metastasis_free_survival` |

**Summary.** Adding a daily oral drug to standard therapy reduced the risk of cancer spreading in men with high-risk prostate cancer. The study found a significant improvement in metastasis-free survival over 24 months.

**Why it matters.** Men with high-risk prostate cancer may benefit from this treatment combination to lower the chance of cancer spreading.

**Seed direction.** Search PubMed for `enzalutamide metastasis_free_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_34487fe908d304a2"`

---

### 18. First effective cancer vaccine shows promise in multiple tumors

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e3c1c7d3ee4af58d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-25 (14d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/25/mrna-cancer-vaccine-merck-moderna-esmo-intismeran-next-applications/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `mrna_cancer_vaccine` |
| **Suggested `outcome.slug`** | `cancer_survival` |

**Summary.** A new mRNA-based cancer vaccine has shown success in treating certain cancers. Researchers are now testing it in additional tumor types.

**Why it matters.** This marks the first time a cancer vaccine has proven effective, offering hope for broader treatments in the future.

**Seed direction.** Search PubMed for `mrna_cancer_vaccine cancer_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_e3c1c7d3ee4af58d"`

---

### 19. New lung cancer drug cuts death risk by 44% in trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_45bbae2461fe2a6f` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-25 (14d ago) |
| **Strength** | 95% |
| **Source** | [Endpoints News](https://endpoints.news/esmo26-roche-details-magnitude-of-its-kras-g12c-inhibitors-win-over-rivals-in-lung-cancer-trial/) |
| **Suggested `factor.slug`** | `kras_g12c_inhibitor` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** In a head-to-head trial, a new drug for non-small cell lung cancer reduced the risk of death by 44% compared to older treatments. The trial included patients previously treated with other therapies.

**Why it matters.** If you or a loved one has this type of lung cancer, this treatment may offer a significant survival advantage.

**Seed direction.** Search PubMed for `kras_g12c_inhibitor overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_45bbae2461fe2a6f"`

---

### 20. New drug shows promise for lung cancer with KRAS mutation

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8ec1e58823b7e321` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/26/roche-kras-drug-divarasib-lung-cancer-treatment-win/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `divarasib` |
| **Suggested `outcome.slug`** | `lung_cancer_kras` |

**Summary.** A Roche drug improved outcomes in patients with a specific type of lung cancer. Results from a major study showed meaningful benefits in survival and disease control.

**Why it matters.** People with this common lung cancer subtype now have a new treatment option that may extend life and improve outcomes.

**Seed direction.** Search PubMed for `divarasib lung_cancer_kras` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_8ec1e58823b7e321"`

---

### 21. New drug cuts death risk by one-third in advanced endometrial cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_22fa798280f1e32d` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/26/merck-kelun-sac-tmt-endometrial-cancer-study-esmo-2026/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `targeted_drug` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** A Phase 3 trial showed a targeted drug reduced the risk of death by one-third in patients with advanced endometrial cancer. The results were based on overall survival data from the study.

**Why it matters.** This treatment offers new hope for patients with advanced endometrial cancer, potentially improving survival rates.

**Seed direction.** Search PubMed for `targeted_drug overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_22fa798280f1e32d"`

---

### 22. New drug combo extends survival in lung cancer with resistance

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ba74938210ba94fa` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42928710/) |
| **Suggested `factor.slug`** | `egfr_met_combination` |
| **Suggested `outcome.slug`** | `progression_free_survival` |

**Summary.** In patients with advanced lung cancer resistant to EGFR therapy and with MET amplification, a combination of two targeted drugs improved outcomes compared to chemotherapy. The trial showed a significant benefit in progression-free survival.

**Why it matters.** If you or a loved one has EGFR-mutated lung cancer that stopped responding to treatment, this combo may offer a better option than chemotherapy.

**Seed direction.** Search PubMed for `egfr_met_combination progression_free_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_ba74938210ba94fa"`

---

### 23. New drug combo approved for advanced prostate cancer with specific gene mutations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3f13862c1b79578e` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-talazoparib-enzalutamide-metastatic-androgen-pathway-modulation-naive-or-sensitive) |
| **Suggested `factor.slug`** | `talazoparib_enzalutamide_combo` |
| **Suggested `outcome.slug`** | `metastatic_prostate_cancer` |

**Summary.** The FDA has approved a combination of talazoparib and enzalutamide for adults with metastatic prostate cancer linked to HRR gene mutations. This treatment is for patients who haven't received prior androgen pathway modulation therapy.

**Why it matters.** Men with certain advanced prostate cancers may now have a new treatment option approved by the FDA.

**Seed direction.** Search PubMed for `talazoparib_enzalutamide_combo metastatic_prostate_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_3f13862c1b79578e"`

---

### 24. New guidance on PARP inhibitors for ovarian cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_236cb9e7c93a47b7` |
| **Stage** | Guideline |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42945508/) |
| **Suggested `factor.slug`** | `parp_inhibitors` |
| **Suggested `outcome.slug`** | `ovarian_cancer_outcomes` |

**Summary.** This updated guideline reviews 79 studies on PARP inhibitors for epithelial ovarian cancer. It provides evidence-based recommendations on testing for DNA repair defects and using these drugs to improve outcomes.

**Why it matters.** Women with ovarian cancer should discuss PARP inhibitor therapy and genetic testing with their doctor to guide treatment decisions.

**Seed direction.** Search PubMed for `parp_inhibitors ovarian_cancer_outcomes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_236cb9e7c93a47b7"`

---

### 25. New treatment combo improves survival for early lung cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e09440eed3ac5880` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-28 (11d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42950173/) |
| **Suggested `factor.slug`** | `pembrolizumab` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** Adding a key immune therapy to radiation improved outcomes in people with early-stage lung cancer who couldn’t have surgery. The study showed a significant reduction in cancer progression or death.

**Why it matters.** If you or a loved one has early-stage lung cancer and can’t have surgery, this treatment may offer better outcomes.

**Seed direction.** Search PubMed for `pembrolizumab overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_e09440eed3ac5880"`

---

### 26. New guidance for advanced lung cancer with specific genetic changes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4fbb3cc990301303` |
| **Stage** | Guideline |
| **Published** | 2026-10-29 (10d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42956324/) |
| **Suggested `factor.slug`** | `targeted_therapy` |
| **Suggested `outcome.slug`** | `non_small_cell_lung_cancer` |

**Summary.** The latest ASCO living guideline updates treatment recommendations for stage IV non-small cell lung cancer patients with driver alterations. It provides evidence-based guidance on targeted therapies based on continuous review of emerging data.

**Why it matters.** Patients with certain lung cancer gene changes should discuss updated treatment options with their doctor.

**Seed direction.** Search PubMed for `targeted_therapy non_small_cell_lung_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_4fbb3cc990301303"`

---

### 27. Genomic testing helps decide chemotherapy for early breast cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb2ac79f30eef936` |
| **Stage** | Guideline |
| **Published** | 2026-10-30 (9d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42962160/) |
| **Suggested `factor.slug`** | `genomic_testing` |
| **Suggested `outcome.slug`** | `chemotherapy_avoidance` |

**Summary.** A new analysis shows that genomic testing can accurately identify which women with early-stage breast cancer can safely avoid chemotherapy. The results support updated guidelines recommending personalized treatment based on genetic risk scores.

**Why it matters.** Women with early breast cancer can now avoid unnecessary chemo if their tumor has a low genetic risk score.

**Seed direction.** Search PubMed for `genomic_testing chemotherapy_avoidance` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_cb2ac79f30eef936"`

---

### 28. FDA approves first DNA-based therapy for recurring throat tumors

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a6b5fd2dc7f769c6` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-31 (8d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-plasmid-dna-based-immunotherapy-adults-recurrent-respiratory-papillomatosis) |
| **Suggested `factor.slug`** | `plasmid_dna_therapy` |
| **Suggested `outcome.slug`** | `recurrent_respiratory_papillomatosis` |

**Summary.** The FDA has approved a new plasmid DNA therapy for adults with recurrent respiratory papillomatosis. It is the first such treatment approved for this rare condition.

**Why it matters.** This approval offers a new treatment option for adults with recurring throat tumors caused by HPV.

**Seed direction.** Search PubMed for `plasmid_dna_therapy recurrent_respiratory_papillomatosis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_a6b5fd2dc7f769c6"`

---

### 29. New staging system improves survival prediction for medullary thyroid cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_69be8d38f2ce8c7d` |
| **Stage** | Guideline |
| **Published** | 2026-11-04 (4d ago) |
| **Strength** | 95% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42981561/) |
| **Suggested `factor.slug`** | `refined_staging_system` |
| **Suggested `outcome.slug`** | `disease_specific_survival` |

**Summary.** A multinational study of 43 centers refined the staging system for medullary thyroid cancer. The updated system better predicts disease-specific survival compared to the previous version.

**Why it matters.** This new staging system helps doctors more accurately assess patient prognosis and guide treatment decisions.

**Seed direction.** Search PubMed for `refined_staging_system disease_specific_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_69be8d38f2ce8c7d"`

---

### 30. New drug approved for advanced head and neck cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_867051790657271d` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-grants-accelerated-approval-new-treatment-head-and-neck-squamous-cell-carcinoma) |
| **Suggested `factor.slug`** | `amivantamab_hyaluronidase` |
| **Suggested `outcome.slug`** | `head_and_neck_squamous_cell_carcinoma` |

**Summary.** The FDA has approved a new treatment for adults with recurrent or metastatic head and neck squamous cell carcinoma that has worsened after platinum-based chemotherapy.

**Why it matters.** This approval offers a new option for patients with advanced head and neck cancer who have limited treatment choices.

**Seed direction.** Search PubMed for `amivantamab_hyaluronidase head_and_neck_squamous_cell_carcinoma` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_867051790657271d"`

---

### 31. New drug approved for advanced head and neck cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_399c9466a3cdf069` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-amivantamab-and-hyaluronidase-lpuj-recurrent-or-metastatic-head-and) |
| **Suggested `factor.slug`** | `amivantamab_hyaluronidase` |
| **Suggested `outcome.slug`** | `head_and_neck_squamous_cell_carcinoma` |

**Summary.** The FDA has approved a new drug combination for adults with recurrent or metastatic head and neck squamous cell carcinoma. It is for patients whose cancer has progressed after platinum-based chemotherapy and anti-PD-(L)1 therapy.

**Why it matters.** This approval offers a new treatment option for patients with advanced head and neck cancer who have limited choices.

**Seed direction.** Search PubMed for `amivantamab_hyaluronidase head_and_neck_squamous_cell_carcinoma` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_399c9466a3cdf069"`

---

### 32. New drug approved for recurrent head and neck cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6a213b70881e7391` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 95% |
| **Source** | [Endpoints News](https://endpoints.news/jjs-rybrevant-nets-fda-approval-in-head-and-neck-cancer/) |
| **Suggested `factor.slug`** | `rybrevant` |
| **Suggested `outcome.slug`** | `head_and_neck_cancer` |

**Summary.** The FDA has approved a new treatment for head and neck cancer that has returned after chemotherapy and immunotherapy. This is the first approval in over a decade for this type of cancer.

**Why it matters.** Patients with recurrent head and neck cancer now have a new treatment option after failing prior therapies.

**Seed direction.** Search PubMed for `rybrevant head_and_neck_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6a213b70881e7391"`

---

### 33. New drug approved for advanced small cell lung cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_672dd645349c4065` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-07 (1d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-grants-traditional-approval-tarlatamab-dlle-extensive-stage-small-cell-lung-cancer) |
| **Suggested `factor.slug`** | `tarlatamab_dlle` |
| **Suggested `outcome.slug`** | `extensive_stage_small_cell_lung_cancer` |

**Summary.** Tarlatamab-dlle received full FDA approval for adults with extensive-stage small cell lung cancer that worsened after platinum chemotherapy. It is the first new treatment approved for this condition in over a decade.

**Why it matters.** Patients with advanced small cell lung cancer now have a new treatment option after chemotherapy failure.

**Seed direction.** Search PubMed for `tarlatamab_dlle extensive_stage_small_cell_lung_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_672dd645349c4065"`

---

### 34. New safety warnings for common chemotherapy drugs

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_1db7a8a8df93d256` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-07 (1d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/safety-labeling-update-capecitabine-and-fluorouracil-5-fu-risks-associated-dihydropyrimidine) |
| **Suggested `factor.slug`** | `capecitabine_fluorouracil` |
| **Suggested `outcome.slug`** | `dpd_deficiency_toxicity` |

**Summary.** The FDA updated labels for two common chemotherapy drugs to warn about severe side effects in people with a rare genetic deficiency. This deficiency affects how the body processes the drugs, increasing the risk of life-threatening reactions.

**Why it matters.** If you're on this chemotherapy, ask your doctor if you should be tested for a genetic condition that raises your risk of serious side effects.

**Seed direction.** Search PubMed for `capecitabine_fluorouracil dpd_deficiency_toxicity` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_1db7a8a8df93d256"`

---

### 35. FDA approves new treatment for aggressive bladder cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_973459ce20b1c7b9` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-08 (0d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-approves-gemcitabine-intravesical-system-non-muscle-invasive-bladder-cancer) |
| **Suggested `factor.slug`** | `gemcitabine_intravesical_system` |
| **Suggested `outcome.slug`** | `non_muscle_invasive_bladder_cancer` |

**Summary.** The FDA has approved gemcitabine delivered directly into the bladder for adults with high-risk non-muscle invasive bladder cancer that did not respond to BCG therapy. This treatment offers a new option for patients with limited alternatives.

**Why it matters.** If you or a loved one has BCG-unresponsive bladder cancer, this approval means a new treatment option is now available.

**Seed direction.** Search PubMed for `gemcitabine_intravesical_system non_muscle_invasive_bladder_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_973459ce20b1c7b9"`

---

### 36. New drug combo approved for BRCA2-mutated prostate cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_307f70fecf5e0204` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-08 (0d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-approves-niraparib-and-abiraterone-acetate-plus-prednisone-brca2-mutated-metastatic-castration) |
| **Suggested `factor.slug`** | `niraparib_abiraterone_prednisone` |
| **Suggested `outcome.slug`** | `brca2_mutation_prostate_cancer` |

**Summary.** The FDA has approved a combination of niraparib and abiraterone acetate with prednisone for adults with BRCA2-mutated metastatic castration-sensitive prostate cancer. This approval is based on clinical trial results showing improved outcomes in this specific subgroup.

**Why it matters.** Men with BRCA2-mutated prostate cancer now have a new FDA-approved treatment option that may improve survival.

**Seed direction.** Search PubMed for `niraparib_abiraterone_prednisone brca2_mutation_prostate_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_307f70fecf5e0204"`

---

### 37. Alectinib approved for early-stage lung cancer with ALK mutation

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_28df138a09674f07` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-08 (0d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-approves-alectinib-adjuvant-treatment-alk-positive-non-small-cell-lung-cancer) |
| **Suggested `factor.slug`** | `alectinib` |
| **Suggested `outcome.slug`** | `recurrence_of_alk_positive_nsclc` |

**Summary.** The FDA has approved alectinib as a follow-up treatment after surgery for people with ALK-positive non-small cell lung cancer. This approval is based on evidence showing it reduces the risk of cancer returning.

**Why it matters.** If you or a loved one has ALK-positive lung cancer, this treatment may help prevent the cancer from coming back after surgery.

**Seed direction.** Search PubMed for `alectinib recurrence_of_alk_positive_nsclc` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_28df138a09674f07"`

---

### 38. New drug combo approved for certain lung cancer patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_af5144f4e2eee96f` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-08 (0d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-approves-amivantamab-vmjw-carboplatin-and-pemetrexed-non-small-cell-lung-cancer-egfr-exon-19) |
| **Suggested `factor.slug`** | `amivantamab_carboplatin_pemetrexed` |
| **Suggested `outcome.slug`** | `non_small_cell_lung_cancer` |

**Summary.** The FDA has approved a combination of amivantamab, carboplatin, and pemetrexed for adults with advanced non-small cell lung cancer driven by specific EGFR mutations. This approval is based on clinical trial results showing improved outcomes in patients with EGFR exon 19 deletions or L858R mutations.

**Why it matters.** Patients with certain EGFR-mutated lung cancers now have a new FDA-approved treatment option that may improve survival.

**Seed direction.** Search PubMed for `amivantamab_carboplatin_pemetrexed non_small_cell_lung_cancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_af5144f4e2eee96f"`

---

### 39. New drug approved for rare lung cancer with EGFR exon 20 mutations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2beec4d9338a3291` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-08 (0d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/cancer-approvals/fda-approves-amivantamab-vmjw-egfr-exon-20-insertion-mutated-non-small-cell-lung-cancer-indications) |
| **Suggested `factor.slug`** | `amivantamab` |
| **Suggested `outcome.slug`** | `egfr_exon20_mutated_nsclc` |

**Summary.** The FDA has approved amivantamab-vmjw combined with chemotherapy for first-line treatment of advanced non-small cell lung cancer with EGFR exon 20 insertions. This approval is based on clinical trial results showing improved outcomes in this specific subtype.

**Why it matters.** Patients with this rare lung cancer type now have a new first-line treatment option approved by the FDA.

**Seed direction.** Search PubMed for `amivantamab egfr_exon20_mutated_nsclc` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_2beec4d9338a3291"`

---

### 40. Removing fallopian tubes during routine surgery may lower ovarian cancer risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_62e029ea6fac2440` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (117d ago) |
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

### 41. FDA approves first new sunscreen ingredient in 30 years

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0c157ee7cbf678cc` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (110d ago) |
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

### 42. New treatment approved for advanced breast cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_df5771162bf505a7` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (31d ago) |
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

### 43. GSK's new cancer drug gets potential approval

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4eacac3f70c777ec` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 90% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/26/gsk-cancer-esmo-adcs-jemperli/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `gsk_cancer_drug` |
| **Suggested `outcome.slug`** | `cancer_approval` |

**Summary.** GSK may soon receive approval for its sixth cancer drug. The company, once out of oncology, is now seeing its return pay off.

**Why it matters.** This could expand treatment options for cancer patients, especially those with hard-to-treat forms.

**Seed direction.** Search PubMed for `gsk_cancer_drug cancer_approval` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_4eacac3f70c777ec"`

---

### 44. New guidelines expand BRCA genetic testing to more families

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b332cc58f359e454` |
| **Stage** | Guideline |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 90% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42945506/) |
| **Suggested `factor.slug`** | `cascade_genetic_testing` |
| **Suggested `outcome.slug`** | `brca1_brca2_pathogenic_variants` |

**Summary.** A new guideline recommends cascade genetic testing for BRCA1/2 variants beyond academic settings. It aims to identify at-risk relatives in real-world clinical practice.

**Why it matters.** If you have a family history of breast or ovarian cancer, ask your doctor about genetic testing for you and your relatives.

**Seed direction.** Search PubMed for `cascade_genetic_testing brca1_brca2_pathogenic_variants` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_b332cc58f359e454"`

---

### 45. SABR radiotherapy works as well as surgery for early lung cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c2061ee3520c82b4` |
| **Stage** | Phase 3 |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 90% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42970669/) |
| **Suggested `factor.slug`** | `sabrtreatment` |
| **Suggested `outcome.slug`** | `lungcancer` |

**Summary.** This study found that stereotactic ablative radiotherapy (SABR) was as effective as surgery for early-stage lung cancer in patients eligible for either treatment. The results were based on an emulated target trial comparing real-world outcomes.

**Why it matters.** If you or a loved one has early-stage lung cancer, SABR may be a safe and effective alternative to surgery.

**Seed direction.** Search PubMed for `sabrtreatment lungcancer` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_c2061ee3520c82b4"`

---

### 46. New chemoimmunotherapy shows promise in high-risk childhood cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_25726cf89cd9b65a` |
| **Stage** | Phase 2 |
| **Published** | 2026-11-03 (5d ago) |
| **Strength** | 90% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42976306/) |
| **Suggested `factor.slug`** | `chemoimmunotherapy` |
| **Suggested `outcome.slug`** | `event_free_survival` |

**Summary.** A combination of chemotherapy and anti-GD2 antibody therapy was safely given during early treatment for high-risk neuroblastoma. It led to improved event-free survival in children with this aggressive cancer.

**Why it matters.** This treatment approach may offer better outcomes for children with high-risk neuroblastoma, a rare and serious childhood cancer.

**Seed direction.** Search PubMed for `chemoimmunotherapy event_free_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_25726cf89cd9b65a"`

---

### 47. Blood test identifies high-risk Ewing sarcoma patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_00910fa16c5ae75f` |
| **Stage** | Phase 2 |
| **Published** | 2026-11-04 (4d ago) |
| **Strength** | 90% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42981545/) |
| **Suggested `factor.slug`** | `ctdna_profiling` |
| **Suggested `outcome.slug`** | `ewing_sarcoma_outcome` |

**Summary.** Circulating tumor DNA profiling in Ewing sarcoma patients revealed that alterations in TP53, STAG2, and CDKN2A are linked to higher risk. These genetic changes were detectable in blood samples and associated with worse outcomes.

**Why it matters.** This blood test may help identify high-risk patients earlier, guiding more personalized treatment decisions.

**Seed direction.** Search PubMed for `ctdna_profiling ewing_sarcoma_outcome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_00910fa16c5ae75f"`

---

### 48. New blood test detects key melanoma mutation with high accuracy

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8b59994355c8587d` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-14 (25d ago) |
| **Strength** | 85% |
| **Source** | [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT07870265?aggFilters=studyType%3Aint) |
| **Suggested `factor.slug`** | `crispr_cas12a_blood_test` |
| **Suggested `outcome.slug`** | `braf_v600e_mutation` |

**Summary.** A new CRISPR-based blood test accurately detected the BRAF V600E mutation in patients with metastatic melanoma. The test was compared to standard genetic tests using blood samples collected over time.

**Why it matters.** This non-invasive test could help monitor melanoma treatment and detect resistance earlier, improving care for patients.

**Seed direction.** Search PubMed for `crispr_cas12a_blood_test braf_v600e_mutation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_8b59994355c8587d"`

---

### 49. New drug extends survival in bile duct cancer patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b785128912d46da3` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-25 (14d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/esmo26-akeso-details-ivonescimabs-biliary-cancer-success-drawing-keytruda-comparisons/) |
| **Suggested `factor.slug`** | `ivonescimab` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** In a late-stage Chinese study, the drug improved survival in patients with biliary tract cancer. Results showed a significant benefit compared to standard treatment.

**Why it matters.** This treatment offers new hope for patients with a hard-to-treat form of bile duct cancer.

**Seed direction.** Search PubMed for `ivonescimab overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_b785128912d46da3"`

---

### 50. New combo therapy delays resistance in lung cancer patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cf8ebbccfa0911b7` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-25 (14d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/esmo26-astrazenecas-tagrisso-orpathys-combo-may-extend-tagrissos-life-in-lung-cancer/) |
| **Suggested `factor.slug`** | `tagrisso_orpathys_combo` |
| **Suggested `outcome.slug`** | `treatment_resistance_delay` |

**Summary.** A combination of two drugs helped patients with mutant non-small cell lung cancer continue treatment longer after resistance developed. The results suggest a potential extension of effective treatment duration.

**Why it matters.** Patients with certain lung cancers may now have a longer window of effective treatment options.

**Seed direction.** Search PubMed for `tagrisso_orpathys_combo treatment_resistance_delay` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_cf8ebbccfa0911b7"`

---

### 51. New drug combo extends survival in advanced eye cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f04805981e1ea4ce` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-28 (11d ago) |
| **Strength** | 85% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42950186/) |
| **Suggested `factor.slug`** | `pkc_met_inhibitor_combo` |
| **Suggested `outcome.slug`** | `overall_survival_mum` |

**Summary.** In a phase 2 trial, a combination of two drugs improved survival in patients with metastatic uveal melanoma. The treatment showed promising results with a median overall survival not yet reached after follow-up.

**Why it matters.** People with advanced eye cancer now have a new treatment option that may extend life, offering hope where options were limited.

**Seed direction.** Search PubMed for `pkc_met_inhibitor_combo overall_survival_mum` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_f04805981e1ea4ce"`

---

### 52. Methylphenidate reduces fatigue in blood cancer patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e4c39e0370354466` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-30 (9d ago) |
| **Strength** | 85% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42962158/) |
| **Suggested `factor.slug`** | `methylphenidate` |
| **Suggested `outcome.slug`** | `cancer_related_fatigue` |

**Summary.** In a trial of 152 adults with blood cancer and severe fatigue, methylphenidate reduced fatigue symptoms compared to placebo over six weeks.

**Why it matters.** If you have blood cancer and feel constantly tired, this treatment may help improve your daily energy levels.

**Seed direction.** Search PubMed for `methylphenidate cancer_related_fatigue` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_e4c39e0370354466"`

---

### 53. New combo therapy improves survival in advanced pancreatic cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_80d45c5a1e8dcfb0` |
| **Stage** | Phase 2 |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 85% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42970668/) |
| **Suggested `factor.slug`** | `pd1_inhibitor_plus_chemotherapy` |
| **Suggested `outcome.slug`** | `progression_free_survival` |

**Summary.** In a phase II trial, adding a PD-1 inhibitor to modified FOLFIRINOX improved outcomes for patients with borderline resectable or locally advanced pancreatic cancer. Results showed a significant benefit in progression-free survival compared to chemotherapy alone.

**Why it matters.** People with advanced pancreatic cancer may now have a more effective treatment option to extend survival and delay disease progression.

**Seed direction.** Search PubMed for `pd1_inhibitor_plus_chemotherapy progression_free_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_80d45c5a1e8dcfb0"`

---

### 54. New imaging method improves colon cancer prognosis prediction

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3fc9cd1edeec971b` |
| **Stage** | Phase 3 |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 85% |
| **Source** | [JCO](https://pubmed.ncbi.nlm.nih.gov/42993920/) |
| **Suggested `factor.slug`** | `image_based_cms_subtyping` |
| **Suggested `outcome.slug`** | `overall_survival` |

**Summary.** A new image-based method using routine pathology scans accurately classified colon cancer subtypes. It predicted survival better than current methods in stage II/III patients.

**Why it matters.** This could help doctors better predict outcomes and tailor treatment for colon cancer patients.

**Seed direction.** Search PubMed for `image_based_cms_subtyping overall_survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_3fc9cd1edeec971b"`

---

### 55. New combination therapy shows promise in advanced eye cancer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_00cf5a85686d1275` |
| **Stage** | Phase 2 |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/sitc26-immunocore-reports-early-data-for-brenetafusp-plus-kimmtrak-in-uveal-melanoma/) |
| **Suggested `factor.slug`** | `t_cell_engager_combination` |
| **Suggested `outcome.slug`** | `overall_survival_in_uveal_melanoma` |

**Summary.** In early testing, about 70% of certain uveal melanoma patients were alive after two years. The treatment uses two T cell-engaging drugs combined for the first time in a solid tumor.

**Why it matters.** People with advanced eye cancer may now have a new treatment option showing longer survival in early trials.

**Seed direction.** Search PubMed for `t_cell_engager_combination overall_survival_in_uveal_melanoma` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_00cf5a85686d1275"`

---

### 56. New algorithm safely rules out blood clots in cancer patients, avoiding CT scans

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_39fdd03b34d86bf2` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-25 (75d ago) |
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

### 57. New guideline adds blood test option for colorectal cancer screening

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e5887844999f1e27` |
| **Stage** | Guideline |
| **Published** | 2026-09-08 (61d ago) |
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


## Cardiovascular  ·  28 candidates
### 58. First heart valve designed to grow with children gets FDA approval

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_e2b180179d60aa40` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-07 (32d ago) |
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

### 59. Faster heart attack testing in ER cuts wait time

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_d87a7da25b387c45` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-19 (20d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42895015/) |
| **Suggested `factor.slug`** | `point_of_care_hs_cTn` |
| **Suggested `outcome.slug`** | `ed_length_of_stay` |

**Summary.** Point-of-care high-sensitivity troponin testing reduced emergency department length of stay. Results were available faster without compromising safety.

**Why it matters.** If you have chest pain, faster testing could mean quicker diagnosis and treatment in the ER.

**Seed direction.** Search PubMed for `point_of_care_hs_cTn ed_length_of_stay` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_d87a7da25b387c45"`

---

### 60. New maps reveal how KCNQ1 gene changes affect heart rhythm

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8dd51b66db1f37ac` |
| **Stage** | Preclinical |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42899351/) |
| **Suggested `factor.slug`** | `kcnq1_variant` |
| **Suggested `outcome.slug`** | `long_qt_syndrome` |

**Summary.** Researchers created detailed maps of KCNQ1 gene variants linked to long QT syndrome. These maps help predict which variants cause dangerous heart rhythms.

**Why it matters.** This improves genetic testing accuracy and helps doctors assess heart risk in patients with unexplained arrhythmias.

**Seed direction.** Search PubMed for `kcnq1_variant long_qt_syndrome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_8dd51b66db1f37ac"`

---

### 61. Heart health starts in childhood for women

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f5e3c847c767b9e1` |
| **Stage** | Guideline |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42929150/) |
| **Suggested `factor.slug`** | `childhood_lifestyle` |
| **Suggested `outcome.slug`** | `cardiovascular_disease` |

**Summary.** A new guideline emphasizes that cardiovascular health in women begins in childhood. Early lifestyle habits significantly influence lifelong heart disease risk.

**Why it matters.** Girls should adopt heart-healthy habits early to reduce heart disease risk later in life.

**Seed direction.** Search PubMed for `childhood_lifestyle cardiovascular_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_f5e3c847c767b9e1"`

---

### 62. New guidelines address heart health in women across life stages

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_29df9fe3456cd421` |
| **Stage** | Guideline |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42929102/) |
| **Suggested `factor.slug`** | `sex_specific_prevention` |
| **Suggested `outcome.slug`** | `cardiovascular_disease` |

**Summary.** A major new guideline from leading medical groups outlines sex-specific strategies for preventing and managing heart disease in girls and women. It emphasizes integrating hormonal, psychosocial, and cardiovascular health across the lifespan.

**Why it matters.** Women should discuss their heart health with providers using these updated guidelines to reduce long-term risk.

**Seed direction.** Search PubMed for `sex_specific_prevention cardiovascular_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_29df9fe3456cd421"`

---

### 63. Heart defect subtype affects survival in newborns

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_191301b0cdd81fca` |
| **Stage** | research |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42934200/) |
| **Suggested `factor.slug`** | `hlhs_subtype` |
| **Suggested `outcome.slug`** | `mortality` |

**Summary.** Newborns with hypoplastic left heart syndrome and ventriculocoronary connections had higher mortality. The MS/AA subtype was linked to worse outcomes.

**Why it matters.** Parents of babies with this heart condition should know that subtype and connections affect survival chances.

**Seed direction.** Search PubMed for `hlhs_subtype mortality` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_191301b0cdd81fca"`

---

### 64. New blood thinner reduces bleeding after heart attack treatment

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ea304db15aca35a9` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-31 (8d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42965935/) |
| **Suggested `factor.slug`** | `bivalirudin_infusion` |
| **Suggested `outcome.slug`** | `bleeding_and_death_after_heart_attack` |

**Summary.** In patients with heart attacks treated with emergency stenting, a new blood thinner plus a high-dose infusion reduced serious bleeding and death at 30 days compared to standard heparin. The benefit was seen primarily in reducing severe bleeding events.

**Why it matters.** If you or a loved one has a heart attack, this treatment may lower the risk of dangerous bleeding during recovery.

**Seed direction.** Search PubMed for `bivalirudin_infusion bleeding_and_death_after_heart_attack` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_ea304db15aca35a9"`

---

### 65. TAVR reduces death and hospitalization in severe aortic regurgitation

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f02b91a996c8e6a2` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-31 (8d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42965504/) |
| **Suggested `factor.slug`** | `tavr` |
| **Suggested `outcome.slug`** | `aortic_regurgitation_outcomes` |

**Summary.** In high-risk patients with severe pure aortic regurgitation, TAVR reduced death and hospitalization compared to medical therapy alone. The SEASON-AR trial showed a significant improvement in outcomes with transfemoral TAVR.

**Why it matters.** If you have severe aortic regurgitation and are high-risk for surgery, TAVR may offer a life-saving option.

**Seed direction.** Search PubMed for `tavr aortic_regurgitation_outcomes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_f02b91a996c8e6a2"`

---

### 66. New treatment reduces death and heart events in rare heart disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_73cc2659a926e2d2` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-03 (5d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42974684/) |
| **Suggested `factor.slug`** | `vutrisiran` |
| **Suggested `outcome.slug`** | `all_cause_mortality_and_cardiovascular_events` |

**Summary.** After 33 to 36 months, the treatment reduced the risk of death and heart problems in people with a rare form of heart disease caused by abnormal protein buildup. It also slowed disease progression.

**Why it matters.** If you or a loved one has this rare heart condition, this treatment may help extend life and reduce serious heart events.

**Seed direction.** Search PubMed for `vutrisiran all_cause_mortality_and_cardiovascular_events` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_73cc2659a926e2d2"`

---

### 67. Heart failure linked to fluid buildup resolved by blood flow restoration

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a447c54f16fc8e4e` |
| **Stage** | case_report |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 95% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42990081/) |
| **Suggested `factor.slug`** | `revascularization` |
| **Suggested `outcome.slug`** | `chylothorax_chylous_ascites` |

**Summary.** A patient with heart failure and dangerous fluid accumulation in the chest and abdomen saw both conditions resolve after treatment to improve blood flow to the heart. This rare case suggests that poor heart circulation may cause these fluid issues.

**Why it matters.** If you have heart failure and unexplained fluid buildup, talk to your doctor about blood flow issues.

**Seed direction.** Search PubMed for `revascularization chylothorax_chylous_ascites` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_a447c54f16fc8e4e"`

---

### 68. Major heart groups agree on a single definition for heart failure

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb5e3b6d8c3e1b49` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (89d ago) |
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

### 69. Updated Heart Disease Guidelines for Older Adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_99b0c6b66be5ad72` |
| **Stage** | Guideline |
| **Published** | 2026-09-22 (47d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853628) |
| **Suggested `factor.slug`** | `age_inclusive_care` |
| **Suggested `outcome.slug`** | `cvd` |

**Summary.** The American College of Cardiology released new guidelines for heart disease care in older adults. These emphasize age-specific treatment adjustments for better outcomes.

**Why it matters.** Older adults with heart disease should ask their doctor about age-appropriate care plans, as new guidelines now standardize personalized treatment approaches.

**Seed direction.** Search PubMed for `age_inclusive_care cvd` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_99b0c6b66be5ad72"`

---

### 70. Microplastics Found in Blood of Heart Attack Patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8b0f91e34d087299` |
| **Stage** | Preclinical |
| **Published** | 2026-10-06 (33d ago) |
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

### 71. Cold-stored platelets work as well as room-temp ones in heart surgery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_503518f8e1f10207` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852951) |
| **Suggested `factor.slug`** | `cold_stored_platelets` |
| **Suggested `outcome.slug`** | `bleeding_during_cardiac_surgery` |

**Summary.** In patients bleeding during heart surgery, platelets stored cold for up to 21 days were as safe and effective as those stored at room temperature for 5 to 7 days.

**Why it matters.** This could extend platelet supply and reduce waste, improving availability for critical surgeries.

**Seed direction.** Search PubMed for `cold_stored_platelets bleeding_during_cardiac_surgery` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_503518f8e1f10207"`

---

### 72. AI-Enhanced CT Scans Predict Survival After Heart Valve Surgery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cef237f25f838825` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42899353/) |
| **Suggested `factor.slug`** | `ai_ct_body_composition` |
| **Suggested `outcome.slug`** | `mortality_after_tavr` |

**Summary.** Deep learning analysis of 3D CT scans showed that body composition is linked to survival after transcatheter aortic valve replacement. Patients with lower muscle mass had higher mortality rates.

**Why it matters.** This AI tool could help doctors identify high-risk patients before heart valve surgery.

**Seed direction.** Search PubMed for `ai_ct_body_composition mortality_after_tavr` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_cef237f25f838825"`

---

### 73. Genetic testing predicts survival in children with heart failure

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a008d7471196e03f` |
| **Stage** | research |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42935448/) |
| **Suggested `factor.slug`** | `genetic_variant` |
| **Suggested `outcome.slug`** | `survival` |

**Summary.** Children with dilated cardiomyopathy and pathogenic gene variants had worse survival. The study found a significant association between genetic causes and disease severity.

**Why it matters.** If your child has heart failure, genetic testing may help predict outcomes and guide care.

**Seed direction.** Search PubMed for `genetic_variant survival` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_a008d7471196e03f"`

---

### 74. New insight into heart failure in children with small left heart

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5d93b72ae78b66c1` |
| **Stage** | Preclinical |
| **Published** | 2026-10-28 (11d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42948889/) |
| **Suggested `factor.slug`** | `diastolic_dysfunction` |
| **Suggested `outcome.slug`** | `left_ventricular_dysfunction` |

**Summary.** Pressure-volume loop analysis in 13 children with borderline left heart showed diastolic dysfunction is due to impaired active relaxation, not stiffness. This clarifies the underlying mechanism in a high-risk group.

**Why it matters.** Understanding the cause helps guide future treatments for children with congenital heart defects affecting heart filling.

**Seed direction.** Search PubMed for `diastolic_dysfunction left_ventricular_dysfunction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_5d93b72ae78b66c1"`

---

### 75. New method reduces heart risks in dialysis patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_fe97cbfed6f1788a` |
| **Stage** | Phase 3 |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42971570/) |
| **Suggested `factor.slug`** | `orbital_atherectomy` |
| **Suggested `outcome.slug`** | `adverse_events_after_stent` |

**Summary.** In patients with severe artery calcification and kidney disease, orbital atherectomy led to better outcomes than balloon angioplasty before stent placement. The study included 2,001 patients and showed improved results with the newer technique.

**Why it matters.** If you have kidney disease and heart artery blockages, ask your doctor about this safer stent method.

**Seed direction.** Search PubMed for `orbital_atherectomy adverse_events_after_stent` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_fe97cbfed6f1788a"`

---

### 76. New tool predicts heart failure risk in veterans

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_1f2cdd36b6eba89b` |
| **Stage** | Guideline |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42969140/) |
| **Suggested `factor.slug`** | `prevent_hf_risk_equation` |
| **Suggested `outcome.slug`** | `heart_failure` |

**Summary.** The PREVENT-HF risk equation accurately predicted heart failure in U.S. veterans. It showed strong performance across diverse groups in the validation study.

**Why it matters.** Veterans and their doctors can use this tool to identify high-risk individuals early and take preventive steps.

**Seed direction.** Search PubMed for `prevent_hf_risk_equation heart_failure` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_1f2cdd36b6eba89b"`

---

### 77. Digital tool improves heart failure care after hospital discharge

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ee4683160cf6c01e` |
| **Stage** | Phase 3 |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 90% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42993694/) |
| **Suggested `factor.slug`** | `digital_health_intervention` |
| **Suggested `outcome.slug`** | `heart_failure_management` |

**Summary.** A digital health intervention helped patients in Brazil follow heart failure treatment guidelines more consistently after hospital discharge. It led to better medication use and improved outcomes compared to standard care.

**Why it matters.** If you or a loved one has heart failure, using a digital tool after hospitalization may help manage treatment more effectively.

**Seed direction.** Search PubMed for `digital_health_intervention heart_failure_management` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_ee4683160cf6c01e"`

---

### 78. IV iron before heart surgery reduces blood transfusions and improves 90-day recovery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b07cf4e81bd58d81` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-26 (74d ago) |
| **Strength** | 85% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100407) |
| **Suggested `factor.slug`** | `intravenous_iron` |
| **Suggested `outcome.slug`** | `recovery_90d` |

**Summary.** A trial of 955 heart surgery patients found IV iron reduced blood transfusions. It also improved 90-day recovery rates, meaning more time alive and out of hospital.

**Why it matters.** Ask your cardiac surgeon if IV iron before surgery could reduce your blood transfusion needs and speed up recovery.

**Seed direction.** Search PubMed for `intravenous_iron recovery_90d` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_b07cf4e81bd58d81"`

---

### 79. Nearly 80% of young adults with metabolic syndrome show early artery damage

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_98d9e89377de3985` |
| **Stage** | research |
| **Published** | 2026-10-06 (33d ago) |
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

### 80. Both high and low testosterone linked to higher AF risk in men

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5e13d4948f96bd0c` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854681) |
| **Suggested `factor.slug`** | `testosterone_level` |
| **Suggested `outcome.slug`** | `atrial_fibrillation` |

**Summary.** Men with either high or low testosterone levels had a higher risk of developing atrial fibrillation. The study found a U-shaped association between testosterone levels and AF risk.

**Why it matters.** Men with extreme testosterone levels should talk to their doctor about heart health risks.

**Seed direction.** Search PubMed for `testosterone_level atrial_fibrillation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_5e13d4948f96bd0c"`

---

### 81. AI tool improves risk prediction in TAVR patients using CT scans

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_1809b0a003003d3b` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-23 (16d ago) |
| **Strength** | 85% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42910413/) |
| **Suggested `factor.slug`** | `ct_ai_body_composition` |
| **Suggested `outcome.slug`** | `tavr_complications` |

**Summary.** A new AI-based method analyzes CT scans to assess body composition and predict risks in patients undergoing transcatheter aortic valve replacement (TAVR). The tool identified patients at higher risk for complications with greater accuracy than traditional methods.

**Why it matters.** Doctors may use this AI tool to better assess patient risk before TAVR, leading to more personalized care.

**Seed direction.** Search PubMed for `ct_ai_body_composition tavr_complications` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_1809b0a003003d3b"`

---

### 82. New study finds one blood thinner better than another for heart patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a91e655b58b42fca` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-29 (10d ago) |
| **Strength** | 85% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42953942/) |
| **Suggested `factor.slug`** | `clopidogrel` |
| **Suggested `outcome.slug`** | `major_adverse_cardiac_events` |

**Summary.** After stopping dual therapy following heart stent placement, patients with higher atherothrombotic risk had better outcomes with clopidogrel alone than with aspirin alone. The benefit was more pronounced in those with greater overall risk.

**Why it matters.** If you've had a stent, ask your doctor if switching to clopidogrel may be better based on your risk level.

**Seed direction.** Search PubMed for `clopidogrel major_adverse_cardiac_events` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_a91e655b58b42fca"`

---

### 83. New pump method improves heart function during ECMO

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_88d14f7cd2aacbb1` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-31 (8d ago) |
| **Strength** | 85% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42966011/) |
| **Suggested `factor.slug`** | `micro_axial_flow_pump` |
| **Suggested `outcome.slug`** | `cardiac_recovery` |

**Summary.** In patients on ECMO for heart failure, a micro-pump reduced heart strain better than a balloon pump. This may improve recovery chances.

**Why it matters.** For patients on ECMO for heart failure, better heart unloading may lead to improved recovery and outcomes.

**Seed direction.** Search PubMed for `micro_axial_flow_pump cardiac_recovery` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_88d14f7cd2aacbb1"`

---

### 84. Polygenic score for HCM works across diverse populations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c51cc9de764aaafc` |
| **Stage** | Phase 3 |
| **Published** | 2026-11-03 (5d ago) |
| **Strength** | 85% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42974673/) |
| **Suggested `factor.slug`** | `polygenic_score` |
| **Suggested `outcome.slug`** | `hypertrophic_cardiomyopathy` |

**Summary.** A polygenic score for hypertrophic cardiomyopathy showed consistent accuracy across diverse US populations. The score maintained predictive power in individuals of African, Hispanic, and Asian ancestry.

**Why it matters.** This means genetic risk scores can be used more broadly in clinical care, improving early detection across racial groups.

**Seed direction.** Search PubMed for `polygenic_score hypertrophic_cardiomyopathy` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_c51cc9de764aaafc"`

---

### 85. New blood test may detect early heart disease in low-risk people

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_28d2c930133806e3` |
| **Stage** | Phase 2 |
| **Published** | 2026-11-05 (3d ago) |
| **Strength** | 85% |
| **Source** | [Circulation](https://pubmed.ncbi.nlm.nih.gov/42985773/) |
| **Suggested `factor.slug`** | `metabolomic_signature` |
| **Suggested `outcome.slug`** | `subclinical_atherosclerosis` |

**Summary.** A new metabolomic test identified 54 metabolites linked to early atherosclerosis in adults without traditional risk factors. The study included 1,212 adults undergoing screening.

**Why it matters.** People without known heart risks may still have early disease—this test could help catch it earlier.

**Seed direction.** Search PubMed for `metabolomic_signature subclinical_atherosclerosis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_28d2c930133806e3"`

---


## Metabolic  ·  14 candidates
### 86. FDA approves first oral drug to lower LDL cholesterol

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a3bf5bc02049572f` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (75d ago) |
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

### 87. First gene therapy approved for children with Sanfilippo syndrome

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f1c1f2dc90e24b4d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (31d ago) |
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

### 88. New once-weekly insulin approved for kids with type 2 diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_1c2a4463c14f3bb3` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-24 (15d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/news-events-human-drugs/fda-approves-first-once-weekly-insulin-type-2-diabetes-mellitus-pediatric-patients) |
| **Suggested `factor.slug`** | `once_weekly_insulin` |
| **Suggested `outcome.slug`** | `type_2_diabetes` |

**Summary.** The FDA has approved the first once-weekly insulin for children and teens with type 2 diabetes. This is the first such treatment specifically approved for this age group.

**Why it matters.** Kids with type 2 diabetes now have a less frequent insulin option that may improve treatment adherence.

**Seed direction.** Search PubMed for `once_weekly_insulin type_2_diabetes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_1c2a4463c14f3bb3"`

---

### 89. First wearable device to continuously track ketones in diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cb73288d61fec98a` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-03 (5d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2855345) |
| **Suggested `factor.slug`** | `continuous_ketone_monitor` |
| **Suggested `outcome.slug`** | `diabetic_ketoacidosis` |

**Summary.** The FDA has approved the first wearable device that continuously monitors ketone levels in people with type 1 diabetes. This allows real-time tracking to help prevent diabetic ketoacidosis.

**Why it matters.** People with type 1 diabetes can now monitor ketones continuously to reduce the risk of dangerous ketoacidosis.

**Seed direction.** Search PubMed for `continuous_ketone_monitor diabetic_ketoacidosis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_cb73288d61fec98a"`

---

### 90. First OTC glucose monitor approved for children with diabetes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3a1173badb98dc91` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-21 (110d ago) |
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

### 91. AI-Powered Eye Scan Improves Diabetes Vision Screening Accuracy

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0a2c6d6f6e7a8c8b` |
| **Stage** | Phase 3 |
| **Published** | 2026-07-21 (110d ago) |
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

### 92. First Drug Approved to Lower Pancreatitis Risk in Severe High Triglycerides

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_66ec86d216139ace` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-11 (89d ago) |
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

### 93. FDA approves gene therapy for children 2+ with sickle cell disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_ab673401325c68f1` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-18 (82d ago) |
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

### 94. New treatment reduces severe itching in rare liver disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a7242dab7528178a` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-12 (27d ago) |
| **Strength** | 90% |
| **Source** | [Endpoints News](https://endpoints.news/mirum-succeeds-in-rare-liver-disease-trial-first-tracks-delivers-in-celiac/) |
| **Suggested `factor.slug`** | `ileal_bile_acid_transporter_inhibitor` |
| **Suggested `outcome.slug`** | `cholestatic_pruritus` |

**Summary.** A new drug significantly reduced cholestatic pruritus in patients with rare liver diseases, including biliary atresia. The results were compared to placebo in a late-stage trial.

**Why it matters.** People with rare liver diseases may find relief from debilitating itching, improving their quality of life.

**Seed direction.** Search PubMed for `ileal_bile_acid_transporter_inhibitor cholestatic_pruritus` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_a7242dab7528178a"`

---

### 95. New gene editing therapy shows early promise for rare liver disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_de670b9a6d2b380d` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/beam-proves-it-can-correct-mutation-pfizer-to-collaborate-with-enodia/) |
| **Suggested `factor.slug`** | `base_editing_therapy` |
| **Suggested `outcome.slug`** | `glycogen_storage_disease_type_ia` |

**Summary.** Beam Therapeutics shared initial data from a Phase 1/2 trial of a base editing therapy for glycogen storage disease type Ia. The therapy successfully corrected the underlying genetic mutation in patients.

**Why it matters.** This approach could offer a long-term treatment for a rare, severe liver condition caused by a single gene defect.

**Seed direction.** Search PubMed for `base_editing_therapy glycogen_storage_disease_type_ia` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_de670b9a6d2b380d"`

---

### 96. New study confirms drug works safely for all frailty levels

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6b90467f56625e64` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854954) |
| **Suggested `factor.slug`** | `semaglutide` |
| **Suggested `outcome.slug`** | `frailty` |

**Summary.** A study in JAMA Cardiology found the drug worked safely and effectively in people with varying levels of frailty. Benefits were seen regardless of frailty status.

**Why it matters.** People of all fitness levels may benefit from this treatment, so discuss options with your doctor.

**Seed direction.** Search PubMed for `semaglutide frailty` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_6b90467f56625e64"`

---

### 97. Ketogenic diet may improve liver health in people with fatty liver

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_fa664b59238a5501` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854949) |
| **Suggested `factor.slug`** | `ketogenic_diet` |
| **Suggested `outcome.slug`** | `liver_health` |

**Summary.** A clinical trial found that a very low-carbohydrate ketogenic diet improved liver health more than a Mediterranean or plant-forward diet. After 10% weight loss, liver fat decreased significantly with the ketogenic diet.

**Why it matters.** If you have fatty liver, a low-carb diet may help improve your liver health more than other diets.

**Seed direction.** Search PubMed for `ketogenic_diet liver_health` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_fa664b59238a5501"`

---

### 98. New Guidelines Standardize Diagnosis and Treatment for Heart-Kidney-Metabolic Condition

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_9da7dbf213dfafac` |
| **Stage** | Guideline |
| **Published** | 2026-08-11 (89d ago) |
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

### 99. Bone health: 600 METs-min/week of walking/jogging, plus falls risk assessment.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7878d119f83dc7e0` |
| **Stage** | Guideline |
| **Published** | 2026-09-10 (59d ago) |
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


## Neuro & Mental Health  ·  26 candidates
### 100. FDA Approves New ADHD Medication

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_33b0fdb6f0ab7d0b` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (61d ago) |
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

### 101. FDA approves first drug for Alexander disease

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4d237501fc6e4ed3` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-08 (31d ago) |
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

### 102. New blood tests can detect Alzheimer’s in adults as young as 40

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a6f0598da597fa67` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854427) |
| **Suggested `factor.slug`** | `alzheimers_blood_test` |
| **Suggested `outcome.slug`** | `alzheimers_disease` |

**Summary.** The FDA has approved two blood tests to help detect Alzheimer’s disease in adults with cognitive symptoms. One test is approved for use in people as young as 40.

**Why it matters.** If you or a loved one has memory concerns, these tests may help identify Alzheimer’s earlier, enabling timely care and planning.

**Seed direction.** Search PubMed for `alzheimers_blood_test alzheimers_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_a6f0598da597fa67"`

---

### 103. Early, personalized rehab improves stroke recovery

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_68ce87171a47622f` |
| **Stage** | Guideline |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854424) |
| **Suggested `factor.slug`** | `early_rehabilitation` |
| **Suggested `outcome.slug`** | `stroke_recovery` |

**Summary.** New guidelines recommend starting stroke rehab as soon as possible. Care should address physical, cognitive, language, and emotional needs.

**Why it matters.** If you or a loved one has had a stroke, early, tailored rehab can significantly improve recovery.

**Seed direction.** Search PubMed for `early_rehabilitation stroke_recovery` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_68ce87171a47622f"`

---

### 104. New multiple sclerosis treatment reduces relapses by one-third

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_540bc97bc50946c7` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-23 (16d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/23/novartis-remibrutinib-multiple-sclerosis-trial-results/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `novartis_ms_treatment` |
| **Suggested `outcome.slug`** | `ms_relapse_rate` |

**Summary.** In a major trial, a new multiple sclerosis treatment cut relapse rates by one-third compared to standard care. The results show significant improvement in managing the disease.

**Why it matters.** People with MS should talk to their doctor about this new option that may help reduce flare-ups.

**Seed direction.** Search PubMed for `novartis_ms_treatment ms_relapse_rate` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_540bc97bc50946c7"`

---

### 105. Asymptomatic carotid stenosis surgery reduces stroke risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5afd5d590347b2fc` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854200) |
| **Suggested `factor.slug`** | `carotid_endarterectomy` |
| **Suggested `outcome.slug`** | `stroke` |

**Summary.** Carotid endarterectomy plus best medical therapy reduced stroke risk compared to medical therapy alone. The procedure did not improve cognitive outcomes.

**Why it matters.** If you have asymptomatic carotid stenosis, surgery may prevent stroke but won't help memory.

**Seed direction.** Search PubMed for `carotid_endarterectomy stroke` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_5afd5d590347b2fc"`

---

### 106. FDA to decide on gene therapy for Huntington’s by May 1

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_04ca03541b909cff` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 95% |
| **Source** | [Endpoints News](https://endpoints.news/uniqure-gets-review-date-and-adcomm-inovias-stock-surges-after-approval/) |
| **Suggested `factor.slug`** | `gene_therapy` |
| **Suggested `outcome.slug`** | `huntingtons_disease` |

**Summary.** The FDA has set a review date of May 1 for UniQure’s gene therapy for Huntington’s disease. The decision could lead to the first approved gene therapy for this condition.

**Why it matters.** People with Huntington’s disease may soon have access to a new treatment option if the FDA approves the therapy.

**Seed direction.** Search PubMed for `gene_therapy huntingtons_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_04ca03541b909cff"`

---

### 107. FDA approves second over-the-counter naloxone nasal spray for opioid overdose

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_47a96cc94db33c7c` |
| **Stage** | Approved / Label |
| **Published** | 2026-07-28 (103d ago) |
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

### 108. Blood thinner more effective than standard drug for migraines linked to heart hole

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_cd80dcb8bd64e525` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-06 (94d ago) |
| **Strength** | 90% |
| **Source** | [BMJ](https://www.bmj.com/content/394/bmj-2026-100103) |
| **Suggested `factor.slug`** | `blood_thinner` |
| **Suggested `outcome.slug`** | `migraine_prevention` |

**Summary.** A blood thinner reduced migraine frequency more than standard treatment in people with a heart hole (PFO). 78% of patients on the blood thinner had fewer migraines versus 62% on standard drug, a 16% absolute improvement.

**Why it matters.** If you have migraines and a heart hole (PFO), ask your doctor if a blood thinner might be a better option than standard migraine medication.

**Seed direction.** Search PubMed for `blood_thinner migraine_prevention` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_cd80dcb8bd64e525"`

---

### 109. FDA approves home start for Alzheimer's antibody treatment

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_7e72d1fb17965942` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-25 (75d ago) |
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

### 110. Carotid stenting may help memory in stroke-prevention patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3f96f6232f59b07e` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854196) |
| **Suggested `factor.slug`** | `carotid_revascularization` |
| **Suggested `outcome.slug`** | `cognitive_outcome` |

**Summary.** In patients with no symptoms but poor blood flow in the brain, carotid stenting or surgery improved cognitive outcomes. The benefit was seen only in those with hemodynamic impairment at baseline.

**Why it matters.** If you have silent carotid stenosis and poor brain blood flow, treatment may help protect memory.

**Seed direction.** Search PubMed for `carotid_revascularization cognitive_outcome` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_3f96f6232f59b07e"`

---

### 111. Revascularization may improve thinking in stroke-prevention patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4b93278d34ea040a` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 90% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854192) |
| **Suggested `factor.slug`** | `revascularization` |
| **Suggested `outcome.slug`** | `cognitive_outcomes` |

**Summary.** In patients with no symptoms but severe carotid artery narrowing and poor brain blood flow, revascularization improved cognitive outcomes. The benefit was greater in those with worse hemodynamic impairment at baseline.

**Why it matters.** If you have silent carotid stenosis and memory issues, talk to your doctor about revascularization to protect brain function.

**Seed direction.** Search PubMed for `revascularization cognitive_outcomes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_4b93278d34ea040a"`

---

### 112. 988 Lifeline linked to 11% drop in youth suicide deaths, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3fbb4c6d2d44e3b8` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-22 (47d ago) |
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

### 113. Optogenetics helps some people see again after retinitis pigmentosa

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2e6814462d8b83c9` |
| **Stage** | Phase 1 |
| **Published** | 2026-10-07 (32d ago) |
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

### 114. Medications help treat opioid use disorder in primary care

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_26d30b09f68b4c8e` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-14 (25d ago) |
| **Strength** | 85% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/drug-safety-and-availability/prescribe-confidence) |
| **Suggested `factor.slug`** | `medications_for_opioid_use_disorder` |
| **Suggested `outcome.slug`** | `opioid_use_disorder` |

**Summary.** Primary care providers can safely and effectively manage opioid use disorder using approved medications. This approach improves patient outcomes and access to treatment.

**Why it matters.** Talk to your doctor about medication options if you or someone you know is struggling with opioid use.

**Seed direction.** Search PubMed for `medications_for_opioid_use_disorder opioid_use_disorder` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_26d30b09f68b4c8e"`

---

### 115. New injection lowers Alzheimer’s protein in early trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_13f75f02cb19bd27` |
| **Stage** | Phase 1 |
| **Published** | 2026-10-14 (25d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/arrowheads-brain-targeting-rna-drug-lowers-alzheimers-protein-in-early-study/) |
| **Suggested `factor.slug`** | `rna_drug` |
| **Suggested `outcome.slug`** | `tau_reduction` |

**Summary.** A subcutaneous injection reduced levels of tau, a protein linked to Alzheimer’s, in an early study. The treatment reached the brain and showed promising results.

**Why it matters.** This approach could lead to new ways to slow Alzheimer’s progression, offering hope for future treatments.

**Seed direction.** Search PubMed for `rna_drug tau_reduction` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_13f75f02cb19bd27"`

---

### 116. New oral drug shows promise for bipolar mania in phase 2 trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_0a14c1fb0a9a9545` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/rapport-says-drug-it-licensed-from-jj-clears-phase-2-bipolar-mania-study/) |
| **Suggested `factor.slug`** | `ampra_receptor_modulator` |
| **Suggested `outcome.slug`** | `bipolar_mania` |

**Summary.** A new oral drug targeting AMPA receptors successfully met its goals in a phase 2 trial for bipolar mania. The results support moving to larger, confirmatory studies next year.

**Why it matters.** This could lead to a new treatment option for people with bipolar mania, potentially offering a different approach than current medications.

**Seed direction.** Search PubMed for `ampra_receptor_modulator bipolar_mania` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_0a14c1fb0a9a9545"`

---

### 117. Post-surgery confusion linked to future memory problems in older adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_06582a505e001bb7` |
| **Stage** | other |
| **Published** | 2026-07-14 (117d ago) |
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

### 118. Ebola survivors may face long-term neurological issues, study finds

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_51281ffea9235180` |
| **Stage** | other |
| **Published** | 2026-07-21 (110d ago) |
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

### 119. Web tool helps patients stay on antidepressants longer

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_82c82aa9bbec1885` |
| **Stage** | Phase 3 |
| **Published** | 2026-08-04 (96d ago) |
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

### 120. Pregnant women using acetaminophen not linked to autism or ADHD in children

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c3b2819380c42865` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (96d ago) |
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

### 121. Mechanical clot removal improves recovery for stroke patients with medium or distal artery blockages.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6fe724c3027f0767` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (68d ago) |
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

### 122. Blood test may predict Alzheimer's-related cognitive decline risk

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_995ae1d23488274d` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-15 (54d ago) |
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

### 123. New injection therapy shows safety in early glaucoma trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b54c506d5e304338` |
| **Stage** | Phase 1 |
| **Published** | 2026-10-09 (30d ago) |
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

### 124. Thrombectomy for Stroke Clots in Smaller Arteries Improves Outcomes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_95c15f102f5df3fe` |
| **Stage** | Phase 3 |
| **Published** | 2026-09-01 (68d ago) |
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

### 125. New noninvasive scan finds clot source in stroke patients, improving treatment decisions

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8e723f61a7b0f64d` |
| **Stage** | Phase 2 |
| **Published** | 2026-09-01 (68d ago) |
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


## Other  ·  38 candidates
### 126. FDA approves first robotic device for blood draws in adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_68d956358a305371` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-06 (33d ago) |
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

### 127. FDA approves first oral drug for adult dermatomyositis

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_39a328133dbdf7ed` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-09 (30d ago) |
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

### 128. New treatment approved for genital herpes

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_024a85dc54b0fe4d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-12 (27d ago) |
| **Strength** | 95% |
| **Source** | [Endpoints News](https://endpoints.news/asahi-kasei-lands-approval-for-new-hsv-treatment/) |
| **Suggested `factor.slug`** | `herpes_treatment` |
| **Suggested `outcome.slug`** | `genital_herpes` |

**Summary.** The FDA has approved a new treatment for genital herpes. The drug was acquired by Asahi Kasei Therapeutics in a deal worth nearly $1 billion.

**Why it matters.** This approval offers a new option for people managing recurrent herpes outbreaks.

**Seed direction.** Search PubMed for `herpes_treatment genital_herpes` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_024a85dc54b0fe4d"`

---

### 129. New antibody therapy mimics clotting factor for hemophilia A

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a1252a6950277bc1` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2853865) |
| **Suggested `factor.slug`** | `bispecific_antibody` |
| **Suggested `outcome.slug`** | `hemophilia_a` |

**Summary.** A bispecific antibody has been developed to mimic factor VIII, treating hemophilia A. It offers a new treatment option for patients with this inherited bleeding disorder.

**Why it matters.** People with hemophilia A may now have a new treatment that reduces bleeding risk without frequent infusions.

**Seed direction.** Search PubMed for `bispecific_antibody hemophilia_a` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_a1252a6950277bc1"`

---

### 130. Platelets now last 21 days when stored cold

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_deaae0c2422d2d84` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2852958) |
| **Suggested `factor.slug`** | `cold_storage_platelets` |
| **Suggested `outcome.slug`** | `platelet_shelf_life` |

**Summary.** Platelets can now be stored at cold temperatures for up to 21 days, extending their shelf life from the previous 5 to 7 days. This change could improve blood supply availability and reduce waste.

**Why it matters.** Cold-stored platelets may help ensure blood is available when and where it's needed most.

**Seed direction.** Search PubMed for `cold_storage_platelets platelet_shelf_life` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_deaae0c2422d2d84"`

---

### 131. Updated COVID-19 vaccines approved for 2026-2027

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_f1cd9e33eb8c55d8` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854683) |
| **Suggested `factor.slug`** | `updated_covid_vaccine` |
| **Suggested `outcome.slug`** | `covid_infection` |

**Summary.** The FDA has approved four updated COVID-19 vaccines for the 2026-2027 season, designed to target the XFG variant. These vaccines are expected to improve protection against current and emerging strains.

**Why it matters.** Get the updated vaccine when available to stay protected against the latest COVID-19 variants.

**Seed direction.** Search PubMed for `updated_covid_vaccine covid_infection` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_f1cd9e33eb8c55d8"`

---

### 132. New guidance recommends oral treatment for severe hair loss

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_5a0488bb6fe0656f` |
| **Stage** | Guideline |
| **Published** | 2026-10-20 (19d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854679) |
| **Suggested `factor.slug`** | `jak_inhibitor` |
| **Suggested `outcome.slug`** | `alopecia_areata` |

**Summary.** Adults with severe alopecia areata should primarily be treated with oral JAK inhibitors. This condition affects over 7 million people in the US.

**Why it matters.** If you have severe hair loss, ask your doctor about oral JAK inhibitor treatment options.

**Seed direction.** Search PubMed for `jak_inhibitor alopecia_areata` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_5a0488bb6fe0656f"`

---

### 133. New injection therapy approved for chronic hepatitis B

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_49eb6e0725235f51` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-21 (18d ago) |
| **Strength** | 95% |
| **Source** | [FDA Approvals](http://www.fda.gov/news-events/press-announcements/fda-approves-first-its-kind-chronic-hepatitis-b-treatment) |
| **Suggested `factor.slug`** | `bepirovirsen` |
| **Suggested `outcome.slug`** | `chronic_hepatitis_b` |

**Summary.** The FDA has approved a new injection therapy to treat chronic hepatitis B in adults without cirrhosis. It is used alongside existing antiviral treatment.

**Why it matters.** This approval offers a new treatment option for people with chronic hepatitis B who need additional therapy.

**Seed direction.** Search PubMed for `bepirovirsen chronic_hepatitis_b` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_49eb6e0725235f51"`

---

### 134. New hepatitis B drug extends functional cure to more patients

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_4f65f7dc7650a5ee` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-21 (18d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/21/biotech-news-gsk-picks-up-hep-b-drug-approval/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `gsk_hepatitis_b_drug` |
| **Suggested `outcome.slug`** | `functional_cure_hepatitis_b` |

**Summary.** GSK's new hepatitis B drug has received FDA approval. It extends functional cures to more patients than previous treatments.

**Why it matters.** People with hepatitis B now have a new treatment option that offers better long-term outcomes.

**Seed direction.** Search PubMed for `gsk_hepatitis_b_drug functional_cure_hepatitis_b` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_4f65f7dc7650a5ee"`

---

### 135. Local anesthetic reduces pain during IUD insertion

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_fb6dec49960c4895` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854257) |
| **Suggested `factor.slug`** | `mepivacaine_instillation` |
| **Suggested `outcome.slug`** | `pain_during_iud_placement` |

**Summary.** In a randomized trial, instilling a local anesthetic into the uterus reduced pain during IUD placement. Participants reported significantly lower pain scores compared to placebo.

**Why it matters.** If you're getting an IUD, ask your provider about numbing the uterus to make the procedure more comfortable.

**Seed direction.** Search PubMed for `mepivacaine_instillation pain_during_iud_placement` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_fb6dec49960c4895"`

---

### 136. Local anesthetic reduces pain during IUD insertion

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_36f5a9bbcb27f794` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854255) |
| **Suggested `factor.slug`** | `intrauterine_anesthetic` |
| **Suggested `outcome.slug`** | `pain_during_iud_placement` |

**Summary.** In a clinical trial, a local anesthetic given directly into the uterus reduced pain during IUD placement. Participants reported significantly less pain compared to those receiving a placebo.

**Why it matters.** Women considering an IUD may ask their provider about pain relief options during insertion.

**Seed direction.** Search PubMed for `intrauterine_anesthetic pain_during_iud_placement` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_36f5a9bbcb27f794"`

---

### 137. FDA recognizes minocycline as effective against Stenotrophomonas

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_aeaabf7c2e67fdef` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-31 (8d ago) |
| **Strength** | 95% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/development-resources/fda-rationale-breakpoints-recognition-decision-minocycline-stenotrophomonas-maltophilia) |
| **Suggested `factor.slug`** | `minocycline` |
| **Suggested `outcome.slug`** | `stenotrophomonas_maltophilia_infection` |

**Summary.** The FDA has recognized minocycline as a treatment option for infections caused by Stenotrophomonas maltophilia. This decision is based on clinical data showing its effectiveness against this resistant bacterium.

**Why it matters.** Patients with hard-to-treat Stenotrophomonas infections may now have a new treatment option approved by the FDA.

**Seed direction.** Search PubMed for `minocycline stenotrophomonas_maltophilia_infection` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_aeaabf7c2e67fdef"`

---

### 138. Generic HIV prevention shot now approved in U.S.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_46221ec19699adf3` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-02 (6d ago) |
| **Strength** | 95% |
| **Source** | [STAT News](https://www.statnews.com/pharmalot/2026/11/02/lenacapavir-generic-version-approved-fda-hiv-prevention-dr-reddys/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `generic_lenacapavir` |
| **Suggested `outcome.slug`** | `hiv_infection` |

**Summary.** The FDA has approved a generic version of an HIV prevention injection. This could improve access in lower-income countries.

**Why it matters.** This approval may help make HIV prevention more affordable and available worldwide.

**Seed direction.** Search PubMed for `generic_lenacapavir hiv_infection` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_46221ec19699adf3"`

---

### 139. Heat kills more workers in some jobs than others

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c0f82228a8885435` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-03 (5d ago) |
| **Strength** | 95% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854852) |
| **Suggested `factor.slug`** | `heat_exposure` |
| **Suggested `outcome.slug`** | `heat_related_mortality` |

**Summary.** A U.S. study found that heat-related deaths among working-age adults varied widely by occupation and industry from 2021 to 2023. Outdoor and agricultural workers faced the highest risk.

**Why it matters.** Know your job's heat risk and take steps to stay safe in hot weather.

**Seed direction.** Search PubMed for `heat_exposure heat_related_mortality` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_c0f82228a8885435"`

---

### 140. ACOG releases 2026 maternal immunization schedule, differing from CDC recommendations

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_da2120b27bcd3d2b` |
| **Stage** | Guideline |
| **Published** | 2026-07-14 (117d ago) |
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

### 141. FDA approves first oral antibiotic for serious urinary tract infections

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_bb11334112b54274` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (96d ago) |
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

### 142. FDA approves first mRNA flu vaccine, offering new protection against influenza

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c4b63497f5702144` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-08 (61d ago) |
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

### 143. FDA approves first freeze-dried plasma product for U.S. use

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6e04af7812b96e19` |
| **Stage** | Approved / Label |
| **Published** | 2026-09-15 (54d ago) |
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

### 144. New drug approved for stubborn herpes sores in immune-compromised adults

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_498b479f8003cd85` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-10 (29d ago) |
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

### 145. New nonprescription eye drop approved for redness relief

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_b7b59ac29b77cb6d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-18 (21d ago) |
| **Strength** | 90% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/drugs/drug-alerts-and-statements/fda-approves-new-nonprescription-eye-drop-relief-eye-redness) |
| **Suggested `factor.slug`** | `nonprescription_eye_drop` |
| **Suggested `outcome.slug`** | `eye_redness` |

**Summary.** The FDA has approved a new nonprescription eye drop to relieve eye redness. It is available without a prescription for over-the-counter use.

**Why it matters.** You can now buy this eye drop without a prescription to help reduce redness in your eyes.

**Seed direction.** Search PubMed for `nonprescription_eye_drop eye_redness` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_b7b59ac29b77cb6d"`

---

### 146. FDA clarifies faster approval for personalized gene therapies

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_adb8d7639b5c346c` |
| **Stage** | Guideline |
| **Published** | 2026-10-27 (12d ago) |
| **Strength** | 90% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/27/fda-personalized-gene-therapy-guidance-individualized-feature-space/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `personalized_gene_therapy` |
| **Suggested `outcome.slug`** | `rare_disease_treatment_access` |

**Summary.** The FDA has released new guidance to help speed up approval of personalized gene therapies. Rare disease advocates say this could improve patient access to treatments.

**Why it matters.** This update may help patients with rare diseases get new gene therapies faster.

**Seed direction.** Search PubMed for `personalized_gene_therapy rare_disease_treatment_access` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_adb8d7639b5c346c"`

---

### 147. FDA outlines path for personalized gene editing therapies

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_53ae29a12a9b5489` |
| **Stage** | Guideline |
| **Published** | 2026-10-28 (11d ago) |
| **Strength** | 90% |
| **Source** | [Endpoints News](https://endpoints.news/fda-charts-path-for-approval-of-individualized-gene-editing-therapies/) |
| **Suggested `factor.slug`** | `gene_editing` |
| **Suggested `outcome.slug`** | `genetic_disorders` |

**Summary.** The FDA has released guidance for approving gene editing treatments tailored to individual patients' genetic mutations. This framework helps developers navigate regulatory approval for these highly personalized medicines.

**Why it matters.** This guidance could accelerate access to custom gene therapies for rare genetic diseases.

**Seed direction.** Search PubMed for `gene_editing genetic_disorders` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Guideline updates draw on multiple trials; cite both the guideline document and the pivotal trials.

**Provenance tag.** `provenance.breakthrough_id = "br_53ae29a12a9b5489"`

---

### 148. Steroid injection improves shoulder function more than usual care

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_c35a5e6166e2f44f` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-05 (3d ago) |
| **Strength** | 90% |
| **Source** | [BMJ](https://www.bmj.com/content/395/bmj-2026-101057/rr) |
| **Suggested `factor.slug`** | `steroid_injection` |
| **Suggested `outcome.slug`** | `shoulder_function` |

**Summary.** Steroid injections led to 10.01 more points in short-term function compared to usual care on a 0-100 scale. This difference meets the threshold for a clinically meaningful improvement.

**Why it matters.** If you have frozen shoulder, steroid injections may offer faster relief than standard treatments.

**Seed direction.** Search PubMed for `steroid_injection shoulder_function` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_c35a5e6166e2f44f"`

---

### 149. More generic drug competition lowers prices

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_d3dbaa9137a3b613` |
| **Stage** | Approved / Label |
| **Published** | 2026-11-06 (2d ago) |
| **Strength** | 90% |
| **Source** | [FDA Drug Safety](http://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/generic-competition-and-drug-prices) |
| **Suggested `factor.slug`** | `generic_competition` |
| **Suggested `outcome.slug`** | `drug_prices` |

**Summary.** FDA report shows increased competition among generic drug makers leads to lower prices. More competitors mean greater price reductions for patients.

**Why it matters.** More generic drug competition can help lower your prescription costs—ask your doctor about cheaper alternatives.

**Seed direction.** Search PubMed for `generic_competition drug_prices` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_d3dbaa9137a3b613"`

---

### 150. Writing style may affect how patients are responded to

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_01baa2a6eb915a69` |
| **Stage** | research |
| **Published** | 2026-10-06 (33d ago) |
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

### 151. Tick bites may raise risk of blood transfusion reactions

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_8bf01ac45f6cff82` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-06 (33d ago) |
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

### 152. New drug shows promise in slowing lung scarring

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_09a0aedc1795ab4a` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-12 (27d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/bristol-myers-reveals-a-pair-of-phase-3-wins-for-fibrosis-rayzebio-drugs/) |
| **Suggested `factor.slug`** | `admilparant` |
| **Suggested `outcome.slug`** | `lung_fibrosis_progression` |

**Summary.** A Phase 3 trial showed that a new drug significantly slowed the progression of lung fibrosis. Results demonstrated a meaningful improvement in lung function compared to placebo.

**Why it matters.** People with progressive lung scarring may now have a new treatment option to help preserve breathing function.

**Seed direction.** Search PubMed for `admilparant lung_fibrosis_progression` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_09a0aedc1795ab4a"`

---

### 153. New use for old leprosy drug now available in US

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_d1f7404786765710` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/novartis-quietly-returns-a-key-antibiotic-to-us-market/) |
| **Suggested `factor.slug`** | `antibiotic_lamprene` |
| **Suggested `outcome.slug`** | `antibiotic_access` |

**Summary.** Novartis has received FDA approval to market an old leprosy drug for a new purpose. The drug is now available in the U.S. market after supplemental approval.

**Why it matters.** This approval means a potentially life-saving treatment is now accessible for patients who need it.

**Seed direction.** Search PubMed for `antibiotic_lamprene antibiotic_access` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_d1f7404786765710"`

---

### 154. Mpox virus now spreading steadily in the U.S.

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_2f65b02f2dc88e06` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-13 (26d ago) |
| **Strength** | 85% |
| **Source** | [JAMA](https://jamanetwork.com/journals/jama/fullarticle/2854428) |
| **Suggested `factor.slug`** | `mpox_virus_clade_ii_b` |
| **Suggested `outcome.slug`** | `endemic_circulation` |

**Summary.** CDC data show the clade IIb mpox virus is now circulating regularly in the U.S., suggesting it may become endemic. Cases have stabilized at a low but persistent level.

**Why it matters.** You should know mpox is no longer just an outbreak threat—it’s now a regular part of U.S. infectious disease patterns.

**Seed direction.** Search PubMed for `mpox_virus_clade_ii_b endemic_circulation` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_2f65b02f2dc88e06"`

---

### 155. Core exercises improved jumping and balance in teen soccer players

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_324ccb8b720adc5b` |
| **Stage** | completed |
| **Published** | 2026-10-14 (25d ago) |
| **Strength** | 85% |
| **Source** | [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT07870083?aggFilters=studyType%3Aint) |
| **Suggested `factor.slug`** | `core_exercise_program` |
| **Suggested `outcome.slug`** | `jumping_performance_balance` |

**Summary.** An 8-week core exercise program improved jumping and balance in recreational soccer players aged 14 to 16. The study found measurable gains in performance without injury.

**Why it matters.** Teen athletes can boost performance and stability with just 8 weeks of simple core training.

**Seed direction.** Search PubMed for `core_exercise_program jumping_performance_balance` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. 

**Provenance tag.** `provenance.breakthrough_id = "br_324ccb8b720adc5b"`

---

### 156. Cognitive therapy may prevent chronic back pain

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_3e5732b66f5d85a8` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-17 (22d ago) |
| **Strength** | 85% |
| **Source** | [ClinicalTrials.gov](https://clinicaltrials.gov/study/NCT07877454?aggFilters=studyType%3Aint) |
| **Suggested `factor.slug`** | `cognitive_functional_therapy` |
| **Suggested `outcome.slug`** | `persistent_disabling_low_back_pain` |

**Summary.** A clinical trial found that cognitive functional therapy reduced the risk of acute low back pain becoming long-term disability. The study compared this therapy to usual care in patients with back pain lasting less than three months.

**Why it matters.** If you have recent back pain, early cognitive therapy may help prevent it from becoming long-lasting.

**Seed direction.** Search PubMed for `cognitive_functional_therapy persistent_disabling_low_back_pain` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_3e5732b66f5d85a8"`

---

### 157. New oral pill shows better colitis remission than existing treatment

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_eb606ebeded5bd21` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-19 (20d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/gileads-pill-posts-stronger-colitis-remission-rates-than-entyvio/) |
| **Suggested `factor.slug`** | `oral_alpha4beta7_inhibitor` |
| **Suggested `outcome.slug`** | `ulcerative_colitis_remission` |

**Summary.** A Phase 2 trial found the oral drug had higher remission rates in ulcerative colitis patients compared to a rival biologic. Results support advancing to late-stage trials.

**Why it matters.** This could mean a more convenient, effective treatment option for people with ulcerative colitis.

**Seed direction.** Search PubMed for `oral_alpha4beta7_inhibitor ulcerative_colitis_remission` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_eb606ebeded5bd21"`

---

### 158. New oral drug clears IBD symptoms in mid-stage trial

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_d43ccfc1a2fe33bd` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-19 (20d ago) |
| **Strength** | 85% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/19/gilead-ibs-drug-succeeds-phase-2-trial/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `gilead_ibd_drug` |
| **Suggested `outcome.slug`** | `ibd_symptoms` |

**Summary.** In a mid-stage study, an oral treatment eliminated symptoms in patients with a type of inflammatory bowel disease. Results were reported by Gilead Sciences.

**Why it matters.** People with IBD may benefit from a new treatment option that could reduce or eliminate symptoms.

**Seed direction.** Search PubMed for `gilead_ibd_drug ibd_symptoms` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_d43ccfc1a2fe33bd"`

---

### 159. New combo therapy works better than Skyrizi alone for Crohn’s

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_fe54e5e763dcf1fc` |
| **Stage** | Phase 2 |
| **Published** | 2026-10-19 (20d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/abbvies-skyrizi-combo-beats-skyrizi-alone-in-mid-stage-crohns-trial/) |
| **Suggested `factor.slug`** | `skyrizi_combo` |
| **Suggested `outcome.slug`** | `crohns_disease` |

**Summary.** In a mid-stage trial, a combination of Skyrizi and another drug worked better than Skyrizi alone in treating Crohn’s disease. The results showed improved outcomes, though specific numbers were not provided.

**Why it matters.** People with Crohn’s disease may benefit from a more effective treatment option in the near future.

**Seed direction.** Search PubMed for `skyrizi_combo crohns_disease` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_fe54e5e763dcf1fc"`

---

### 160. New immune drug shows success in treating eye inflammation

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_143fe40bc6144a51` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-21 (18d ago) |
| **Strength** | 85% |
| **Source** | [STAT News](https://www.statnews.com/2026/10/21/roivant-immune-drug-lisraya-noninfectious-uveitis-trial-results/?utm_campaign=rss) |
| **Suggested `factor.slug`** | `immune_drug` |
| **Suggested `outcome.slug`** | `noninfectious_uveitis` |

**Summary.** Roivant's immune drug demonstrated positive results in clinical trials for non-infectious uveitis. The trial showed significant improvement in patients' eye inflammation.

**Why it matters.** People with chronic eye inflammation may have a new treatment option that reduces symptoms and improves vision.

**Seed direction.** Search PubMed for `immune_drug noninfectious_uveitis` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_143fe40bc6144a51"`

---

### 161. New drug shows strong results in severe skin condition

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6390062ea2eac471` |
| **Stage** | Phase 3 |
| **Published** | 2026-10-22 (17d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/abbvie-notches-phase-3-win-in-painful-skin-condition-fda-filing-likely-next-year/) |
| **Suggested `factor.slug`** | `il_1_inhibitor` |
| **Suggested `outcome.slug`** | `painful_skin_condition` |

**Summary.** In a Phase 3 trial, the drug significantly improved symptoms in patients with a painful skin disease. Results support an upcoming FDA submission.

**Why it matters.** People with this severe skin condition may have a new treatment option soon.

**Seed direction.** Search PubMed for `il_1_inhibitor painful_skin_condition` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Phase 2/3 readouts usually have a registered ClinicalTrials.gov ID — confirm primary endpoint definitions.

**Provenance tag.** `provenance.breakthrough_id = "br_6390062ea2eac471"`

---

### 162. AI system outperforms doctors in diagnosing medical cases

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_a5b9147e23ced53d` |
| **Stage** | Approved / Label |
| **Published** | 2026-10-26 (13d ago) |
| **Strength** | 85% |
| **Source** | [Endpoints News](https://endpoints.news/microsofts-ai-gives-more-accurate-diagnoses-than-doctors-study-finds/) |
| **Suggested `factor.slug`** | `microsoft_ai_diagnostic_system` |
| **Suggested `outcome.slug`** | `diagnostic_accuracy` |

**Summary.** Microsoft's AI system was twice as accurate as doctors in diagnosing cases from medical journals and emergency room visits.

**Why it matters.** AI may help improve diagnosis accuracy in real-world clinical settings.

**Seed direction.** Search PubMed for `microsoft_ai_diagnostic_system diagnostic_accuracy` and pull the
underlying registrational study. If the breakthrough cites a specific trial
(see source URL), start there. Approval/label updates reflect post-marketing surveillance; cite the FDA notice plus the underlying registrational data.

**Provenance tag.** `provenance.breakthrough_id = "br_a5b9147e23ced53d"`

---

### 163. FDA approves first generic single-dose flu treatment, increasing affordability

| Field | Value |
|---|---|
| **Breakthrough ID** | `br_6385c93e7b351a52` |
| **Stage** | Approved / Label |
| **Published** | 2026-08-04 (96d ago) |
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

