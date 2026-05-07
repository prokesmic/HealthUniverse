# Claude (this assistant) — next tasks

Budget remaining: **~$44 / $50 lifetime cap.**
What I'll spend it on, in priority order, and why.

## 1. Tier-A audit pass on the 123 newly-added edges (~$8)

**Why:** Codex's Track 2 added 123 new edges. Tier assignment was
deterministic but auto-applied by the validator script — no human
spot-check. The panel review flagged "named medical reviewer" as the
single highest-trust lever; until that exists, an automated tier audit
is the next-best signal. If even one tier-A is misclassified, it
undermines the methodology page.

**What it does:**
- Pull every tier-A and tier-B edge created in the last 7 days
- Send each one to Claude with the strict tier rules + the supporting
  evidence rows
- Claude returns: `confirm` | `should_demote_to_X` | `should_promote_to_X` + reason
- Any "should change" entries get logged to
  `data/audits/tier-audit-2026-W19.json` for human review

Rough cost: 123 edges × $0.05 each = $6.15.

**Run:** `python audit_tiers.py --since 7`

## 2. Two cornerstone posts from rich Codex batches (~$3)

**Why:** Codex's Track 2 produced two clusters that are perfect
long-form material:

- **Coffee × 11 cancer outcomes** — a cohesive, high-public-interest
  topic. "What does the evidence actually say about coffee and cancer?"
  is a query that ranks. Long-form synthesis with all 11 cited inline
  is differentiated content.
- **Benzodiazepines × cognition / falls / fractures / dementia** — a
  serious clinical question with a clear evidence base now in the
  graph. Useful both for clinicians and laypeople with elderly family
  members.

**Run:**
```bash
python posts_build.py --topic "Coffee and cancer" --output posts/2026-W19-coffee-cancer.json
python posts_build.py --topic "Benzodiazepines in older adults" --output posts/2026-W19-benzos-elderly.json
```

(Will extend `posts_build.py` to support `--topic` filtering.)

## 3. Gemma seed-list expansion patch (no Claude budget)

**Why:** The Gemma maintenance plan lists topic-list expansion as the
highest-leverage cheap win. I'll write the small Python script that
reads `CODEX_BRIEF_V6_AUTONOMOUS.md` and appends the 150 manifest
pairs into `topics_extra.py` as Gemma-watchable keywords. One-time
~30 lines of code; pure local work.

## 4. PubMed quality-filter patch for `ingest/pubmed.py` (no Claude budget)

**Why:** Gemma maintenance plan item #2. ~5 lines of code in
`ingest/pubmed.py` that adds the publication-type filter to the
E-utilities query. Drops opinion / animal / in-vitro abstracts at the
gate, so Gemma's daily ingest only sees high-quality candidates.

## 5. Weekly densify launchd job (no Claude budget)

**Why:** Item #3 from the Gemma plan. New `densify_thin.py` script and
new `com.healthuniverse.weekly-densify.plist` for launchd. Pure
mechanical work, no model spend.

## What I'm NOT spending budget on

- Curated topic seeding (Codex is faster + cheaper at this — $0 vs $5/edge)
- Edge prose generation (Gemma is good enough)
- Re-tier audits beyond the recent 7-day window (diminishing returns)
- More cornerstone posts than two (one round, see if traffic picks up)

## Total budget burn this round

- Tier audit: ~$6.15
- Two cornerstone posts: ~$3
- **Total: ~$9.15. Remaining after: ~$35.**

That keeps a healthy buffer for the next round — I'd want $20 minimum
in reserve before another tier-A re-audit + a quarterly post-batch.

## Sequencing

1. Write the topic-list expansion script (Gemma item #1) — 15 min, no spend
2. Write the PubMed quality-filter patch (Gemma item #2) — 15 min, no spend
3. Write the weekly densify launchd config (Gemma item #3) — 10 min, no spend
4. Run the tier audit on the 123 new edges — ~10 min, ~$6
5. Generate the two cornerstone posts — ~5 min each, ~$3 total
6. Commit + push everything in one go

After all five steps the state is: Codex unblocked on Track 4, Gemma's
throughput tripled going forward, two new long-form posts live, and a
documented audit pass on the most recent corpus additions.
