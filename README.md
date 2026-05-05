# Health Universe

A living knowledge graph of how nutrition, lifestyle, supplements, and
environmental exposures affect chronic-disease risk. Continuously updated.

🌐 **Live:** https://health-universe.vercel.app

![evidence summary count](https://img.shields.io/badge/edges-513-1f3a2e) ![tier-A](https://img.shields.io/badge/tier_A-130-3b8e5a) ![spent](https://img.shields.io/badge/lifetime_Claude_spend-%245.49%2F%2450-c9a961)

---

## What it is

Each `(factor → outcome)` is an **edge** with:

- direction — `protective`, `harmful`, `neutral`, `u_shaped`, `mixed`
- confidence tier — `A` strong evidence, `B` moderate, `C` emerging,
  `D` limited, `X` contested
- 4–10 evidence rows with real citations (PubMed-verified)
- plain-language summary + factor-specific mechanism
- change history

Rendered as cream-and-forest-green cards inspired by editorial design.

## Stack

- **FastAPI + Jinja** — server-rendered, no React
- **SQLite** — read-only on Vercel, written by offline scripts
- **Anthropic Claude Sonnet 4.6** — one-off seed deep research + tier
  A/B adjudication, **hard-capped at $50 lifetime** in `claude_client.py`
- **Local Gemma 4:26b via Ollama** — daily abstract triage, claim
  extraction, summarization, dedup-via-embeddings (free)
- **nomic-embed-text via Ollama** — entity + edge embeddings for
  near-duplicate detection (free)
- **Pillow** — `/edge/{id}.png` OpenGraph share cards
- **Vercel** — serverless deployment of the read path

## Pipelines

```
        ┌────────────────────────────────────────────┐
        │  ONE-OFF SEED (Claude, paid, $50 cap)       │
        │   topics.py / topics_extra.py → seed.py    │
        │   Codex payloads → seed_from_payloads.py    │
        └────────────────────┬────────────────────────┘
                             │
        ┌────────────────────┴────────────────────────┐
        │            SQLite knowledge graph           │
        └────────────────────┬────────────────────────┘
                             │
   ┌─────────────────────────┴───────────────────────────┐
   │  DAILY (Gemma, free, 05:15 via launchd)            │
   │   1. fetch new abstracts (PubMed, Europe PMC)      │
   │   2. Gemma extracts claims                         │
   │   3. embeddings auto-fold near-duplicates          │
   │   4. re-score edges from evidence weights          │
   │   5. Claude adjudicates tier A/B promotions only   │
   │   6. ntfy push on real discoveries                 │
   │   7. auto-commit DB → Vercel redeploys             │
   └────────────────────────────────────────────────────┘
```

## Quick start

```bash
git clone https://github.com/prokesmic/HealthUniverse.git
cd HealthUniverse
./setup.sh
cp .env.example .env  # then edit ANTHROPIC_API_KEY
source .venv/bin/activate
uvicorn web.app:app --reload --port 8000
```

Run a Claude seed pair:

```bash
python seed.py --pair magnesium,sleep_quality
```

## App routes

| route | what |
|---|---|
| `/` | home — hero + stats + 9-category grid + featured + buckets |
| `/discoveries` | newly-promoted-to-A/B and recent C+ edges |
| `/edge/{id}` | full evidence table + history + share PNG link |
| `/edge/{id}.png` | 1200×630 OpenGraph share card |
| `/category/{slug}` | by-category list |
| `/tier/{A,B,C,D,X}` | by-tier list |
| `/myths` | deprecated + contested edges |
| `/changes` | recent tier history |
| `/me` | local-only profile + personalized re-rank |
| `/search?q=…` | substring search |
| `/api/edges`, `/api/entities/{slug}` | JSON for third parties |
| `/sitemap.xml`, `/robots.txt` | crawler hints |

## Cost discipline (locked in)

- Claude is used **only** for seed research and tier-A/B adjudication.
- Gemma does everything else.
- Hard cap of $50 lifetime enforced in `claude_client.py` via the
  `cost_ledger` table. Every call writes a row.

See `AGENTS.md` for repo etiquette and the brief that external
contributors follow.

## License

MIT. Not medical advice.
