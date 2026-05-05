# Claude Brief: Tier and Category Lists

Routes:
- `/tier/{tier}`
- `/category/{slug}`

Files:
- `web/templates/list.html`
- `web/static/style.css`
- `web/illustrations.py` if list-card art variants are needed

Goal:
- Upgrade generic list pages into polished evidence-browsing surfaces.

Current function to preserve:
- title and counts
- paginated edge lists
- per-card summary and metadata
- links into edge pages

Design direction:
- this is browsing, not discovery
- cards should be calmer and more systematic than homepage featured cards
- still premium, but less editorial and more library-like

What to improve:
- page header hierarchy
- list-card consistency
- card density and scanability
- better pagination treatment

Acceptance criteria:
- category and tier pages feel like a high-quality evidence library
- cards are easier to compare
- art, if used, is quieter than homepage featured surfaces
