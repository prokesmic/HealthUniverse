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
import re
from functools import lru_cache
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
    # Multi-profile: optional named alternates (e.g. self + parent + spouse)
    # Each entry is the same shape minus alternates/email itself.
    name:           str | None = None         # display label for the active profile
    alternates:     list[dict] = field(default_factory=list)

    @property
    def condition_slugs(self) -> list[str]:
        """Picked conditions with groups expanded ("Cancer" → every cancer)."""
        return expand_conditions(self.conditions)
    # Email is OPTIONAL and only stored when user opts into magic-link sync
    # or the digest. Used as recovery anchor and unsubscribe key.
    email:          str | None = None


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


_PROFILE_FIELDS = ("age", "sex", "conditions", "goals", "stack",
                   "watch_factors", "watch_outcomes", "watch_edges",
                   "name", "alternates", "email")


def decode(token: str | None) -> Profile:
    if not token: return Profile()
    raw = _unsign(token)
    if not raw: return Profile()
    try:
        data = json.loads(raw)
        return _canonical(Profile(**{k: data.get(k) for k in _PROFILE_FIELDS if k in data}))
    except Exception:
        return Profile()


def _canonical(p: Profile) -> Profile:
    """Slugs saved before an entity merge point at the canonical entity
    (entity_redirect), so a stack with `ppi` still matches its edges."""
    try:
        from db import slug_redirects
        m = slug_redirects()
    except Exception:
        return p
    if not m:
        return p
    for f in ("conditions", "stack", "watch_factors", "watch_outcomes"):
        v = getattr(p, f, None)
        if isinstance(v, list):
            setattr(p, f, list(dict.fromkeys(m.get(s, s) if isinstance(s, str) else s for s in v)))
    return p


# ----------------------------------------------------------------------------
# Magic-link sync — short-lived signed tokens that ENCODE the profile.
# Click on a new device → cookie restored. No server-side accounts table.
# ----------------------------------------------------------------------------

def make_sync_token(p: Profile, ttl_seconds: int = 60 * 60 * 24) -> str:
    """Return a token that encodes the profile + expiry. Email this in a
    /restore?token=X link. The receiver verifies HMAC and sets the cookie."""
    import time
    payload = {
        "p": asdict(p),
        "exp": int(time.time()) + ttl_seconds,
    }
    return _sign(json.dumps(payload, separators=(",", ":")).encode())


def verify_sync_token(token: str) -> Profile | None:
    """Return Profile if token is valid AND unexpired, else None."""
    import time
    raw = _unsign(token)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        prof_data = data.get("p", {})
        return Profile(**{k: prof_data.get(k) for k in _PROFILE_FIELDS
                          if k in prof_data})
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Condition groups — picking "Cancer" means every cancer (17.11.2026).
# The general entity cancer_incidence holds only the all-cancer studies; the
# graph keeps colorectal, breast, lung … as their own entities. Expansion is
# applied wherever conditions are matched against edges (Profile.condition_slugs);
# `conditions` itself stays what the person picked, for forms, labels and the cookie.
# ----------------------------------------------------------------------------

_CANCER = re.compile(r"cancer|carcinoma|lymphoma|leuk(a)?emi|melanoma|neoplas|tumou?r|myeloma|sarcoma", re.I)
_NOT_RISK = re.compile(r"detection|screening|survivor|reduction$", re.I)


@lru_cache(maxsize=1)
def _cancer_members() -> tuple[str, ...]:
    try:
        from db import connect
        with connect() as conn:
            rows = conn.execute("""SELECT slug, name FROM entity
                                   WHERE kind IN ('condition','process','outcome')""").fetchall()
    except Exception:
        return ()
    return tuple(r[0] for r in rows if is_cancer(r[0], r[1]))


def is_cancer(slug: str, name: str | None) -> bool:
    """A cancer outcome someone can prevent or manage — not 'Cancer detection rate'."""
    return bool(_CANCER.search(slug) or _CANCER.search(name or "")) and not _NOT_RISK.search(name or "")


CONDITION_GROUPS = {"cancer_incidence": _cancer_members}


def expand_conditions(slugs) -> list[str]:
    out: list[str] = []
    for s in slugs or []:
        for m in [s, *(CONDITION_GROUPS[s]() if s in CONDITION_GROUPS else ())]:
            if m not in out:
                out.append(m)
    return out


def picked_condition_for(outcome_slug: str, picked) -> str | None:
    """Which of the person's picked conditions an edge outcome belongs to."""
    for s in picked or []:
        if outcome_slug == s or (s in CONDITION_GROUPS and outcome_slug in CONDITION_GROUPS[s]()):
            return s
    return None


# ----------------------------------------------------------------------------
# Personalized ranking helpers (used by the home + me pages)
# ----------------------------------------------------------------------------

def relevance_score(edge: dict, p: Profile) -> float:
    """Higher = more relevant to this user. Cheap, computed at request time."""
    s = 0.0
    if p.conditions and edge.get("o_slug") in p.condition_slugs:
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
