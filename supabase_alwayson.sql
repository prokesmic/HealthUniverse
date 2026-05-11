-- Health Universe — always-on assistant schema.
-- Paste into Supabase SQL editor and run once.

-- ─── synced_data ─────────────────────────────────────────────────
-- End-to-end encrypted blob of the user's localStorage personal
-- data. The server stores ciphertext bytes only. Decryption key
-- lives client-side, derived from the user's passphrase.
create table if not exists public.synced_data (
  account_id uuid primary key references public.accounts(id) on delete cascade,
  ciphertext text not null,
  iv text not null,             -- IV for AES-GCM
  salt text not null,           -- salt for PBKDF2 key derivation
  iterations int not null default 200000,
  updated_at timestamptz default now(),
  size_bytes int generated always as (length(ciphertext)) stored
);

alter table public.synced_data enable row level security;
create policy "synced_select_own" on public.synced_data
  for select using (auth.uid() = account_id);
create policy "synced_upsert_own" on public.synced_data
  for insert with check (auth.uid() = account_id);
create policy "synced_update_own" on public.synced_data
  for update using (auth.uid() = account_id);
create policy "synced_delete_own" on public.synced_data
  for delete using (auth.uid() = account_id);

-- ─── compute_summaries ───────────────────────────────────────────
-- The user's OPT-IN minimal "summary view" the server can read
-- to run the daily compute on their behalf. Holds derived numbers
-- only (z-scores, trend deltas, watchlist edge IDs, open
-- recommendations, next visit date) — NOT raw lab values, NOT raw
-- wearable streams. Users who want maximum privacy can leave this
-- empty and only get the weekly briefing.
create table if not exists public.compute_summaries (
  account_id uuid primary key references public.accounts(id) on delete cascade,
  updated_at timestamptz default now(),
  timezone text default 'UTC',          -- IANA TZ, e.g. 'America/Los_Angeles'
  watch_edges int[] default '{}',
  anomaly_zscores jsonb default '{}'::jsonb,  -- e.g. {"rhr":{"z":2.1,"dir":"up","ts":"..."}}
  recent_trends jsonb default '{}'::jsonb,    -- e.g. {"sleep_hours":{"7d":7.1,"30d":7.4}}
  open_recommendations jsonb default '[]'::jsonb,  -- mirrored from recommendations_log
  next_visit jsonb,                            -- {"date":"YYYY-MM-DD","clinician":"..."}
  flagged_labs jsonb default '[]'::jsonb,      -- [{"name":"ApoB","value":118,"direction":"high"}]
  active_protocols jsonb default '[]'::jsonb,  -- {"factor":"creatine","ends_at":"..."}
  agreed_to_daily_compute boolean default false,
  agreed_at timestamptz
);

alter table public.compute_summaries enable row level security;
create policy "summary_select_own" on public.compute_summaries
  for select using (auth.uid() = account_id);
create policy "summary_upsert_own" on public.compute_summaries
  for insert with check (auth.uid() = account_id);
create policy "summary_update_own" on public.compute_summaries
  for update using (auth.uid() = account_id);

-- ─── push_subscriptions ──────────────────────────────────────────
-- Web Push API subscription endpoints. One per device.
create table if not exists public.push_subscriptions (
  id uuid primary key default gen_random_uuid(),
  account_id uuid references public.accounts(id) on delete cascade,
  endpoint text unique not null,
  p256dh text not null,
  auth text not null,
  created_at timestamptz default now(),
  last_seen_at timestamptz default now(),
  user_agent text
);

alter table public.push_subscriptions enable row level security;
create policy "push_select_own" on public.push_subscriptions
  for select using (auth.uid() = account_id);
create policy "push_insert_own" on public.push_subscriptions
  for insert with check (auth.uid() = account_id);
create policy "push_delete_own" on public.push_subscriptions
  for delete using (auth.uid() = account_id);

-- ─── daily_briefings (memory) ────────────────────────────────────
-- Each daily compute produces one row. The next day's compute reads
-- the last 7 rows to ground its output ("4 days in a row your sleep
-- has been below 6h…"). This is what makes the system have memory.
create table if not exists public.daily_briefings (
  id uuid primary key default gen_random_uuid(),
  account_id uuid references public.accounts(id) on delete cascade,
  generated_at timestamptz default now(),
  generated_for_date date not null,
  headline text,
  observations jsonb default '[]'::jsonb,
  actions jsonb default '[]'::jsonb,
  doctor_question text,
  trends_snapshot jsonb,
  sent_via text[] default '{}',
  unique (account_id, generated_for_date)
);

alter table public.daily_briefings enable row level security;
create policy "briefings_select_own" on public.daily_briefings
  for select using (auth.uid() = account_id);

create index if not exists idx_briefings_account_date on public.daily_briefings (account_id, generated_for_date desc);

-- ─── shift_alerts (event-driven, Move 5) ─────────────────────────
-- When the corpus's edge_history changes for an edge on the user's
-- watch_edges, we queue an alert here. The push-sender cron drains
-- this table.
create table if not exists public.shift_alerts (
  id uuid primary key default gen_random_uuid(),
  account_id uuid references public.accounts(id) on delete cascade,
  edge_id int not null,
  shift_kind text not null,
  old_value text,
  new_value text,
  changed_at timestamptz not null,
  queued_at timestamptz default now(),
  delivered_at timestamptz,
  delivered_via text
);

alter table public.shift_alerts enable row level security;
create policy "shifts_select_own" on public.shift_alerts
  for select using (auth.uid() = account_id);

create index if not exists idx_shifts_pending on public.shift_alerts (account_id) where delivered_at is null;
