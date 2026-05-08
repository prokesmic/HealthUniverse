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
import time
import urllib.parse
import urllib.request
import urllib.error
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
# render — call a free image-gen API for each pending job (no GPU needed)
# ─────────────────────────────────────────────────────────────────────

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

# Pollinations free tier sometimes leaks a thin watermark band along the
# lower-left, despite nologo=true. We render a few extra pixels of height,
# then crop the bottom band back off to the requested size. Net effect:
# clean output at the size the caller asked for.
_WATERMARK_PAD_PX = 48


def _strip_watermark(raw: bytes, target_w: int, target_h: int) -> bytes:
    """Crop the bottom watermark band off a Pollinations JPEG and return
    a JPEG at exactly target_w × target_h. Falls back to the original
    bytes on any error so we never lose a render."""
    try:
        from io import BytesIO
        from PIL import Image
        im = Image.open(BytesIO(raw))
        w, h = im.size
        # If the API delivered the padded size, crop the bottom strip.
        if h > target_h:
            im = im.crop((0, 0, w, target_h))
        elif h == target_h and h > 80:
            # Same size came back — chop a thin bottom band proportional
            # to the requested padding, then resize back up to target_h.
            im = im.crop((0, 0, w, h - _WATERMARK_PAD_PX))
            im = im.resize((target_w, target_h), Image.LANCZOS)
        # If width drifted, resize.
        if im.size != (target_w, target_h):
            im = im.resize((target_w, target_h), Image.LANCZOS)
        out = BytesIO()
        im.convert("RGB").save(out, format="JPEG", quality=88, optimize=True)
        return out.getvalue()
    except Exception:
        return raw


def _render_one(job: dict, out_dir: Path, *, model: str, timeout: int,
                retries: int, retry_sleep: float) -> tuple[bool, str]:
    """Render a single job via Pollinations.ai. Saves the image as .jpg
    (the API returns JPEG) and writes a sidecar JSON next to it whose
    output_filename matches. Returns (ok, message)."""
    prompt = job.get("prompt") or ""
    if not prompt:
        return False, "empty prompt"
    seed = int(job.get("seed") or 0)
    size = job.get("size") or [800, 520]
    width, height = int(size[0]), int(size[1])

    base_name = job.get("output_filename") or f"{job['factor_slug']}__{job['outcome_slug']}__{job.get('kind','featured')}.webp"
    # Pollinations returns JPEG — switch the extension so the file on
    # disk matches its real format. The sidecar carries this name so
    # `import` writes the right manifest entry.
    img_name = Path(base_name).stem + ".jpg"
    img_path = out_dir / img_name
    if img_path.exists() and img_path.stat().st_size > 5_000:
        return True, f"skip (already rendered): {img_name}"

    # Render a slightly taller image so we can crop the watermark band.
    api_height = height + _WATERMARK_PAD_PX
    qs = urllib.parse.urlencode({
        "width":   width,
        "height":  api_height,
        "seed":    seed,
        "model":   model,
        "nologo":  "true",
        "private": "true",
        "enhance": "true",
        "safe":    "true",
    })
    url = POLLINATIONS_URL.format(prompt=urllib.parse.quote(prompt, safe="")) + "?" + qs

    last_err = ""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "HealthUniverse-art-pipeline/1.0",
                "Accept": "image/*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if len(data) < 5_000:
                last_err = f"tiny response ({len(data)} bytes)"
            else:
                cleaned = _strip_watermark(data, width, height)
                tmp = img_path.with_suffix(".part")
                tmp.write_bytes(cleaned)
                tmp.replace(img_path)
                # Sidecar so `import` picks up the right output_filename
                # (with the corrected .jpg extension) without touching prompts/.
                sidecar = img_path.with_suffix(".json")
                sidecar_job = {**job, "output_filename": img_name,
                               "rendered_at": datetime.now().isoformat(timespec="seconds"),
                               "renderer": "pollinations",
                               "model": model}
                sidecar.write_text(json.dumps(sidecar_job, indent=2, sort_keys=True))
                return True, f"ok: {img_name} ({len(data)//1024} KB)"
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            last_err = f"URL error: {e.reason}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt < retries:
            time.sleep(retry_sleep * attempt)  # linear backoff
    return False, last_err or "unknown error"


def cmd_render(args: argparse.Namespace) -> None:
    """Call a free image-gen API for every job in renders/pending/ (or
    prompts/ if pending is empty), saving outputs into renders/done/.

    Default provider is Pollinations.ai — free, no auth, ~3-5 sec/image.
    Re-running is safe: existing images in done/ are skipped."""
    src_dir = PENDING_DIR if any(PENDING_DIR.glob("*.json")) else PROMPTS_DIR
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    jobs = sorted(src_dir.glob("*.json"))
    if args.limit:
        jobs = jobs[: args.limit]
    if not jobs:
        print(f"[render] no jobs found in {src_dir}")
        return
    print(f"[render] {len(jobs)} job(s) from {src_dir.name}/ → {DONE_DIR}")
    print(f"         provider=pollinations model={args.model} "
          f"timeout={args.timeout}s retries={args.retries}")
    ok = skipped = failed = 0
    t0 = time.time()
    for i, jf in enumerate(jobs, 1):
        try:
            job = json.loads(jf.read_text())
        except Exception as e:
            print(f"  [{i}/{len(jobs)}] ! parse {jf.name}: {e}")
            failed += 1
            continue
        good, msg = _render_one(
            job, DONE_DIR, model=args.model, timeout=args.timeout,
            retries=args.retries, retry_sleep=args.retry_sleep)
        tag = "✓" if good else "✗"
        print(f"  [{i:>3}/{len(jobs)}] {tag} {jf.stem[:50]:50s} {msg}")
        if good:
            if msg.startswith("skip"): skipped += 1
            else: ok += 1
        else:
            failed += 1
        if args.sleep > 0 and i < len(jobs):
            time.sleep(args.sleep)
    dt = time.time() - t0
    print(f"[render] done in {dt:.1f}s — {ok} ok, {skipped} skipped, {failed} failed")


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

    p = sub.add_parser("render", help="Call free image-gen API for each pending job")
    p.add_argument("--model", default="flux",
                   help="Pollinations model (flux, flux-realism, turbo, etc.)")
    p.add_argument("--timeout", type=int, default=120,
                   help="Per-request timeout in seconds (default 120)")
    p.add_argument("--retries", type=int, default=3,
                   help="Retry attempts per job on failure (default 3)")
    p.add_argument("--retry-sleep", type=float, default=4.0,
                   help="Base seconds between retries — multiplied by attempt #")
    p.add_argument("--sleep", type=float, default=0.5,
                   help="Seconds to wait between successful jobs (default 0.5)")
    p.add_argument("--limit", type=int, default=0,
                   help="Render only the first N jobs (0 = all)")
    p.set_defaults(func=cmd_render)

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
