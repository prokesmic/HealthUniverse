from __future__ import annotations

import pytest

from claude_client import cost_of
from seed import _validate


def test_cost_of_math_is_correct():
    assert cost_of("claude-sonnet-4-6", 1_000_000, 0) == 3.0
    assert cost_of("claude-sonnet-4-6", 0, 1_000_000) == 15.0
    assert cost_of("claude-haiku-4-5", 500_000, 500_000) == 3.0


def test_validate_accepts_good_payload():
    payload = {
        "direction": "protective",
        "tier": "B",
        "effect_size": "small",
        "population": "general adult",
        "mechanism": "May support relaxation pathways.",
        "summary": "Some evidence suggests improved sleep quality.",
        "evidence": [{"citation": "Smith 2024", "study_type": "rct"}],
    }
    _validate(payload)


def test_validate_rejects_bad_payload():
    with pytest.raises(ValueError):
        _validate({"direction": "wrong", "tier": "A", "effect_size": "small", "population": "x", "mechanism": "y", "summary": "z", "evidence": [{}]})

    with pytest.raises(ValueError):
        _validate({
            "direction": "protective",
            "tier": "A",
            "effect_size": "small",
            "population": "general adult",
            "mechanism": "x",
            "summary": "y",
            "evidence": [],
        })
