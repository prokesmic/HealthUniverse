# Claude Brief: Premium Homepage Box Art System

Repo: `https://github.com/prokesmic/HealthUniverse`

Read first:
- `AGENTS.md`

Primary goal:
- Redesign the homepage card visuals so they match the premium editorial direction in the supplied screenshot.
- Replace the current abstract SVG strip treatment on homepage cards with a reusable premium box-art system.

Important clarification:
- Do **not** revert to the current abstract band/header graphics.
- Do **not** use generic placeholder gradients.
- The target is the richer **box-led** visual style from the reference:
  - more literal, topic-aware imagery
  - stronger editorial composition
  - cleaner cream content surface for text
  - premium health-publication feel

## Visual target

Use the supplied screenshot as the design reference for:
- hero balance
- category strip placement
- featured card composition
- evidence-strength cards
- right-rail spotlight hierarchy

The key change is in the boxes:
- `Featured Evidence` cards should feel like premium article cards with visual scenes or object-led compositions
- `New discoveries` cards should also be visual, but lighter than featured cards
- `Browse by Evidence Strength` cards should use subtle structured background waves, not literal scenes

## Scope

In scope:
- homepage visual system
- homepage card artwork
- homepage section spacing and composition if needed to support the new box system

Out of scope for now:
- evidence subpage redesign
- search/results pages
- data model changes
- paid Claude paths

## Files to change

Primary:
- `web/templates/home.html`
- `web/static/style.css`
- `web/illustrations.py`

Optional if needed:
- helper code only if necessary to support reusable card-art variants

## Implementation direction

Build a **reusable premium box-art system** with section-specific variants.

### 1. Homepage overall composition

Keep:
- large serif hero on the left
- confidence + spotlight rail on the right
- category strip directly under the hero

Adjust if needed:
- spacing between hero, categories, and featured section
- featured section vertical rhythm so the cards feel like the main editorial block

### 2. Replace current homepage card art treatment

Current problem:
- cards use a shallow abstract art band across the top
- this reads as decorative filler instead of premium content design

Replace with:
- image-led or object-led compositions inside the card box
- visuals that occupy a meaningful portion of the card
- text area on a cleaner cream/soft surface
- stronger separation between visual zone and content zone

### 3. Section-specific visual system

#### A. Featured Evidence cards

These should be the most premium.

Desired composition:
- card has a visual zone that feels designed for the topic
- can be right-heavy, background-heavy, or split composition
- content remains highly readable and restrained

Examples of visual language:
- Mediterranean diet: olive oil, grains, fresh ingredients, warm green-gold palette
- Omega-3 / supplements: capsules, glassy forms, amber highlights
- Oncology-support topics: botanical or molecular forms in a calmer, more editorial composition

Requirements:
- no stock-photo dependence unless already available locally
- use procedural or illustrated compositions if needed
- avoid cheesy medical imagery
- avoid generic AI-slop collage feel

#### B. Discoveries cards

Desired composition:
- smaller/lighter than featured cards
- still clearly more intentional than the current abstract strip
- can use compact scene fragments, object clusters, or simpler topic motifs

Requirements:
- should harmonize with featured cards
- must not overpower the headline

#### C. Evidence Strength cards

Desired composition:
- subtle structured wave or contour treatment at the bottom
- no scene art here
- emphasis remains on dots, label, and blurb

Requirements:
- elegant and quiet
- should echo the homepage hero wave energy from the mock

## Art system requirements

The implementation should scale.

Build `web/illustrations.py` so it can generate **different card-art modes** rather than one generic edge illustration:

Suggested API direction:
- a featured-card mode
- a discovery-card mode
- a subtle strength/wave mode

You do **not** need to use these exact function names, but the system should support distinct visual outputs for different homepage components.

Design principles:
- deterministic output per topic/edge
- warm cream-based palette
- forest, ochre, muted coral, and restrained violet where appropriate
- more representational than the current orbit/blob strip
- still elegant and editorial

Avoid:
- busy scientific doodle fields
- random molecule spam
- flat placeholder gradients
- over-detailed pseudo-photorealism

## Template changes

### home.html

Update homepage sections to support richer box visuals:

- `Featured Evidence`
  - allow a larger visual area or integrated visual block
  - ensure badges and metadata still sit cleanly

- `New discoveries`
  - use a lighter variant of the new card art system

- `Browse by Evidence Strength`
  - use subtle wave/footer art only

### style.css

Introduce section-specific card classes, for example:
- featured card with premium art layout
- discovery card with lighter art layout
- strength card with subtle footer wave

Design goals:
- cleaner hierarchy
- better balance between image and text
- more premium card proportions
- preserve readability and the cream/forest brand system

## Acceptance criteria

The work is done when:

1. Homepage cards no longer use the current abstract top-band treatment.
2. `Featured Evidence` cards feel premium and topic-aware, visually closer to the screenshot.
3. `New discoveries` cards use a lighter but related box-art style.
4. `Browse by Evidence Strength` cards use subtle structured wave/footer treatments.
5. The homepage still feels cohesive with the existing brand.
6. The implementation is reusable, not one-off per card.
7. Mobile remains clean and readable.

## Validation

Run with the existing repo environment if needed:

```bash
"/Users/michal/Documents/New project/HealthUniverse/.venv/bin/python" -m uvicorn web.app:app --port 8011
```

Check:
- `GET /`
- `GET /tier/A`
- `GET /category/nutrition`

Visual QA:
- desktop homepage is the main approval surface
- confirm the cards feel closer to a premium editorial health product than to a data dashboard

## Summary for Claude

Build a scalable homepage card-art system that matches the reference screenshot’s premium editorial box style. Replace the current abstract strip graphics with richer, topic-aware compositions for `Featured Evidence`, lighter related visuals for `New discoveries`, and subtle structured wave treatments for `Browse by Evidence Strength`.
