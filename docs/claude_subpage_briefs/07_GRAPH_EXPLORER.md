# Claude Brief: Graph Explorer

Route:
- `/explore`

Files:
- `web/templates/explore.html`
- `web/static/style.css`

Goal:
- Make `/explore` feel like a real knowledge-graph exploration surface, not a plain SVG demo.

Current function to preserve:
- entity picker
- focus-based graph rendering
- edge list
- in-page filter
- links from nodes and edges

Design direction:
- elegant research map
- more spatial, more intentional, more premium
- should still feel light and fast

What to improve:
- picker panel hierarchy
- focus entity framing
- graph canvas presentation
- edge list styling
- empty state

Acceptance criteria:
- graph view feels like a real exploration tool
- picker is easier to use
- graph remains functional and understandable
- no change to route/data behavior
