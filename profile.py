"""Local-only user profile.

The profile is stored in a single signed cookie on the user's browser.
Vercel runtime never writes — the only storage is the cookie itself.
This keeps the read-only-on-Vercel constraint intact and means health
data never leaves the user's machine unless they explicitly share.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

COOKIE = "hu_profile"
SECRET = (os.getenv("PROFILE_SECRET") or "dev-not-secret").encode()


@dataclass
class Profile:
    age:        int | None = None
    sex:        str | None = None             # 'female' | 'male' | 'other'
    conditions: list[str] = field(default_factory=list)   # entity slugs
    goals:      list[str] = field(default_factory=list)   # entity slugs / free
    stack:      list[str] = field(default_factory=list)   # factor slugs (current supplements/diet)
    # Watchlists — explicit follow signals for change intelligence
    watch_factors:  list[str] = field(default_factory=list)
    watch_outcomes: list[str] = field(default_factory=list)
    watch_edges:    list[int] = field(default_factory=list)


def _sign(payload: bytes) -> str:
    sig = hmac.new(SECRET, payload, hashlib.sha256).digest()[:12]
    return base64.urlsafe_b64encode(payload).decode().rstrip("=") + "." + \
           base64.urlsafe_b64encode(sig).decode().rstrip("=")


def _unsign(token: str) -> bytes | None:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        pad = "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(payload_b64 + pad)
        sig = base64.urlsafe_b64decode(sig_b64 + ("=" * (-len(sig_b64) % 4)))
        expected = hmac.new(SECRET, payload, hashlib.sha256).digest()[:12]
        if not hmac.compare_digest(sig, expected):
            return None
        return payload
    except Exception:
        return None


def encode(p: Profile) -> str:
    return _sign(json.dumps(asdict(p), separators=(",", ":")).encode())


def decode(token: str | None) -> Profile:
    if not token: return Profile()
    raw = _unsign(token)
    if not raw: return Profile()
    try:
        data = json.loads(raw)
        return Profile(**{k: data.get(k) for k in
                          ("age", "sex", "conditions", "goals", "stack",
                           "watch_factors", "watch_outcomes", "watch_edges")
                          if k in data})
    except Exception:
        return Profile()


# ----------------------------------------------------------------------------
# Personalized ranking helpers (used by the home + me pages)
# ----------------------------------------------------------------------------

def relevance_score(edge: dict, p: Profile) -> float:
    """Higher = more relevant to this user. Cheap, computed at request time."""
    s = 0.0
    if p.conditions and edge.get("o_slug") in p.conditions:
        s += 5.0
    if p.goals and (edge.get("o_slug") in p.goals or edge.get("f_slug") in p.goals):
        s += 2.5
    if p.stack and edge.get("f_slug") in p.stack:
        s += 3.0
    tier_bonus = {"A": 2.0, "B": 1.5, "C": 1.0, "X": 1.5, "D": 0.5}.get(edge.get("tier"), 0.5)
    s += tier_bonus
    if edge.get("direction") == "harmful" and edge.get("f_slug") in (p.stack or []):
        s += 4.0  # surface conflicts in current stack
    return s
