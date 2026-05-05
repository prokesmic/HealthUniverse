Repo: https://github.com/prokesmic/HealthUniverse

Read `AGENTS.md` first.

Then read this index:
- https://raw.githubusercontent.com/prokesmic/HealthUniverse/codex/claude-homepage-box-art-brief/docs/claude_subpage_briefs/00_INDEX.md

Your job:
- redesign the subpages of Health Universe using the published briefs in that folder
- preserve the existing FastAPI + Jinja + SQLite architecture
- preserve all existing route behavior, data behavior, and non-UI product logic unless a brief explicitly calls for a structural change
- keep the same cream / forest / ochre / editorial brand world

Hard rules:
- one PR per brief or per tightly related page family only
- do not combine unrelated page redesigns into one giant branch
- start from `main`
- create a fresh branch for each task
- open a PR into `main`
- do not merge
- do not touch paid Claude paths
- do not touch schema / ingest / cost-cap / AGENTS avoid-list files unless genuinely required for the assigned page
- preserve accessibility and mobile usability

Working order:
1. `/edge/{id}` using `08_EDGE_DETAIL.md`
2. `/discoveries` using `01_DISCOVERIES.md`
3. `/tier/{tier}` and `/category/{slug}` using `10_TIER_AND_CATEGORY_LISTS.md`
4. `/search` using `09_SEARCH.md`
5. `/myths` using `11_MYTHS_AND_CONTESTED.md`
6. `/changes` using `12_CHANGES_FEED.md`
7. `/me` using `02_MY_STACK.md`
8. `/risk` using `04_RISK_DIAL.md`
9. `/ask` using `03_ASK.md`
10. `/diary` using `05_STACK_DIARY.md`
11. `/explore` using `07_GRAPH_EXPLORER.md`
12. `/about` using `06_ABOUT.md`

Process for every task:
1. Branch from `main`
2. Read only the relevant brief plus any directly related template/CSS files
3. Implement the redesign for that page
4. Run the app locally
5. Verify the target route visually
6. Run at least these checks when applicable:
   - `GET /`
   - the target route for the page you changed
   - one adjacent route if your CSS/template changes are shared
7. Include verification notes in the PR description
8. Stop after opening the PR

PR requirements:
- title should clearly name the page/task
- PR description should include:
  - which brief was used
  - what changed visually
  - what routes were checked
  - any remaining limitations or intentional follow-ups

Route map:
- `/discoveries`
- `/me`
- `/ask`
- `/risk`
- `/diary`
- `/about`
- `/explore`
- `/edge/{id}`
- `/search`
- `/tier/{tier}`
- `/category/{slug}`
- `/myths`
- `/changes`

Visual standard:
- premium editorial health product
- less dashboard, more evidence publication
- clearer hierarchy
- stronger card composition
- better typography rhythm
- better empty states
- trust and readability first

Important:
- do not redesign everything at once
- do not improvise beyond the brief for a page
- finish one page well, open the PR, then move to the next

First task:
- start with `/edge/{id}`
- use:
  - https://raw.githubusercontent.com/prokesmic/HealthUniverse/codex/claude-homepage-box-art-brief/docs/claude_subpage_briefs/08_EDGE_DETAIL.md

