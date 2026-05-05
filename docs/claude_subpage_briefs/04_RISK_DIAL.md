# Claude Brief: Risk Dial

Route:
- `/risk`

Files:
- `web/templates/risk.html`
- `web/static/style.css`

Goal:
- Turn `/risk` into a strong “high-leverage factors” view for the user’s profile.

Current function to preserve:
- requires saved profile
- surfaces tier A/B movers
- indicates why each card is relevant
- links to edges

Design direction:
- feels like a personalized briefing
- directional, important, and calm
- should not look like a clinical score calculator

What to improve:
- page intro should better explain what this dial is and is not
- cards should emphasize leverage and direction
- “in your stack” vs “for a condition you track” should read clearly
- empty state should feel useful and motivating

Acceptance criteria:
- page reads like a personalized risk brief
- movers are easier to prioritize visually
- disclaimers remain clear
- underlying ranking logic remains unchanged
