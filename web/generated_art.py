"""Cached-art adapter for templates.

Templates already call featured_card_svg(...) and discovery_card_svg(...)
as Jinja globals. We register OVERRIDES from this module so each call
becomes:

  1. look up (factor_slug, outcome_slug, kind) in data/art_manifest.json
  2. if there's an entry whose qa_status != 'regenerate' AND the file
     actually exists on disk → return an <img> snippet
  3. otherwise fall back to the procedural SVG from web/illustrations.py

No image generation happens here. Manifest is loaded once and cached
in-process; reload by restarting the server (acceptable since updates
are batch jobs, not per-request).

This module is a thin facade — the heavy lifting (prompt generation,
Draw Things workflow, manifest writing) lives in the art_pipeline/
package and the generate_edge_art.py CLI.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

# Procedural SVG fallback — always available, never depends on the manifest.
from . import illustrations as _illus

# Repo-relative paths
_ROOT = Path(__file__).parent.parent
_STATIC_ART = _ROOT / "web" / "static" / "art"

# Lazy-loaded singleton manifest
_MANIFEST_CACHE: dict[str, Any] | None = None


def _load_manifest() -> dict[str, Any]:
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is not None:
        return _MANIFEST_CACHE
    try:
        from art_pipeline.manifest import load_manifest as _lm
        _MANIFEST_CACHE = _lm()
    except Exception:
        _MANIFEST_CACHE = {"version": 1, "entries": {}}
    return _MANIFEST_CACHE


def reload_manifest() -> None:
    """Force a re-read on next call — useful after `import` / `review`."""
    global _MANIFEST_CACHE
    _MANIFEST_CACHE = None


def _lookup(factor_slug: str, outcome_slug: str, kind: str) -> dict | None:
    m = _load_manifest()
    key = f"{factor_slug}__{outcome_slug}__{kind}"
    entry = m.get("entries", {}).get(key)
    if not entry:
        return None
    if entry.get("qa_status") == "regenerate":
        return None
    out = entry.get("output_path", "")
    if not out:
        return None
    full = _ROOT / "web" / out.lstrip("/")
    if not full.exists():
        return None
    return entry


def _img_html(entry: dict, *, w: int, h: int, alt: str = "") -> str:
    """Render the manifest entry as an <img> tag matching the visual
    footprint the SVG would have produced."""
    src = entry["output_path"]
    return (
        f'<img src="{src}" width="{w}" height="{h}" alt="{alt}" '
        f'loading="lazy" decoding="async" '
        f'class="card-art card-art-{entry.get("kind","featured")}" '
        f'style="width:100%;height:100%;object-fit:cover;display:block">'
    )


# ----------------------------------------------------------------------------
# Public API — same signatures as illustrations.featured_card_svg etc.
# Templates and Jinja globals call these by the same names; the wrapper
# decides whether to return cached image HTML or the procedural SVG.
# ----------------------------------------------------------------------------

def featured_card_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
                      factor_kind: str | None = None,
                      outcome_kind: str | None = None,
                      w: int = 800, h: int = 520) -> str:
    entry = _lookup(factor_slug, outcome_slug, "featured")
    if entry:
        return _img_html(entry, w=w, h=h,
                         alt=f"{factor_slug.replace('_',' ')} and "
                             f"{outcome_slug.replace('_',' ')}")
    return _illus.featured_card_svg(
        factor_slug=factor_slug, outcome_slug=outcome_slug, tier=tier,
        factor_kind=factor_kind, outcome_kind=outcome_kind, w=w, h=h)


def discovery_card_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
                       factor_kind: str | None = None,
                       outcome_kind: str | None = None,
                       w: int = 480, h: int = 240) -> str:
    entry = _lookup(factor_slug, outcome_slug, "discovery")
    if entry:
        return _img_html(entry, w=w, h=h,
                         alt=f"{factor_slug.replace('_',' ')} and "
                             f"{outcome_slug.replace('_',' ')}")
    return _illus.discovery_card_svg(
        factor_slug=factor_slug, outcome_slug=outcome_slug, tier=tier,
        factor_kind=factor_kind, outcome_kind=outcome_kind, w=w, h=h)


# Pass-through — these don't have cached variants today; site uses SVG.
def edge_svg(*, factor_slug: str, outcome_slug: str, tier: str = "C",
             factor_kind: str | None = None, outcome_kind: str | None = None,
             w: int = 460, h: int = 220) -> str:
    return _illus.edge_svg(factor_slug=factor_slug, outcome_slug=outcome_slug,
                           tier=tier, factor_kind=factor_kind,
                           outcome_kind=outcome_kind, w=w, h=h)


def hero_svg() -> str:
    return _illus.hero_svg()


def strength_wave_svg(*, tier: str) -> str:
    return _illus.strength_wave_svg(tier=tier)
