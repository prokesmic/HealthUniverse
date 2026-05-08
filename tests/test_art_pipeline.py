"""Tests for the portable art pipeline.

Covers:
  • manifest read / write + atomic upsert
  • prompt builder (heuristic) determinism
  • Gemma external-prompt merge
  • job export → import round trip
  • review heuristic + external priority
  • site fallback: when no manifest entry, SVG is returned;
                   when entry exists + image on disk, <img> is returned.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from art_pipeline import (                                           # noqa: E402
    load_manifest, save_manifest, manifest_key,
    build_heuristic_prompt, merge_external_prompts,
    write_prompt_job, scan_done_renders,
    load_reviews, apply_reviews,
)
from art_pipeline.manifest import upsert_entry, SCHEMA_VERSION       # noqa: E402
from art_pipeline import jobs as jobs_mod                            # noqa: E402
from art_pipeline import review as review_mod                        # noqa: E402


# ── manifest ──────────────────────────────────────────────────────────

def test_manifest_load_missing_file_returns_empty(tmp_path):
    p = tmp_path / "art_manifest.json"
    m = load_manifest(p)
    assert m == {"version": SCHEMA_VERSION, "entries": {}}


def test_manifest_save_then_load_round_trip(tmp_path):
    p = tmp_path / "art_manifest.json"
    m = {"version": 1, "entries": {"a__b__featured": {"x": 1}}}
    save_manifest(m, p)
    out = load_manifest(p)
    assert out["entries"]["a__b__featured"]["x"] == 1


def test_manifest_save_is_atomic_and_pretty(tmp_path):
    p = tmp_path / "art_manifest.json"
    save_manifest({"version": 1, "entries": {}}, p)
    text = p.read_text()
    # Pretty-printed (indent=2) and sorted keys for stable diffs
    assert text.startswith("{") and "\n  " in text


def test_upsert_entry_validates_required_fields():
    m = {"version": 1, "entries": {}}
    with pytest.raises(ValueError):
        upsert_entry(m, {"factor_slug": "x"})        # missing edge_id etc.


def test_upsert_entry_writes_under_canonical_key():
    m = {"version": 1, "entries": {}}
    upsert_entry(m, {
        "edge_id": 12, "factor_slug": "f", "outcome_slug": "o",
        "kind": "featured", "output_path": "/static/art/f__o__featured.webp",
    })
    assert "f__o__featured" in m["entries"]
    assert m["entries"]["f__o__featured"]["edge_id"] == 12


# ── prompts ───────────────────────────────────────────────────────────

def test_heuristic_prompt_is_deterministic():
    a = build_heuristic_prompt(
        edge_id=42, factor_slug="fiber", factor_name="Dietary fibre",
        factor_kind="nutrient", outcome_slug="cvd",
        outcome_name="CVD", outcome_kind="condition",
        tier="A", direction="protective")
    b = build_heuristic_prompt(
        edge_id=42, factor_slug="fiber", factor_name="Dietary fibre",
        factor_kind="nutrient", outcome_slug="cvd",
        outcome_name="CVD", outcome_kind="condition",
        tier="A", direction="protective")
    assert a == b


def test_heuristic_prompt_carries_required_fields():
    p = build_heuristic_prompt(
        edge_id=1, factor_slug="x", factor_name="X", factor_kind="behavior",
        outcome_slug="y", outcome_name="Y", outcome_kind="condition",
        tier="C", direction="harmful")
    for k in ("scene", "palette", "tone", "composition", "prompt", "seed"):
        assert k in p
    assert "Y" in p["prompt"]                # outcome name interpolated


def test_gemma_merge_overrides_only_supplied_fields(tmp_path):
    base = build_heuristic_prompt(
        edge_id=12, factor_slug="f", factor_name="F", factor_kind="food",
        outcome_slug="o", outcome_name="O", outcome_kind="condition",
        tier="B", direction="protective")
    job = {"edge_id": 12, **base}
    ext = tmp_path / "g.json"
    ext.write_text(json.dumps({
        "12": {"prompt": "Custom Gemma prompt", "seed": 999}
    }))
    merge_external_prompts([job], ext)
    assert job["prompt"] == "Custom Gemma prompt"
    assert job["seed"] == 999
    assert job["scene"] == base["scene"]      # untouched
    assert job["prompt_provider"] == "gemma"


def test_gemma_merge_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        merge_external_prompts([], tmp_path / "nope.json")


# ── jobs export/import ────────────────────────────────────────────────

def test_write_prompt_job_uses_deterministic_filename(tmp_path):
    job = {"edge_id": 7, "factor_slug": "f", "outcome_slug": "o",
           "kind": "featured", "prompt": "...", "seed": 1}
    written = write_prompt_job(job, dest=tmp_path)
    assert written.exists()
    assert "f__o__featured" in written.name
    data = json.loads(written.read_text())
    assert data["schema_version"] == 1
    assert data["edge_id"] == 7


def test_scan_done_renders_pairs_image_with_sidecar(tmp_path, monkeypatch):
    done = tmp_path / "done"; done.mkdir()
    img = done / "fiber__cvd__featured.webp"
    img.write_bytes(b"\x00" * 6000)
    sidecar = done / "fiber__cvd__featured.json"
    sidecar.write_text(json.dumps({
        "edge_id": 12, "factor_slug": "fiber", "outcome_slug": "cvd",
        "kind": "featured", "prompt": "x", "seed": 1,
        "output_filename": "fiber__cvd__featured.webp",
    }))
    monkeypatch.setattr(jobs_mod, "DONE_DIR", done)
    monkeypatch.setattr(jobs_mod, "PROMPTS_DIR", tmp_path / "prompts_unused")
    found = list(scan_done_renders())
    assert len(found) == 1
    assert found[0]["job"]["edge_id"] == 12
    assert found[0]["image_path"] == img


def test_scan_done_renders_falls_back_to_filename_when_no_sidecar(tmp_path, monkeypatch):
    done = tmp_path / "done"; done.mkdir()
    (done / "fiber__cvd__featured.webp").write_bytes(b"\x00" * 6000)
    monkeypatch.setattr(jobs_mod, "DONE_DIR", done)
    monkeypatch.setattr(jobs_mod, "PROMPTS_DIR", tmp_path / "prompts_empty")
    found = list(scan_done_renders())
    assert found and found[0]["job"]["factor_slug"] == "fiber"
    assert found[0]["job"]["outcome_slug"] == "cvd"
    assert found[0]["job"]["kind"] == "featured"


# ── review ────────────────────────────────────────────────────────────

def test_heuristic_review_flags_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "ROOT", tmp_path)
    entry = {"output_path": "/static/art/missing.webp"}
    status, reason = review_mod.heuristic_review(entry)
    assert status == "regenerate"
    assert "missing" in reason


def test_heuristic_review_flags_tiny_file(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "ROOT", tmp_path)
    art = tmp_path / "web" / "static" / "art"
    art.mkdir(parents=True)
    (art / "tiny.webp").write_bytes(b"x")
    status, _ = review_mod.heuristic_review({"output_path": "/static/art/tiny.webp"})
    assert status == "regenerate"


def test_heuristic_review_passes_normal_file(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "ROOT", tmp_path)
    art = tmp_path / "web" / "static" / "art"
    art.mkdir(parents=True)
    (art / "ok.webp").write_bytes(b"\x00" * 6000)
    status, _ = review_mod.heuristic_review({"output_path": "/static/art/ok.webp"})
    assert status == "approved"


def test_external_review_overrides_heuristic(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "ROOT", tmp_path)
    art = tmp_path / "web" / "static" / "art"
    art.mkdir(parents=True)
    (art / "fiber__cvd__featured.webp").write_bytes(b"\x00" * 6000)  # would pass heuristic
    manifest = {"version": 1, "entries": {
        "fiber__cvd__featured": {
            "edge_id": 12, "factor_slug": "fiber", "outcome_slug": "cvd",
            "kind": "featured",
            "output_path": "/static/art/fiber__cvd__featured.webp",
        },
    }}
    external = {"fiber__cvd__featured": {
        "qa_status": "regenerate", "reason": "subject mismatch"}}
    counts = apply_reviews(manifest, external=external, run_heuristic=True)
    assert counts["regenerate"] == 1
    assert manifest["entries"]["fiber__cvd__featured"]["qa_status"] == "regenerate"
    assert manifest["entries"]["fiber__cvd__featured"]["qa_source"] == "external"


# ── site fallback ─────────────────────────────────────────────────────

def test_site_returns_svg_when_manifest_empty(monkeypatch, tmp_path):
    # Force a fresh empty manifest
    from web import generated_art as ga
    monkeypatch.setattr(ga, "_MANIFEST_CACHE", {"version": 1, "entries": {}})
    out = ga.featured_card_svg(factor_slug="x", outcome_slug="y", tier="C",
                               factor_kind="food", outcome_kind="condition",
                               w=400, h=260)
    # SVG fallback always starts with an <svg> root
    assert out.lstrip().startswith("<svg")


def test_site_returns_img_when_manifest_has_entry(monkeypatch, tmp_path):
    from web import generated_art as ga
    art = ROOT / "web" / "static" / "art"
    art.mkdir(parents=True, exist_ok=True)
    img_file = art / "_test__pair__featured.webp"
    img_file.write_bytes(b"\x00" * 6000)
    try:
        monkeypatch.setattr(ga, "_MANIFEST_CACHE", {
            "version": 1, "entries": {
                "_test__pair__featured": {
                    "edge_id": 999, "factor_slug": "_test", "outcome_slug": "pair",
                    "kind": "featured",
                    "output_path": "/static/art/_test__pair__featured.webp",
                    "qa_status": "approved",
                },
            }})
        out = ga.featured_card_svg(factor_slug="_test", outcome_slug="pair", tier="C",
                                   factor_kind="food", outcome_kind="condition",
                                   w=400, h=260)
        assert "<img " in out
        assert "_test__pair__featured.webp" in out
    finally:
        img_file.unlink(missing_ok=True)


def test_site_falls_back_when_qa_says_regenerate(monkeypatch):
    from web import generated_art as ga
    monkeypatch.setattr(ga, "_MANIFEST_CACHE", {
        "version": 1, "entries": {
            "x__y__featured": {
                "edge_id": 1, "factor_slug": "x", "outcome_slug": "y",
                "kind": "featured", "output_path": "/static/art/x__y__featured.webp",
                "qa_status": "regenerate",
            },
        }})
    out = ga.featured_card_svg(factor_slug="x", outcome_slug="y", tier="C",
                               factor_kind="food", outcome_kind="condition",
                               w=400, h=260)
    assert out.lstrip().startswith("<svg")


def test_site_falls_back_when_image_file_missing(monkeypatch, tmp_path):
    from web import generated_art as ga
    monkeypatch.setattr(ga, "_MANIFEST_CACHE", {
        "version": 1, "entries": {
            "ghost__pair__featured": {
                "edge_id": 1, "factor_slug": "ghost", "outcome_slug": "pair",
                "kind": "featured",
                "output_path": "/static/art/ghost__pair__featured.webp",
                "qa_status": "approved",
            },
        }})
    # No image file written → must fall back
    out = ga.featured_card_svg(factor_slug="ghost", outcome_slug="pair",
                               tier="C", factor_kind="food",
                               outcome_kind="condition", w=400, h=260)
    assert out.lstrip().startswith("<svg")


# ── load_reviews ──────────────────────────────────────────────────────

def test_load_reviews_merges_multiple_files(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "REVIEWS_DIR", tmp_path)
    (tmp_path / "a.json").write_text(json.dumps({
        "x__y__featured": {"qa_status": "approved", "reason": "fine"}}))
    (tmp_path / "b.json").write_text(json.dumps({
        "p__q__featured": {"qa_status": "regenerate", "reason": "bad"}}))
    out = load_reviews(tmp_path)
    assert out["x__y__featured"]["qa_status"] == "approved"
    assert out["p__q__featured"]["qa_status"] == "regenerate"


def test_load_reviews_ignores_invalid_status(tmp_path, monkeypatch):
    monkeypatch.setattr(review_mod, "REVIEWS_DIR", tmp_path)
    (tmp_path / "bad.json").write_text(json.dumps({
        "x__y__featured": {"qa_status": "lookin_good_chief"}}))
    assert load_reviews(tmp_path) == {}
