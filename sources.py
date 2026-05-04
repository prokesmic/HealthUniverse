"""Source registry. Trust weights are 0..2; 1.0 is the neutral default.
Higher = more authoritative. Used to weight evidence during edge re-scoring."""
from __future__ import annotations

from db import connect, upsert_source

SOURCES: list[dict] = [
    # Top-tier evidence synthesis
    {"slug": "cochrane",         "name": "Cochrane Library",        "kind": "registry", "trust_weight": 2.0, "homepage": "https://www.cochranelibrary.com"},
    {"slug": "uptodate",         "name": "UpToDate",                "kind": "registry", "trust_weight": 1.8, "homepage": "https://www.uptodate.com"},
    # Core literature databases
    {"slug": "pubmed",           "name": "PubMed / MEDLINE",        "kind": "registry", "trust_weight": 1.4, "homepage": "https://pubmed.ncbi.nlm.nih.gov"},
    {"slug": "europepmc",        "name": "Europe PMC",              "kind": "registry", "trust_weight": 1.4, "homepage": "https://europepmc.org"},
    {"slug": "biorxiv",          "name": "bioRxiv",                 "kind": "preprint", "trust_weight": 0.7, "homepage": "https://www.biorxiv.org", "notes": "Preprint, not peer reviewed"},
    {"slug": "medrxiv",          "name": "medRxiv",                 "kind": "preprint", "trust_weight": 0.7, "homepage": "https://www.medrxiv.org"},
    # High-impact journals
    {"slug": "nejm",             "name": "New England Journal of Medicine", "kind": "journal", "trust_weight": 1.8, "homepage": "https://www.nejm.org"},
    {"slug": "lancet",           "name": "The Lancet",              "kind": "journal", "trust_weight": 1.8, "homepage": "https://www.thelancet.com"},
    {"slug": "jama",             "name": "JAMA",                    "kind": "journal", "trust_weight": 1.7, "homepage": "https://jamanetwork.com"},
    {"slug": "bmj",              "name": "BMJ",                     "kind": "journal", "trust_weight": 1.7, "homepage": "https://www.bmj.com"},
    {"slug": "nature_medicine",  "name": "Nature Medicine",         "kind": "journal", "trust_weight": 1.7, "homepage": "https://www.nature.com/nm"},
    {"slug": "ajcn",             "name": "American Journal of Clinical Nutrition", "kind": "journal", "trust_weight": 1.5, "homepage": "https://academic.oup.com/ajcn"},
    {"slug": "circulation",      "name": "Circulation",             "kind": "journal", "trust_weight": 1.6, "homepage": "https://www.ahajournals.org/journal/circ"},
    {"slug": "diabetes_care",    "name": "Diabetes Care",           "kind": "journal", "trust_weight": 1.5, "homepage": "https://diabetesjournals.org/care"},
    # Regulators / agencies
    {"slug": "who",              "name": "World Health Organization", "kind": "agency", "trust_weight": 1.6, "homepage": "https://www.who.int"},
    {"slug": "fda",              "name": "U.S. FDA",                "kind": "agency", "trust_weight": 1.5, "homepage": "https://www.fda.gov"},
    {"slug": "ema",              "name": "European Medicines Agency","kind": "agency", "trust_weight": 1.5, "homepage": "https://www.ema.europa.eu"},
    {"slug": "efsa",             "name": "European Food Safety Authority", "kind": "agency", "trust_weight": 1.5, "homepage": "https://www.efsa.europa.eu"},
    {"slug": "nih_ods",          "name": "NIH Office of Dietary Supplements", "kind": "agency", "trust_weight": 1.5, "homepage": "https://ods.od.nih.gov"},
    {"slug": "iarc",             "name": "IARC (WHO cancer agency)","kind": "agency", "trust_weight": 1.6, "homepage": "https://www.iarc.who.int"},
    {"slug": "cdc",              "name": "U.S. CDC",                "kind": "agency", "trust_weight": 1.4, "homepage": "https://www.cdc.gov"},
    # Long cohorts (often cited)
    {"slug": "ukbiobank",        "name": "UK Biobank",              "kind": "registry", "trust_weight": 1.3, "homepage": "https://www.ukbiobank.ac.uk"},
    {"slug": "framingham",       "name": "Framingham Heart Study",  "kind": "registry", "trust_weight": 1.3, "homepage": "https://www.framinghamheartstudy.org"},
    {"slug": "nhs_cohort",       "name": "Nurses' Health Study",    "kind": "registry", "trust_weight": 1.3, "homepage": "https://nurseshealthstudy.org"},
    # Press (low weight, used for novelty signals only)
    {"slug": "sciencedaily",     "name": "ScienceDaily",            "kind": "press",   "trust_weight": 0.4, "homepage": "https://www.sciencedaily.com"},
    {"slug": "statnews",         "name": "STAT News",               "kind": "press",   "trust_weight": 0.6, "homepage": "https://www.statnews.com"},
]


def seed_sources() -> int:
    with connect() as conn:
        for s in SOURCES:
            upsert_source(
                conn,
                slug=s["slug"],
                name=s["name"],
                kind=s["kind"],
                trust_weight=s["trust_weight"],
                homepage=s.get("homepage", ""),
                notes=s.get("notes", ""),
            )
    return len(SOURCES)


if __name__ == "__main__":
    n = seed_sources()
    print(f"Seeded {n} sources")
