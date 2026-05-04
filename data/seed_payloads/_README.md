# Seed payloads

Each `.json` file in this directory is one or more pre-researched
`(factor → outcome)` edges that get ingested into `data/healthuniverse.db`
via `seed_from_payloads.py`.

This is how external contributors (Codex, future PR authors) seed the graph
without using the project owner's Anthropic API key.

See `CODEX_BRIEF_500.md` at the repo root for the full schema and quality
rubric, and the topic list to cover.

To validate every payload here without writing to the DB:

    python seed_from_payloads.py validate

To import everything to the DB:

    python seed_from_payloads.py ingest

Files starting with `_` (like this README) are ignored.
