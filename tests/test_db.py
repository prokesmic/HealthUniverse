def test_upsert_entity_idempotent(tmpdb):
    with tmpdb.connect() as conn:
        a = tmpdb.upsert_entity(conn, "magnesium", "Magnesium", "supplement")
        b = tmpdb.upsert_entity(conn, "magnesium", "Magnesium", "supplement")
    assert a == b


def test_record_cost_and_total(tmpdb):
    with tmpdb.connect() as conn:
        tmpdb.record_cost(conn, provider="anthropic", model="claude-sonnet-4-6",
                          operation="seed", input_tokens=1000, output_tokens=500,
                          usd=0.0105, ref="t1")
        tmpdb.record_cost(conn, provider="anthropic", model="claude-sonnet-4-6",
                          operation="adjudicate", input_tokens=2000, output_tokens=1000,
                          usd=0.021, ref="t2")
    with tmpdb.connect() as conn:
        assert tmpdb.total_spent_usd(conn) == 0.0315


def test_edge_unique_constraint(tmpdb, seeded):
    with tmpdb.connect() as conn:
        # Same (factor, outcome, population) should fail
        try:
            conn.execute(
                "INSERT INTO edge (factor_id, outcome_id, direction, tier, "
                "summary, mechanism, population, seed_source) "
                "VALUES (?, ?, 'protective', 'B', '', '', 'general adult', 'claude_seed')",
                (seeded["factor_id"], seeded["outcome_id"]))
            assert False, "expected unique violation"
        except Exception as e:
            assert "UNIQUE" in str(e).upper()
