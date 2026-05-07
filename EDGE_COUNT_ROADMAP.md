# Edge-count roadmap: how big to be unique on the market, and how to get there fast

## Where we are today

| Metric | Today |
|---|---|
| Edges | **~830** (after Codex Track 1 + daily ingest) |
| Evidence rows | ~3,600 |
| Distinct PMIDs | ~3,500 |
| Average rows/edge | ~4.3 |

## Where the market sits

| Competitor | Coverage | Format |
|---|---|---|
| **Examine.com** | ~50,000 supplement × outcome cells | Single-supplement deep-dives, paywalled |
| **UpToDate** | ~14,000 clinical topics | Long-form clinical, $560/yr/seat |
| **Cochrane** | ~9,000 systematic reviews | Reviews only, free abstracts |
| **NICE** | ~2,500 clinical guidelines | UK clinical, free |
| **PubMed** | 30M+ papers | Raw, no synthesis |
| **WebMD / Healthline** | Tens of thousands of articles | SEO-driven, no rigour |
| **ChatGPT / Perplexity** | Whatever they hallucinate | No persistent graph, no PMIDs |

**Our differentiation isn't quantity.** It's the combination:
- Bidirectional graph (factor ↔ outcome) that no competitor has
- PMID-verified at validator time
- Tiered with explicit deterministic rules
- Personalised layer (`/my-plan`, `/coach`, `/today`, drug interactions)
- Privacy-first architecture
- Auditable changelog

## The "super unique" target

You don't need 50,000 to dominate — you need enough to never say "we don't cover this" for the top 200 conditions × top 100 factors that drive 95 % of clinical decisions.

That math:

- 200 outcomes × 100 factors = **20,000 cells**
- But ~70 % of those cells are zeros (most factors don't affect most conditions)
- So the saturated graph is **~5,000–6,000 meaningful edges**

**Concrete target:**

| Milestone | Edges | What it unlocks |
|---|---|---|
| **2,500** | First-quartile-of-market | Strong enough to launch paid tier; covers top-50 chronic conditions deeply |
| **5,000** | Best-in-class for a graph product | Enough that every plausible user query hits a real edge — *the* differentiator |
| **10,000** | Functionally complete | Edge cases covered; product becomes the citation source for journalists & clinicians |
| **20,000+** | Examine territory but with our rigour | Marginal returns — we shouldn't chase this unless funded |

**Recommended target: 5,000 edges in 6 months, 10,000 in 12.** Past that, depth (more rows per edge, more meta-analyses) beats breadth.

## How to get there fastest — three engines in parallel

### Engine 1 — Codex (the highest-yield)

What it does best:
- Curated topic batches: "give me 25 occupational-medicine pairs", "give me 25 paediatric immunology pairs"
- Each pair = ≥3 PMID-verified evidence rows
- Validator catches fabricated PMIDs at the gate
- Each PR = ~250 new pairs in 1–2 days of work

**Throughput:** ~1,000 new edges per month at sustainable pace.

Best targets to assign next:
1. `CODEX_BRIEF_NEXT.md` Track 2 — already written, 250 new pairs in v4 topic areas (sports, occupational, paediatric immunology, geriatric polypharmacy, dermatology, women's repro, ophthalmology, hematology, cancer prevention)
2. **CODEX_BRIEF_V6** — write the next 500-pair topic list. Areas we still under-cover:
   - Mental health interventions × condition outcomes (~80 pairs)
   - Drug × cognitive outcomes for older adults (~50 pairs)
   - Pregnancy-period exposures × maternal/fetal outcomes (~60 pairs)
   - Environmental exposures (microplastics, PFAS, air quality) × chronic conditions (~50 pairs)
   - Sleep architecture × cognitive/metabolic outcomes (~40 pairs)
   - Specific GI conditions × diet patterns (~50 pairs)
   - Athletic performance × supplement / training interventions (~80 pairs)
   - Skin / dermatology × diet / topical agents (~40 pairs)
   - Travel / chronobiology / shift-work × outcomes (~30 pairs)
   - Drug class × kidney function (~50 pairs)
3. **Densify v3** — re-run densify on the next 250 thinnest edges (3-row tier-B/C edges that need 1 more meta-analysis to promote)

**Codex monthly cadence: 2 topic batches + 1 densify pass = 750 new edges + 1,000 new evidence rows.**

### Engine 2 — Gemma daily ingest (free, slow, broad)

What it does best:
- Watches PubMed for new abstracts in tracked topic areas
- Extracts: factor, outcome, direction, study type, n_participants
- Routes to the right edge (or proposes a new one if no match)
- Auto-tier based on rules

**Current throughput:** ~3–5 new edges/day if it runs daily. ~100/month.

Improvements that 5× this:
1. **Expand the topic seed list** that Gemma watches. Today it's ~80 keywords; should be 300–500.
2. **Auto-propose new entities.** When Gemma finds a recurring novel exposure (e.g. "valproate"), let it create the entity automatically rather than requiring manual addition.
3. **PubMed E-utilities filter on study quality.** Right now Gemma ingests opinion pieces too. Filter to RCTs + meta-analyses only — fewer rows but higher quality, fewer manual cleanups.
4. **Wire into a Vercel cron** on top of the local launchd job, so even if my mac is offline a daily sweep still runs.

**Improved Gemma cadence: ~500 new edges/quarter.**

### Engine 3 — Claude (high-value, sparingly)

Budget remaining: **~$44** of the $50 lifetime cap.

Claude is best at the things Gemma can't do:
- **Re-tier audits.** Run a Claude pass on every tier-A and tier-B edge: confirm the rule application, flag anything misclassified. ~$0.05/edge × 500 edges = $25.
- **High-value seed research.** When Codex hits a topic where the literature requires careful judgment (e.g. "intermittent fasting × cancer survival"), Claude does the deep dive once. ~$0.20/edge × 50 edges = $10.
- **Cornerstone post writing** when Gemma's prose isn't good enough. ~$0.05/post × 50 posts = $2.50.

Don't use Claude for bulk generation — Codex + Gemma are 100× cheaper at scale.

## Quarterly milestones

| Quarter | Codex | Gemma | Claude | Net new edges | Cumulative |
|---|---|---|---|---|---|
| Now (Q2 2026) | 0 | 0 | 0 | 0 | 830 |
| Q3 2026 | 750 (Track 2 + Track 3) | 300 | tier audit | 1,000 | **1,830** |
| Q4 2026 | 1,000 (3 tracks) | 400 | seed research | 1,400 | **3,230** |
| Q1 2027 | 1,000 | 500 | densify audit | 1,500 | **4,730** |
| Q2 2027 | 750 | 500 | — | 1,250 | **5,980** ← **5k milestone** |
| Q3 2027 | 1,000 | 600 | — | 1,600 | **7,580** |
| Q4 2027 | 1,000 | 700 | — | 1,700 | **9,280** ← near 10k |

## What I'd do this week

1. **Push `CODEX_BRIEF_V6` to main** with 5 new tracks of ~100 pairs each (500 pairs total, 1,500 evidence rows). Codex can chip away at one per week.
2. **Audit the Gemma daily ingest cron** — currently runs locally; add a Vercel-cron variant so we get continuous ingest even when my Mac is off.
3. **Add `/api/admin/seed-watchlist` endpoint** that lets you push new topic keywords for Gemma to watch without redeploying.
4. **Quarterly: run a Claude tier-A audit** ($25 budget). Catches misclassifications before they undermine trust.

The 5k milestone is reachable by Q2 2027 if the cadence holds. The combination of curated Codex pairs + autonomous Gemma sweeps + targeted Claude audits is genuinely hard for a competitor to replicate without our agent stack — that's the moat we should lean on.
