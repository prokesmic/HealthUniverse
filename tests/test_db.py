from __future__ import annotations

import db


def test_db_round_trip_entities_sources_and_costs(isolated_db):
    with db.connect() as conn:
        first = db.upsert_entity(conn, "omega3", "Omega-3", "supplement", aliases=["fish oil"])
        second = db.upsert_entity(conn, "omega3", "Omega-3", "supplement")
        assert first == second

        source_id = db.upsert_source(
            conn,
            slug="pubmed",
            name="PubMed",
            kind="journal",
            trust_weight=2.0,
            homepage="https://pubmed.ncbi.nlm.nih.gov/",
        )
        assert source_id > 0

        db.record_cost(
            conn,
            provider="anthropic",
            model="claude-sonnet-4-6",
            operation="seed",
            input_tokens=1000,
            output_tokens=500,
            usd=0.0105,
            ref="omega3->cvd",
        )

    with db.connect() as conn:
        assert db.total_spent_usd(conn) == 0.0105
