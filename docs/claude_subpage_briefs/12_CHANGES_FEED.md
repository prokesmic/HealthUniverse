# Claude Brief: Changes Feed

Route:
- `/changes`

Files:
- `web/templates/changes.html`
- `web/static/style.css`

Goal:
- Make `/changes` feel like a transparent product changelog for evidence movement.

Current function to preserve:
- lists recent edge changes
- shows date, actor, relationship, and tier movement or field change
- links back to the affected edge

Design direction:
- compact, transparent, and credible
- more “evidence operations feed” than generic audit list

What to improve:
- clearer visual distinction for promotions, demotions, and new edges
- stronger hierarchy between date, relationship, and delta
- better empty state

Acceptance criteria:
- page is easier to scan quickly
- important changes stand out immediately
- transparency feels like a product strength
