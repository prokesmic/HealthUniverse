"""Health Universe edge-art CLI.

A single entry point for the cross-machine art pipeline.

Subcommands:
  prepare    Build prompt jobs from the corpus → art_jobs/prompts/
  export     Mirror prompts → art_jobs/renders/pending/ (ship to render machine)
  import     Scan art_jobs/renders/done/ → copy images to web/static/art/,
             update data/art_manifest.json
  review     Run QA pass (heuristic + external reviews) → manifest qa_status
  status     Print a count summary of the current pipeline state
  list       List edges that already have / lack a cached image

All commands operate on stable JSON files. None of them call paid APIs
or assume Draw Things has a CLI.

Cross-machine workflow (the priority):
  on dev machine:
    python generate_edge_art.py prepare --kind featured --limit 50
    python generate_edge_art.py export
    git add art_jobs/ && git commit -m "Art batch: 50 prompts" && git push
  on render machine:
    git pull
    open art_jobs/renders/pending/*.json in Draw Things, render each,
    save the .webp output as the listed `output_filename`
    into art_jobs/renders/done/
    git add art_jobs/renders/done/ && git commit && git push
  back on dev machine:
    git pull
    python generate_edge_art.py import       # copies images, updates manifest
    python generate_edge_art.py review       # heuristic QA + any external reviews
    git add data/art_manifest.json web/static/art/ art_jobs/ && git commit && git push

Same-machine workflow: same as above, just skip the git push/pull steps.
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

from db import connect                                   # noqa: E402
from art_pipeline import (                               # noqa: E402
    load_manifest, save_manifest, manifest_key,
    build_heuristic_prompt, merge_external_prompts,
    write_prompt_job, scan_done_renders,
    load_reviews, apply_reviews,
)
from art_pipeline.jobs import (                          # noqa: E402
    output_filename, export_pending, scan_pending_jobs,
    PROMPTS_DIR, PENDING_DIR, DONE_DIR, REVIEWS_DIR, STATIC_ART,
)
from art_pipeline.manifest import upsert_entry           # noqa: E402

KIND_SIZES = {"featured": (800, 520), "discovery": (480, 480)}


# ─────────────────────────────────────────────────────────────────────
# prepare
# ─────────────────────────────────────────────────────────────────────

def cmd_prepare(args: argparse.Namespace) -> None:
    """Build prompt jobs for `--limit` edges. Uses heuristic by default;
    `--prompt-provider gemma --gemma-input <file.json>` merges external
    Gemma-generated prompts on top of the heuristic baseline."""
    where = "e.tier IN ('A','B','C','X')"
    params: list = []
    if args.tiers:
        where = "e.tier IN ({})".format(
            ",".join(["?"] * len(args.tiers.split(","))))
        params = args.tiers.split(",")
    sql = f"""
        SELECT e.id, e.tier, e.direction,
               f.slug AS f_slug, f.name AS f_name, f.kind AS f_kind,
               o.slug AS o_slug, o.name AS o_name, o.kind AS o_kind
        FROM edge e
        JOIN entity f ON f.id=e.factor_id
        JOIN entity o ON o.id=e.outcome_id
        WHERE {where}
        ORDER BY CASE e.tier WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END,
                 e.id
        LIMIT ?"""
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, [*params, args.limit]).fetchall()]
    if not rows:
        print("[prepare] no edges matched.")
        return

    # Skip edges that already have a cached image (unless --rebuild).
    manifest = load_manifest()
    skip_keys = set(manifest.get("entries", {}).keys()) if not args.rebuild else set()

    width, height = KIND_SIZES.get(args.kind, KIND_SIZES["featured"])
    jobs: list[dict] = []
    for r in rows:
        key = manifest_key(r["f_slug"], r["o_slug"], args.kind)
        if key in skip_keys:
            continue
        prompt = build_heuristic_prompt(
            edge_id=r["id"], factor_slug=r["f_slug"], factor_name=r["f_name"],
            factor_kind=r["f_kind"], outcome_slug=r["o_slug"],
            outcome_name=r["o_name"], outcome_kind=r["o_kind"],
            tier=r["tier"], direction=r["direction"], kind=args.kind)
        jobs.append({
            "edge_id":         r["id"],
            "factor_slug":     r["f_slug"],
            "factor_name":     r["f_name"],
            "outcome_slug":    r["o_slug"],
            "outcome_name":    r["o_name"],
            "tier":            r["tier"],
            "direction":       r["direction"],
            "kind":            args.kind,
            **prompt,
            "size":            [width, height],
            "renderer":        args.renderer,
            "model":           args.model,
            "prompt_provider": "heuristic",
            "output_filename": output_filename(r["f_slug"], r["o_slug"], args.kind),
        })

    if args.prompt_provider == "gemma":
        if not args.gemma_input:
            sys.exit("[prepare] --prompt-provider=gemma requires --gemma-input PATH")
        jobs = merge_external_prompts(jobs, args.gemma_input)

    for j in jobs:
        write_prompt_job(j)
    print(f"[prepare] wrote {len(jobs)} job(s) → {PROMPTS_DIR}")
    if args.rebuild:
        print("           (rebuild mode — also includes already-cached entries)")


# ─────────────────────────────────────────────────────────────────────
# export — mirror prompts/ → renders/pending/
# ─────────────────────────────────────────────────────────────────────

def cmd_export(args: argparse.Namespace) -> None:
    n = export_pending()
    print(f"[export] copied {n} job(s) → {PENDING_DIR}")
    print("         Ship the prompts/ or renders/pending/ directory to your")
    print("         rendering machine. Each job's output_filename tells you")
    print("         the exact name to save the rendered image as in done/.")


# ─────────────────────────────────────────────────────────────────────
# import — scan renders/done/ + update manifest + copy to web/static/art/
# ─────────────────────────────────────────────────────────────────────

def cmd_import(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    STATIC_ART.mkdir(parents=True, exist_ok=True)
    imported = 0; skipped = 0
    for found in scan_done_renders():
        job = found["job"]
        img: Path = found["image_path"]
        if not job:
            print(f"  ! could not match job for {img.name}, skipping")
            skipped += 1
            continue
        # Copy image to web/static/art/<output_filename>
        out_name = job.get("output_filename") or img.name
        target = STATIC_ART / out_name
        try:
            shutil.copy2(img, target)
        except Exception as exc:
            print(f"  ! copy fail {img.name}: {exc}")
            continue
        entry = {
            "edge_id":         job.get("edge_id"),
            "factor_slug":     job.get("factor_slug"),
            "outcome_slug":    job.get("outcome_slug"),
            "kind":            job.get("kind", "featured"),
            "prompt_provider": job.get("prompt_provider", "heuristic"),
            "renderer":        job.get("renderer", "manual"),
            "model":           job.get("model", "qwen-image-8bit"),
            "prompt":          job.get("prompt", ""),
            "seed":            job.get("seed"),
            "scene":           job.get("scene"),
            "tone":            job.get("tone"),
            "palette":         job.get("palette"),
            "composition":     job.get("composition"),
            "size":            job.get("size", list(KIND_SIZES.get(job.get("kind","featured"), (800,520)))),
            "output_path":     f"/static/art/{out_name}",
            "updated_at":      datetime.now().isoformat(timespec="seconds"),
            "qa_status":       None,
        }
        try:
            upsert_entry(manifest, entry)
            imported += 1
        except ValueError as exc:
            print(f"  ! manifest upsert fail for {img.name}: {exc}")
            skipped += 1
    save_manifest(manifest)
    print(f"[import] {imported} imported, {skipped} skipped → manifest updated.")


# ─────────────────────────────────────────────────────────────────────
# review — heuristic + optional external reviews → manifest qa_status
# ─────────────────────────────────────────────────────────────────────

def cmd_review(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    external = load_reviews() if args.external else {}
    counts = apply_reviews(manifest, external=external,
                           run_heuristic=not args.no_heuristic)
    save_manifest(manifest)
    print(f"[review] applied: {counts}")


# ─────────────────────────────────────────────────────────────────────
# status / list
# ─────────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    n_entries = len(manifest.get("entries", {}))
    n_pending = len(list(PROMPTS_DIR.glob("*.json"))) if PROMPTS_DIR.exists() else 0
    n_export  = len(list(PENDING_DIR.glob("*.json"))) if PENDING_DIR.exists() else 0
    n_done    = sum(1 for ext in ("webp", "png", "jpg", "jpeg")
                    for _ in DONE_DIR.glob(f"*.{ext}")) if DONE_DIR.exists() else 0
    qa = {"approved":0,"needs_review":0,"regenerate":0,"unset":0}
    for e in manifest.get("entries", {}).values():
        qa[e.get("qa_status") or "unset"] = qa.get(e.get("qa_status") or "unset", 0) + 1
    print(f"  prompts queued:    {n_pending}")
    print(f"  exported pending:  {n_export}")
    print(f"  rendered (done/):  {n_done}")
    print(f"  manifest entries:  {n_entries}")
    print(f"  qa: {qa}")


def cmd_list(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    keys = set(manifest.get("entries", {}).keys())
    with connect() as conn:
        rows = conn.execute(
            "SELECT e.id, f.slug AS fs, o.slug AS os, e.tier "
            "FROM edge e JOIN entity f ON f.id=e.factor_id "
            "JOIN entity o ON o.id=e.outcome_id "
            "WHERE e.tier IN ('A','B') ORDER BY e.id LIMIT ?",
            (args.limit,)).fetchall()
    print(f"{'edge_id':<8}{'tier':<6}{'factor → outcome':<60}cached?")
    for r in rows:
        for kind in ("featured", "discovery"):
            k = manifest_key(r["fs"], r["os"], kind)
            mark = "✓" if k in keys else "·"
            print(f"  {r['id']:<6}{r['tier']:<6}{(r['fs']+' → '+r['os'])[:58]:<60}{mark} {kind}")


# ─────────────────────────────────────────────────────────────────────
# argparse
# ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="Build prompt jobs from the corpus")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--kind", choices=("featured", "discovery"), default="featured")
    p.add_argument("--tiers", default="A,B", help="Comma list of tiers (default A,B)")
    p.add_argument("--prompt-provider", choices=("heuristic", "gemma"),
                   default="heuristic",
                   help="heuristic: built-in rule-based; "
                        "gemma: merge external file produced by Gemma elsewhere")
    p.add_argument("--gemma-input", help="Path to Gemma-produced prompt JSON")
    p.add_argument("--renderer", choices=("none", "drawthings", "manual"),
                   default="drawthings")
    p.add_argument("--model", default="qwen-image-8bit")
    p.add_argument("--rebuild", action="store_true",
                   help="Re-prepare even for edges already in manifest")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("export", help="Mirror prompts/ to renders/pending/")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="Pull rendered images into the manifest")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("review", help="Apply QA review to manifest entries")
    p.add_argument("--external", action="store_true",
                   help="Include external review JSON in art_jobs/reviews/")
    p.add_argument("--no-heuristic", action="store_true",
                   help="Skip the heuristic existence/size check")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("status", help="Show counts at every stage")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="List edges and whether they have a cached image")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
