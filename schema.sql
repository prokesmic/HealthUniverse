-- Health Universe knowledge graph schema
-- Entities are factors (foods, nutrients, supplements, drugs, activities,
-- behaviors, environmental, pathogens, genes, biomarkers) and outcomes
-- (conditions, biomarkers, processes). Edges are factor->outcome claims
-- with confidence tier, populated and re-scored over time.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS entity (
    id            INTEGER PRIMARY KEY,
    slug          TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    kind          TEXT NOT NULL CHECK (kind IN (
                    'food','nutrient','supplement','drug','activity',
                    'behavior','environmental','pathogen','gene',
                    'biomarker','condition','process')),
    aliases       TEXT,           -- JSON array
    description   TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_entity_kind ON entity(kind);

CREATE TABLE IF NOT EXISTS edge (
    id              INTEGER PRIMARY KEY,
    factor_id       INTEGER NOT NULL REFERENCES entity(id),
    outcome_id      INTEGER NOT NULL REFERENCES entity(id),
    direction       TEXT NOT NULL CHECK (direction IN (
                      'protective','harmful','neutral','u_shaped','mixed')),
    tier            TEXT NOT NULL CHECK (tier IN ('A','B','C','D','X','deprecated')),
    effect_size     TEXT,         -- qualitative: trivial/small/moderate/large
    effect_quant    TEXT,         -- e.g. "RR 0.82 (0.74-0.91)"
    population      TEXT,         -- e.g. "adults>50; ApoE4 carriers"
    mechanism       TEXT,         -- 1-paragraph plain English
    summary         TEXT,         -- card body copy
    caveats         TEXT,
    seed_source     TEXT NOT NULL CHECK (seed_source IN ('claude_seed','gemma_daily','manual')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_reviewed   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(factor_id, outcome_id, population)
);

CREATE INDEX IF NOT EXISTS idx_edge_tier ON edge(tier);
CREATE INDEX IF NOT EXISTS idx_edge_factor ON edge(factor_id);
CREATE INDEX IF NOT EXISTS idx_edge_outcome ON edge(outcome_id);

-- Evidence rows underpin every edge. We keep them granular so we can
-- re-score edges as new evidence arrives.
CREATE TABLE IF NOT EXISTS evidence (
    id            INTEGER PRIMARY KEY,
    edge_id       INTEGER NOT NULL REFERENCES edge(id) ON DELETE CASCADE,
    citation      TEXT NOT NULL,
    url           TEXT,
    doi           TEXT,
    pmid          TEXT,
    year          INTEGER,
    study_type    TEXT CHECK (study_type IN (
                    'meta_analysis','systematic_review','rct','cohort',
                    'case_control','cross_sectional','mechanistic',
                    'animal','case_report','expert_opinion')),
    n_participants INTEGER,
    direction     TEXT,           -- direction this study supports
    quality       TEXT CHECK (quality IN ('high','moderate','low','very_low')),
    notes         TEXT,
    source_id     INTEGER REFERENCES source(id),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_evidence_edge ON evidence(edge_id);
CREATE INDEX IF NOT EXISTS idx_evidence_pmid ON evidence(pmid);

CREATE TABLE IF NOT EXISTS evidence_status (
    pmid            TEXT PRIMARY KEY,
    is_retracted    INTEGER NOT NULL DEFAULT 0,
    retraction_note TEXT,
    last_checked    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_status_retracted
    ON evidence_status(is_retracted);

-- History: every tier change recorded so cards can show "what changed".
CREATE TABLE IF NOT EXISTS edge_history (
    id          INTEGER PRIMARY KEY,
    edge_id     INTEGER NOT NULL REFERENCES edge(id) ON DELETE CASCADE,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    field       TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    reason      TEXT,
    actor       TEXT             -- 'claude_seed','gemma_daily','claude_adjudicator','human'
);

CREATE TABLE IF NOT EXISTS source (
    id            INTEGER PRIMARY KEY,
    slug          TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    kind          TEXT NOT NULL,   -- 'journal','registry','agency','press','preprint'
    trust_weight  REAL NOT NULL DEFAULT 1.0,  -- 0..2
    homepage      TEXT,
    notes         TEXT
);

-- Topic matrix: the seed pairs we want Claude to research.
CREATE TABLE IF NOT EXISTS seed_topic (
    id           INTEGER PRIMARY KEY,
    factor_slug  TEXT NOT NULL,
    outcome_slug TEXT NOT NULL,
    priority     INTEGER NOT NULL DEFAULT 5,   -- 1=highest
    status       TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','running','done','failed','skipped')),
    edge_id      INTEGER REFERENCES edge(id),
    cost_usd     REAL,
    error        TEXT,
    started_at   TEXT,
    finished_at  TEXT,
    UNIQUE(factor_slug, outcome_slug)
);

CREATE INDEX IF NOT EXISTS idx_seed_status ON seed_topic(status);

-- Daily ingestion: abstracts we've seen, so we don't reprocess.
CREATE TABLE IF NOT EXISTS ingested_paper (
    id            INTEGER PRIMARY KEY,
    pmid          TEXT UNIQUE,
    doi           TEXT UNIQUE,
    title         TEXT NOT NULL,
    abstract      TEXT,
    journal       TEXT,
    year          INTEGER,
    source_id     INTEGER REFERENCES source(id),
    fetched_at    TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at  TEXT,
    extraction    TEXT             -- JSON of extracted claims
);

CREATE INDEX IF NOT EXISTS idx_paper_processed ON ingested_paper(processed_at);

-- Cost ledger so we can enforce the cap.
CREATE TABLE IF NOT EXISTS cost_ledger (
    id            INTEGER PRIMARY KEY,
    occurred_at   TEXT NOT NULL DEFAULT (datetime('now')),
    provider      TEXT NOT NULL,   -- 'anthropic'
    model         TEXT NOT NULL,
    operation     TEXT NOT NULL,   -- 'seed','adjudicate'
    input_tokens  INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    usd           REAL NOT NULL,
    ref           TEXT             -- e.g. seed_topic id
);
