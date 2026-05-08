"""Optional QA / review pass.

Two sources, either or both:

  • Heuristic — run by the repo: image exists, file size > 5 KB,
    not a 0-byte placeholder. Marks failures as 'regenerate'.
    Everything else passes silently as 'approved'.

  • External (Gemma) — JSON files dropped in art_jobs/reviews/ with shape:
        { "<key>": { "qa_status": "approved" | "needs_review" | "regenerate",
                     "reason": "..." }, ... }
    where <key> is the manifest key (factor__outcome__kind).
    These override heuristic decisions when both are present.

Reviews are applied to the manifest in-place and persisted via
manifest.save_manifest().
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from .manifest import manifest_key
from .jobs import REVIEWS_DIR, ROOT, STATIC_ART

VALID_STATUSES = {"approved", "needs_review", "regenerate"}


def heuristic_review(entry: dict) -> tuple[str, str]:
    """Return (qa_status, reason) from a manifest entry."""
    out = entry.get("output_path", "")
    if not out:
        return ("regenerate", "no output_path on entry")
    # Resolve relative to repo root (output_path is "/static/art/...")
    p = ROOT / "web" / out.lstrip("/")
    if not p.exists():
        return ("regenerate", f"image file missing: {p.name}")
    size = p.stat().st_size
    if size < 5_000:
        return ("regenerate", f"file too small ({size} bytes), likely empty")
    return ("approved", "heuristic check passed")


def load_reviews(reviews_dir: Path | None = None) -> dict[str, dict]:
    """Merge every JSON file in art_jobs/reviews/ into one dict keyed by
    manifest_key. Later files override earlier ones."""
    src = Path(reviews_dir) if reviews_dir else REVIEWS_DIR
    if not src.exists():
        return {}
    merged: dict[str, dict] = {}
    for f in sorted(src.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        for key, val in data.items():
            if not isinstance(val, dict):
                continue
            status = val.get("qa_status")
            if status not in VALID_STATUSES:
                continue
            merged[key] = {"qa_status": status,
                           "reason": val.get("reason", ""),
                           "source_file": f.name}
    return merged


def apply_reviews(manifest: dict[str, Any],
                  external: dict[str, dict] | None = None,
                  run_heuristic: bool = True) -> dict[str, int]:
    """Mutate manifest in place: write qa_status onto every entry.
    External reviews take priority over heuristic ones.
    Returns a count summary like {'approved': N, 'needs_review': M, ...}."""
    counts: dict[str, int] = {"approved": 0, "needs_review": 0,
                              "regenerate": 0, "unset": 0}
    ext = external or {}
    for key, entry in manifest.get("entries", {}).items():
        status, reason = (None, None)
        if key in ext:
            status = ext[key]["qa_status"]
            reason = ext[key].get("reason", "")
            entry["qa_source"] = "external"
        elif run_heuristic:
            status, reason = heuristic_review(entry)
            entry["qa_source"] = "heuristic"
        if status:
            entry["qa_status"] = status
            entry["qa_reason"] = reason
            counts[status] = counts.get(status, 0) + 1
        else:
            counts["unset"] += 1
    return counts
