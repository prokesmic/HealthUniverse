-- Breakthroughs feed — Supabase mirror.
-- v1 reads/writes data/breakthroughs.json on disk. This schema is the
-- target for v2 when we want admin write-back, per-user save/dismiss,
-- and cross-device sync of the seen/unseen state.

create table if not exists breakthroughs (
  id              text primary key,
  published_at    date not null,
  category        text not null check (category in
                   ('oncology','cardio','metabolic','neuro','longevity','other')),
  stage           text not null check (stage in
                   ('preclinical','phase1','phase2','phase3','approved','guideline','recall')),
  headline        text not null,
  summary         text not null,
  why_it_matters  text,
  graphic         jsonb not null,
  strength        real  not null check (strength between 0 and 1),
  source_name     text  not null,
  source_url      text  not null,
  factor_slug     text,
  outcome_slug    text,
  edge_id         text,
  is_orphan       boolean not null default true,
  ingested_at     timestamptz not null default now()
);

create index if not exists breakthroughs_published_at_idx
  on breakthroughs (published_at desc);
create index if not exists breakthroughs_cat_pub_idx
  on breakthroughs (category, published_at desc);
create index if not exists breakthroughs_orphan_idx
  on breakthroughs (is_orphan) where is_orphan = true;

-- RLS: feed is public-read; only the cron service role writes.
alter table breakthroughs enable row level security;

drop policy if exists "Breakthroughs are publicly readable" on breakthroughs;
create policy "Breakthroughs are publicly readable"
  on breakthroughs for select using (true);

-- Per-user save/dismiss state (lets the home band hide what you've seen).
create table if not exists breakthroughs_user_state (
  account_id      uuid not null references auth.users(id) on delete cascade,
  breakthrough_id text not null references breakthroughs(id) on delete cascade,
  state           text not null check (state in ('saved','dismissed','seen')),
  updated_at      timestamptz not null default now(),
  primary key (account_id, breakthrough_id)
);

alter table breakthroughs_user_state enable row level security;
drop policy if exists "Users manage their own state" on breakthroughs_user_state;
create policy "Users manage their own state"
  on breakthroughs_user_state for all
  using  (auth.uid() = account_id)
  with check (auth.uid() = account_id);
