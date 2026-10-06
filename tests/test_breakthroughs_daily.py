"""breakthroughs_daily: grounding gate, judged-item memory, fair share per source.

Everything external is stubbed before main() runs: RSS, Ollama, the feed
file and the seen file all live in tmp_path / memory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import breakthroughs_daily as bd  # noqa: E402

DESIGN = "This randomized trial assesses the effect of A on B among older adults."


def item(src, n, summary="In 400 patients, A reduced B by 20%."):
    return {"title": f"{src} item {n}", "link": f"https://{src}.example/{n}",
            "summary": summary, "published": "2026-10-05", "source_name": src}


# ─── grounding gate ───────────────────────────────────────────────

def test_gate_rejects_design_only_and_invented_numbers():
    assert "design" in bd.ungrounded(item("j", 1, DESIGN), {"headline": "A helps", "summary": "A improved B."})
    assert "30" in bd.ungrounded(item("j", 2), {"headline": "A cuts B 30%", "summary": "x"})
    assert "letter" in bd.ungrounded({"title": "x", "summary": "To the Editor Dr X", "link": "l"}, {})
    assert bd.ungrounded(item("j", 3), {"headline": "A cuts B by 20%", "summary": "400 patients."}) is None


# ─── interleave ───────────────────────────────────────────────────

def test_interleave_is_round_robin_and_keeps_feed_order():
    c = [item("jama", i) for i in range(5)] + [item("fda", 0), item("stat", 0), item("stat", 1)]
    got = [(x["source_name"], x["title"][-1]) for x in bd.interleave(c)][:5]
    assert got == [("jama", "0"), ("fda", "0"), ("stat", "0"), ("jama", "1"), ("stat", "1")]


# ─── main(): memory of judged links ───────────────────────────────

@pytest.fixture
def world(tmp_path, monkeypatch):
    feeds = {"jama": [item("jama", i) for i in range(30)],
             "fda": [item("fda", i) for i in range(3)]}
    state = {"feed": {"items": []}, "calls": [], "fail": set()}
    monkeypatch.setattr(bd, "FEEDS", [(k, k) for k in feeds])
    monkeypatch.setattr(bd, "fetch_rss", lambda url: [dict(i) for i in feeds[url]])
    monkeypatch.setattr(bd.time, "sleep", lambda s: None)
    monkeypatch.setattr(bd, "load_feed", lambda: json.loads(json.dumps(state["feed"])))
    monkeypatch.setattr(bd, "save_feed", lambda f: state.__setitem__("feed", f))
    monkeypatch.setattr(bd, "match_corpus", lambda f, o: None)
    monkeypatch.setattr(bd, "SEEN_PATH", tmp_path / "cache" / "seen.json")

    def classify(raw):
        state["calls"].append(raw["link"])
        if raw["link"] in state["fail"]:
            return None                       # Ollama error / unparseable
        return {"is_breakthrough": False, "strength": 0.1}
    monkeypatch.setattr(bd, "gemma_classify", classify)
    return state


def test_fda_is_reached_even_when_jama_fills_the_limit(world):
    bd.main(["--limit", "6"])
    assert sum("fda" in c for c in world["calls"]) == 3


def test_judged_items_are_not_sent_again(world):
    bd.main(["--limit", "6"])
    first = list(world["calls"]); world["calls"].clear()
    bd.main(["--limit", "6"])
    assert not set(first) & set(world["calls"])
    seen = json.loads(bd.SEEN_PATH.read_text())
    assert set(first) <= set(seen) and seen[first[0]]["verdict"] == "rejected"


def test_ollama_failure_is_retried_not_remembered(world):
    world["fail"].add("https://fda.example/0")
    bd.main(["--limit", "6"])
    assert "https://fda.example/0" not in json.loads(bd.SEEN_PATH.read_text())
    world["calls"].clear(); world["fail"].clear()
    bd.main(["--limit", "6"])
    assert "https://fda.example/0" in world["calls"]


def test_removed_card_never_comes_back(world):
    bd.SEEN_PATH.parent.mkdir(parents=True)
    bd.SEEN_PATH.write_text(json.dumps({"https://fda.example/1": {"verdict": "removed", "at": "2026-01-01"}}))
    bd.main(["--limit", "40"])
    assert "https://fda.example/1" not in world["calls"]
    assert "https://fda.example/1" in json.loads(bd.SEEN_PATH.read_text())  # old, but kept


def test_dry_run_writes_no_memory(world):
    bd.main(["--dry", "--limit", "6"])
    assert not bd.SEEN_PATH.exists()
