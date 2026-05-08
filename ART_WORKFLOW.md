# Health Universe — portable art pipeline

A cross-machine workflow for replacing the procedural SVG card art on
Featured Evidence and Discoveries with locally-rendered images, while
keeping the live site purely offline.

The repo is portable: nothing here assumes the rendering machine is the
same as the dev machine. Code lives in the repo, prompts and render
jobs are stable JSON files you can ship between machines, and the live
site never generates anything at request time.

## What this does, in one paragraph

You run `generate_edge_art.py prepare` on the dev machine. That writes
one stable JSON file per edge under `art_jobs/prompts/` describing what
to render. You ship those JSON files to a machine that has Gemma 4
locally and Draw Things installed. You render each one in Draw Things
and save the resulting `.webp` (or `.png`) under a deterministic
filename into `art_jobs/renders/done/`. You ship that directory back
to the dev machine and run `generate_edge_art.py import`. That copies
the images into `web/static/art/`, updates `data/art_manifest.json`,
and the site automatically uses them on the next request. Edges
without a cached image keep using the existing procedural SVGs.

## Layout

```
generate_edge_art.py            CLI entry point
art_pipeline/
  __init__.py                   public API: load/save manifest, prompts, jobs, reviews
  manifest.py                   data/art_manifest.json read/write
  prompts.py                    heuristic prompt builder + Gemma merge
  jobs.py                       export / import / scan helpers
  review.py                     QA pass (heuristic + external)
web/generated_art.py            adapter — cached image OR procedural SVG fallback
web/illustrations.py            untouched; still the SVG fallback layer
web/static/art/                 rendered images (committed to git)
data/art_manifest.json          single source of truth
art_jobs/
  prompts/                      prepare → here
  renders/pending/              export → here (ship this to render machine)
  renders/done/                 deposit rendered images here (return)
  reviews/                      optional QA JSON files
```

## Same-machine workflow

Quick path when dev and rendering happen on one Mac.

```bash
# 1. Generate 50 prompt jobs for tier-A/B Featured cards.
python generate_edge_art.py prepare --kind featured --tiers A,B --limit 50

# 2. (optional) Stage them as "pending render" — useful if you want
#    to keep prompts/ as the source-of-truth and renders/pending/ as
#    a working tray.
python generate_edge_art.py export

# 3. Open Draw Things. Render each prompt with the listed seed and
#    size. Save the output under the listed `output_filename` in
#    `art_jobs/renders/done/`. (Filename is deterministic:
#    factor__outcome__kind.webp)

# 4. Pull the renders into the manifest + static folder.
python generate_edge_art.py import

# 5. Optional QA pass — heuristic checks (file exists, > 5 KB).
python generate_edge_art.py review

# 6. Confirm the site is using them.
python generate_edge_art.py status

# 7. Commit + deploy.
git add data/art_manifest.json web/static/art/ art_jobs/
git commit -m "Cached art batch — N edges"
git push
```

## Different-machine workflow (the priority)

The repo is online, so the simplest transport is git itself.

### On the dev machine — prepare and ship

```bash
# 1. Build prompt jobs.  Default provider is heuristic; swap to
#    Gemma-merged if you have a JSON file of Gemma-curated prompts:
python generate_edge_art.py prepare \
    --kind featured --tiers A,B --limit 50

# (optional Gemma override — see "Gemma prompt merge" below)
python generate_edge_art.py prepare \
    --prompt-provider gemma --gemma-input gemma-prompts.json \
    --kind featured --limit 50

# 2. Stage them for rendering.
python generate_edge_art.py export

# 3. Commit + push the prompts.
git add art_jobs/prompts art_jobs/renders/pending
git commit -m "Art batch: 50 featured prompts"
git push
```

### On the rendering machine — render and ship back

```bash
# 1. Pull.
git pull

# 2. Open Draw Things.  For each JSON file in art_jobs/renders/pending/
#    (or art_jobs/prompts/), render with:
#      • model:  qwen-image-8bit
#      • prompt: the `prompt` field from the JSON
#      • seed:   the `seed` field from the JSON
#      • size:   the `size` field [width, height]
#    Save the rendered image as the JSON's `output_filename` value
#    into art_jobs/renders/done/.
#
#    A clean batch convention: also drop the source job JSON next to
#    the image with the same stem (e.g. fiber__cvd__featured.webp +
#    fiber__cvd__featured.json).  The import step will pick them up
#    as a pair.  Without the sidecar, the import falls back to
#    matching by output_filename against art_jobs/prompts/, so you
#    can also just drop the .webp file alone — the pipeline still
#    finds the right metadata.

# 3. Commit + push back.
git add art_jobs/renders/done
git commit -m "Art batch: 50 renders"
git push
```

### On the dev machine — import + deploy

```bash
git pull

# 1. Copy images into web/static/art/ and update data/art_manifest.json.
python generate_edge_art.py import

# 2. Heuristic QA: flag empty / corrupted files for re-render.
python generate_edge_art.py review

# 3. Sanity-check.
python generate_edge_art.py status

# 4. Commit + deploy.
git add data/art_manifest.json web/static/art/ art_jobs/
git commit -m "Cached art batch: 50 imported, 0 needs_review"
git push
vercel --prod --yes
```

## Gemma prompt merge

`heuristic` is the default and always available. To use Gemma-generated
prompts (better creative copy, often), run Gemma on a separate machine
with a JSON output file shaped like:

```json
{
  "12": {
    "prompt": "Editorial photograph: still life of leafy greens on a sunlit kitchen counter, ...",
    "scene": "still-life-botanical",
    "palette": "cream-forest",
    "tone": "calm-confident",
    "composition": "Vermeer-style still life, single ingredient hero",
    "seed": 1739
  },
  "29": {
    "prompt": "...",
    "seed": 4271
  }
}
```

Keys are stringified `edge_id`. Any field is optional — missing fields
fall back to the heuristic baseline. Then on the dev machine:

```bash
python generate_edge_art.py prepare \
    --prompt-provider gemma --gemma-input ~/Downloads/gemma-prompts.json \
    --kind featured --limit 50
```

The job JSONs that get written carry both the prompt text AND the
structured `scene` / `palette` / `tone` / `composition` so the
rendering machine can use them however it wants.

## Reviews / QA

Optional. Two layers, can stack:

**Heuristic (always available, runs locally):**
- File exists at `output_path`? If not → `regenerate`.
- File size > 5 KB? If not → `regenerate`.
- Otherwise → `approved`.

**External (Gemma on render machine):**
Drop a JSON file in `art_jobs/reviews/` shaped like:

```json
{
  "fiber__cvd__featured": {
    "qa_status": "approved",
    "reason": "matches scene + palette correctly"
  },
  "alcohol_evening__rem_sleep__featured": {
    "qa_status": "regenerate",
    "reason": "subject is incorrect, looks like a wine glass not a sleep scene"
  }
}
```

Keys are manifest keys (factor__outcome__kind). Then on dev:

```bash
python generate_edge_art.py review --external
```

External reviews override heuristic decisions. The site treats
`regenerate` like a missing image — it falls back to the SVG. So
flagging a render as `regenerate` instantly stops it from rendering
on the live site.

## Site behaviour (unchanged contract)

- `web/illustrations.py` is untouched — still the always-safe procedural
  SVG layer.
- `web/generated_art.py` is the adapter; templates call its
  `featured_card_svg()` / `discovery_card_svg()` (same names, same
  signatures — no template changes).
- For each call:
  1. lookup `(factor_slug, outcome_slug, kind)` in `data/art_manifest.json`
  2. if a manifest entry exists, `qa_status` is not `regenerate`, AND
     the file is on disk → return an `<img>` snippet
  3. else → return the procedural SVG
- No image generation in request handlers. No paid API calls. No new
  Python deps beyond what was already in `requirements.txt`.

## Determinism + scaling

- Filenames are `factor__outcome__kind.webp` — deterministic, so the
  rendering machine knows exactly what to save them as.
- Seeds are deterministic by default (`edge_id * 7919 % 2³¹`) so
  re-rendering produces identical images unless overridden.
- `data/art_manifest.json` is sorted-keys JSON for line-stable diffs.
- Pipeline is batch-friendly to hundreds of edges per run; scaling is
  bounded only by the rendering machine's GPU.

## Hard rules (for the brief)

- ✅ Live site is read-only at request time.
- ✅ Cached image preferred when present, SVG fallback otherwise.
- ✅ No Vercel-side rendering, no paid API.
- ✅ No absolute local paths in any file the repo writes.
- ✅ Pipeline works from a machine that doesn't have Gemma / Draw Things.
- ✅ Procedural SVG layer (`web/illustrations.py`) is untouched.
- ✅ Templates unchanged — same Jinja globals, same call sites.
