# Claude Brief: Ask My Universe

Route:
- `/ask`

Files:
- `web/templates/ask.html`
- `web/static/style.css`

Goal:
- Make `/ask` feel like a serious evidence-backed question surface, not a toy chatbot.

Current function to preserve:
- textarea question input
- example prompts
- answer rendering
- refusal / error states
- cited edges linking back to evidence cards

Design direction:
- elegant research-assistant feel
- minimal but confident
- answer area should feel like a premium editorial memo

What to improve:
- better framing for the question composer
- clearer distinction between examples, answer, citations, and disclaimer
- cited edges should look like evidence references, not plain list items
- error state should feel informative, not broken

Acceptance criteria:
- asking a question feels deliberate and high-trust
- returned answer is easy to read and visually structured
- citations feel connected to the graph
- no change to underlying ask logic
