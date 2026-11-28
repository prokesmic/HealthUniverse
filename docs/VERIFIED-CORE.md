# Verified core and narrowed site — versions and rollback

Shipped 28.11.2026. One module, `web/core.py`, defines what the public
site may show. Everything here can be undone at five levels, smallest
first. Nothing was deleted: switched-off pages are still in the code.

## What changed

| Area | Before | Now |
|---|---|---|
| Home, Discoveries, RSS, social cron | any tier A/B/C edge | verified core only |
| Stack Brief | tier A/B/C/X, 3 items, Pro waitlist | verified core only, 12 items, no waitlist |
| Unchecked edges | published the same night | left out of the web DB until checked |
| Citation check | run by hand | every night before the web DB is built |
| Navigation | 28 links | 5 (Stack Brief, Breakthroughs, Graph, Library, Trust) |
| Labs, SNP, wearables, Prevent, My plan, Start, Coach, Today, Diary, Score, Risk, Protocols, Products, Claim checker, digest sign-up, `/api/me/*` | live | redirect to `/` (pages) or 404 (API) |
| Same event from several sources | one card per source | one card, "+N more sources" |

Levels (`web/core.py`):

- **core** — tier A or B, `review_status = verified_evidence`, at least
  two evidence rows with `relevance_status = verified`.
- **labelled** — everything else that went through the check.
- **hidden** — `unreviewed`, `needs_recheck`, or listed in
  `data/hidden_edges.json`. Removed from the published DB by
  `scripts/build_web_db.py`.

## Versions

| Tag | State |
|---|---|
| `pre-core-2026-11-28` | last commit before this work |
| `core-v1-2026-11-28` | this work, as deployed |

Backup of the working DB taken before the first full citation check:
`~/HealthUniverse-backups/healthuniverse-2026-11-28-pre-core.db`.

## Rollback, smallest first

### 1. One edge

Bring a hand-hidden edge back: delete its row in `data/hidden_edges.json`,
then rebuild and push the web DB (step in "Publish" below). Hide one more:
add a row.

### 2. Switches (no code change)

| Variable | Effect of setting it |
|---|---|
| `HU_NARROW=0` | all switched-off pages and the old navigation return |
| `HU_CORE_GATE=0` | the site stops filtering by level; the builder stops removing hidden edges |
| `HU_CORE_STRICT_PROMOTION=1` | stricter core: an A/B tier last set by the local model alone is not core (off by default) |

On Vercel (site behaviour), then redeploy:

```bash
cd ~/HealthUniverse && printf 0 | vercel env add HU_NARROW production && vercel --prod
```

On the Mac (what the nightly builder publishes): add `HU_CORE_GATE=0` to
`~/HealthUniverse/.env`, then run the "Publish" step. Both sides are needed
to get unchecked edges back on the site: the site-side switch alone only
stops the filtering of what the DB already holds.

To switch back on, remove the variable (`vercel env rm HU_NARROW production`,
delete the `.env` line) and redeploy / republish.

### 3. Previous deployment (seconds, site only)

```bash
cd ~/HealthUniverse && vercel rollback
```

This points production at the previous deployment. The next nightly push
deploys current `main` again, so follow with step 4 if the rollback should
stay.

### 4. Code

```bash
cd ~/HealthUniverse && git revert --no-edit core-v1-2026-11-28 && git push origin main
```

One commit carries the whole change, so one revert removes it. The web DB
committed after it keeps the `public_level` column and lacks the hidden
edges until the next build; run "Publish" to rebuild it without the gate.

### 5. Data

The citation check wrote `evidence.real_title / relevance_score /
relevance_status` and `edge.review_status`. To put those four columns back
as they were in a backup, leaving newer rows alone:

```bash
cd ~/HealthUniverse && .venv/bin/python scripts/restore_review.py --from ~/HealthUniverse-backups/healthuniverse-2026-11-28-pre-core.db
```

That reports only; add `--yes` to write. Whole-DB restore (loses every
edge and study ingested since the backup) is a last resort: stop the
launchd jobs, copy the backup over `data/healthuniverse.db`.

## Publish (rebuild and push the web DB by hand)

```bash
cd ~/HealthUniverse && .venv/bin/python scripts/build_web_db.py && git add data/healthuniverse.web.db && git commit -m "web DB rebuild" && git push origin main
```

The builder refuses to replace the web DB when fewer than 300 edges are
core (`HU_CORE_FLOOR`): that means the check state was lost, and the live
site keeps the previous DB.

## Checking the state

```bash
cd ~/HealthUniverse && .venv/bin/python scripts/build_web_db.py --dry-run
```

prints the level counts without replacing anything. The Trust page shows
the same three numbers for the published DB.
