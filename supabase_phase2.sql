-- Health Universe — phase 2 always-on additions.
-- Paste into Supabase SQL Editor and run once.

-- ─── weekly_checkins (the "manual wearable") ─────────────────────
-- A 30-second Sunday-morning self-report. Five fields, scored 1-10
-- with optional free-text. Builds the weekly time-series we don't
-- get from wearable APIs.
create table if not exists public.weekly_checkins (
  id uuid primary key default gen_random_uuid(),
  account_id uuid references public.accounts(id) on delete cascade,
  for_week_start date not null,         -- Monday of the week being scored
  energy int,                            -- 1-10
  sleep_quality int,                     -- 1-10
  mood int,                              -- 1-10
  stress int,                            -- 1-10 (higher = worse)
  new_symptoms text,                     -- free-text
  changed_in_stack text,                 -- free-text: what they started/stopped this week
  submitted_at timestamptz default now(),
  unique (account_id, for_week_start)
);

alter table public.weekly_checkins enable row level security;
create policy "checkins_select_own" on public.weekly_checkins
  for select using (auth.uid() = account_id);
create policy "checkins_insert_own" on public.weekly_checkins
  for insert with check (auth.uid() = account_id);
create policy "checkins_update_own" on public.weekly_checkins
  for update using (auth.uid() = account_id);

create index if not exists idx_checkins_account_week on public.weekly_checkins (account_id, for_week_start desc);

-- ─── intervention_class on recommendations_log ───────────────────
-- Cadence depends on the kind of intervention. Sleep/mood get a 7d
-- check-in; strength/body comp gets 28d/56d/84d; lipid-targeting
-- pairs with a lab recheck at 8w; etc.
alter table public.recommendations_log
  add column if not exists intervention_class text default 'general';

alter table public.recommendations_log
  add column if not exists next_nudge_at timestamptz;

alter table public.recommendations_log
  add column if not exists nudge_count int default 0;

create index if not exists idx_recs_due_nudge
  on public.recommendations_log (next_nudge_at)
  where closed_at is null and next_nudge_at is not null;

-- ─── corpus_feed_state ───────────────────────────────────────────
-- Per-account marker of "the last edge_history change I sent you,"
-- so the daily cron doesn't re-send already-shown shifts.
create table if not exists public.corpus_feed_state (
  account_id uuid primary key references public.accounts(id) on delete cascade,
  last_seen_history_at timestamptz default now()
);

alter table public.corpus_feed_state enable row level security;
create policy "feed_state_select_own" on public.corpus_feed_state
  for select using (auth.uid() = account_id);
create policy "feed_state_upsert_own" on public.corpus_feed_state
  for insert with check (auth.uid() = account_id);
create policy "feed_state_update_own" on public.corpus_feed_state
  for update using (auth.uid() = account_id);
