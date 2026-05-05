# Claude Brief: Must Build Now + High Leverage Next

Repo: `https://github.com/prokesmic/HealthUniverse`

Read first:
- `AGENTS.md`

Reference materials:
- Homepage premium box-art brief:
  - `https://raw.githubusercontent.com/prokesmic/HealthUniverse/codex/claude-homepage-box-art-brief/docs/CLAUDE_HOMEPAGE_PREMIUM_BOX_ART_BRIEF.md`
- Subpage briefs index:
  - `https://raw.githubusercontent.com/prokesmic/HealthUniverse/codex/claude-homepage-box-art-brief/docs/claude_subpage_briefs/00_INDEX.md`

This brief is not about polishing isolated pages.
It is about building the product features that turn Health Universe from a promising evidence site into a uniquely valuable preventive-health platform.

The product category we are aiming for:

**Health Universe = a citation-verifiable, contradiction-aware, continuously rescored personal evidence graph for preventive health, usable by both humans and AI agents.**

Your mission:
- implement the **must-build-now** and **high-leverage-next** features in a sequence of focused PRs
- keep the existing FastAPI + Jinja + SQLite architecture
- preserve the local-first / low-cost philosophy
- preserve citation trust, retraction logic, and evidence rigor

Hard rules:
- one focused PR per feature or tightly related feature family
- branch from `main` every time
- open PR into `main`
- do not merge
- do not run paid `seed.py` / `adjudicate.py`
- do not touch the Claude cost-cap logic
- do not touch avoid-list files from `AGENTS.md` unless required for the feature
- do not degrade accessibility, mobile usability, or API stability

---

## Product priorities

### Must build now

These define the product’s unique proposition and should be built first.

1. Compare mode
2. Profile-aware daily / weekly brief
3. Richer agent / API layer
4. “Red flags in my stack” and “No-regret moves” views
5. Flagship evidence dossier upgrade for edge pages

### High leverage next

These materially improve retention, trust, and defensibility.

6. Supplement product-quality layer
7. Lab / wearable ingestion foundations
8. N-of-1 protocol builder
9. Intent-aware search and guided onboarding
10. Change intelligence and watchlists

---

## Execution order

Build in this order unless code realities force a minor change:

1. Agent / API layer foundation
2. Compare mode
3. Daily / weekly profile brief
4. Red flags + No-regret views
5. Edge dossier upgrade
6. Change intelligence + watchlists
7. Intent-aware search + onboarding
8. Supplement product-quality layer
9. N-of-1 protocol builder
10. Lab / wearable ingestion foundations

Reason:
- APIs first unlock agent usability and make later features easier
- compare + briefing + stack intelligence form the clearest user-facing wedge
- dossier upgrade makes the evidence graph feel premium and trustworthy
- product-quality, experiments, and data ingestion deepen the moat after the core is coherent

---

## MUST BUILD NOW

---

### 1. Richer agent / API layer

Goal:
- make Health Universe genuinely usable by agents, not just browsable by humans

Current state:
- `/api/edges`
- `/api/entities/{slug}`

Build:

#### A. Edge detail API
- Add `GET /api/edges/{id}`
- Return a complete structured payload for one edge:
  - edge metadata
  - factor and outcome objects
  - summary
  - mechanism
  - caveats
  - effect size / effect quant
  - population
  - supporting evidence rows
  - counter-evidence rows
  - retraction status
  - history
  - study-count summary
  - confidence / tier explanation helpers if available

#### B. Compare API
- Add `GET /api/compare`
- Support at least:
  - `?outcome=...&factors=a,b,c`
  - `?factor=...&outcomes=x,y,z`
- Return normalized comparable objects so agents can rank or narrate differences

#### C. Changes API
- Add `GET /api/changes`
- Parameters:
  - `since`
  - `days`
  - optional `tier`
  - optional `direction`
  - optional `factor`
  - optional `outcome`
- Purpose:
  - allow agents and future watchlists to fetch recent evidence movement

#### D. Profile-aware brief API
- Add `GET /api/profile-brief`
- Use saved cookie profile when called from the browser
- Return:
  - top relevant edges
  - red flags
  - no-regret moves
  - what changed recently for this profile
  - top tracked conditions / stack interpretations

#### E. API shape improvements
- Ensure stable field names
- Return canonical citation objects per evidence row:
  - citation
  - pmid
  - doi
  - year
  - study_type
  - n_participants
  - quality
  - direction
  - is_retracted
  - notes
- Add explicit booleans / enums rather than requiring string parsing

#### F. OpenAPI usability
- Ensure endpoints appear cleanly in FastAPI docs
- Add helpful docstrings and response examples where practical

Acceptance criteria:
- an external agent can fetch one edge, compare multiple edges, inspect changes, and get a profile-aware brief without scraping HTML
- JSON is stable, coherent, and easy to narrate from

Suggested PR title:
- `Add structured edge, compare, changes, and profile brief APIs`

---

### 2. Compare mode

Goal:
- help people answer the most important practical question:
  - “What is the best-supported option for my goal?”

Build both:
- API support
- human UI support

#### A. Compare page
- Add a route like `/compare`
- Basic first version can be query-string driven
- Support:
  - compare factors for one outcome
  - compare outcomes for one factor

#### B. Comparison model
- Show each candidate in a consistent frame:
  - tier
  - direction
  - study mix
  - participant volume
  - applicability / population
  - effect size if present
  - contradiction presence
  - retraction flags
  - summary in one concise block

#### C. Comparison outputs
- “Best-supported”
- “Most uncertain”
- “Potential downside”
- “Most applicable to you” if profile exists

#### D. Fast paths
- Support prebuilt flows:
  - `/compare?outcome=sleep_quality&factors=magnesium,melatonin,cbt_i`
  - `/compare?outcome=cardiovascular_disease&factors=mediterranean_diet,exercise,omega_3`

Acceptance criteria:
- users can compare multiple interventions or outcomes without opening many tabs
- the page feels like a decision aid, not a generic table

Suggested PR title:
- `Add evidence compare mode for factors and outcomes`

---

### 3. Profile-aware daily / weekly brief

Goal:
- make the product feel alive and personally relevant every time the user comes back

Build:

#### A. Browser surface
- Add a dedicated brief surface, likely `/brief`
- If profile exists, homepage should be able to link prominently into it

#### B. Daily brief content
- top relevant beneficial moves
- top relevant cautions
- what changed recently in tracked areas
- one featured relationship worth reading

#### C. Weekly brief content
- strongest upgrades or downgrades this week
- notable new evidence in the user’s tracked areas
- unresolved contradictions
- recommended next readings

#### D. Brief logic
- use:
  - profile conditions
  - stack
  - goals if present later
  - recent changes feed
  - tier and direction

#### E. Agent usability
- same logic should feed `/api/profile-brief`

Acceptance criteria:
- returning users immediately see why the product matters to them now
- brief reads like a premium personalized evidence memo

Suggested PR title:
- `Add profile-aware daily and weekly evidence briefs`

---

### 4. Red flags in my stack + No-regret moves

Goal:
- convert the graph into action-oriented personal intelligence

Build:

#### A. Red flags in my stack
- page section or dedicated route
- surface harmful or questionable edges involving factors the user currently does / takes
- prioritize by:
  - tier
  - downside strength
  - relevance to tracked conditions

For each flag show:
- factor
- outcome
- why this matters to the user
- evidence tier
- quick action framing:
  - “review”
  - “monitor”
  - “consider replacing”

#### B. No-regret moves
- surface broad-upside, low-downside factors
- not “the absolute best thing” but strongest beneficial moves with relatively low controversy and broad applicability

For each move show:
- what it helps
- why confidence is high
- why downside is low
- who it is most relevant for

#### C. Integration
- show these inside `/me`, `/risk`, and `/brief`

Acceptance criteria:
- users can quickly see “what to watch out for” and “what is worth doing”
- product becomes more useful without overclaiming medical advice

Suggested PR title:
- `Add stack red flags and no-regret moves views`

---

### 5. Flagship edge dossier upgrade

Goal:
- make `/edge/{id}` the defining trust surface of the product

This is partly visual and partly structural.

Build:

#### A. Stronger dossier hierarchy
- summary, mechanism, caveats, supporting evidence, counter-evidence, history
- present these as clearly segmented sections

#### B. Evidence controls
- filter or sort evidence rows by:
  - study type
  - quality
  - year
  - supporting vs counter

#### C. Evidence summary rail
- compact right-side or top metrics:
  - study mix
  - total rows
  - retractions
  - counter-evidence count
  - last reviewed

#### D. Better contradiction treatment
- if counter-evidence exists, do not bury it
- especially for tier X or high-stakes topics

#### E. Machine-friendly
- align the UI sections with the structured API payload

Acceptance criteria:
- edge page feels like a premium evidence brief
- users can understand trust, uncertainty, and applicability fast

Suggested PR title:
- `Upgrade edge detail into flagship evidence dossier`

---

## HIGH LEVERAGE NEXT

---

### 6. Change intelligence + watchlists

Goal:
- make updates matter to the user, not just exist in a feed

Build:

#### A. Watchlist model
- allow users to watch:
  - factors
  - outcomes
  - categories
  - specific edges

#### B. Personalized changes feed
- page that filters `/changes` through watchlist/profile

#### C. What changed and why
- every important change should explain:
  - promotion / demotion / contradiction / retraction
  - what triggered it
  - what the user may want to review

Acceptance criteria:
- product becomes habit-forming because changes are relevant

Suggested PR title:
- `Add evidence watchlists and personalized change intelligence`

---

### 7. Intent-aware search + guided onboarding

Goal:
- reduce first-session confusion and convert curiosity into useful flows

Build:

#### A. Intent-aware search
- detect queries such as:
  - what helps with X
  - what harms X
  - compare A and B
  - what changed for X
  - best evidence for X

#### B. Guided entry flows
- first-use quick starts such as:
  - improve energy
  - reduce cardiovascular risk
  - cancer prevention
  - improve sleep
  - optimize supplement stack

#### C. Result framing
- route users into compare mode, edge dossiers, category views, or profile setup depending on intent

Acceptance criteria:
- new users understand where to go
- search feels smart, not just lexical

Suggested PR title:
- `Add intent-aware search and guided onboarding flows`

---

### 8. Supplement product-quality layer

Goal:
- add a unique trust layer that evidence libraries and lab dashboards usually lack

This is one of the most defensible future wedges if done carefully.

Build foundation only first:

#### A. Product entity layer
- introduce a way to represent products / brands separately from intervention evidence

#### B. Quality dimensions
- label accuracy
- contamination risk
- dosage alignment with evidence-supported ranges
- third-party testing / certification
- formulation issues

#### C. Product card concept
- not “this supplement works”
- but:
  - “if you choose to take X, here’s which product qualities matter”

Important:
- do not fabricate testing
- if no independent data exists, say so clearly

Acceptance criteria:
- product-quality intelligence is scaffolded without compromising trust

Suggested PR title:
- `Add supplement product-quality data model and UI foundation`

---

### 9. N-of-1 protocol builder

Goal:
- turn Health Universe into a self-experimentation operating system

Build:

#### A. Protocol builder
- user chooses:
  - intervention
  - target outcome
  - duration
  - measures to track

#### B. Protocol template page
- example:
  - magnesium for sleep onset
  - earlier dinner for glucose / sleep
  - creatine for strength / cognition

#### C. Diary integration
- connect protocols to `/diary`

#### D. Interpretation
- simple summaries only
- no fake certainty

Acceptance criteria:
- users can run structured self-experiments using the evidence graph

Suggested PR title:
- `Add N-of-1 protocol builder integrated with diary`

---

### 10. Lab / wearable ingestion foundations

Goal:
- give the product a path toward becoming a true personal evidence operating system

Do not overbuild first pass.

Build foundation:

#### A. Data model + upload hooks
- support basic uploaded lab values and wearable summaries

#### B. First integrations or placeholders
- start with upload-based flow before live sync if needed
- prioritize:
  - bloodwork upload
  - Apple Health / Garmin / Oura / WHOOP-compatible conceptual model

#### C. Relevance integration
- lab or wearable state should influence profile-aware ranking and briefs later

Acceptance criteria:
- architecture is ready for personalization via real measurements
- no fragile overpromising integrations

Suggested PR title:
- `Add foundations for lab and wearable data ingestion`

---

## Cross-feature design rules

- premium editorial, not dashboard clutter
- confidence and contradiction should be first-class UI signals
- every recommendation surface must distinguish:
  - evidence strength
  - personal relevance
  - downside / uncertainty
- trust beats flash
- any “action” language must avoid pretending to be medical advice

---

## Cross-feature product rules

- never fabricate citations
- never hide counter-evidence
- never collapse nuanced evidence into false certainty
- if personalization logic is heuristic, make that clear
- if product-quality data is absent, say so

---

## Recommended PR plan

Use this exact PR sequence:

1. `Add structured edge, compare, changes, and profile brief APIs`
2. `Add evidence compare mode for factors and outcomes`
3. `Add profile-aware daily and weekly evidence briefs`
4. `Add stack red flags and no-regret moves views`
5. `Upgrade edge detail into flagship evidence dossier`
6. `Add evidence watchlists and personalized change intelligence`
7. `Add intent-aware search and guided onboarding flows`
8. `Add supplement product-quality data model and UI foundation`
9. `Add N-of-1 protocol builder integrated with diary`
10. `Add foundations for lab and wearable data ingestion`

Open a separate PR for each.
Do not combine them.

---

## Validation expectations for each PR

For each PR:

1. Run the app locally
2. Verify `/`
3. Verify the target route(s)
4. Verify one adjacent route impacted by shared CSS / shared logic
5. Include verification notes in the PR description

If the feature adds an API:
- include at least one sample request and response shape in the PR description

If the feature adds personalization:
- test with both:
  - empty profile
  - populated profile

---

## Final instruction to Claude

Do not treat this as abstract strategy.
Implement the features in the order above, one focused branch and one PR at a time, using the existing codebase architecture and preserving Health Universe’s trust model.

