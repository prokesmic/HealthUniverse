"""Supabase auth integration.

Two-tier identity model:

  1. Anonymous (cookie only) — the existing `hu_profile` cookie carries
     conditions / stack / watchlist / goals. No account needed.
  2. Email-verified — the user clicks a magic link, we set an
     additional `hu_session` cookie carrying their Supabase user id.
     Server-side personalised features (Sunday email, recommendations
     mirror, Pro paywall) check this second cookie.

The two cookies coexist intentionally. Anonymous browsing keeps full
parity with today's UX; signing in is purely additive.

All sensitive personal data (PHI: labs, wearables, genetics, records,
protocol logs) STAYS in browser localStorage. Supabase only ever sees
the email + a Stripe ID + an opt-in flag for the Sunday digest.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from itsdangerous import BadSignature, URLSafeSerializer
from supabase import Client, create_client

# ─── Cookie helpers ──────────────────────────────────────────────────

SESSION_COOKIE = "hu_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 90  # 90 days


def _serializer() -> URLSafeSerializer:
    secret = os.environ.get("PROFILE_SECRET", "hu-dev-fallback-secret")
    return URLSafeSerializer(secret, salt="hu-session-v1")


def encode_session(user_id: str, email: str) -> str:
    """Sign a small payload identifying the logged-in user. We rely on
    Supabase's actual JWT only at sign-in time; thereafter we keep our
    own signed cookie so we don't have to round-trip Supabase on every
    page load."""
    return _serializer().dumps({"u": user_id, "e": email})


def decode_session(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    try:
        return _serializer().loads(token)
    except BadSignature:
        return None
    except Exception:
        return None


# ─── Supabase client ─────────────────────────────────────────────────

_ANON_CLIENT: Optional[Client] = None
_SERVICE_CLIENT: Optional[Client] = None


def supabase_anon() -> Optional[Client]:
    """Anon client — used for sign-in / sign-up flows. RLS applies."""
    global _ANON_CLIENT
    if _ANON_CLIENT is not None:
        return _ANON_CLIENT
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    _ANON_CLIENT = create_client(url, key)
    return _ANON_CLIENT


def supabase_service() -> Optional[Client]:
    """Service-role client — bypasses RLS. Used only server-side for
    privileged writes (waitlist, card_reports, recommendations_log
    mirroring). Must NEVER be called with user input as the service-
    role key in a path that returns data to the user without auth."""
    global _SERVICE_CLIENT
    if _SERVICE_CLIENT is not None:
        return _SERVICE_CLIENT
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    _SERVICE_CLIENT = create_client(url, key)
    return _SERVICE_CLIENT


# ─── Public API ──────────────────────────────────────────────────────


@dataclass
class Account:
    user_id: str
    email: str
    pro_until: Optional[str] = None
    cron_subscribed: bool = True

    @property
    def is_pro(self) -> bool:
        # Real Pro: paid subscription with a valid until-date.
        if self.pro_until:
            from datetime import date
            try:
                if date.fromisoformat(self.pro_until) >= date.today():
                    return True
            except Exception:
                pass
        # Beta bridge: until Stripe is wired, we allowlist Pro by email
        # via BETA_PRO_EMAILS env (comma-separated). Lets the founder
        # and friends-and-family use Pro features today.
        beta = os.environ.get("BETA_PRO_EMAILS", "")
        beta_emails = {e.strip().lower() for e in beta.split(",") if e.strip()}
        return self.email.lower() in beta_emails


def require_pro(account: Optional[Account]) -> Optional[JSONResponse]:
    """Return a 402 JSON response if the user isn't Pro; None if they are.
    Endpoints call this at entry; if non-None, return it directly."""
    from fastapi.responses import JSONResponse
    if not account:
        return JSONResponse({
            "error": "auth_required",
            "message": "Sign in first.",
            "tier": "anonymous",
        }, status_code=401)
    if not account.is_pro:
        return JSONResponse({
            "error": "pro_required",
            "message": "This feature is part of the Pro tier. "
                       "Founder pricing $19/mo — join the waitlist.",
            "tier": "free",
            "upgrade_url": "/stack#pro-waitlist",
        }, status_code=402)
    return None


def current_account(session_cookie: Optional[str]) -> Optional[Account]:
    """Decode the session cookie + look up the account row.
    Returns None if not signed in or Supabase isn't configured."""
    payload = decode_session(session_cookie)
    if not payload:
        return None
    sb = supabase_service()
    if sb is None:
        # No service-role key configured — fall back to cookie data only.
        return Account(user_id=payload["u"], email=payload["e"])
    try:
        resp = sb.table("accounts").select(
            "id, email, pro_until, cron_subscribed"
        ).eq("id", payload["u"]).limit(1).execute()
        rows = resp.data or []
        if not rows:
            return Account(user_id=payload["u"], email=payload["e"])
        r = rows[0]
        return Account(
            user_id=r["id"], email=r["email"],
            pro_until=str(r["pro_until"]) if r.get("pro_until") else None,
            cron_subscribed=bool(r.get("cron_subscribed", True)),
        )
    except Exception as exc:
        print(f"[auth] account lookup failed: {exc}")
        return Account(user_id=payload["u"], email=payload["e"])


def send_magic_link(email: str, redirect_to: str) -> tuple[bool, str]:
    """Ask Supabase to email a magic link. Returns (ok, message)."""
    sb = supabase_anon()
    if sb is None:
        return False, "Supabase is not configured on this server."
    try:
        sb.auth.sign_in_with_otp({
            "email": email,
            "options": {"email_redirect_to": redirect_to},
        })
        return True, "ok"
    except Exception as exc:
        return False, str(exc)[:200]


def exchange_token_for_session(access_token: str) -> tuple[Optional[Account], str]:
    """Validate a Supabase access token (from a magic-link callback)
    and return the matching Account if valid. Falls through to
    'service-role lookup by user id' if needed."""
    sb = supabase_anon()
    if sb is None:
        return None, "Supabase is not configured."
    try:
        # Supabase Python client validates the token via its auth API.
        user_resp = sb.auth.get_user(access_token)
        if not user_resp or not user_resp.user:
            return None, "Token did not resolve to a user."
        u = user_resp.user
        return Account(user_id=u.id, email=u.email or ""), "ok"
    except Exception as exc:
        return None, str(exc)[:200]
