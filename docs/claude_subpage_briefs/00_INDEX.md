# Claude Subpage Briefs Index

Repo: `https://github.com/prokesmic/HealthUniverse`

Read first:
- `AGENTS.md`

These briefs cover the current non-homepage product surfaces in the FastAPI app.
Use them page-by-page. Do not combine unrelated redesign work into one giant PR.

Design north star for all subpages:
- same cream / forest / ochre brand system
- same editorial tone as the premium homepage direction
- more premium health-journal product, less dashboard
- preserve existing logic, routes, and data behavior unless a brief explicitly says otherwise

Brief set:
- `01_DISCOVERIES.md` → `/discoveries`
- `02_MY_STACK.md` → `/me`
- `03_ASK.md` → `/ask`
- `04_RISK_DIAL.md` → `/risk`
- `05_STACK_DIARY.md` → `/diary`
- `06_ABOUT.md` → `/about`
- `07_GRAPH_EXPLORER.md` → `/explore`
- `08_EDGE_DETAIL.md` → `/edge/{id}`
- `09_SEARCH.md` → `/search`
- `10_TIER_AND_CATEGORY_LISTS.md` → `/tier/{tier}`, `/category/{slug}`
- `11_MYTHS_AND_CONTESTED.md` → `/myths`
- `12_CHANGES_FEED.md` → `/changes`

Shared implementation rules:
- do not touch paid Claude paths
- do not change schema or ingestion logic for visual redesign tasks
- preserve accessibility
- preserve mobile usability
- prefer refining existing templates and CSS over framework churn
