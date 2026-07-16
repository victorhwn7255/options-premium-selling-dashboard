"""Owner-only auth for the trade-journal surface (positions / journal / settings).

Fail-closed by design: with no credentials configured, every request is 403.
Three accepted credentials, checked in order:

1. **Cloudflare Access JWT** — the browser path in prod. Cloudflare injects
   `Cf-Access-Jwt-Assertion` after the Access login (email OTP / service token);
   we verify its RS256 signature against the team's JWKS and the app AUD.
   Enabled when CF_ACCESS_TEAM_DOMAIN + CF_ACCESS_AUD are set (needs PyJWT).
2. **Bearer token** — `Authorization: Bearer $JOURNAL_TOKEN`. The Mac automation
   and scripts/curl path. Constant-time compare.
3. **Dev-open** — `JOURNAL_DEV_OPEN=1`. Local development only; never set on prod.

The public scan/regime/CPS endpoints do NOT use this module — the demo stays open.
See tasks/positions-journal-build-plan.md §3.1.
"""
from __future__ import annotations

import hmac
import logging
import os

from fastapi import HTTPException, Request

logger = logging.getLogger("option-harvest")

_JOURNAL_TOKEN = os.environ.get("JOURNAL_TOKEN") or ""
_CF_TEAM_DOMAIN = os.environ.get("CF_ACCESS_TEAM_DOMAIN") or ""  # e.g. myteam.cloudflareaccess.com
_CF_AUD = os.environ.get("CF_ACCESS_AUD") or ""
_DEV_OPEN = os.environ.get("JOURNAL_DEV_OPEN") == "1"

_jwks_client = None
_jwt_ready = False
if _CF_TEAM_DOMAIN and _CF_AUD:
    try:
        import jwt as _pyjwt  # PyJWT
        from jwt import PyJWKClient

        _jwks_client = PyJWKClient(
            f"https://{_CF_TEAM_DOMAIN}/cdn-cgi/access/certs", cache_keys=True)
        _jwt_ready = True
    except ImportError:
        logger.warning(
            "CF_ACCESS_* configured but PyJWT not installed — the Cloudflare "
            "Access path is disabled; only the bearer token will be accepted.")


def _cf_jwt_valid(assertion: str) -> bool:
    """Verify a Cf-Access-Jwt-Assertion against the team JWKS + app AUD."""
    if not (_jwt_ready and assertion):
        return False
    try:
        key = _jwks_client.get_signing_key_from_jwt(assertion)
        _pyjwt.decode(assertion, key.key, algorithms=["RS256"], audience=_CF_AUD)
        return True
    except Exception:  # noqa: BLE001 — any verification failure means "not you"
        return False


def _bearer_valid(auth_header: str) -> bool:
    if not (_JOURNAL_TOKEN and auth_header.startswith("Bearer ")):
        return False
    return hmac.compare_digest(auth_header[7:], _JOURNAL_TOKEN)


async def require_owner(request: Request) -> None:
    """FastAPI dependency: raise 403 unless the request proves it's the owner."""
    if _DEV_OPEN:
        return
    if _cf_jwt_valid(request.headers.get("Cf-Access-Jwt-Assertion", "")):
        return
    if _bearer_valid(request.headers.get("Authorization", "")):
        return
    raise HTTPException(status_code=403, detail="owner credentials required")
