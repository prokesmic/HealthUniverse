# Claude Brief: Discoveries Page

Route:
- `/discoveries`

Files:
- `web/templates/discoveries.html`
- `web/static/style.css`
- `web/illustrations.py` if needed for discovery-card art

Goal:
- Turn `/discoveries` into a premium “what’s newly important” editorial page.

Current function to preserve:
- shows recent promotions and new high-confidence edges
- paginated
- each card links to its evidence page

Design direction:
- keep it card-based, but make it feel more like a discovery desk than a generic list
- cards should be visually lighter than homepage featured cards, but more premium than the current implementation
- emphasize “newness”, recency, and why this matters

What to improve:
- stronger page intro and hierarchy
- better discovery card composition
- clearer promoted/new status language
- date and evidence count should be visible but secondary

Card treatment:
- use the lighter discovery-card visual system from the homepage brief
- avoid shallow decorative strips
- visual should support the topic without overpowering the headline

Acceptance criteria:
- page feels like a curated feed of newly meaningful findings
- cards are more premium and readable
- pagination still works
- mobile remains clean
