"""Prompt generation for art jobs.

Two providers:

  • heuristic  — pure-Python rule-based builder using factor/outcome
                 kinds + tier + direction. Always available, no
                 external dependency. Default.

  • gemma      — does NOT call Gemma directly (deliberately portable).
                 Instead, reads a prompt JSON file produced by Gemma
                 on a separate machine and merges its `prompt`,
                 `scene`, `palette`, `tone`, `composition` fields
                 into the heuristic baseline.

Either way, every job carries a structured prompt:
  {
    "scene":       e.g. "wave" | "mediterranean" | "supplement"
    "palette":     e.g. "cream-forest" | "ochre-sage"
    "tone":        e.g. "calm" | "alert" | "neutral"
    "composition": e.g. "centered subject + soft horizon"
    "prompt":      free-text prompt fed to the renderer
  }
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------------
# Style vocabulary — kept small so prompts stay coherent across the corpus.
# ----------------------------------------------------------------------------

PALETTE_BY_DIRECTION = {
    "protective": "cream-forest",   # warm cream + deep green
    "harmful":    "ochre-rust",     # gold + burnt-orange caution
    "u_shaped":   "cream-amber",    # cream + amber middle-ground
    "mixed":      "cream-sage",     # cream + muted sage
    "neutral":    "cream-stone",    # cream + grey-stone
}
TONE_BY_DIRECTION = {
    "protective": "calm-confident",
    "harmful":    "serious-cautionary",
    "u_shaped":   "balanced-thoughtful",
    "mixed":      "neutral-reflective",
    "neutral":    "quiet-factual",
}

# Scene picker keyed on outcome kind / slug stem
def _pick_scene(factor_slug: str, factor_kind: str | None,
                outcome_slug: str, outcome_kind: str | None) -> str:
    f, o = factor_slug or "", outcome_slug or ""
    if any(t in o for t in ("cvd", "myocardial", "stroke", "heart")):
        return "heart-currents"
    if any(t in o for t in ("cancer", "carcinoma", "leukemia", "lymphoma")):
        return "cellular-tides"
    if any(t in o for t in ("dementia", "alzheimer", "cognitive", "parkinson")):
        return "brain-constellation"
    if any(t in o for t in ("sleep", "insomnia", "rem")):
        return "moonlit-stillness"
    if any(t in o for t in ("depression", "anxiety", "ptsd", "mental")):
        return "soft-horizon-figure"
    if any(t in f for t in ("fish", "omega")):
        return "ocean-currents"
    if any(t in f for t in ("vegetable", "fruit", "leafy", "berry", "olive")):
        return "still-life-botanical"
    if any(t in f for t in ("statin", "metformin", "ssri", "antibiotic")):
        return "supplement-line-art"
    if any(t in f for t in ("walking", "running", "exercise", "training")):
        return "motion-light-trail"
    if any(t in f for t in ("alcohol", "smoking", "cigarette")):
        return "smoke-and-glass"
    return "wave-form-abstract"


def _pick_composition(scene: str) -> str:
    return {
        "heart-currents":        "centred subject, gentle radial currents, low horizon",
        "cellular-tides":        "abstract cellular pattern, soft focus, full bleed",
        "brain-constellation":   "stylised neural arcs over deep field, gold dots",
        "moonlit-stillness":     "low horizon, single soft moon, layered silhouettes",
        "soft-horizon-figure":   "single contemplative figure, dawn horizon, minimalism",
        "ocean-currents":        "flowing ribbon waves, top-down perspective",
        "still-life-botanical":  "Vermeer-style still life, single ingredient hero",
        "supplement-line-art":   "isometric pill / glass, warm-cream backdrop",
        "motion-light-trail":    "long-exposure light trails, side profile",
        "smoke-and-glass":       "a single glass / wisp, deep amber light",
        "wave-form-abstract":    "horizontal wave-form, gradient horizon, sparse detail",
    }.get(scene, "centred subject, soft horizon")


def build_heuristic_prompt(*, edge_id: int, factor_slug: str, factor_name: str,
                           factor_kind: str | None, outcome_slug: str,
                           outcome_name: str, outcome_kind: str | None,
                           tier: str, direction: str,
                           kind: str = "featured",
                           seed: int | None = None) -> dict:
    """Return a structured prompt dict for one edge.
    Deterministic given the same inputs (seed default = edge_id)."""
    scene = _pick_scene(factor_slug, factor_kind, outcome_slug, outcome_kind)
    palette = PALETTE_BY_DIRECTION.get(direction, "cream-stone")
    tone = TONE_BY_DIRECTION.get(direction, "quiet-factual")
    composition = _pick_composition(scene)
    aspect = "16:9 (800x520)" if kind == "featured" else "1:1 (480x480)"
    text = (
        f"Editorial photograph in the style of a 2026 Atlantic Health "
        f"feature: {scene.replace('-', ' ')}. {composition}. "
        f"Subject hints: {factor_name} and {outcome_name}. "
        f"Palette: {palette}. Tone: {tone}. Soft natural light, "
        f"shallow depth of field, no text overlay, no watermark, "
        f"no logos, no celebrity faces. Aspect {aspect}."
    )
    return {
        "scene":       scene,
        "palette":     palette,
        "tone":        tone,
        "composition": composition,
        "prompt":      text,
        "seed":        seed if seed is not None else (edge_id * 7919 % 2**31),
    }


# ----------------------------------------------------------------------------
# External / Gemma merge — read prompts produced on another machine.
# ----------------------------------------------------------------------------

def merge_external_prompts(jobs: list[dict], external_path: str | Path) -> list[dict]:
    """Merge external prompt JSON into the in-memory job list.

    External file shape (line-stable JSON, easy to inspect):

        {
          "12": {
            "scene": "wave-form-abstract",
            "palette": "cream-forest",
            "tone": "calm-confident",
            "composition": "...",
            "prompt": "...",
            "seed": 42
          },
          ...
        }

    Keys are stringified edge_id. Missing fields fall back to whatever
    the heuristic builder wrote. Unknown keys are ignored. This means
    Gemma can write a partial override (e.g. just the prompt text) and
    the rest still works.
    """
    p = Path(external_path)
    if not p.exists():
        raise FileNotFoundError(f"external prompts file not found: {p}")
    try:
        ext = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"could not parse {p}: {exc}") from exc

    OVERRIDABLE = ("scene", "palette", "tone", "composition", "prompt", "seed")
    for job in jobs:
        eid = str(job.get("edge_id"))
        override = ext.get(eid)
        if not isinstance(override, dict):
            continue
        for k in OVERRIDABLE:
            if k in override and override[k] not in (None, ""):
                job[k] = override[k]
        job["prompt_provider"] = "gemma"
    return jobs
