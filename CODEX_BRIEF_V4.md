# Codex brief v4 — three parallel tracks

> **Repo:** https://github.com/prokesmic/HealthUniverse
> **Read first:** `AGENTS.md`, `CODEX_BRIEF_500_V2.md` (validator schema),
> `CODEX_BRIEF_500_V3.md` (latest topic-area structure).
>
> **Three tracks below.** Pick one per PR and one branch per track. They
> don't conflict with each other — feel free to do all three, but as
> three separate PRs, not one mega-PR. Each track has its own scope and
> validator.

---

## Track A — v4 payload batch (~250 more pairs)

Same JSON schema as v2/v3, same validator, same hard rules. New topic
areas Codex hasn't covered yet.

### Branch: `feat/codex-seed-batch-4`

### Coverage areas (target ~250 pairs across 11 areas)

#### 1. Sports & performance nutrition (25 pairs)
- Beta-alanine × muscular endurance
- Sodium bicarbonate × short anaerobic performance
- Beetroot/nitrate × time-trial performance
- Caffeine timing × endurance / strength outcomes (separate from CV)
- Tart cherry × DOMS recovery
- HMB × resistance-training-induced muscle gain
- Pre-sleep casein × overnight muscle protein synthesis
- Glycogen-loading protocols × endurance
- BCAA vs whey × muscle protein synthesis
- Carbohydrate periodization × adaptation outcomes
- Caloric deficit × strength loss in athletes
- Heat acclimation × performance
- Altitude training (live high / train low) × VO2 max

#### 2. Occupational medicine (25 pairs)
- Night shift × specific cancers (separate edges per cancer)
- Sedentary office work × low back pain, hip impingement
- Repetitive strain × specific conditions (carpal tunnel, tennis elbow)
- Construction work / vibration × HAVS
- Chemical exposures (formaldehyde, methylene chloride, perchloroethylene)
  × specific cancers
- Healthcare-worker night shift × medication errors / mental health
- Long commute (>1 hour each way) × CVD, depression, divorce
- Occupational stress (job strain, effort-reward imbalance) × CV events
- Working long hours (≥55h/week) × stroke, depression
- Outdoor work × skin cancer, vitamin D status
- Cold exposure occupations × specific outcomes

#### 3. Gut-brain axis specifics (25 pairs)
- Specific Lactobacillus strains × anxiety, depression separately
- Bifidobacterium × IBS-D vs IBS-C separately
- Vagal nerve activity (HRV) × inflammation, mood
- SIBO × specific systemic outcomes (rosacea, fibromyalgia)
- LPS / endotoxemia × systemic inflammation
- Fecal microbiota transplant × autism (early evidence — likely tier C/D/X)
- Dietary fiber types (specifically) × short-chain fatty acid production
- Fermented food intake × inflammatory markers
- Gut barrier markers (zonulin) × autoimmune outcomes
- Antibiotic disruption × specific neuropsychiatric outcomes

#### 4. Paediatric immunology + early-life programming (20 pairs)
- Hygiene hypothesis variants: pet ownership × allergic disease
- Sibling exposure / daycare × asthma protection
- Helminth exposure (developing countries) × allergic disease
- Maternal microbiome → infant outcomes
- Vaginal vs C-section × infant immune development
- Breastfeeding × specific autoimmune diseases (T1D, IBD)
- Solid food introduction timing × food allergy
- Vitamin D status in pregnancy × child outcomes
- Maternal stress in pregnancy × child outcomes (asthma, anxiety)
- Early antibiotic exposure × specific autoimmune outcomes
- Cesarean × childhood obesity (separate from asthma)

#### 5. Geriatric polypharmacy (20 pairs)
- Anticholinergic burden score × dementia risk, falls
- Specific drug classes × falls in older adults (sedatives,
  antihypertensives, opioids)
- Statins in elderly × cognitive function (controversy)
- Benzodiazepines in elderly × falls, fractures, cognition
- Beers Criteria adherence × outcomes
- Deprescribing interventions × outcomes
- Polypharmacy threshold (5+ vs 10+ meds) × mortality
- PIMs (potentially inappropriate medications) × outcomes

#### 6. Dermatology (20 pairs)
- Tretinoin × photoaging
- Topical niacinamide × specific skin conditions
- Sunscreen (chemical vs mineral, SPF dose-response) × skin cancer
- Acne treatments × hormonal vs antibiotic mechanisms
- Atopic dermatitis treatments (specific biologics)
- Topical steroid potency × outcomes
- Diet (high-glycemic, dairy) × acne
- Stress × specific dermatologic conditions (psoriasis, alopecia areata)
- Hair-loss interventions × outcomes (minoxidil, finasteride, microneedling)

#### 7. Women's reproductive endocrinology beyond menopause (15 pairs)
- Specific contraceptive types × specific cancers (the IUD/breast/cervix
  picture is nuanced)
- Polycystic ovary syndrome × specific lifestyle interventions
- Endometriosis × specific dietary factors (gluten, low-FODMAP)
- Premenstrual dysphoric disorder treatments
- Fertility-tracking apps × pregnancy rates
- Antimullerian hormone × ovarian-reserve interpretation
- Egg-freezing outcomes by age band

#### 8. Ophthalmology beyond AMD/cataracts (15 pairs)
- Myopia progression: outdoor time × incidence
- Atropine drops × myopia progression
- Glaucoma: pressure-lowering interventions × visual-field decline
- Diabetic retinopathy × glycemic control intensity
- Eye-screen distance × eye strain symptoms
- Blue-light blocking lenses × actual outcomes (likely tier D/X)
- Vitamin A × specific eye conditions

#### 9. Hematology / nutrition crossover (15 pairs)
- Iron deficiency anemia × cognition, fatigue
- Anemia of chronic disease × outcomes
- B12 deficiency neurological symptoms × cognitive decline
- Folate deficiency × specific outcomes (separate from MTHFR pair)
- Hereditary hemochromatosis × specific outcomes
- Sickle cell disease × specific lifestyle modifications
- Thalassemia minor × athletic performance

#### 10. Specific cancer prevention through diet (15 pairs)
- Coffee × specific cancers (each cancer separate, since signals differ)
- Tea (green/black) × specific cancers
- Spice intake (curcumin, ginger, garlic) × specific cancers
- Soy isoflavones × breast cancer (premenopausal vs postmenopausal)
- Cruciferous vegetables × bladder, prostate cancer separately
- Tomato/lycopene × prostate cancer

#### 11. Misc + underrepresented (15 pairs)
- Periodic fasting × cancer outcomes (autophagy theory)
- Cold exposure × brown adipose tissue activation
- Hot baths × CVD (recent evidence)
- Forest bathing (shinrin-yoku) × specific markers
- Music therapy × dementia outcomes
- Loneliness × inflammation markers (CRP, IL-6)
- Pet ownership × CV outcomes (separate from immune dev)
- Religious/spiritual community × longevity

### Validation gate (mandatory)

```bash
git checkout -b feat/codex-seed-batch-4
./setup.sh
source .venv/bin/activate
python seed_from_payloads.py validate --verify    # MUST end "0 failed"
python seed_from_payloads.py ingest --dry-run     # MUST succeed
git add data/seed_payloads/
git commit -m "Codex seed batch v4: ~250 pairs in 11 new areas"
git push -u origin feat/codex-seed-batch-4
gh pr create --title "Codex seed batch v4 — 250 pairs"
```

PR body must include:
1. Full `--verify` output ending "0 failed"
2. 5 random `(factor, outcome, PMID, year, journal)` rows
3. **One sample summary + one sample mechanism** (the reviewer will check
   for templated prose — see v3 review feedback in `CODEX_BRIEF_500_V3.md`)
4. Areas covered (which #1–11 above)

### Quality bar (non-blocking but reviewed)

- Mechanism must be **specific to the factor**, not a kitchen-sink list.
- Summary must anchor on the strongest piece of evidence with a
  concrete fact ("a 2019 meta-analysis of 5.7M people found…").
- Don't reuse the v3 skeleton "*What makes this pair believable is not
  one flashy paper but the way the literature stacks up…*" across many
  edges. Each summary written in its own voice.

---

## Track B — Accessibility (WCAG 2.1 AA) audit + fixes

### Branch: `feat/a11y-audit`

### Scope

Make the entire site pass WCAG 2.1 AA. Touch only the templates and
CSS — no schema, no Python beyond minor route metadata.

### Required fixes (audit and address each)

1. **Color contrast.** Verify all text/background combinations hit ≥4.5:1
   (3:1 for large text). Common failure spots in this app:
   - `.muted` (`#8a8278`) on `--surface` (`#fffdf6`) — likely fails 4.5:1
   - tier-D coral on cream — borderline
   - badge text on tier-bg-D backgrounds
   - Edit `web/static/style.css` — propose darker shades that keep the
     warm cream feel.

2. **Visible focus rings.** Every interactive element (`a`, `button`,
   `input`, `select`, `[role=button]`, the chip checkboxes, the strip
   cards) must show a clear focus state. Add a `:focus-visible` rule
   with the gold accent or the forest-green primary.

3. **ARIA labels on icon-only buttons.** Already present on the bell /
   bookmark in topnav, but verify the heart on featured cards, the
   dismiss-X on spotlight, and the SVG nav targets.

4. **Semantic landmarks.** Verify every page has `<main>`, the topnav
   has `<nav aria-label="Primary">`, and the side panels use `<aside>`
   correctly. `base.html` already has `<main>` — check the rest.

5. **Skip link.** Add a "Skip to main content" link at the top of the
   page, hidden until focused.

6. **Form labels.** All `<input>` and `<select>` in `/me` must have
   associated `<label for>` (or be wrapped in a `<label>`). The age
   and sex fields are inside labels — verify the chip checkboxes have
   text content as their label.

7. **Keyboard nav.** Every workflow must be completable without a
   mouse. Walk through: load /, tab through nav, tab into search, tab
   into hero, tab through featured cards, tab through evidence buckets.
   Tab into /me, fill form, save. /explore: tab into picker filter,
   tab through entity list. Document any traps.

8. **Image alt text.** All `<svg>` decorative art has `aria-label`
   already (in `web/illustrations.py`). Verify it's descriptive, not
   `aria-hidden`.

9. **Reduced motion.** Wrap any animation in
   `@media (prefers-reduced-motion: reduce) { … }` overrides.

10. **Heading order.** No skipped levels. Every `<h2>` must follow an
    `<h1>` ancestor; `<h3>` follows `<h2>`. Check `/me`, `/edge/{id}`,
    `/explore`.

### Validation

Run [axe-core](https://github.com/dequelabs/axe-core-npm) via
`@axe-core/cli`. Add to `package.json` as a dev dependency:

```bash
npm install --save-dev @axe-core/cli
# then
npx axe http://127.0.0.1:8000/ -d 100  # plus a few other routes
```

PR body must include:
1. axe-core report for `/`, `/edge/1`, `/me`, `/explore`, `/discoveries`
   showing **0 critical and 0 serious violations**
2. Before/after Lighthouse accessibility score for `/` (should reach ≥95)
3. List of CSS color changes made (so the visual diff is reviewable)

### Don't touch

- Color palette tokens for tier and brand colors (`--tier-A`, `--gold`,
  `--primary`) — those are the brand. You can adjust `--muted` and
  `--ink-soft` if needed for contrast.
- The Fraunces / Inter font choices.
- `web/illustrations.py` — leave the SVG art alone.
- Any Python file other than tiny ARIA-related template tweaks.

---

## Track C — PMID retraction watcher

### Branch: `feat/pmid-watcher`

### Scope

Add a recurring job that re-checks every PMID in the `evidence` table
against PubMed and flags retracted papers. Retracted citations should
be visibly marked in the UI and the affected edges should be queued for
review.

### What to build

1. **`pmid_watcher.py`** — script that:
   - Pulls all distinct PMIDs from `evidence` table
   - Hits PubMed esummary in batches of 100 with rate-limit (`0.4s`
     between requests)
   - Checks for retraction signals in the response: `pubtype` containing
     "Retracted Publication" or "Retraction of Publication", or
     `recordstatus` indicating retraction
   - Writes a row to a new `evidence_status` table for each PMID
     checked (`pmid`, `is_retracted`, `last_checked`, `note`)
   - For any newly-detected retraction, also writes an
     `edge_history` row (`actor='pmid_watcher'`,
     `reason='evidence row {citation} was retracted'`)

2. **Schema migration `migrations/002_add_evidence_status.py`**:
   ```sql
   CREATE TABLE IF NOT EXISTS evidence_status (
     pmid          TEXT PRIMARY KEY,
     is_retracted  INTEGER NOT NULL DEFAULT 0,
     retraction_note TEXT,
     last_checked  TEXT NOT NULL DEFAULT (datetime('now'))
   );
   CREATE INDEX IF NOT EXISTS idx_status_retracted
     ON evidence_status(is_retracted);
   ```

3. **UI changes in `web/templates/edge.html`**:
   - For each evidence row, JOIN against `evidence_status` and show a
     red "RETRACTED" pill next to the citation if `is_retracted=1`
   - At the top of the page, if any evidence is retracted, show a
     prominent banner: "This edge has N retracted study/studies. Tier
     should be reconsidered."

4. **launchd plist** `launchd/com.healthuniverse.weekly-pmid.plist`:
   - Runs `python pmid_watcher.py` once a week (Sunday 04:30)
   - Logs to `data/logs/pmid-watcher-YYYYMMDD.log`
   - On detected retractions, ntfy push notification with edge IDs

5. **Tests** in `tests/test_pmid_watcher.py`:
   - Mock the PubMed esummary response with a known retracted PMID
     (e.g. `12345678` with `pubtype: ["Retracted Publication"]`)
   - Assert `evidence_status` row created with `is_retracted=1`
   - Assert `edge_history` row written

### Validation

```bash
python migrations/002_add_evidence_status.py
python pmid_watcher.py --limit 50    # smoke test on a small sample
python -m pytest tests/test_pmid_watcher.py -v
```

PR body:
1. Output of the smoke test (50-PMID run, summary line)
2. pytest output showing all new tests pass
3. Screenshot of an `/edge/{id}` page with a (test-injected) retracted
   row showing the red pill
4. The launchd plist content

---

## Track D — Counter-evidence sidebar

> Note for the reviewer: Track B was merged 2026-05-05. Track A and
> Track C are still open. Track D is new as of this revision.

### Branch: `feat/codex-counter-evidence`

### Why this matters

Right now `/edge/{id}` shows only studies that *support* the edge's
direction. That's an honesty problem. For tier-X (contested) edges
especially, but also for tier-A/B, credibility jumps when we
side-by-side the strongest disagreeing studies. This is what real
researchers look for first when reading a claim.

### What to build

#### 1. Schema migration `migrations/003_add_counter_evidence.py`

Add a boolean column to the existing `evidence` table:

```sql
ALTER TABLE evidence ADD COLUMN is_counter INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_evidence_counter
  ON evidence(edge_id, is_counter);
```

Idempotent — check `PRAGMA table_info(evidence)` before adding (same
pattern as `migrations/001_add_embeddings.py`).

#### 2. New payload format under `data/counter_evidence_payloads/`

Each file is `{factor_slug}__{outcome_slug}.json`:

```json
{
  "schema_version": 1,
  "factor_slug":  "vitamin_d",
  "outcome_slug": "cvd",
  "edge_direction": "protective",
  "counter_evidence": [
    {
      "citation":      "Bjelakovic G et al 2014 Cochrane Database Syst Rev",
      "pmid":          "24414552",
      "doi":           "10.1002/14651858.CD007470.pub3",
      "year":          2014,
      "study_type":    "systematic_review",
      "n_participants": 95286,
      "direction":     "neutral",
      "quality":       "high",
      "notes":         "Cochrane review found no consistent reduction in cardiovascular mortality from vitamin D supplementation in adults; effect was confined to all-cause mortality with vitamin D3."
    }
  ]
}
```

#### 3. Extend `seed_from_payloads.py`

Add a new mode `seed_from_payloads.py counter ingest` and
`counter validate --verify`. Reuses the existing `verify_citations`
function. Additional rule: every counter row's `direction` MUST DIFFER
from the existing edge's `direction` (else it's just normal supporting
evidence). Validator must look up the edge to check this.

When ingesting, set `is_counter=1` on the inserted evidence rows. Write
an `edge_history` row with `actor='codex_counter'` and
`reason='added counter-evidence'`.

#### 4. UI changes in `web/templates/edge.html`

Add a separate panel below the supporting Evidence table:

```jinja
{% if counter_evidence %}
<h2>Counter-evidence ({{ counter_evidence|length }})</h2>
<p class="muted body-sm">High-quality studies that disagree with the
direction above. We show them so the picture stays honest.</p>
<table class="evidence-table evidence-counter">
  ...
</table>
{% endif %}
```

Update the `/edge/{id}` route in `web/app.py` to fetch counter rows
separately:

```python
evidence = conn.execute(
    "SELECT * FROM evidence WHERE edge_id=? AND is_counter=0 "
    "ORDER BY year DESC", (edge_id,)).fetchall()
counter = conn.execute(
    "SELECT * FROM evidence WHERE edge_id=? AND is_counter=1 "
    "ORDER BY year DESC", (edge_id,)).fetchall()
```

For tier-X edges, render the counter panel **expanded by default** (it's
the whole point of tier-X — both sides matter equally).

CSS: tint counter rows with `--tier-X-bg` left border so the panel reads
visually different from the supporting table without being aggressive.

#### 5. Coverage requirements

Submit counter-evidence payloads for **at least these target edges** —
get them from the live API:

```bash
# All current tier-X edges (whole point of the panel)
curl 'https://health-universe.vercel.app/api/edges?tier=X&limit=50'
# Top 30 tier-A edges (highest stakes; counter-evidence here is most valuable)
curl 'https://health-universe.vercel.app/api/edges?tier=A&limit=30'
# Plus any tier-B edge where you happen to know a strong counter exists
```

Aim for **80–120 counter-evidence files**, each with 1–4 disagreeing
studies. Don't pad — if a tier-A edge truly has no high-quality
counter-evidence, skip it. Quality > quantity.

#### 6. Tests in `tests/test_counter_evidence.py`

- Schema migration is idempotent (running twice is safe)
- Validator rejects a counter row whose `direction` matches the edge's
  direction
- Validator rejects a counter row without a PMID for stat-quantitative
  study types (reuses Track-A rules)
- Ingester sets `is_counter=1`
- `/edge/{id}` route returns counter rows in the response when present
- Tier-X page shows the counter panel expanded

### Validation gate

```bash
git checkout -b feat/codex-counter-evidence
python migrations/003_add_counter_evidence.py
source .venv/bin/activate
python seed_from_payloads.py counter validate --verify  # MUST end "0 failed"
python seed_from_payloads.py counter ingest --dry-run
python -m pytest tests/test_counter_evidence.py -v
```

PR body must include:
1. Full `--verify` output ending "0 failed"
2. Number of edges covered, broken down by tier (A / B / X)
3. 5 random `(factor, outcome, counter PMID, year, journal, direction)`
   rows
4. Screenshot of an `/edge/{id}` page (any tier-X edge) showing the
   counter panel rendered

### Quality bar

- Counter-evidence must come from **real high-quality studies that
  genuinely disagree**, not weak studies cherry-picked to muddy the
  water. A Cochrane review concluding "no effect" against a tier-A
  "protective" claim is gold; a single low-quality cross-sectional that
  happened to find no association is not.
- Notes field must explain *why* the study disagrees — the design
  difference, the population, the timeframe — not just restate the
  finding.
- If a tier-A edge has no honest counter-evidence after good-faith
  searching, **say so in the PR description rather than fabricating**.
  The reviewer would rather see "tier-A on alcohol → breast cancer:
  could find no high-quality counter-evidence; the effect is too well
  established" than weak filler.

### Don't touch

- `seed.py`, `adjudicate.py`, `claude_client.py` — paid path
- `web/illustrations.py` — visual identity is locked
- The existing `evidence` rows (`is_counter=0`) — don't repoint them
- Tier values, direction values, summary, mechanism — those are owned
  by the edge, not by counter-evidence

---

## Hand-off summary — what to tell Codex

> Pick a track. One PR per track. Don't combine.
>
> **Track A** (most content): `CODEX_BRIEF_V4.md` §A — produce ~250
> payloads, run `validate --verify`, PR.
>
> **Track B** ✅ shipped 2026-05-05. Skip.
>
> **Track C** (most plumbing): `CODEX_BRIEF_V4.md` §C — build PMID
> retraction watcher with schema migration, UI integration, launchd
> job, and tests. PR.
>
> **Track D** (highest credibility upgrade): `CODEX_BRIEF_V4.md` §D —
> counter-evidence sidebar. New schema column, new payload format,
> extends the existing validator, UI panel on `/edge/{id}`. ~80-120
> counter-evidence files prioritising tier-X and tier-A edges. PR.
>
> Repo etiquette in `AGENTS.md`. Don't run our paid Claude paths. Don't
> touch the schema except as part of Track C's or Track D's migration.
> PRs only.

---

## Why separate tracks (rather than one big PR)

Each is small enough to review independently:
- **A** is data only — no code changes.
- **B** is CSS + template tweaks, no Python logic. ✅ shipped.
- **C** is one new module + schema migration + tests + plist — clearly
  scoped and doesn't touch existing routes' logic.

- **D** is a new schema column + a new payload format + an additive UI
  panel — touches the same areas C touches but cleanly separable.

If you do all open ones (A, C, D), ship them as three separate PRs in
order A → C → D. Each lands independently.
