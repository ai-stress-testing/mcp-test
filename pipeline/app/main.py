"""
pipeline/app/main.py -- the pricing/checkout request-path service
(ADR-0002 Decision 3: a small containerized FastAPI service, not Edge
Functions; talks to Postgres via store.py). Fixed interface contract:
ASGI object `app`, uvicorn on :8000, GET /healthz -> 200. Do not change
the routes/response shapes below without a new ticket -- other agents
build to this contract.

Security posture this file is responsible for (docs/sprint-7-26-19-26/
reviews/security-threat-model.md, opsec-gate.md):
  F1  region is derived SERVER-SIDE from the trusted connecting IP.
      Any client-supplied state value in the /assign body is read
      nowhere in this file -- not validated-then-ignored, just never
      looked at.
  F2  price is server-authoritative: /create-checkout reads the amount
      from the visitor's stored assignment_event row; /webhook asserts
      amount_total == that stored price BEFORE writing anything.
  F4  a `converted` outcome (an orders row) can only be produced by a
      signature-verified webhook -- there is no other code path that
      writes to orders.
  F6  webhook signature + timestamp tolerance verified, deduped on
      Stripe's event.id, idempotent insert.
"""
from __future__ import annotations

import ipaddress
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

# pricing_engine.py lives one directory up (pipeline/), outside this
# app's own package. KNOWN GAP (not this ticket's file to fix): the
# containerization ticket's Dockerfile build context is pipeline/app/
# only (see pipeline/app/Dockerfile), so this import resolves when run
# from a repo checkout -- as the runnable check below does -- but will
# fail inside the actual built image until that Dockerfile's build
# context is widened or pricing_engine.py is vendored alongside this
# app. Flagged in the sprint log, not silently worked around here.
_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)
from pricing_engine import DEFAULT_REGION, PricingEngine, canonical_region  # noqa: E402

import owner_auth  # sibling module -- owner-only /admin/* auth gate
import store  # sibling module -- flat import to match `uvicorn main:app`
import stripe_gateway  # (Dockerfile CMD, no package context)

app = FastAPI(title="regional-pricing-pipeline")

VISITOR_COOKIE_NAME = "visitor_id"
DISCLOSURE = (
    "Pricing may vary by region and is determined automatically based on "
    "your approximate location at time of purchase."
)

# --- interaction capture (owner-only analytics / heatmap, product-brief
# "owner-only analytics" + threat-model/opsec-gate F8) -------------------
#
# ANALYTICS_COOKIE_NAME is DELIBERATELY separate from VISITOR_COOKIE_NAME:
# the interaction_event.session_id it carries is never read into a
# pricing decision and is never joined to visitor_id/orders anywhere in
# this file, store.py, or the schema (0006 migration) -- see that
# migration's header comment. Reusing VISITOR_COOKIE_NAME here would
# silently make analytics re-identifiable against order data; that's the
# one thing this split exists to prevent.
ANALYTICS_COOKIE_NAME = "session_id"
ALLOWED_INTERACTION_EVENT_TYPES = frozenset(
    {"pageview", "click", "scroll", "cta_view", "cta_click"}
)
MAX_TRACK_BODY_BYTES = 4096
MAX_LOGIN_BODY_BYTES = 1024
MAX_PATH_LEN = 512
MAX_VIEWPORT_W = 20000


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def _base_price_cents() -> int:
    return int(_env("BASE_PRICE_CENTS", "6000"))


def _epoch_hours() -> float:
    return float(_env("EPOCH_HOURS", "24"))


def _cookie_secure() -> bool:
    return _env("COOKIE_SECURE", "true").strip().lower() not in ("0", "false", "no")


def _engine() -> PricingEngine:
    # Cheap to construct (no I/O); rebuilt per call so BASE_PRICE_CENTS
    # env changes (e.g. between test runs in the same process) take
    # effect without a restart.
    return PricingEngine(base_price=_base_price_cents() / 100.0)


def current_epoch_id(epoch_hours: Optional[float] = None, now: Optional[datetime] = None) -> int:
    epoch_hours = epoch_hours if epoch_hours is not None else _epoch_hours()
    now = now or datetime.now(timezone.utc)
    return int(now.timestamp() // (epoch_hours * 3600))


async def _read_bounded_body(request: Request, limit: int) -> bytes:
    """Read the request body in chunks, aborting with 413 the moment it
    exceeds `limit` -- unlike checking the Content-Length header, this is
    not spoofable by omitting/lying about that header or using chunked
    transfer-encoding (F11-adjacent: cheap rejection of an oversized body
    before it's ever handed to json.loads)."""
    body = b""
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            raise HTTPException(status_code=413, detail="request body too large")
    return body


def _clamp_pct(value: object) -> Optional[int]:
    """Coerce an interaction-event percent field to an int in [0, 100],
    or None if it's absent/not a plain number. bool is explicitly
    excluded even though Python's bool is an int subclass (True/False
    are not meaningful percentages)."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return max(0, min(int(round(value)), 100))
    except (TypeError, ValueError):
        return None


def _client_ip(request: Request) -> str:
    """Trusted-IP derivation for F1: X-Forwarded-For's LAST hop (the one
    appended by our own reverse proxy; anything to its left is
    attacker-controlled and not trusted) or request.client as fallback."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        hop = xff.split(",")[-1].strip()
        if hop:
            return hop
    return request.client.host if request.client else "0.0.0.0"


def derive_region(request: Request) -> str:
    """F1: ALWAYS derived server-side from the trusted connecting IP.
    Nothing from the request body is consulted here -- a client-supplied
    state_code is a non-authoritative hint that this function never even
    reads. Raw IP is used transiently and discarded post-derivation (F8:
    it is never persisted anywhere in this schema)."""
    ip = _client_ip(request)
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return DEFAULT_REGION

    if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
        # No real geo signal for private/local/test traffic -- collapses
        # to the shared default arm, same as an unrecognized state.
        return DEFAULT_REGION

    geoip_db = _env("GEOIP_DB_PATH")
    if geoip_db and os.path.exists(geoip_db):
        try:
            import geoip2.database  # optional dep, only touched if configured
            with geoip2.database.Reader(geoip_db) as reader:
                resp = reader.subdivisions(ip)
                code = resp.subdivisions.most_specific.iso_code
                return canonical_region(code)
        except Exception:
            return DEFAULT_REGION

    # No GeoIP database wired up in this environment -- this is the seam
    # for a real IP->state provider (MaxMind or similar). A public IP
    # with no lookup available collapses to the shared default bucket;
    # it never falls back to anything client-supplied.
    return DEFAULT_REGION


# --- routes ---------------------------------------------------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def index():
    web_index = os.path.join(_PIPELINE_DIR, "web", "index.html")
    if os.path.exists(web_index):
        return FileResponse(web_index)
    return HTMLResponse(
        "<html><body><h1>regional-pricing-pipeline</h1>"
        "<p>placeholder -- pipeline/web/index.html not present yet "
        "(pipeline/web/ is a separate ticket's seam).</p></body></html>"
    )


@app.post("/assign")
async def assign(request: Request, response: Response):
    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}
    if not isinstance(raw_body, dict):
        raw_body = {}

    # F1: raw_body may contain "state_code" (or anything else) -- it is
    # deliberately never read. The only body field consulted is
    # device_class, which is analytics-only (never priced -- see
    # pricing_engine.py's ALLOWED_PRICING_INPUTS and this schema's
    # device_class column comments).
    device_class = raw_body.get("device_class")
    if not isinstance(device_class, str):
        device_class = None

    region = derive_region(request)
    epoch_id = current_epoch_id()

    visitor_id = request.cookies.get(VISITOR_COOKIE_NAME)
    is_new_visitor = not visitor_id
    if is_new_visitor:
        visitor_id = secrets.token_urlsafe(24)

    try:
        with store.get_conn() as conn:
            arm = store.get_epoch_arm(conn, region, epoch_id)
            if arm is None:
                engine = _engine()
                baseline_dollars = engine.baseline_for(region)
                price_cents = round(baseline_dollars * 100)
                variant_id = f"{region}@{baseline_dollars:.2f}"
                arm = store.ensure_bootstrap_arm(conn, region, epoch_id, price_cents, variant_id)

            stored = store.upsert_first_assignment(
                conn, visitor_id, region, epoch_id,
                arm["variant_id"], arm["price_cents"], device_class,
            )
            conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"assignment failed: {exc}") from exc

    if is_new_visitor:
        response.set_cookie(
            VISITOR_COOKIE_NAME,
            visitor_id,
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            max_age=60 * 60 * 24 * 400,
        )

    return {
        "variant_id": stored["variant_id"],
        "price_cents": stored["price_cents"],
        "currency": "usd",
        "region": stored["region"],
        "disclosure": DISCLOSURE,
    }


@app.post("/create-checkout")
async def create_checkout(request: Request):
    visitor_id = request.cookies.get(VISITOR_COOKIE_NAME)
    if not visitor_id:
        raise HTTPException(status_code=400, detail="no assignment for this visitor; call /assign first")

    try:
        with store.get_conn() as conn:
            stored = store.get_assignment_for_visitor(conn, visitor_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"lookup failed: {exc}") from exc

    if stored is None:
        raise HTTPException(status_code=400, detail="no assignment for this visitor; call /assign first")

    try:
        session = stripe_gateway.create_checkout_session(
            price_cents=stored["price_cents"],  # F2: amount from the STORED assignment, never the client
            currency="usd",
            variant_id=stored["variant_id"],
            visitor_id=visitor_id,
            region=stored["region"],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"checkout session creation failed: {exc}") from exc

    return {"checkout_url": session["url"]}


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    webhook_secret = _env("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not configured")

    try:
        event = stripe_gateway.verify_and_construct_event(payload, sig_header, webhook_secret)
    except ValueError as exc:
        # F6: unsigned/expired/tampered-signature webhook is rejected
        # outright, before any DB read or write.
        raise HTTPException(status_code=400, detail=f"webhook verification failed: {exc}") from exc

    event_id = event.get("id")
    event_type = event.get("type")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="malformed event")

    try:
        with store.get_conn() as conn:
            if store.order_exists_by_event_id(conn, event_id):
                # F6: duplicate delivery of an already-processed event --
                # no-op, not an error.
                return JSONResponse({"status": "duplicate", "event_id": event_id})

            if event_type != "checkout.session.completed":
                return JSONResponse({"status": "ignored", "event_id": event_id})

            session_obj = (event.get("data") or {}).get("object") or {}
            session_id = session_obj.get("id")
            amount_total = session_obj.get("amount_total")
            metadata = session_obj.get("metadata") or {}
            visitor_id = metadata.get("visitor_id")

            if not session_id or amount_total is None or not visitor_id:
                raise HTTPException(status_code=400, detail="incomplete checkout.session.completed payload")

            stored = store.get_assignment_for_visitor(conn, visitor_id)
            if stored is None:
                raise HTTPException(status_code=400, detail=f"no assignment_event for visitor_id={visitor_id}")

            if int(amount_total) != int(stored["price_cents"]):
                # F2: reject a mismatched amount BEFORE writing anything --
                # this is the primary control the schema's trigger backstops.
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"amount_total {amount_total} != stored price_cents "
                        f"{stored['price_cents']} for visitor_id={visitor_id}"
                    ),
                )

            # F4: this insert is the ONLY code path in the service that
            # can produce a `converted` outcome, and it only runs after
            # signature verification + the F2 amount check above.
            inserted = store.insert_order(
                conn, session_id, event_id, visitor_id,
                stored["region"], stored["epoch_id"], stored["variant_id"], int(amount_total),
            )
            conn.commit()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"webhook processing failed: {exc}") from exc

    return JSONResponse({"status": "ok" if inserted else "duplicate", "event_id": event_id})


# --- interaction capture (public, privacy-safe -- F8) ----------------------

@app.post("/track")
async def track(request: Request, response: Response):
    body_bytes = await _read_bounded_body(request, MAX_TRACK_BODY_BYTES)
    try:
        raw_body = json.loads(body_bytes) if body_bytes else {}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"malformed JSON body: {exc}") from exc
    if not isinstance(raw_body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")

    event_type = raw_body.get("event_type")
    if event_type not in ALLOWED_INTERACTION_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="unknown event_type")

    path = raw_body.get("path")
    if not isinstance(path, str) or not path.startswith("/") or len(path) > MAX_PATH_LEN:
        raise HTTPException(status_code=400, detail="invalid path")

    viewport_w_raw = raw_body.get("viewport_w")
    if isinstance(viewport_w_raw, bool) or not isinstance(viewport_w_raw, int):
        raise HTTPException(status_code=400, detail="viewport_w must be an integer")
    viewport_w = max(0, min(viewport_w_raw, MAX_VIEWPORT_W))

    # Percentages are CLAMPED, not rejected (requirement 2) -- an
    # out-of-range or malformed value degrades to null rather than
    # failing the whole (otherwise-valid) event.
    x_pct = _clamp_pct(raw_body.get("x_pct"))
    y_pct = _clamp_pct(raw_body.get("y_pct"))
    scroll_pct = _clamp_pct(raw_body.get("scroll_pct"))

    # F8: session_id is never read from the client -- it comes solely
    # from ANALYTICS_COOKIE_NAME, minted server-side exactly like
    # visitor_id, and is a wholly separate token from it (never the
    # pricing visitor_id, never PII).
    session_id = request.cookies.get(ANALYTICS_COOKIE_NAME)
    is_new_session = not session_id
    if is_new_session:
        session_id = secrets.token_urlsafe(16)

    try:
        with store.get_conn() as conn:
            store.insert_interaction_event(
                conn, session_id, event_type, path, x_pct, y_pct, scroll_pct, viewport_w,
            )
            conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"track failed: {exc}") from exc

    if is_new_session:
        response.set_cookie(
            ANALYTICS_COOKIE_NAME,
            session_id,
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

    return {"status": "ok"}


# --- owner-only admin: auth + reads ------------------------------------------

@app.post("/admin/login")
async def admin_login(request: Request, response: Response):
    body_bytes = await _read_bounded_body(request, MAX_LOGIN_BODY_BYTES)
    try:
        raw_body = json.loads(body_bytes) if body_bytes else {}
    except Exception:
        raw_body = {}
    passcode = raw_body.get("passcode") if isinstance(raw_body, dict) else None
    if not isinstance(passcode, str):
        passcode = ""

    if not owner_auth.check_passcode(passcode):
        # Deliberately identical response/shape whether the passcode is
        # wrong or OWNER_PASSCODE isn't configured at all -- no signal to
        # a caller about which.
        raise HTTPException(status_code=401, detail="invalid passcode")

    try:
        token = owner_auth.issue_session_token()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response.set_cookie(
        owner_auth.OWNER_COOKIE_NAME,
        token,
        httponly=True,
        secure=_cookie_secure(),
        samesite="strict",
        max_age=owner_auth.session_ttl_seconds(),
    )
    return {"status": "ok"}


@app.get("/admin/metrics")
def admin_metrics(_owner: None = Depends(owner_auth.require_owner)):
    """Per-region arm/conversion/revenue + top-of-funnel counts. 401
    without a valid owner session (enforced by the require_owner
    dependency before this body runs)."""
    try:
        with store.get_conn() as conn:
            regions = store.region_metrics(conn)
            funnel = store.funnel_counts(conn)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"metrics query failed: {exc}") from exc

    return {
        "regions": [
            {
                "region": row["region"],
                "price_cents": row["price_cents"],
                "trials": row["trials"],
                "conversions": row["conversions"],
                "revenue_cents": row["revenue_cents"],
            }
            for row in regions
        ],
        "funnel": funnel,
    }


@app.get("/admin/heatmap")
def admin_heatmap(path: str = "/", _owner: None = Depends(owner_auth.require_owner)):
    """Aggregated click-density bins + scroll-depth histogram for one
    path. AGGREGATE ONLY (F8) -- store.heatmap_bins never selects
    session_id or any other per-row field into the response; only counts
    grouped by bin/bucket leave the database. 401 without a valid owner
    session."""
    if not isinstance(path, str) or not path.startswith("/") or len(path) > MAX_PATH_LEN:
        raise HTTPException(status_code=400, detail="invalid path")

    try:
        with store.get_conn() as conn:
            click_bins, scroll_hist = store.heatmap_bins(conn, path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"heatmap query failed: {exc}") from exc

    return {
        "path": path,
        "bin_size_pct": 10,
        "click_bins": [
            {"x_bin": row["x_bin"], "y_bin": row["y_bin"], "count": row["clicks"]}
            for row in click_bins
        ],
        "scroll_depth_histogram": [
            {"bucket_pct": row["bucket"] * 10, "sessions": row["sessions"]}
            for row in scroll_hist
        ],
    }
