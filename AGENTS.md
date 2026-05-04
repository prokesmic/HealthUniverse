# HealthUniverse — Agent Handoff

> **Repo:** https://github.com/prokesmic/HealthUniverse
> **Live:** https://health-universe.vercel.app
> **Owner:** Michal (prokesmic@gmail.com)

This file exists so a coding agent (Codex, Claude Code, etc.) can clone the
repo and contribute usefully without breaking the cost discipline or the
architecture.

---

## What this is

A living knowledge graph of how nutrition, lifestyle, supplements, and
environmental exposures affect chronic-disease risk. Each `(factor → outcome)`
pair is an **edge** with a confidence tier (A–D, X for contested), direction
(protective / harmful / neutral / u_shaped / mixed), evidence list, and history.

The product surface is a stream of cards on `health-universe.vercel.app`,
plus per-edge detail pages.

---

## Quick start

```bash
git clone https://github.com/prokesmic/HealthUniverse.git
cd HealthUniverse
./setup.sh            # creates .venv, installs deps, inits DB, seeds sources & topics
cp .env.example .env  # then edit ANTHROPIC_API_KEY
source .venv/bin/activate
uvicorn web.app:app --reload --port 8000
```

Run a single Claude seed pair (writes to DB):
```bash
python seed.py --pair magnesium,sleep_quality
```
Drain the queue with cap enforcement:
```bash
python seed.py --next --limit 200
```

---

## Architecture rules — DO NOT VIOLATE

1. **LLM budget split is non-negotiable:**
   - **Claude (Anthropic API)** is used **only** for: (a) one-off seed deep
     research on `(factor, outcome)` pairs, (b) tier-A/B promotion
     adjudication when evidence crosses a critical threshold.
   - **Gemma 4:26b via local Ollama** does *everything else*: daily abstract
     triage, claim extraction, dedup, summarization, card copy, re-scoring.
   - There is a **$50 lifetime cost cap** enforced in `claude_client.py` via
     `cost_ledger`. Never bypass it. Never call Claude in a hot path.

2. **SQLite at `data/healthuniverse.db` is the source of truth.** It is
   committed to the repo so Vercel can read it. Vercel runs read-only — do
   not write to the DB from a request handler. Writes happen in offline
   scripts (seed, ingest, digest) on the user's Mac, then `git push` triggers
   redeploy.

3. **No new frameworks without justification.** Stack is FastAPI + Jinja +
   SQLite + Anthropic SDK + httpx. No React, no SQLAlchemy, no Postgres,
   no Docker. We may add `sqlite-vec` for embeddings later.

4. **Design language is fixed.** Cream/ivory background, Fraunces serif
   headlines, Inter body, deep forest green primary, ochre accent, tier
   color ramp green → yellow → orange → coral. See `web/static/style.css`.
   Do not introduce a new color palette or font without an issue first.

5. **Never fabricate citations.** Prompts already instruct this. If you add
   new prompts that ask an LLM for evidence, include the same guardrail.

---

## File layout

```
schema.sql              knowledge graph + cost ledger schema
db.py                   sqlite access; READ_ONLY mode auto-detected on Vercel
sources.py              26 trusted sources with trust weights (run once)
topics.py               78 entities + 106 seed pairs (run once)
claude_client.py        Anthropic wrapper with hard $50 cap
seed.py                 Claude seed researcher CLI
web/app.py              FastAPI routes
web/templates/          Jinja templates
web/static/style.css    design tokens + components
api/index.py            Vercel serverless entrypoint (re-exports app)
vercel.json             Vercel build config (includes templates, DB, etc.)
data/healthuniverse.db  committed SQLite DB
```

When phases 2/4/5 land they will add:
```
ollama_client.py        local Gemma wrapper (Phase 2)
ingest/pubmed.py        E-utilities client (Phase 2)
ingest/europepmc.py     Europe PMC client (Phase 2)
ingest/daily.py         daily ingestion pipeline (Phase 2)
profile.py              local-only user profile (Phase 4)
digest.py               weekly digest generator (Phase 4)
launchd/                .plist files (Phase 2 & 4)
```

---

## Tasks open for parallel work (good for Codex)

The owner is building phases 2 (Gemma daily ingestion), 4 (profiles + digest),
and 5 (polish). Codex should pick from the list below — these are scoped to
NOT collide with that work.

### Independent / safe to work on now

- [ ] **Test suite.** Add `pytest` + a `tests/` folder. Cover: `db.py`
      round-trips, `claude_client.cost_of` math, `seed._validate` accepts
      good payloads & rejects bad ones, FastAPI routes return 200 with empty
      DB and with a fixture-loaded DB. Use a temp SQLite per test.
- [ ] **Expand `topics.py`.** Add another ~80–120 high-leverage seed pairs
      across mental health, women's health, men's health, paediatrics,
      pregnancy, peri/menopause, immunity. Keep the existing priority scale
      (1=highest). Don't change the tuple shape.
- [ ] **Better hero illustration.** The current globe in `home.html` is a
      placeholder. Replace with a more refined inline SVG (still inline, no
      raster files), keeping the cream/gold palette and the orbital-rings
      vibe. See the design reference described in README.md.
- [ ] **Accessibility pass.** Ensure all interactive elements have visible
      focus rings, sufficient contrast, ARIA labels on icon-only buttons,
      semantic landmarks (`<main>`, `<nav>`, `<aside>`).
- [ ] **Search endpoint.** `GET /search?q=...` over `entity.name`,
      `entity.aliases`, `edge.summary`. Server-rendered results page using
      the same card style. No JS framework — a plain `<form>` is fine.
- [ ] **PNG share-card export.** `GET /edge/{id}.png` renders the edge card
      as a 1200×630 OpenGraph image. Use `Pillow` server-side; do not pull
      in Playwright/headless Chrome. Write to `data/cache/og/{id}.png` so
      Vercel can serve it on subsequent hits (cache is fine to be cold).
- [ ] **Sitemap + robots.txt.** Generate `/sitemap.xml` from edges and
      categories. `/robots.txt` allows everything.
- [ ] **Add OpenGraph + Twitter meta tags** to `base.html` and a per-edge
      override in `edge.html` once the PNG share-card task is done.
- [ ] **README.md.** Currently missing. One-pager with screenshot, the
      LLM-budget rule, quick start, and a link to this AGENTS.md.

### Avoid (owner is touching these)

- `ollama_client.py`, `ingest/*`, `digest.py`, `profile.py`, `launchd/*`
- The `_featured`/`_evidence_strength_buckets` queries in `web/app.py`
- The cost-cap logic in `claude_client.py`
- Schema migrations (talk first)

---

## Workflow rules for any agent

1. **Branch per task.** `feat/<short-name>` or `fix/<short-name>`. PR into
   `main`. Don't push directly to `main`.
2. **Each PR runs the smoke test.** Add to your PR description:
   ```
   python -m pytest -q
   uvicorn web.app:app --port 8000  # then curl /, /tier/A, /category/nutrition
   ```
3. **Don't commit secrets.** `.env` is gitignored; the API key never leaves
   the user's machine.
4. **Don't expand the LLM budget.** If a task seems to want Claude in the
   hot path, stop and open a discussion issue.
5. **Surface the live URL** in PR descriptions when changes will be visible
   on https://health-universe.vercel.app .

---

## Dispatching to Codex (or any cloud agent)

When handing this off:

> Repo: https://github.com/prokesmic/HealthUniverse
> Read AGENTS.md first.
> Pick one task from the "Independent / safe to work on now" list, branch,
> implement, open a PR.
> Do not modify anything in the "Avoid" list.
> Cost discipline: never call Claude outside `seed.py` /
> `claude_client.py`'s `operation='adjudicate'` path.

<!-- deploy-verify: 2026-05-04 -->

