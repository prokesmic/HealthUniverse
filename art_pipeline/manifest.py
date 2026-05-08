"""Cached-art manifest — single source of truth for which edges have a
rendered image and where to find it.

File: data/art_manifest.json
Schema:
{
  "version": 1,
  "entries": {
    "<key>": {
      "edge_id":         12,
      "factor_slug":     "fiber",
      "outcome_slug":    "cvd",
      "kind":            "featured" | "discovery",
      "prompt_provider": "heuristic" | "gemma",
      "renderer":        "drawthings" | "manual" | "none",
      "model":           "qwen-image-8bit" | …,
      "prompt":          "...",
      "seed":            42,
      "scene":           "wave",
      "tone":            "calm",
      "palette":         "cream-forest",
      "size":            [800, 520],
      "output_path":     "/static/art/fiber__cvd__featured.webp",
      "updated_at":      "2026-05-08T12:34:56",
      "qa_status":       "approved" | "needs_review" | "regenerate" | null
    }
  }
}

The manifest itself is portable JSON, line-stable, and safe to diff in
git. All writes are atomic (tmp file + os.replace) so partial runs
can't leave the manifest corrupt.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).parent.parent / "data" / "art_manifest.json"
SCHEMA_VERSION = 1


def manifest_key(factor_slug: str, outcome_slug: str, kind: str) -> str:
    """Stable key used inside manifest['entries']."""
    return f"{factor_slug}__{outcome_slug}__{kind}"


def load_manifest(path: Path | str | None = None) -> dict[str, Any]:
    """Load (or create empty) manifest. Never raises on missing file."""
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        return {"version": SCHEMA_VERSION, "entries": {}}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError:
        return {"version": SCHEMA_VERSION, "entries": {}}
    data.setdefault("version", SCHEMA_VERSION)
    data.setdefault("entries", {})
    return data


def save_manifest(manifest: dict[str, Any], path: Path | str | None = None) -> Path:
    """Atomic write: dump to .tmp, then os.replace. Returns final path."""
    p = Path(path) if path else DEFAULT_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    os.replace(tmp, p)
    return p


def upsert_entry(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    """Add or update one entry in-place. Validates required fields."""
    required = ("edge_id", "factor_slug", "outcome_slug", "kind", "output_path")
    missing = [k for k in required if entry.get(k) is None]
    if missing:
        raise ValueError(f"manifest entry missing fields: {missing}")
    key = manifest_key(entry["factor_slug"], entry["outcome_slug"], entry["kind"])
    manifest.setdefault("entries", {})
    manifest["entries"][key] = entry


def lookup_entry(manifest: dict[str, Any], factor_slug: str,
                 outcome_slug: str, kind: str) -> dict | None:
    return manifest.get("entries", {}).get(
        manifest_key(factor_slug, outcome_slug, kind))
