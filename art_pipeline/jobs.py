"""Render-job export / import — the portable hand-off between the
repo and the offline rendering machine.

Layout under repo root:

  art_jobs/
    prompts/             one JSON per edge — produced by `prepare`
      <eid>__<slug>.json
    renders/
      pending/           jobs ready to render (mirror of prompts/)
      done/              rendered .webp / .png + sidecar .json,
                         deposited from the rendering machine
    reviews/             optional QA JSON files

A "job" is portable JSON that describes everything a renderer needs:

  {
    "edge_id":         12,
    "factor_slug":     "fiber",
    "factor_name":     "Dietary fibre",
    "outcome_slug":    "cvd",
    "outcome_name":    "Cardiovascular disease",
    "tier":            "B",
    "direction":       "protective",
    "kind":            "featured",
    "scene":           "still-life-botanical",
    "palette":         "cream-forest",
    "tone":            "calm-confident",
    "composition":     "...",
    "prompt":          "...",
    "seed":            42,
    "size":            [800, 520],
    "renderer":        "drawthings" | "manual",
    "model":           "qwen-image-8bit",
    "output_filename": "fiber__cvd__featured.webp",
    "prompt_provider": "heuristic" | "gemma"
  }

The output_filename is deterministic — `{factor}__{outcome}__{kind}.webp`
— so the rendering machine knows exactly what to save it as, and the
import step knows where to find it.
"""
from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).parent.parent
ART_JOBS_DIR = ROOT / "art_jobs"
PROMPTS_DIR  = ART_JOBS_DIR / "prompts"
PENDING_DIR  = ART_JOBS_DIR / "renders" / "pending"
DONE_DIR     = ART_JOBS_DIR / "renders" / "done"
REVIEWS_DIR  = ART_JOBS_DIR / "reviews"
STATIC_ART   = ROOT / "web" / "static" / "art"


def _ensure_dirs() -> None:
    for p in (PROMPTS_DIR, PENDING_DIR, DONE_DIR, REVIEWS_DIR, STATIC_ART):
        p.mkdir(parents=True, exist_ok=True)


def _job_filename(edge_id: int, factor_slug: str, outcome_slug: str,
                  kind: str) -> str:
    return f"{edge_id:05d}__{factor_slug}__{outcome_slug}__{kind}.json"


def output_filename(factor_slug: str, outcome_slug: str, kind: str,
                    ext: str = "webp") -> str:
    """Deterministic filename for the rendered image. The rendering
    machine MUST save its output under this exact name."""
    return f"{factor_slug}__{outcome_slug}__{kind}.{ext}"


def write_prompt_job(job: dict, dest: Path | None = None) -> Path:
    """Write one job to art_jobs/prompts/. Returns the file path."""
    _ensure_dirs()
    target_dir = dest or PROMPTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    fname = _job_filename(job["edge_id"], job["factor_slug"],
                          job["outcome_slug"], job.get("kind", "featured"))
    path = target_dir / fname
    job_out = {
        "schema_version": 1,
        "exported_at":    datetime.now().isoformat(timespec="seconds"),
        **job,
    }
    path.write_text(json.dumps(job_out, indent=2, sort_keys=True))
    return path


def export_pending(prompts_dir: Path | None = None,
                   pending_dir: Path | None = None) -> int:
    """Mirror prompts/ → renders/pending/. Used to mark "this batch is
    ready to ship to the rendering machine". Returns count copied."""
    src = Path(prompts_dir) if prompts_dir else PROMPTS_DIR
    dst = Path(pending_dir) if pending_dir else PENDING_DIR
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in src.glob("*.json"):
        shutil.copy2(f, dst / f.name)
        count += 1
    return count


def scan_pending_jobs(pending_dir: Path | None = None) -> Iterator[dict]:
    """Yield every pending job dict. Used by the rendering machine if
    it has Python (e.g. for batch automation). Manual workflows just
    open the JSONs in a text editor."""
    src = Path(pending_dir) if pending_dir else PENDING_DIR
    if not src.exists():
        return
    for f in sorted(src.glob("*.json")):
        try:
            yield json.loads(f.read_text())
        except json.JSONDecodeError:
            continue


def scan_done_renders(done_dir: Path | None = None) -> Iterator[dict]:
    """Yield {job_dict, image_path, sidecar_path} for every rendered
    image found in done/. Pairs an image (.webp / .png) with the
    matching prompt JSON (same stem) so the manifest can be updated.

    A render is "done" when:
      • an image file exists with one of: .webp, .png, .jpg, .jpeg
      • a prompt JSON with the same stem (or matching output_filename)
        is also present in done/, OR can be matched against
        prompts/ by output_filename.
    """
    src = Path(done_dir) if done_dir else DONE_DIR
    if not src.exists():
        return
    images = []
    for ext in ("*.webp", "*.png", "*.jpg", "*.jpeg"):
        images.extend(src.glob(ext))
    for img in images:
        # Look for sidecar JSON with same stem in done/
        sidecar = img.with_suffix(".json")
        job: dict | None = None
        if sidecar.exists():
            try: job = json.loads(sidecar.read_text())
            except Exception: job = None
        if job is None:
            # Fall back: search prompts/ for a job whose
            # output_filename matches this image's name
            for pf in PROMPTS_DIR.glob("*.json"):
                try:
                    candidate = json.loads(pf.read_text())
                except Exception:
                    continue
                if candidate.get("output_filename") == img.name:
                    job = candidate
                    sidecar = pf
                    break
        if job is None:
            # Last resort: parse the image filename
            stem_parts = img.stem.split("__")
            if len(stem_parts) >= 3:
                job = {"factor_slug": stem_parts[0],
                       "outcome_slug": stem_parts[1],
                       "kind": stem_parts[2]}
        yield {"job": job, "image_path": img, "sidecar_path": sidecar
               if sidecar.exists() else None}
