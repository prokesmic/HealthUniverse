import pytest
from claude_client import cost_of
from seed import _validate


def test_cost_of_math():
    assert cost_of("claude-sonnet-4-6", 1_000_000, 0) == 3.0
    assert cost_of("claude-sonnet-4-6", 0, 1_000_000) == 15.0
    assert cost_of("claude-haiku-4-5", 500_000, 500_000) == 3.0


def test_validate_accepts_good():
    _validate({
        "direction": "protective", "tier": "B", "effect_size": "small",
        "population": "adults", "mechanism": "...", "summary": "...",
        "evidence": [{"citation": "X 2024"}],
    })


def test_validate_rejects_bad_direction():
    with pytest.raises(ValueError):
        _validate({"direction": "bad", "tier": "A", "effect_size": "small",
                   "population": "x", "mechanism": "y", "summary": "z",
                   "evidence": [{"citation": "X 2024"}]})


def test_validate_rejects_bad_tier():
    with pytest.raises(ValueError):
        _validate({"direction": "protective", "tier": "Z", "effect_size": "small",
                   "population": "x", "mechanism": "y", "summary": "z",
                   "evidence": [{"citation": "X 2024"}]})


def test_validate_rejects_empty_evidence():
    with pytest.raises(ValueError):
        _validate({"direction": "protective", "tier": "A", "effect_size": "small",
                   "population": "x", "mechanism": "y", "summary": "z",
                   "evidence": []})


def test_payload_validator_catches_codex_v1():
    """The v2 validator's anti-fabrication rules must reject Codex v1 style."""
    from seed_from_payloads import validate_payload, verify_citations
    payload = {
        "schema_version": 1,
        "edges": [{
            "factor_slug": "magnesium", "outcome_slug": "sleep_quality",
            "direction": "protective", "tier": "B",
            "summary": "x" * 100, "mechanism": "y" * 80,
            "evidence": [
                {"citation": "M 2023 Sleep Med", "study_type": "meta_analysis",
                 "quality": "high", "notes": "test"},
            ],
        }],
    }
    errs = validate_payload(payload, known_factor_slugs={"magnesium"},
                            known_outcome_slugs={"sleep_quality"})
    # Need at least 3 evidence rows
    assert any("evidence must have >=3" in e for e in errs)
    # Single-letter author + missing PMID + missing n_participants
    errs2 = verify_citations(payload, pubmed_cache={})
    assert any("requires a PMID" in e for e in errs2)
    assert any("single-letter token" in e for e in errs2)
    assert any("requires n_participants" in e for e in errs2)
