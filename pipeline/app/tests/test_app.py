"""
pipeline/app/tests/test_app.py -- the runnable check for this ticket.

Exercises, against a local Postgres with the migrations applied and
STRIPE_MODE=stub (offline, no live Stripe network):

  * /assign returns a price.
  * F1: a client passing a cheaper state_code in the body does NOT
    change the price (region is server-derived, body is never read).
  * /create-checkout (stub) creates a Checkout session using the STORED
    price, never a client-supplied one.
  * /webhook (stub) with the correct amount creates exactly ONE order.
  * A DUPLICATE webhook delivery (same Stripe event.id) still yields
    exactly one order (F6).
  * A webhook with a TAMPERED amount is REJECTED and writes no order (F2).

Required env vars (set by the caller, not hardcoded here -- see the repo
root's runnable-check invocation): DATABASE_URL, STRIPE_WEBHOOK_SECRET,
STRIPE_MODE=stub, BASE_PRICE_CENTS, EPOCH_HOURS.
"""
from __future__ import annotations

import os
import sys

import psycopg
import pytest
from psycopg.rows import dict_row

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # pipeline/app

for _required in ("DATABASE_URL", "STRIPE_WEBHOOK_SECRET"):
    if not os.environ.get(_required):
        raise RuntimeError(f"test_app.py requires {_required} to be set in the environment")
os.environ.setdefault("STRIPE_MODE", "stub")
os.environ.setdefault("BASE_PRICE_CENTS", "6000")
os.environ.setdefault("EPOCH_HOURS", "24")

import main  # noqa: E402  (sibling app module)
import stripe_gateway  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    """Start every run from an empty state so counts below are exact,
    not additive across repeated runs against the same scratch DB."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "truncate table public.orders, public.impression, "
                "public.assignment_event, public.epoch_assignment, "
                "public.posterior cascade"
            )
        conn.commit()
    yield


@pytest.fixture()
def client():
    return TestClient(main.app)


def _db():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def _order_count(stripe_event_id: str) -> int:
    with _db() as conn, conn.cursor() as cur:
        cur.execute("select count(*) as n from public.orders where stripe_event_id = %s", (stripe_event_id,))
        return cur.fetchone()["n"]


def _assign(client: TestClient, body: dict | None = None, cookies: dict | None = None):
    return client.post("/assign", json=body or {}, cookies=cookies or {})


# --- basic contract ---------------------------------------------------------

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_serves_placeholder_when_no_web_index(client):
    r = client.get("/")
    assert r.status_code == 200


def test_assign_returns_a_price(client):
    r = _assign(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["price_cents"] > 0
    assert body["currency"] == "usd"
    assert body["variant_id"]
    assert body["region"]
    assert "visitor_id" in r.cookies


# --- F1: client-supplied state is never authoritative ------------------------

def test_assign_ignores_client_supplied_state_code(client):
    """Two DIFFERENT visitors (no shared cookie), one sending no state
    hint and one sending a cheap state, hit /assign from the same
    (test-client) IP. If the server derived price from the client body,
    the second visitor would get a different (lower) price. It must not."""
    r_honest = _assign(client, body={})
    assert r_honest.status_code == 200
    honest = r_honest.json()

    r_spoofed = _assign(client, body={"state_code": "MS"})  # MS has the lowest PPP index configured
    assert r_spoofed.status_code == 200
    spoofed = r_spoofed.json()

    assert honest["region"] == spoofed["region"], "region must be IP-derived, not body-derived"
    assert honest["price_cents"] == spoofed["price_cents"], (
        "F1 VIOLATION: client-supplied state_code changed the assigned price"
    )


def test_assign_is_sticky_for_returning_visitor(client):
    r1 = _assign(client)
    vid = r1.cookies["visitor_id"]
    first = r1.json()

    # Same visitor, now trying to relabel themselves as a cheaper state --
    # must get back their ORIGINAL stored price (sticky), not a recompute.
    r2 = _assign(client, body={"state_code": "MS"}, cookies={"visitor_id": vid})
    second = r2.json()
    assert second["price_cents"] == first["price_cents"]
    assert second["variant_id"] == first["variant_id"]


# --- F2 / checkout / webhook flow --------------------------------------------

def test_checkout_uses_stored_price_not_client_supplied(client, monkeypatch):
    r = _assign(client)
    vid = r.cookies["visitor_id"]
    stored_price_cents = r.json()["price_cents"]

    captured = {}
    real_create = stripe_gateway.create_checkout_session

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return real_create(*args, **kwargs)

    monkeypatch.setattr(main.stripe_gateway, "create_checkout_session", spy)

    r2 = client.post("/create-checkout", cookies={"visitor_id": vid})
    assert r2.status_code == 200, r2.text
    assert "checkout_url" in r2.json()
    assert captured["price_cents"] == stored_price_cents, (
        "F2 VIOLATION: checkout amount did not come from the stored assignment"
    )


def test_webhook_correct_amount_creates_exactly_one_order(client):
    r = _assign(client)
    vid = r.cookies["visitor_id"]
    price_cents = r.json()["price_cents"]

    r2 = client.post("/create-checkout", cookies={"visitor_id": vid})
    session_id = r2.json()["checkout_url"].rsplit("/", 1)[-1]

    payload, sig = stripe_gateway.fabricate_signed_event(
        event_type="checkout.session.completed",
        session_id=f"cs_stub_{session_id}",
        amount_total=price_cents,
        metadata={"visitor_id": vid, "variant_id": r.json()["variant_id"]},
        webhook_secret=os.environ["STRIPE_WEBHOOK_SECRET"],
    )
    event_id = __import__("json").loads(payload)["id"]

    r3 = client.post("/webhook", content=payload, headers={"stripe-signature": sig})
    assert r3.status_code == 200, r3.text
    assert r3.json()["status"] == "ok"
    assert _order_count(event_id) == 1


def test_webhook_duplicate_delivery_still_one_order(client):
    r = _assign(client)
    vid = r.cookies["visitor_id"]
    price_cents = r.json()["price_cents"]

    payload, sig = stripe_gateway.fabricate_signed_event(
        event_type="checkout.session.completed",
        session_id="cs_stub_dup_test",
        amount_total=price_cents,
        metadata={"visitor_id": vid, "variant_id": r.json()["variant_id"]},
        webhook_secret=os.environ["STRIPE_WEBHOOK_SECRET"],
    )
    event_id = __import__("json").loads(payload)["id"]

    r1 = client.post("/webhook", content=payload, headers={"stripe-signature": sig})
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"
    assert _order_count(event_id) == 1

    # Redeliver the EXACT SAME event (same event.id, same signature) --
    # simulates Stripe's at-least-once webhook delivery.
    r2 = client.post("/webhook", content=payload, headers={"stripe-signature": sig})
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
    assert _order_count(event_id) == 1, "F6 VIOLATION: duplicate webhook created a second order"


def test_webhook_tampered_amount_is_rejected(client):
    r = _assign(client)
    vid = r.cookies["visitor_id"]
    price_cents = r.json()["price_cents"]
    tampered_amount = price_cents - 100 if price_cents > 100 else price_cents + 100

    payload, sig = stripe_gateway.fabricate_signed_event(
        event_type="checkout.session.completed",
        session_id="cs_stub_tamper_test",
        amount_total=tampered_amount,  # validly signed, but WRONG amount
        metadata={"visitor_id": vid, "variant_id": r.json()["variant_id"]},
        webhook_secret=os.environ["STRIPE_WEBHOOK_SECRET"],
    )
    event_id = __import__("json").loads(payload)["id"]

    r2 = client.post("/webhook", content=payload, headers={"stripe-signature": sig})
    assert r2.status_code == 400, r2.text
    assert _order_count(event_id) == 0, "F2 VIOLATION: a tampered-amount webhook created an order"


def test_webhook_bad_signature_is_rejected(client):
    r = _assign(client)
    vid = r.cookies["visitor_id"]
    price_cents = r.json()["price_cents"]

    payload, _sig = stripe_gateway.fabricate_signed_event(
        event_type="checkout.session.completed",
        session_id="cs_stub_badsig_test",
        amount_total=price_cents,
        metadata={"visitor_id": vid, "variant_id": r.json()["variant_id"]},
        webhook_secret="wrong-secret-not-the-real-one",
    )
    r2 = client.post("/webhook", content=payload, headers={"stripe-signature": _sig})
    assert r2.status_code == 400
