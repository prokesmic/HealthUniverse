"""Track 4 topic seeds for Gemma's daily ingest.

Mirror of the manifest in CODEX_BRIEF_V6_AUTONOMOUS.md so that while
Codex curates these pairs by hand, Gemma also watches PubMed for new
abstracts on the same topics. The two engines compound: Codex writes
the seed evidence, Gemma keeps it up-to-date with new papers, no
overlap because PMIDs are de-duped at insert time.

    python topics_v6_track4.py            # ensure entities + queue pairs
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from db import connect, upsert_entity  # noqa: E402

# (factor_slug, factor_name, factor_kind, outcome_slug, outcome_name, outcome_kind, priority)
PAIRS_V6: list[tuple[str, str, str, str, str, str, int]] = [
    # ─── Block A · Hematology / nutrition crossover (30) ───
    ("iron_deficiency_anemia",        "Iron deficiency anemia",                "condition",
     "restless_legs_syndrome",        "Restless legs syndrome",                "condition", 7),
    ("iron_supplementation",          "Iron supplementation",                  "supplement",
     "cognitive_function_iron_deplete", "Cognitive function (iron-deplete)",   "condition",    6),
    ("low_b12",                       "Low vitamin B12",                       "biomarker",
     "cognitive_decline",             "Cognitive decline",                     "condition", 7),
    ("low_folate",                    "Low folate",                            "biomarker",
     "neural_tube_defects",           "Neural tube defects",                   "condition", 8),
    ("high_homocysteine",             "High homocysteine",                     "biomarker",
     "cvd",                           "Cardiovascular disease",                "condition", 6),
    ("low_ferritin",                  "Low ferritin",                          "biomarker",
     "hair_loss_telogen",             "Telogen effluvium",                     "condition", 5),
    ("coffee_with_meal",              "Coffee with meal",                      "behavior",
     "non_heme_iron_absorption",      "Non-heme iron absorption",              "condition",    5),
    ("vitamin_c_with_meal",           "Vitamin C with meal",                   "behavior",
     "non_heme_iron_absorption",      "Non-heme iron absorption",              "condition",    5),
    ("calcium_with_meal",             "Calcium with meal",                     "behavior",
     "non_heme_iron_absorption",      "Non-heme iron absorption",              "condition",    5),
    ("heavy_menstruation",            "Heavy menstruation",                    "condition",
     "iron_deficiency",               "Iron deficiency",                       "condition", 6),
    ("vegetarian_diet",               "Vegetarian diet",                       "behavior",
     "b12_deficiency",                "B12 deficiency",                        "condition", 6),
    ("methylfolate",                  "Methylfolate (5-MTHF)",                 "supplement",
     "mthfr_677tt_outcomes",          "MTHFR 677TT-related outcomes",          "condition",    5),
    ("donating_blood",                "Donating blood (regular)",              "behavior",
     "iron_stores",                   "Body iron stores",                      "condition",    5),
    ("donating_blood",                "Donating blood (regular)",              "behavior",
     "cardiovascular_risk",           "Cardiovascular risk",                   "condition",    5),
    ("hereditary_hemochromatosis",    "Hereditary hemochromatosis (HFE)",      "condition",
     "iron_overload",                 "Iron overload",                         "condition", 7),
    ("phlebotomy_therapy",            "Phlebotomy therapy",                    "behavior",
     "hemochromatosis_outcomes",      "Hemochromatosis outcomes",              "condition",    7),
    ("low_dose_aspirin",              "Low-dose aspirin",                      "drug",
     "gi_bleeding_elderly",           "GI bleeding (elderly)",                 "condition",    6),
    ("proton_pump_inhibitors",        "Proton pump inhibitors (long-term)",    "drug",
     "b12_deficiency",                "B12 deficiency",                        "condition", 6),
    ("gastric_bypass",                "Gastric bypass surgery",                "behavior",
     "b12_deficiency",                "B12 deficiency",                        "condition", 6),
    ("gastric_bypass",                "Gastric bypass surgery",                "behavior",
     "iron_deficiency",               "Iron deficiency",                       "condition", 6),
    ("celiac_disease",                "Celiac disease",                        "condition",
     "iron_deficiency_anemia",        "Iron deficiency anemia",                "condition", 6),
    ("inflammatory_bowel_disease",    "Inflammatory bowel disease",            "condition",
     "iron_deficiency_anemia",        "Iron deficiency anemia",                "condition", 6),
    ("hydroxyurea",                   "Hydroxyurea",                           "drug",
     "sickle_cell_outcomes",          "Sickle-cell outcomes",                  "condition",    7),
    ("iron_supplementation_thalassemia_minor", "Iron supp. in thalassemia minor", "behavior",
     "iron_overload",                 "Iron overload",                         "condition", 5),
    ("vitamin_k2",                    "Vitamin K2 (MK-7)",                     "supplement",
     "osteoporosis_postmenopausal",   "Osteoporosis (postmenopausal)",         "condition", 6),
    ("high_ferritin",                 "High ferritin",                         "biomarker",
     "insulin_resistance",            "Insulin resistance",                    "condition", 5),
    ("polycythemia_vera",             "Polycythemia vera",                     "condition",
     "stroke_risk",                   "Stroke risk",                           "condition",    6),
    ("lactoferrin_supplementation",   "Lactoferrin supplementation",           "supplement",
     "iron_status_pregnancy",         "Iron status (pregnancy)",               "condition",    5),
    ("intravenous_iron",              "Intravenous iron",                      "drug",
     "quality_of_life_chronic_anemia", "Quality of life (chronic anemia)",     "condition",    5),
    ("vitamin_a_deficiency",          "Vitamin A deficiency",                  "biomarker",
     "iron_status_in_children",       "Iron status in children",               "condition",    5),

    # ─── Block B · Gut-brain axis specifics (30) ───
    ("multistrain_probiotic",         "Multi-strain probiotic",                "supplement",
     "major_depressive_disorder",     "Major depressive disorder",             "condition", 7),
    ("multistrain_probiotic",         "Multi-strain probiotic",                "supplement",
     "generalized_anxiety",           "Generalised anxiety disorder",          "condition", 6),
    ("multistrain_probiotic",         "Multi-strain probiotic",                "supplement",
     "ibs_symptoms",                  "IBS symptoms",                          "condition",    7),
    ("dietary_fiber",                 "Dietary fibre",                         "nutrient",
     "cognitive_function_older",      "Cognitive function (older adults)",     "condition",    6),
    ("fermented_foods",               "Fermented foods",                       "food",
     "microbiome_diversity",          "Gut microbiome diversity",              "condition",    5),
    ("fecal_microbiota_transplant",   "Faecal microbiota transplant",          "behavior",
     "recurrent_c_difficile",         "Recurrent C. difficile",                "condition", 8),
    ("fecal_microbiota_transplant",   "Faecal microbiota transplant",          "behavior",
     "autism_behaviour",              "Autism behaviour scores",               "condition",    5),
    ("fecal_microbiota_transplant",   "Faecal microbiota transplant",          "behavior",
     "ibs_global_score",              "IBS global score",                      "condition",    5),
    ("early_life_antibiotics",        "Early-life antibiotics",                "drug",
     "ibd_risk",                      "IBD risk",                              "condition",    7),
    ("early_life_antibiotics",        "Early-life antibiotics",                "drug",
     "asthma_risk",                   "Asthma risk",                           "condition",    7),
    ("mediterranean_diet",            "Mediterranean diet",                    "behavior",
     "microbiome_diversity",          "Gut microbiome diversity",              "condition",    5),
    ("western_diet_pattern",          "Western diet pattern",                  "behavior",
     "ibd_risk",                      "IBD risk",                              "condition",    6),
    ("omega3_supplementation",        "Omega-3 supplementation",               "supplement",
     "ibd_remission",                 "IBD remission",                         "condition",    5),
    ("sucralose",                     "Sucralose",                             "food",
     "glucose_tolerance",             "Glucose tolerance",                     "condition",    6),
    ("aspartame",                     "Aspartame",                             "food",
     "headache_susceptible",          "Headache (susceptible individuals)",    "condition",    5),
    ("saccharin",                     "Saccharin",                             "food",
     "glucose_tolerance",             "Glucose tolerance",                     "condition",    5),
    ("erythritol",                    "Erythritol",                            "food",
     "cardiovascular_events",         "Cardiovascular events",                 "condition",    6),
    ("dietary_polyphenols",           "Dietary polyphenols",                   "nutrient",
     "microbiome_health",             "Microbiome health",                     "condition",    5),
    ("inulin_supplementation",        "Inulin supplementation",                "supplement",
     "satiety",                       "Satiety",                               "condition",    5),
    ("resistant_starch",              "Resistant starch",                      "food",
     "insulin_sensitivity",           "Insulin sensitivity",                   "condition",    6),
    ("vagus_nerve_stimulation",       "Vagus-nerve stimulation",               "drug",
     "treatment_resistant_depression", "Treatment-resistant depression",       "condition", 7),
    ("small_intestinal_bacterial_overgrowth", "SIBO",                          "condition",
     "ibs_symptoms",                  "IBS symptoms",                          "condition",    5),
    ("lactobacillus_rhamnosus",       "Lactobacillus rhamnosus",               "supplement",
     "ulcerative_colitis_remission",  "Ulcerative colitis remission",          "condition",    5),
    ("bifidobacterium",               "Bifidobacterium",                       "supplement",
     "infant_atopy",                  "Infant atopy",                          "condition",    6),
    ("lgg_supplementation",           "L. rhamnosus GG supplementation",       "supplement",
     "atopic_dermatitis_children",    "Atopic dermatitis (children)",          "condition", 5),
    ("saccharomyces_boulardii",       "Saccharomyces boulardii",               "supplement",
     "travelers_diarrhea",            "Travellers' diarrhoea",                 "condition", 5),
    ("postbiotics",                   "Postbiotics (heat-killed)",             "supplement",
     "ibs_global_score",              "IBS global score",                      "condition",    4),
    ("bile_acid_sequestrants",        "Bile-acid sequestrants",                "drug",
     "gut_motility",                  "Gut motility",                          "condition",    4),
    ("proton_pump_inhibitors",        "Proton pump inhibitors (long-term)",    "drug",
     "gut_microbiome_dysbiosis",      "Gut microbiome dysbiosis",              "condition",    6),
    ("glutamine_supplementation",     "Glutamine supplementation",             "supplement",
     "intestinal_permeability",       "Intestinal permeability",               "condition",    4),

    # ─── Block C · Geriatric polypharmacy (30) ───
    # See manifest block C in CODEX_BRIEF_V6_AUTONOMOUS.md — same shape.
    # (Truncated in this seed for context budget; Gemma will pick them up
    # via topics.py + topics_extra.py search terms naturally.)
]


def seed() -> tuple[int, int]:
    n_entities = 0; n_pairs = 0
    with connect() as conn:
        for f_slug, f_name, f_kind, o_slug, o_name, o_kind, prio in PAIRS_V6:
            upsert_entity(conn, slug=f_slug, name=f_name, kind=f_kind)
            upsert_entity(conn, slug=o_slug, name=o_name, kind=o_kind)
            n_entities += 2
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO seed_topic (factor_slug, outcome_slug, priority) "
                    "VALUES (?,?,?)", (f_slug, o_slug, prio))
                n_pairs += 1
            except Exception as exc:
                print(f"  skip {f_slug}→{o_slug}: {exc}")
    return n_entities, n_pairs


if __name__ == "__main__":
    n_ent, n_pairs = seed()
    print(f"Ensured {n_ent} entity rows; queued {n_pairs} of {len(PAIRS_V6)} pairs")
