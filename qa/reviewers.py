"""Reviewer prompts.

Each reviewer is a Claude call with a specific lens. Input: a structured
transcript chunk (persona, scenario, request, response). Output: JSON
list of findings { severity, category, headline, evidence, suggestion }.

Severity scale:
  P0 — safety / clinical harm (must fix)
  P1 — clear correctness or trust issue (high priority)
  P2 — UX / completeness gap (next sprint)
  P3 — nice-to-have polish
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional


def _claude_call(system: str, user: str, max_tokens: int = 900) -> Optional[str]:
    """Single Claude Haiku call. Returns text or None on failure."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        from anthropic import Anthropic
        client = Anthropic()
        resp = client.messages.create(
            model=os.environ.get("HU_QA_MODEL", "claude-haiku-4-5"),
            max_tokens=max_tokens,
            temperature=0.1,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    except Exception as exc:
        print(f"[reviewer] {exc}")
        return None


def _extract_findings(text: Optional[str]) -> list[dict]:
    """Pull the JSON-array of findings out of a reviewer response."""
    if not text:
        return []
    # Prefer fenced code block; fall back to first JSON-looking array.
    m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    raw = m.group(1) if m else None
    if not raw:
        m = re.search(r"(\[[\s\S]*?\])", text)
        raw = m.group(1) if m else None
    if not raw:
        return []
    try:
        rows = json.loads(raw)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


# ─── Reviewer prompts ──────────────────────────────────────────────


TECHNICAL_SYSTEM = (
    "You are a technical QA reviewer for a FastAPI + JS health app. "
    "You inspect HTTP request/response transcripts and flag: wrong "
    "status codes, schema drift, exception leakage, broken endpoints, "
    "stack traces in responses, missing CORS / auth handling, slow "
    "responses, or anything an engineer would call a bug. "
    "Return a JSON ARRAY of findings, each: "
    '{"severity":"P0|P1|P2|P3","category":"technical",'
    '"headline":"short","evidence":"copy the exact request+response snippet",'
    '"suggestion":"specific code change"}. '
    "Return [] if nothing meaningful. No prose, JSON only."
)

MEDICAL_SYSTEM = (
    "You are a board-certified internal-medicine reviewer for a "
    "consumer health-evidence product. You inspect what the product "
    "returned to a specific patient persona and flag: unsafe advice, "
    "missing contraindications, dangerous drug-supplement interactions, "
    "incorrect mechanism claims, age/sex/condition mismatches, off-label "
    "presented as standard, or tier assignments that don't match "
    "established guidelines (USPSTF, ACC/AHA, ADA, GRADE). "
    "Persona context is included; use it. "
    "Return a JSON ARRAY of findings, each: "
    '{"severity":"P0|P1|P2|P3","category":"medical",'
    '"headline":"short","evidence":"what specifically was wrong",'
    '"suggestion":"specific clinical-correctness change"}. '
    "Return [] if nothing meaningful. No prose, JSON only. "
    "Be honest; flag P0s when warranted."
)

EVIDENCE_SYSTEM = (
    "You are an evidence-synthesis reviewer. You inspect product "
    "outputs that cite the corpus (edge labels, tier assignments, "
    "direction labels, PMIDs, mechanism notes) and flag: tier inflation "
    "(claiming A when GRADE would say B/C), direction errors, mismatch "
    "between cited PMID and the actual claim, missing counter-evidence, "
    "or 'protective' classifications for u-shaped/mixed relationships. "
    "Return a JSON ARRAY of findings, each: "
    '{"severity":"P0|P1|P2|P3","category":"evidence",'
    '"headline":"short","evidence":"specific edge/PMID/quote",'
    '"suggestion":"specific corpus change"}. '
    "Return [] if nothing meaningful. JSON only."
)

PRIVACY_SYSTEM = (
    "You are a privacy + safety reviewer. You inspect transcripts and "
    "flag: PHI leakage to server logs, user data accidentally in URLs, "
    "weak disclaimers, claim creep (product saying 'do X' instead of "
    "'evidence suggests X — discuss with clinician'), missing 'this is "
    "not medical advice', dark patterns, or anything that crosses into "
    "clinical decision support without proper guard-rails. "
    "Return a JSON ARRAY of findings, each: "
    '{"severity":"P0|P1|P2|P3","category":"privacy",'
    '"headline":"short","evidence":"specific quote/leak",'
    '"suggestion":"specific change"}. '
    "Return [] if nothing meaningful. JSON only."
)

UX_SYSTEM = (
    "You are a UX reviewer. You inspect product responses + descriptions "
    "and flag: confusing empty states, jargon without explanation, broken "
    "or missing CTAs, redundant or contradicting recommendations, dead-end "
    "flows, inconsistent terminology, and accessibility issues you can "
    "detect from the HTML/text. "
    "Return a JSON ARRAY of findings, each: "
    '{"severity":"P0|P1|P2|P3","category":"ux",'
    '"headline":"short","evidence":"specific quote",'
    '"suggestion":"specific copy or interaction change"}. '
    "Return [] if nothing meaningful. JSON only."
)


def _format_transcript(persona: dict, scenario_name: str, events: list[dict]) -> str:
    """Render an event log into a tight prompt-friendly transcript."""
    lines = [
        f"PERSONA: {persona.get('id')} — {persona.get('label')}",
        f"  age={persona.get('age')} sex={persona.get('sex')} conditions={persona.get('conditions')}",
        f"  expected concerns: {persona.get('expected_concerns') or '(none flagged a priori)'}",
        f"SCENARIO: {scenario_name}",
        "TRANSCRIPT:",
    ]
    for ev in events:
        kind = ev.get("kind", "?")
        if kind == "request":
            lines.append(f"  → {ev.get('method','GET')} {ev.get('path')} body={_short(ev.get('body'))}")
        elif kind == "response":
            lines.append(f"  ← {ev.get('status')} {_short(ev.get('body'), 1200)}")
        elif kind == "note":
            lines.append(f"  · {ev.get('text','')}")
    return "\n".join(lines)


def _short(obj: Any, limit: int = 400) -> str:
    if obj is None:
        return ""
    if isinstance(obj, (dict, list)):
        s = json.dumps(obj, ensure_ascii=False)
    else:
        s = str(obj)
    if len(s) > limit:
        return s[:limit] + "…"
    return s


REVIEWERS = {
    "technical": TECHNICAL_SYSTEM,
    "medical":   MEDICAL_SYSTEM,
    "evidence":  EVIDENCE_SYSTEM,
    "privacy":   PRIVACY_SYSTEM,
    "ux":        UX_SYSTEM,
}


def review(reviewer_name: str, persona: dict, scenario: str, events: list[dict]) -> list[dict]:
    """Run a single reviewer over one persona's scenario transcript."""
    system = REVIEWERS.get(reviewer_name)
    if not system:
        return []
    transcript = _format_transcript(persona, scenario, events)
    text = _claude_call(system, transcript)
    findings = _extract_findings(text)
    # Stamp each finding with reviewer / persona / scenario for the report.
    for f in findings:
        f["reviewer"] = reviewer_name
        f["persona"] = persona.get("id")
        f["scenario"] = scenario
    return findings
