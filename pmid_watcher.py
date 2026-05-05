"""Weekly PMID watcher that flags retracted evidence rows."""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from db import connect

load_dotenv(Path(__file__).parent / ".env", override=True)

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_LIMIT_S = 0.4
BATCH_SIZE = 100
NTFY_BASE = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "healthuniverse-tDr8FqPh3xLmQ2")
SITE_URL = os.getenv("HEALTH_UNIVERSE_URL", "https://health-universe.vercel.app")

RETRACTION_PUBTYPES = {
    "retracted publication",
    "retraction of publication",
}


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _distinct_pmids(conn, limit: int | None = None) -> list[str]:
    sql = """
        SELECT DISTINCT pmid
        FROM evidence
        WHERE pmid IS NOT NULL AND TRIM(pmid) != ''
        ORDER BY pmid
    """
    params: tuple[object, ...] = ()
    if limit:
        sql += " LIMIT ?"
        params = (limit,)
    rows = conn.execute(sql, params).fetchall()
    return [str(r["pmid"]).strip() for r in rows]


def _retraction_signal(record: dict) -> tuple[bool, str]:
    title = (record.get("title") or "").strip()
    recordstatus = (record.get("recordstatus") or "").strip()
    pubtypes = [p for p in record.get("pubtype") or [] if p]
    lowered = {p.lower() for p in pubtypes}

    reasons: list[str] = []
    if lowered & RETRACTION_PUBTYPES:
        reasons.append("pubtype contains a retraction marker")
    if "retract" in recordstatus.lower():
        reasons.append(f"recordstatus={recordstatus}")
    if title.upper().startswith("RETRACTED"):
        reasons.append("title starts with RETRACTED")

    is_retracted = bool(reasons)
    if is_retracted:
        return True, "; ".join(reasons)
    return False, "No retraction signal in PubMed esummary"


def fetch_status_batch(pmids: list[str], client: httpx.Client | None = None) -> dict[str, dict]:
    """Return {pmid: {is_retracted, retraction_note}} for one esummary batch."""
    if not pmids:
        return {}

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=60.0)
    assert client is not None

    try:
        response = client.get(
            f"{EUTILS}/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
        )
        response.raise_for_status()
        result = response.json().get("result", {})
    finally:
        if owns_client:
            client.close()

    out: dict[str, dict] = {}
    for pmid in pmids:
        record = result.get(str(pmid))
        if not isinstance(record, dict):
            out[str(pmid)] = {
                "is_retracted": 0,
                "retraction_note": "PMID did not resolve on PubMed esummary",
            }
            continue
        is_retracted, note = _retraction_signal(record)
        out[str(pmid)] = {
            "is_retracted": int(is_retracted),
            "retraction_note": note,
        }
    return out


def _upsert_evidence_status(conn, *, pmid: str, is_retracted: int, retraction_note: str) -> bool:
    prev = conn.execute(
        "SELECT is_retracted FROM evidence_status WHERE pmid=?",
        (pmid,),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO evidence_status (pmid, is_retracted, retraction_note, last_checked)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(pmid) DO UPDATE SET
            is_retracted=excluded.is_retracted,
            retraction_note=excluded.retraction_note,
            last_checked=excluded.last_checked
        """,
        (pmid, is_retracted, retraction_note),
    )
    return bool(prev["is_retracted"]) if prev else False


def _record_new_retraction_history(conn, pmid: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT ev.edge_id, ev.citation,
               f.name AS factor_name, o.name AS outcome_name
        FROM evidence ev
        JOIN edge e ON e.id = ev.edge_id
        JOIN entity f ON f.id = e.factor_id
        JOIN entity o ON o.id = e.outcome_id
        WHERE ev.pmid = ?
        ORDER BY ev.edge_id, ev.id
        """,
        (pmid,),
    ).fetchall()

    events: list[dict] = []
    for row in rows:
        conn.execute(
            """
            INSERT INTO edge_history (edge_id, field, old_value, new_value, reason, actor)
            VALUES (?, 'evidence_status', 'active', 'retracted', ?, 'pmid_watcher')
            """,
            (row["edge_id"], f"evidence row {row['citation']} was retracted"),
        )
        events.append({
            "pmid": pmid,
            "edge_id": row["edge_id"],
            "citation": row["citation"],
            "factor_name": row["factor_name"],
            "outcome_name": row["outcome_name"],
        })
    return events


def _push_ntfy(events: list[dict]) -> bool:
    if not events:
        return False
    title = f"Health Universe — {len(events)} retracted evidence row(s) detected"
    lines = [
        f"• edge {e['edge_id']}: {e['factor_name']} → {e['outcome_name']} (PMID {e['pmid']})"
        for e in events[:5]
    ]
    if len(events) > 5:
        lines.append(f"• …and {len(events) - 5} more")
    try:
        response = httpx.post(
            f"{NTFY_BASE}/{NTFY_TOPIC}",
            data="\n".join(lines).encode(),
            headers={
                "Title": title,
                "Priority": "high",
                "Click": f"{SITE_URL}/edge/{events[0]['edge_id']}",
            },
            timeout=15.0,
        )
        return response.is_success
    except Exception as exc:  # pragma: no cover - network failures are logged, not fatal
        print(f"[pmid_watcher] ntfy push failed: {exc}")
        return False


def run(*, limit: int | None = None, push: bool = False, sleep_s: float = RATE_LIMIT_S) -> dict:
    newly_retracted_events: list[dict] = []
    checked = 0
    retracted = 0

    with connect() as conn:
        pmids = _distinct_pmids(conn, limit)
        if not pmids:
            summary = {
                "checked": 0,
                "retracted": 0,
                "newly_retracted_pmids": 0,
                "history_rows": 0,
                "push_sent": False,
            }
            print("[pmid_watcher] checked=0 retracted=0 newly_retracted_pmids=0 history_rows=0")
            return summary

        with httpx.Client(timeout=60.0) as client:
            for idx, batch in enumerate(_chunks(pmids, BATCH_SIZE)):
                statuses = fetch_status_batch(batch, client=client)
                for pmid, status in statuses.items():
                    checked += 1
                    retracted += int(bool(status["is_retracted"]))
                    was_retracted = _upsert_evidence_status(
                        conn,
                        pmid=pmid,
                        is_retracted=int(status["is_retracted"]),
                        retraction_note=status["retraction_note"],
                    )
                    if status["is_retracted"] and not was_retracted:
                        newly_retracted_events.extend(_record_new_retraction_history(conn, pmid))
                if idx < len(_chunks(pmids, BATCH_SIZE)) - 1:
                    time.sleep(sleep_s)

    push_sent = _push_ntfy(newly_retracted_events) if push and newly_retracted_events else False
    summary = {
        "checked": checked,
        "retracted": retracted,
        "newly_retracted_pmids": len({e["pmid"] for e in newly_retracted_events}),
        "history_rows": len(newly_retracted_events),
        "push_sent": push_sent,
    }
    print(
        "[pmid_watcher] "
        f"checked={summary['checked']} "
        f"retracted={summary['retracted']} "
        f"newly_retracted_pmids={summary['newly_retracted_pmids']} "
        f"history_rows={summary['history_rows']} "
        f"push_sent={summary['push_sent']}"
    )
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="Only check this many distinct PMIDs.")
    ap.add_argument("--push", action="store_true",
                    help="Send an ntfy push when new retractions are detected.")
    ap.add_argument("--sleep-s", type=float, default=RATE_LIMIT_S,
                    help="Delay between PubMed batches (default 0.4s).")
    args = ap.parse_args()
    run(limit=args.limit, push=args.push, sleep_s=args.sleep_s)
