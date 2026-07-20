"""
pipeline/app/owner_auth.py -- single-owner authentication gate for the
`/admin/*` routes (product-brief "owner-only analytics": "only I can view
data"; threat-model/opsec-gate F8 access-control leg).

No hand-rolled crypto beyond stdlib `hmac`/`hashlib`/`secrets`; no
invented password hashing (there is exactly one credential -- an operator
passcode -- compared in constant time, not stored/hashed at rest since it
lives only in an env var the operator controls).

Two secrets, both from env, never hardcoded:
  OWNER_PASSCODE          the operator's shared secret. Compared with
                           hmac.compare_digest (constant-time) -- never a
                           plain `==`.
  OWNER_SESSION_SECRET    HMAC key for signing session tokens. Unrelated
                           to OWNER_PASSCODE; compromising one does not
                           compromise the other.

Session token shape: "{expiry_unix_ts}.{hex hmac-sha256 signature}". The
token carries NO secret material -- not the passcode, not the session
secret, just an integer expiry and its signature -- so a leaked cookie
reveals nothing beyond "a session valid until <ts> existed". TTL is short
and configurable (OWNER_SESSION_TTL_SECONDS, default 8h).

`require_owner` is the FastAPI dependency main.py attaches to every
`/admin/*` route: missing/invalid/expired cookie -> 401, before any
handler code (and therefore any DB query) runs.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Optional

from fastapi import HTTPException, Request

OWNER_COOKIE_NAME = "owner_session"

_DEFAULT_SESSION_TTL_SECONDS = 8 * 60 * 60  # 8h


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def _passcode() -> Optional[str]:
    return _env("OWNER_PASSCODE")


def _session_secret() -> str:
    secret = _env("OWNER_SESSION_SECRET")
    if not secret:
        # Fail closed: no configured signing secret means no session can
        # ever be legitimately issued or verified. Callers must treat
        # this as "auth unavailable", never silently trust an unsigned
        # token.
        raise RuntimeError("OWNER_SESSION_SECRET not configured")
    return secret


def session_ttl_seconds() -> int:
    return int(_env("OWNER_SESSION_TTL_SECONDS", str(_DEFAULT_SESSION_TTL_SECONDS)))


def check_passcode(candidate: str) -> bool:
    """Constant-time comparison against OWNER_PASSCODE. Returns False
    (never raises) if OWNER_PASSCODE isn't configured -- fail closed, not
    open. Compares HMAC-SHA256 digests of both sides (not the raw
    strings) so equal-length stdlib compare_digest also avoids leaking
    the configured passcode's length via early-return-on-length-mismatch
    timing."""
    expected = _passcode()
    if not expected or not isinstance(candidate, str):
        return False
    key = expected.encode("utf-8")  # any fixed key works; reusing the
    # expected value itself as the HMAC key needs no extra secret and
    # keeps this function self-contained.
    mac_candidate = hmac.new(key, candidate.encode("utf-8"), hashlib.sha256).digest()
    mac_expected = hmac.new(key, expected.encode("utf-8"), hashlib.sha256).digest()
    return hmac.compare_digest(mac_candidate, mac_expected)


def issue_session_token(now: Optional[float] = None) -> str:
    """Mint a signed session token good for session_ttl_seconds() from
    `now`. Raises RuntimeError if OWNER_SESSION_SECRET isn't configured
    -- callers (main.py's /admin/login) must let that surface as a 500,
    never issue an unsigned/fake token as a fallback."""
    secret = _session_secret()
    exp = int((now if now is not None else time.time()) + session_ttl_seconds())
    payload = str(exp)
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_session_token(token: Optional[str], now: Optional[float] = None) -> bool:
    """Constant-time-verify a token minted by issue_session_token and
    check it hasn't expired. False for any malformed/missing/unsigned/
    expired/misconfigured-secret case -- never raises to a caller in the
    request path (require_owner below converts every False into a 401)."""
    if not token or not isinstance(token, str):
        return False
    try:
        secret = _session_secret()
    except RuntimeError:
        return False

    try:
        payload, sig = token.split(".", 1)
        exp = int(payload)
    except (ValueError, AttributeError):
        return False

    expected_sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return False

    current = now if now is not None else time.time()
    return current <= exp


def require_owner(request: Request) -> None:
    """FastAPI dependency: attach to every `/admin/*` route. Unauthenticated
    or expired session -> 401, raised before the route handler body (and
    therefore before any DB query) runs."""
    token = request.cookies.get(OWNER_COOKIE_NAME)
    if not verify_session_token(token):
        raise HTTPException(status_code=401, detail="owner authentication required")
