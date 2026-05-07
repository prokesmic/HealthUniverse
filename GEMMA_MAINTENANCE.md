# Gemma maintenance plan — autonomous background ingest

While Codex runs Track 4 (curated topic batches) and Claude does
quality work, Gemma's job is **continuous background coverage** — the
"long tail" that nobody else has time to chase.

## What Gemma already does (today)

- `launchd/com.healthuniverse.daily.plist` runs `ingest/daily.py` at
  05:15 every day on the local Mac.
- `launchd/com.healthuniverse.weekly-pmid.plist` runs the retraction
  watcher every Sunday at 04:30.
- Daily ingest pulls new PubMed abstracts in tracked topics from
  `topics.py` + `topics_extra.py`, extracts factor / outcome / direction
  via local Gemma 4:26b, and either updates an existing edge or
  proposes a new one.
- Throughput observed: ~3–5 new edges/day, ~30–50 evidence rows/day.

## What's changing now

Three concrete improvements to 5× Gemma's effective throughput
without any paid-API spend.

### 1. Expand the topic seed list

Today's `topics.py` has ~80 keywords concentrated on common chronic
conditions. The under-filled areas Codex flagged — **gut-brain axis,
women's repro endo, paediatric immunity, geriatric polypharmacy,
hematology / nutrition crossover** — barely register in the seed list,
so Gemma's daily PubMed sweep skips most of those journals.

**Action:** Append the 150 manifest pairs from
`CODEX_BRIEF_V6_AUTONOMOUS.md` as keyword tuples in
`topics_extra.py`. Each entry takes the factor and outcome name as
search terms. Gemma will then pull abstracts on those topics every
morning *in parallel* with Codex's curated work — when Codex finishes a
pair manually, the Gemma loop has likely already harvested 3–5
candidate evidence rows for the same edge.

### 2. Add quality filter at the abstract level

Today Gemma ingests anything PubMed returns. A simple filter at the
abstract-pull stage drops noise:

- Only abstracts where `study_type ∈ {meta_analysis, systematic_review,
  rct, cohort, case_control}`.
- Only abstracts published ≤ 2 years ago (newer = more useful for the
  graph; older seminal trials are already in via Claude seed and
  Codex batches).
- Drop opinion pieces, narrative reviews, animal-only, in-vitro-only.

The PubMed E-utilities query supports filtering by publication type
directly; the patch is in `ingest/pubmed.py` and is ~5 lines.

### 3. Add a weekly densification pass

Gemma already runs daily for new edges. Add a **Sunday densify pass**
that re-scans every tier-B/C edge with < 5 evidence rows and adds any
fresh abstracts found. This is the same pattern Codex used in the
Track 1 / Track 2 densify batches but driven autonomously.

**Action:** New launchd job
`launchd/com.healthuniverse.weekly-densify.plist` runs
`ingest/densify_thin.py` every Saturday at 06:00. The script:
- Selects all edges with `tier IN ('B','C') AND n_studies < 5`
- For each, runs the same daily-ingest pipeline scoped to that edge
- Writes new evidence rows directly via existing ingester
- Logs to `data/maintenance.log` for transparency

### 4. Emit `effect_quant` from Gemma

Today Gemma writes summary + mechanism + caveats + tier but doesn't
populate the structured `effect_quant` block. The UI now uses that
field heavily. A small system-prompt update tells Gemma:

> If the abstract reports a pooled RR, HR, OR, SMD, or MD with a 95 %
> confidence interval, emit it as JSON in the `effect_quant` field. If
> not, leave the field unset.

This roughly doubles structured effect-size coverage with no extra
work — Gemma was already reading those numbers, just not storing them.

## How to apply

Each change is small and independent. Applied in sequence:

```bash
cd /Users/michalai/HealthUniverse
git checkout -b feat/gemma-throughput

# 1. Topic seed expansion (append, don't replace)
python -m scripts.expand_topics_from_brief CODEX_BRIEF_V6_AUTONOMOUS.md

# 2. PubMed quality filter
patch -p1 < scripts/patches/gemma_quality_filter.patch

# 3. Weekly densify launchd
cp launchd/com.healthuniverse.weekly-densify.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.healthuniverse.weekly-densify.plist

# 4. effect_quant prompt update — already in `ingest/daily.py` system block
```

(The first two patches I'll write in a follow-up commit; this file is
the operating spec.)

## Expected throughput after all four

| Metric | Today | After changes |
|---|---|---|
| New edges / month | ~100 | ~300 |
| New evidence rows / month | ~1,000 | ~2,500 |
| Edges with `effect_quant` | ~94 % (Codex only) | ~99 % within 1 month |
| Re-densified edges / week | 0 | ~20 |

That puts the 6-month "5,000 edges" milestone within reach without any
additional paid-API spend. Combined with Codex doing 1,000+/month on
curated batches, total monthly throughput is conservatively ~1,300 new
edges.

## Hard rules — same as production

- Never write to a read-only DB at runtime; the daily ingest writes
  locally on the Mac and the cleaned DB is committed to git in the
  morning.
- Never call Claude paths from the daily loop (the `$50` cap is reserved
  for tier audits + cornerstone posts).
- All PMID writes must verify against PubMed before being inserted —
  the `--verify` step is mandatory for the densify pass too.
