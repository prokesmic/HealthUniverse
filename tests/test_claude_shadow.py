"""Claude shadow week (17.11.2026): queue → batches → side-by-side results; never touches real files."""
import json

import pytest

import claude_shadow as cs


@pytest.fixture
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "AUDIT", tmp_path)
    monkeypatch.setattr(cs, "QUEUE", tmp_path / "q.jsonl")
    monkeypatch.setattr(cs, "OUT", tmp_path / "out.jsonl")
    monkeypatch.setattr(cs, "MARKER", tmp_path / "SHADOW_ON")
    monkeypatch.delenv("HU_SHADOW", raising=False)
    (tmp_path / "SHADOW_ON").touch()
    monkeypatch.setattr(cs, "claude", lambda *a, **k: pytest.fail("real claude called"))
    return tmp_path


def test_off_without_marker(iso):
    (iso / "SHADOW_ON").unlink()
    cs.record("x", "p", {"a": 1})
    assert not cs.QUEUE.exists()


def test_off_by_env(iso, monkeypatch):
    monkeypatch.setenv("HU_SHADOW", "0")
    cs.record("x", "p", {"a": 1})
    assert not cs.QUEUE.exists()


def test_batches_are_same_site_and_bounded(iso):
    items = [{"site": "a", "prompt": f"p{i}", "system": ""} for i in range(45)] + \
            [{"site": "b", "prompt": "q", "system": ""}]
    bs = cs.batches(items)
    assert all(len(b) <= cs.BATCH for b in bs)
    assert all(len({x["site"] for x in b}) == 1 for b in bs)
    assert sum(len(b) for b in bs) == 46 and len(bs) == 4


def test_batches_respect_char_budget(iso, monkeypatch):
    monkeypatch.setattr(cs, "BATCH_CHARS", 100)
    items = [{"site": "a", "prompt": "x" * 60, "system": ""} for _ in range(3)]
    assert [len(b) for b in cs.batches(items)] == [1, 1, 1]


def test_run_pairs_answers_in_order_and_dedupes(iso):
    for i in range(3):
        cs.record("bt", f"prompt {i}", {"keep": i % 2 == 0})
    cs.record("bt", "prompt 0", {"keep": True})            # same prompt again → asked once
    sent = []

    def fake(prompt, system):
        sent.append(prompt)
        return "here: " + json.dumps([{"keep": True}, {"keep": True}, {"keep": False}])

    st = cs.run(call=fake)
    assert st["calls"] == 1 and st["sent"] == 3 and st["answered"] == 3
    assert "TASK 3" in sent[0] and "TASK 4" not in sent[0]
    rows = [json.loads(l) for l in cs.OUT.read_text().splitlines()]
    assert [r["claude"]["keep"] for r in rows] == [True, True, False]
    assert [r["local"]["keep"] for r in rows] == [True, False, True]
    assert cs.QUEUE.read_text() == ""


def test_failed_call_requeues_then_gives_up(iso):
    cs.record("bt", "p", {"keep": True})

    def boom(prompt, system):
        raise RuntimeError("token expired")

    for _ in range(2):
        assert cs.run(call=boom)["failed_calls"] == 1
        assert cs.QUEUE.read_text().strip()               # back on the queue
    cs.run(call=boom)                                     # third failure: dropped
    assert cs.QUEUE.read_text().strip() == ""
    assert not cs.OUT.exists()


def test_parse_array_pads_and_rejects():
    assert cs.parse_array('[{"a":1}]', 3) == [{"a": 1}, None, None]
    assert cs.parse_array("no json", 2) == [None, None]


def test_agree_and_report(iso):
    assert cs.agree({"keep": True, "tier": "A"}, {"keep": True, "tier": "b"}) == 0.5
    assert cs.agree(None, {"keep": True}) is None
    cs.OUT.write_text(json.dumps({"at": "2026-11-17T06:30", "site": "bt", "local": {"keep": True},
                                  "claude": {"keep": True}}) + "\n")
    assert "bt: 1 prompts" in cs.report() and "agreement 100%" in cs.report()
