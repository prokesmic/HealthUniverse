"""Each scenario is a function (persona, client) → list of events.

Events are typed dicts the reviewers will inspect:
  {"kind":"request","method":"GET","path":"/api/...","body":...}
  {"kind":"response","status":200,"body":<json or HTML excerpt>}
  {"kind":"note","text":"..."}

Scenarios deliberately avoid signed-in flows (which require a real
Supabase user + magic-link). They cover what an anonymous user can
do — which is the bulk of the conversion funnel. Signed-in surfaces
(briefing, checkup, risks) have their own renderers that we can
also exercise statelessly via the form path.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from fastapi.testclient import TestClient


def _req(events: list[dict], method: str, path: str, body: Any = None) -> None:
    events.append({"kind": "request", "method": method, "path": path, "body": body})


def _resp(events: list[dict], r) -> None:
    body: Any
    try:
        body = r.json()
    except Exception:
        body = r.text[:1500]
    events.append({"kind": "response", "status": r.status_code, "body": body})


def _note(events: list[dict], text: str) -> None:
    events.append({"kind": "note", "text": text})


# ─── Scenarios ─────────────────────────────────────────────────────


def scenario_browse_corpus(persona: dict, c: TestClient) -> list[dict]:
    """Anonymous corpus browse — home, discoveries, library, an edge."""
    events: list[dict] = []
    _note(events, "Anonymous landing flow; should not require auth.")
    for path in ["/", "/discoveries", "/tier/A", "/trust", "/explore"]:
        _req(events, "GET", path)
        _resp(events, c.get(path))
    # Sample one edge in the persona's interest area, if we can find one.
    cond = (persona.get("conditions") or ["cvd"])[0]
    _req(events, "GET", f"/explore?focus={cond}")
    _resp(events, c.get(f"/explore?focus={cond}"))
    return events


def scenario_stack_brief(persona: dict, c: TestClient) -> list[dict]:
    """Submit the persona's stack, capture the brief output."""
    events: list[dict] = []
    items = ",".join(persona.get("stack") or [])
    path = f"/stack?items={items}"
    _req(events, "GET", path)
    r = c.get(path, follow_redirects=True)
    body_excerpt = r.text[:3000] if "text" in (r.headers.get("content-type") or "") else r.json()
    events.append({"kind": "response", "status": r.status_code, "body": body_excerpt})
    # Synergy API check
    _req(events, "GET", f"/api/me/synergies?stack={items}")
    _resp(events, c.get(f"/api/me/synergies?stack={items}"))
    return events


def scenario_lab_evidence(persona: dict, c: TestClient) -> list[dict]:
    """Walk through each lab in the persona and capture the evidence
    overlay the system returns. This is the per-lab response that
    appears on /me/data when a lab is added."""
    events: list[dict] = []
    for lab in (persona.get("labs") or [])[:6]:
        params = f"?name={lab['name']}&value={lab['value']}&unit={lab['unit']}"
        _req(events, "GET", "/api/me/lab-evidence" + params)
        _resp(events, c.get("/api/me/lab-evidence" + params))
    return events


def scenario_genetic_overlay(persona: dict, c: TestClient) -> list[dict]:
    """For each genetic variant in the persona, capture the SNP
    evidence overlay."""
    events: list[dict] = []
    for v in (persona.get("genetics") or []):
        params = f"?rsid={v['rsid']}&genotype={v['genotype']}"
        _req(events, "GET", "/api/me/snp-evidence" + params)
        _resp(events, c.get("/api/me/snp-evidence" + params))
    if not (persona.get("genetics") or []):
        _note(events, "Persona has no genetic data; scenario skipped.")
    return events


def scenario_stack_analysis(persona: dict, c: TestClient) -> list[dict]:
    """Stack composition + lab-recheck cadence via the anonymous-friendly
    POST endpoint."""
    events: list[dict] = []
    body = {
        "stack_slugs": persona.get("stack") or [],
        "lab_names": [l["name"] for l in (persona.get("labs") or [])],
    }
    _req(events, "POST", "/api/me/stack-analysis", body)
    _resp(events, c.post("/api/me/stack-analysis", json=body))
    return events


def scenario_claim_check(persona: dict, c: TestClient) -> list[dict]:
    """Push a wellness claim through the checker, with the persona's
    context. Pick a claim that's intentionally adjacent to their stack
    so we can see whether the system handles cross-references right."""
    events: list[dict] = []
    claims_by_persona = {
        "P1_biohacker": "Magnesium glycinate cures insomnia",
        "P2_metabolic_at_risk": "Apple cider vinegar before meals lowers blood sugar dramatically",
        "P3_apoe4_carrier": "Lions mane regenerates neurons and prevents Alzheimer's",
        "P4_postmenopausal_osteoporosis": "Bisphosphonates cause more harm than good and should be avoided",
        "P5_polypharmacy_elderly": "All elderly patients should be on a baby aspirin daily",
    }
    claim = claims_by_persona.get(persona["id"], "Vitamin D fixes everything")
    body = {
        "claim": claim,
        "profile_hints": {
            "age": persona.get("age"),
            "sex": persona.get("sex"),
            "conditions": persona.get("conditions") or [],
        },
    }
    _req(events, "POST", "/api/claim-check", body)
    _resp(events, c.post("/api/claim-check", json=body))
    return events


def scenario_challenge_plan(persona: dict, c: TestClient) -> list[dict]:
    """Persona-specific 'I'm thinking about X' challenge mode probe."""
    events: list[dict] = []
    plans_by_persona = {
        "P1_biohacker": "I'm going to add NMN, NR, and methylene blue daily for longevity",
        "P2_metabolic_at_risk": "I'm going to try a 5-day water fast every month and quit drinking",
        "P3_apoe4_carrier": "Given my APOE-ε4 status I want to take low-dose lithium and high-dose DHA",
        "P4_postmenopausal_osteoporosis": "I want to skip the bisphosphonate my doctor offered and use bone broth + strontium instead",
        "P5_polypharmacy_elderly": "I want to stop my PPI and statin without telling my doctor",
    }
    plan = plans_by_persona.get(persona["id"], "I'm going to start a 7-day water fast")
    body = {"plan": plan}
    _req(events, "POST", "/api/me/challenge", body)
    _resp(events, c.post("/api/me/challenge", json=body))
    return events


def scenario_risk_projection(persona: dict, c: TestClient) -> list[dict]:
    """Compute ASCVD + FINDRISC for the persona."""
    events: list[dict] = []
    # Pull what we can from the persona's labs.
    by_name = {l["name"].lower(): l for l in (persona.get("labs") or [])}
    def _v(*candidates):
        for c in candidates:
            for k, lab in by_name.items():
                if c in k:
                    return lab["value"]
        return None
    body = {
        "age": persona.get("age"),
        "sex": persona.get("sex"),
        "race": persona.get("race") or "white",
        "total_cholesterol": _v("ldl") and (_v("ldl") + (_v("hdl") or 50) + (_v("triglycer") or 100)/5),
        "hdl": _v("hdl"),
        "systolic_bp": 130,
        "bp_treated": "ace_inhibitors" in (persona.get("stack") or []),
        "smoker": False,
        "diabetes": "t2d" in (persona.get("conditions") or []),
        "bmi": 27,
        "waist_cm": 95 if persona.get("sex") == "M" else 84,
        "family_diabetes": "first_degree" if "t2d" in (persona.get("conditions") or []) else "none",
        "physical_activity_30min_daily": True,
        "eats_vegetables_or_fruit_daily": True,
        "on_bp_medication": "ace_inhibitors" in (persona.get("stack") or []),
        "ever_high_blood_glucose": (_v("hba1c") or 5.0) >= 5.7,
    }
    if body["total_cholesterol"] is None or body["hdl"] is None:
        # Use sensible defaults if labs lack key fields.
        body["total_cholesterol"] = 200
        body["hdl"] = 50
    _req(events, "POST", "/api/me/risk-projection", body)
    _resp(events, c.post("/api/me/risk-projection", json=body))
    return events


SCENARIOS: dict[str, Callable[[dict, TestClient], list[dict]]] = {
    "browse_corpus":    scenario_browse_corpus,
    "stack_brief":      scenario_stack_brief,
    "lab_evidence":     scenario_lab_evidence,
    "genetic_overlay":  scenario_genetic_overlay,
    "stack_analysis":   scenario_stack_analysis,
    "claim_check":      scenario_claim_check,
    "challenge_plan":   scenario_challenge_plan,
    "risk_projection":  scenario_risk_projection,
}
