"""Seed topic matrix. Each row becomes one Claude deep-research run.
Priority 1 = critical (run first), 5 = nice to have.
Curated for chronic-disease leverage rather than completeness."""
from __future__ import annotations

from db import connect

# Entities we'll auto-create as we register topics. (slug, name, kind)
ENTITIES: list[tuple[str, str, str]] = [
    # ---------- OUTCOMES (chronic conditions + key processes) ----------
    ("cvd",                    "Cardiovascular disease",            "condition"),
    ("hypertension",           "Hypertension",                      "condition"),
    ("t2d",                    "Type 2 diabetes",                   "condition"),
    ("obesity",                "Obesity",                           "condition"),
    ("nafld",                  "Non-alcoholic fatty liver disease", "condition"),
    ("alzheimers",             "Alzheimer's disease",               "condition"),
    ("dementia",               "Dementia (all-cause)",              "condition"),
    ("parkinsons",             "Parkinson's disease",               "condition"),
    ("depression",             "Depression",                        "condition"),
    ("anxiety",                "Anxiety disorders",                 "condition"),
    ("colorectal_cancer",      "Colorectal cancer",                 "condition"),
    ("breast_cancer",          "Breast cancer",                     "condition"),
    ("prostate_cancer",        "Prostate cancer",                   "condition"),
    ("lung_cancer",            "Lung cancer",                       "condition"),
    ("osteoporosis",           "Osteoporosis",                      "condition"),
    ("sarcopenia",             "Sarcopenia",                        "condition"),
    ("ckd",                    "Chronic kidney disease",            "condition"),
    ("ibd",                    "Inflammatory bowel disease",        "condition"),
    ("autoimmune",             "Autoimmune disease (general)",      "condition"),
    ("all_cause_mortality",    "All-cause mortality",               "condition"),
    ("inflammation",           "Chronic systemic inflammation",     "process"),
    ("insulin_resistance",     "Insulin resistance",                "process"),
    ("sleep_quality",          "Sleep quality",                     "process"),
    ("cognitive_decline",      "Age-related cognitive decline",     "process"),
    ("gut_microbiome",         "Gut microbiome diversity",          "process"),

    # ---------- FACTORS: foods ----------
    ("vegetables_leafy",       "Leafy green vegetables",            "food"),
    ("vegetables_cruciferous", "Cruciferous vegetables",            "food"),
    ("berries",                "Berries",                           "food"),
    ("legumes",                "Legumes",                           "food"),
    ("whole_grains",           "Whole grains",                      "food"),
    ("nuts",                   "Nuts",                              "food"),
    ("olive_oil",              "Extra-virgin olive oil",            "food"),
    ("fish_fatty",             "Fatty fish",                        "food"),
    ("red_meat",               "Red meat",                          "food"),
    ("processed_meat",         "Processed meat",                    "food"),
    ("ultra_processed",        "Ultra-processed food",              "food"),
    ("sugar_sweetened_drinks", "Sugar-sweetened beverages",         "food"),
    ("artificial_sweeteners",  "Artificial sweeteners",             "food"),
    ("alcohol",                "Alcohol",                           "food"),
    ("coffee",                 "Coffee",                            "food"),
    ("green_tea",              "Green tea",                         "food"),
    ("dairy_fermented",        "Fermented dairy (yogurt/kefir)",    "food"),
    ("dairy_milk",              "Milk",                             "food"),

    # ---------- FACTORS: nutrients & supplements ----------
    ("omega3",                 "Omega-3 (EPA/DHA)",                 "supplement"),
    ("vitamin_d",              "Vitamin D",                         "supplement"),
    ("vitamin_b12",            "Vitamin B12",                       "supplement"),
    ("vitamin_k2",             "Vitamin K2",                        "supplement"),
    ("magnesium",              "Magnesium",                         "supplement"),
    ("creatine",                "Creatine monohydrate",             "supplement"),
    ("fiber_soluble",          "Soluble fiber",                     "nutrient"),
    ("polyphenols",            "Dietary polyphenols",               "nutrient"),
    ("zinc",                   "Zinc",                              "supplement"),
    ("iron",                   "Iron",                              "supplement"),
    ("selenium",               "Selenium",                          "supplement"),
    ("curcumin",               "Curcumin",                          "supplement"),
    ("probiotics",             "Probiotics (multi-strain)",         "supplement"),
    ("multivitamin",           "Multivitamin",                      "supplement"),

    # ---------- FACTORS: activities & behaviors ----------
    ("aerobic_exercise",       "Aerobic exercise",                  "activity"),
    ("resistance_training",    "Resistance training",               "activity"),
    ("walking_daily",          "Daily walking (steps)",             "activity"),
    ("sitting_prolonged",      "Prolonged sitting",                 "behavior"),
    ("sleep_short",            "Short sleep duration (<6h)",        "behavior"),
    ("sleep_long",             "Long sleep duration (>9h)",         "behavior"),
    ("smoking",                "Smoking",                           "behavior"),
    ("vaping",                 "Vaping (nicotine)",                 "behavior"),
    ("intermittent_fasting",   "Time-restricted eating",            "behavior"),
    ("social_isolation",       "Social isolation / loneliness",     "behavior"),
    ("chronic_stress",         "Chronic psychological stress",      "behavior"),
    ("sauna",                  "Regular sauna use",                 "activity"),
    ("cold_exposure",          "Deliberate cold exposure",          "activity"),

    # ---------- FACTORS: environmental ----------
    ("pm25",                   "Fine particulate air pollution (PM2.5)", "environmental"),
    ("nighttime_light",        "Nighttime light exposure",          "environmental"),
    ("noise_chronic",          "Chronic noise exposure",            "environmental"),
    ("microplastics",          "Microplastics",                     "environmental"),
    ("bpa",                    "Bisphenol A (BPA)",                 "environmental"),
    ("pfas",                   "PFAS (forever chemicals)",          "environmental"),
    ("uv_sunlight",            "Sunlight / UV exposure",            "environmental"),
    ("daylight_morning",       "Morning bright-light exposure",     "environmental"),
]

# Pairs to research. (factor_slug, outcome_slug, priority)
PAIRS: list[tuple[str, str, int]] = [
    # ---- Cardiometabolic core ----
    ("vegetables_leafy", "cvd", 1),
    ("vegetables_cruciferous", "cvd", 2),
    ("berries", "cvd", 2),
    ("legumes", "cvd", 1),
    ("whole_grains", "cvd", 1),
    ("nuts", "cvd", 1),
    ("olive_oil", "cvd", 1),
    ("fish_fatty", "cvd", 1),
    ("red_meat", "cvd", 1),
    ("processed_meat", "cvd", 1),
    ("ultra_processed", "cvd", 1),
    ("sugar_sweetened_drinks", "cvd", 1),
    ("alcohol", "cvd", 1),
    ("coffee", "cvd", 2),
    ("omega3", "cvd", 1),
    ("vitamin_d", "cvd", 2),
    ("magnesium", "cvd", 2),
    ("fiber_soluble", "cvd", 1),
    ("aerobic_exercise", "cvd", 1),
    ("resistance_training", "cvd", 2),
    ("sitting_prolonged", "cvd", 1),
    ("smoking", "cvd", 1),
    ("pm25", "cvd", 1),
    ("chronic_stress", "cvd", 2),
    ("sauna", "cvd", 3),

    # ---- Type 2 diabetes ----
    ("ultra_processed", "t2d", 1),
    ("sugar_sweetened_drinks", "t2d", 1),
    ("whole_grains", "t2d", 1),
    ("legumes", "t2d", 1),
    ("nuts", "t2d", 2),
    ("coffee", "t2d", 2),
    ("artificial_sweeteners", "t2d", 2),
    ("aerobic_exercise", "t2d", 1),
    ("resistance_training", "t2d", 1),
    ("intermittent_fasting", "t2d", 2),
    ("sleep_short", "t2d", 1),
    ("vitamin_d", "t2d", 3),
    ("magnesium", "t2d", 2),

    # ---- Cancers ----
    ("processed_meat", "colorectal_cancer", 1),
    ("red_meat", "colorectal_cancer", 1),
    ("alcohol", "colorectal_cancer", 1),
    ("alcohol", "breast_cancer", 1),
    ("fiber_soluble", "colorectal_cancer", 1),
    ("vegetables_cruciferous", "colorectal_cancer", 2),
    ("aerobic_exercise", "colorectal_cancer", 2),
    ("smoking", "lung_cancer", 1),
    ("vaping", "lung_cancer", 2),
    ("pm25", "lung_cancer", 2),
    ("dairy_milk", "prostate_cancer", 3),
    ("uv_sunlight", "vitamin_d", 4),  # mechanistic helper

    # ---- Brain / cognition / mood ----
    ("fish_fatty", "alzheimers", 1),
    ("omega3", "cognitive_decline", 1),
    ("berries", "cognitive_decline", 2),
    ("aerobic_exercise", "alzheimers", 1),
    ("aerobic_exercise", "depression", 1),
    ("resistance_training", "depression", 2),
    ("social_isolation", "dementia", 1),
    ("sleep_short", "alzheimers", 1),
    ("ultra_processed", "depression", 2),
    ("alcohol", "dementia", 1),
    ("smoking", "dementia", 1),
    ("vitamin_b12", "cognitive_decline", 2),
    ("vitamin_d", "depression", 3),
    ("daylight_morning", "depression", 2),
    ("daylight_morning", "sleep_quality", 1),
    ("nighttime_light", "sleep_quality", 1),
    ("magnesium", "sleep_quality", 2),
    ("coffee", "parkinsons", 3),

    # ---- Inflammation / autoimmune / gut ----
    ("ultra_processed", "inflammation", 1),
    ("omega3", "inflammation", 1),
    ("olive_oil", "inflammation", 2),
    ("curcumin", "inflammation", 3),
    ("probiotics", "gut_microbiome", 2),
    ("dairy_fermented", "gut_microbiome", 2),
    ("fiber_soluble", "gut_microbiome", 1),
    ("artificial_sweeteners", "gut_microbiome", 3),

    # ---- Bone / muscle / longevity ----
    ("resistance_training", "sarcopenia", 1),
    ("resistance_training", "osteoporosis", 1),
    ("creatine", "sarcopenia", 2),
    ("vitamin_d", "osteoporosis", 1),
    ("vitamin_k2", "osteoporosis", 3),
    ("walking_daily", "all_cause_mortality", 1),
    ("aerobic_exercise", "all_cause_mortality", 1),
    ("resistance_training", "all_cause_mortality", 1),
    ("sitting_prolonged", "all_cause_mortality", 1),
    ("smoking", "all_cause_mortality", 1),
    ("alcohol", "all_cause_mortality", 1),
    ("nuts", "all_cause_mortality", 2),
    ("olive_oil", "all_cause_mortality", 2),
    ("ultra_processed", "all_cause_mortality", 1),

    # ---- Environmental hazards ----
    ("pm25", "all_cause_mortality", 1),
    ("pm25", "dementia", 2),
    ("pfas", "ckd", 3),
    ("bpa", "insulin_resistance", 4),
    ("microplastics", "inflammation", 4),
    ("noise_chronic", "hypertension", 2),

    # ---- Sleep upstream/downstream ----
    ("sleep_short", "all_cause_mortality", 1),
    ("sleep_short", "obesity", 2),
    ("sleep_short", "depression", 2),
    ("sleep_long", "all_cause_mortality", 3),

    # ---- Metabolic process pairs (mechanism cards) ----
    ("intermittent_fasting", "insulin_resistance", 2),
    ("aerobic_exercise", "insulin_resistance", 2),
    ("resistance_training", "insulin_resistance", 2),
    ("ultra_processed", "insulin_resistance", 2),
    ("fiber_soluble", "insulin_resistance", 2),
    ("sleep_short", "insulin_resistance", 2),
]


def seed_topics() -> tuple[int, int]:
    """Insert entities and seed_topic rows. Idempotent."""
    from db import upsert_entity
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
    print(f"Ensured {n_ent} entities; inserted {n_pairs} new seed pairs "
          f"(of {len(PAIRS)} defined)")
