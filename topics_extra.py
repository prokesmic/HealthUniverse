"""Round-2 topic expansion — ~125 pairs for Claude seed run.

Complements `topics.py` (106 pairs, Claude-seeded) and the Codex v2 batch
(250 pairs, awaiting PR). This file fills gaps that neither Codex's
brief nor the original cover: specific mental-health subtypes,
endocrine detail, occupational/sport-specific exposures, sensory health,
infectious-disease prevention, and a few high-leverage drug-condition
pairs.

Run after Codex v2 lands (or run anytime — `seed.py` is idempotent on the
seed_topic table).

    python topics_extra.py            # ensure entities + queue pairs
    python seed.py --next --limit 200 # seed everything pending
"""
from __future__ import annotations

from db import connect, upsert_entity

# ---------- New entities (factors + outcomes not yet in graph) ----------
ENTITIES: list[tuple[str, str, str]] = [
    # Outcomes — mental health detail
    ("ptsd",                       "Post-traumatic stress disorder",        "condition"),
    ("ocd",                        "Obsessive-compulsive disorder",         "condition"),
    ("eating_disorders",           "Eating disorders (general)",            "condition"),
    ("bipolar",                    "Bipolar disorder",                      "condition"),
    ("schizophrenia",              "Schizophrenia",                         "condition"),
    ("autism_spectrum",            "Autism spectrum disorder",              "condition"),
    ("burnout",                    "Burnout",                               "condition"),
    ("suicidality",                "Suicidality",                           "condition"),
    # Outcomes — endocrine
    ("hypothyroidism",             "Hypothyroidism",                        "condition"),
    ("hyperthyroidism",            "Hyperthyroidism",                       "condition"),
    ("low_testosterone",           "Low testosterone (male)",               "condition"),
    ("adrenal_fatigue",            "HPA-axis dysregulation",                "process"),
    ("cortisol_elevated",          "Chronically elevated cortisol",         "biomarker"),
    # Outcomes — sensory
    ("hearing_loss",               "Age-related hearing loss",              "condition"),
    ("tinnitus",                   "Tinnitus",                              "condition"),
    ("amd",                        "Age-related macular degeneration",      "condition"),
    ("cataracts",                  "Cataracts",                             "condition"),
    ("dry_eye",                    "Dry eye disease",                       "condition"),
    # Outcomes — musculoskeletal / dental
    ("low_back_pain",              "Chronic low back pain",                 "condition"),
    ("osteoarthritis_knee",        "Knee osteoarthritis",                   "condition"),
    ("periodontal_disease",        "Periodontal disease",                   "condition"),
    ("dental_caries",              "Dental caries",                         "condition"),
    # Outcomes — infectious / immune
    ("influenza",                  "Influenza infection",                   "condition"),
    ("urinary_tract_infection",    "Urinary tract infection (recurrent)",   "condition"),
    ("h_pylori",                   "Helicobacter pylori infection",         "condition"),
    ("antimicrobial_resistance",   "Antimicrobial resistance carriage",     "condition"),
    # Outcomes — performance / function
    ("vo2_max",                    "VO2 max",                               "biomarker"),
    ("grip_strength",              "Grip strength",                         "biomarker"),
    ("hrv",                        "Heart rate variability",                "biomarker"),
    ("crp",                        "C-reactive protein",                    "biomarker"),
    ("hba1c",                      "HbA1c",                                 "biomarker"),
    ("ldl_c",                      "LDL cholesterol",                       "biomarker"),
    ("apob",                       "ApoB",                                  "biomarker"),
    ("homocysteine",               "Homocysteine",                          "biomarker"),
    # Factors — drugs
    ("statins",                    "Statins",                               "drug"),
    ("metformin",                  "Metformin",                             "drug"),
    ("aspirin_low",                "Low-dose aspirin",                      "drug"),
    ("ssri",                       "SSRIs",                                 "drug"),
    ("ppi",                        "Proton pump inhibitors",                "drug"),
    ("benzodiazepines",            "Benzodiazepines (long-term)",           "drug"),
    ("hrt_estrogen",               "Estrogen-only HRT",                     "drug"),
    ("hrt_combined",               "Combined estrogen+progesterone HRT",    "drug"),
    ("glp1_agonists",              "GLP-1 receptor agonists",               "drug"),
    ("nsaids_chronic",             "Chronic NSAID use",                     "drug"),
    # Factors — supplements / nutrients
    ("vitamin_e",                  "Vitamin E (alpha-tocopherol)",          "supplement"),
    ("ashwagandha",                "Ashwagandha",                           "supplement"),
    ("rhodiola",                   "Rhodiola rosea",                        "supplement"),
    ("glycine",                    "Glycine",                               "supplement"),
    ("nac",                        "N-acetylcysteine",                      "supplement"),
    ("coq10",                      "Coenzyme Q10",                          "supplement"),
    ("d_ribose",                   "D-ribose",                              "supplement"),
    ("collagen",                   "Collagen peptides",                     "supplement"),
    ("lutein_zeaxanthin",          "Lutein + zeaxanthin",                   "supplement"),
    ("taurine",                    "Taurine",                               "supplement"),
    # Factors — foods detail
    ("oily_fish_servings",         "Oily fish (≥2 servings/week)",          "food"),
    ("ultra_processed_high",       "Ultra-processed >50% of calories",      "food"),
    ("plant_based_diet",           "Plant-based dietary pattern",           "food"),
    ("ketogenic_diet",             "Ketogenic diet",                        "behavior"),
    ("flavanols_cocoa",            "Cocoa flavanols",                       "nutrient"),
    # Factors — activities / behaviors
    ("hiit",                       "High-intensity interval training",      "activity"),
    ("yoga",                       "Yoga",                                  "activity"),
    ("meditation",                 "Meditation / mindfulness practice",     "activity"),
    ("singing_choir",              "Group singing / choir",                 "activity"),
    ("nature_exposure",            "Time in nature (>120 min/week)",        "behavior"),
    ("cognitive_engagement",       "Cognitive engagement / learning",       "behavior"),
    ("flossing",                   "Daily flossing",                        "behavior"),
    ("oral_hygiene",               "Twice-daily toothbrushing with fluoride","behavior"),
    # Factors — environmental / occupational
    ("shift_work",                 "Rotating shift work",                   "behavior"),
    ("loud_noise_occupational",    "Occupational loud noise exposure",      "environmental"),
    ("uv_eye_exposure",            "UV eye exposure (no sunglasses)",       "environmental"),
    ("digital_screen_hours",       "Digital screen use >8h/day",            "behavior"),
]

# ---------- (factor_slug, outcome_slug, priority) ----------
PAIRS: list[tuple[str, str, int]] = [
    # ---- Mental health detail ----
    ("aerobic_exercise",   "ptsd",            2),
    ("aerobic_exercise",   "ocd",             3),
    ("meditation",         "ptsd",            2),
    ("meditation",         "anxiety",         1),
    ("meditation",         "depression",      2),
    ("meditation",         "burnout",         2),
    ("yoga",               "anxiety",         2),
    ("yoga",               "depression",      3),
    ("yoga",               "low_back_pain",   2),
    ("nature_exposure",    "depression",      2),
    ("nature_exposure",    "anxiety",         2),
    ("nature_exposure",    "burnout",         2),
    ("ssri",               "suicidality",     1),
    ("ssri",               "bipolar",         3),
    ("benzodiazepines",    "dementia",        2),
    ("ashwagandha",        "anxiety",         3),
    ("ashwagandha",        "low_testosterone",3),
    ("ashwagandha",        "cortisol_elevated",3),
    ("rhodiola",           "burnout",         3),
    ("singing_choir",      "depression",      3),
    ("cognitive_engagement","dementia",       1),
    ("social_isolation",   "suicidality",     1),

    # ---- Endocrine ----
    ("selenium",           "hypothyroidism",  3),
    ("iodine",             "hypothyroidism",  3),
    ("vitamin_d",          "hypothyroidism",  4),
    ("aerobic_exercise",   "low_testosterone",3),
    ("resistance_training","low_testosterone",2),
    ("sleep_short",        "low_testosterone",2),
    ("ultra_processed",    "low_testosterone",3),
    ("alcohol",            "low_testosterone",2),
    ("chronic_stress",     "cortisol_elevated",1),
    ("aerobic_exercise",   "cortisol_elevated",2),
    ("hrt_estrogen",       "breast_cancer",   1),
    ("hrt_combined",       "breast_cancer",   1),
    ("hrt_combined",       "osteoporosis",    2),
    ("hrt_estrogen",       "cvd",             2),

    # ---- Sensory ----
    ("loud_noise_occupational", "hearing_loss", 1),
    ("smoking",            "hearing_loss",    2),
    ("aerobic_exercise",   "hearing_loss",    3),
    ("vitamin_b12",        "tinnitus",        4),
    ("uv_eye_exposure",    "amd",             2),
    ("smoking",            "amd",             1),
    ("lutein_zeaxanthin",  "amd",             2),
    ("omega3",             "amd",             3),
    ("uv_eye_exposure",    "cataracts",       2),
    ("smoking",            "cataracts",       2),
    ("digital_screen_hours","dry_eye",        2),

    # ---- Musculoskeletal / dental ----
    ("yoga",               "low_back_pain",   2),
    ("walking_daily",      "low_back_pain",   2),
    ("resistance_training","low_back_pain",   2),
    ("sitting_prolonged",  "low_back_pain",   1),
    ("walking_daily",      "osteoarthritis_knee", 2),
    ("resistance_training","osteoarthritis_knee", 2),
    ("collagen",           "osteoarthritis_knee", 4),
    ("flossing",           "periodontal_disease", 1),
    ("oral_hygiene",       "dental_caries",   1),
    ("smoking",            "periodontal_disease", 1),
    ("ultra_processed",    "dental_caries",   2),
    ("sugar_sweetened_drinks","dental_caries", 1),
    ("periodontal_disease","cvd",             2),
    ("periodontal_disease","alzheimers",      3),

    # ---- Infectious / immune ----
    ("vitamin_d",          "respiratory_infection", 2),
    ("vitamin_d",          "influenza",       3),
    ("zinc",               "respiratory_infection", 3),
    ("aerobic_exercise",   "influenza",       3),
    ("sleep_short",        "respiratory_infection", 1),
    ("nac",                "respiratory_infection", 4),
    ("probiotics",         "urinary_tract_infection", 3),
    ("h_pylori",           "colorectal_cancer", 4),
    ("ultra_processed",    "antimicrobial_resistance", 4),

    # ---- Performance / fitness biomarkers ----
    ("aerobic_exercise",   "vo2_max",         1),
    ("hiit",               "vo2_max",         1),
    ("hiit",               "insulin_resistance", 2),
    ("hiit",               "all_cause_mortality", 2),
    ("resistance_training","grip_strength",   1),
    ("grip_strength",      "all_cause_mortality", 1),
    ("vo2_max",            "all_cause_mortality", 1),
    ("hrv",                "all_cause_mortality", 2),
    ("meditation",         "hrv",             3),
    ("aerobic_exercise",   "hrv",             2),
    ("alcohol",            "hrv",             3),

    # ---- Drug-condition / drug-nutrient ----
    ("statins",            "ldl_c",           1),
    ("statins",            "cvd",             1),
    ("statins",            "coq10",           3),  # CoQ10 depletion mechanism
    ("metformin",          "vitamin_b12",     2),
    ("metformin",          "all_cause_mortality", 3),
    ("aspirin_low",        "colorectal_cancer", 2),
    ("aspirin_low",        "cvd",             2),
    ("ppi",                "vitamin_b12",     2),
    ("ppi",                "magnesium",       3),
    ("ppi",                "osteoporosis",    3),
    ("nsaids_chronic",     "ckd",             2),
    ("glp1_agonists",      "obesity",         1),
    ("glp1_agonists",      "t2d",             1),
    ("glp1_agonists",      "cvd",             2),

    # ---- Specific biomarker movements ----
    ("ultra_processed",    "crp",             2),
    ("omega3",             "crp",             2),
    ("aerobic_exercise",   "crp",             2),
    ("ketogenic_diet",     "ldl_c",           3),
    ("ketogenic_diet",     "hba1c",           2),
    ("plant_based_diet",   "ldl_c",           2),
    ("plant_based_diet",   "apob",            3),
    ("oily_fish_servings", "apob",            3),
    ("vitamin_b12",        "homocysteine",    2),
    ("folate",             "homocysteine",    2),

    # ---- Sleep + circadian detail ----
    ("shift_work",         "cvd",             1),
    ("shift_work",         "t2d",             1),
    ("shift_work",         "breast_cancer",   2),
    ("shift_work",         "depression",      2),
    ("glycine",            "sleep_quality",   3),
    ("nature_exposure",    "sleep_quality",   3),

    # ---- Foods detail ----
    ("flavanols_cocoa",    "cognitive_decline", 3),
    ("flavanols_cocoa",    "hypertension",    3),
    ("oily_fish_servings", "all_cause_mortality", 1),
    ("oily_fish_servings", "alzheimers",      2),
    ("plant_based_diet",   "all_cause_mortality", 1),
    ("plant_based_diet",   "cvd",             1),
    ("ultra_processed_high","all_cause_mortality", 1),
    ("ultra_processed_high","cvd",            1),
    ("ultra_processed_high","depression",     2),

    # ---- Eye / vision ----
    ("nature_exposure",    "amd",             4),
    ("digital_screen_hours","sleep_quality",  2),
    ("digital_screen_hours","depression",     3),

    # ---- Misc / underrepresented ----
    ("taurine",            "all_cause_mortality", 4),
    ("collagen",           "sarcopenia",      4),
    ("creatine",           "cognitive_decline", 3),
    ("ashwagandha",        "sleep_quality",   3),
]


def seed_topics() -> tuple[int, int]:
    with connect() as conn:
        for slug, name, kind in ENTITIES:
            upsert_entity(conn, slug=slug, name=name, kind=kind)
        n_inserted = 0
        for factor, outcome, priority in PAIRS:
            cur = conn.execute(
                "INSERT OR IGNORE INTO seed_topic (factor_slug, outcome_slug, priority) "
                "VALUES (?, ?, ?)",
                (factor, outcome, priority),
            )
            n_inserted += cur.rowcount
    return len(ENTITIES), n_inserted


if __name__ == "__main__":
    n_ent, n_pairs = seed_topics()
    print(f"Ensured {n_ent} entities; queued {n_pairs} new pairs "
          f"(of {len(PAIRS)} defined)")
