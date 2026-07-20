"""
pipeline/app/stripe_gateway.py -- Stripe adapter with two modes,
selected by STRIPE_MODE:

  STRIPE_MODE=stub          fabricates deterministic Checkout sessions
                             and validly-signed webhook payloads, no
                             network -- lets /assign, /create-checkout,
                             /webhook be exercised end-to-end offline
                             (this sandbox has no live Stripe network).
  STRIPE_MODE=test|live     the real `stripe` SDK against Stripe's API,
                             keyed by STRIPE_SECRET_KEY (test vs live key
                             is the only thing that differs -- ADR-0002
                             Decision 4).

Signature verification (`verify_and_construct_event`) uses Stripe's
publicly documented scheme (HMAC-SHA256 over "{timestamp}.{payload}")
directly in BOTH modes for stub-fabricated events; in test/live mode it
prefers the official SDK's `stripe.Webhook.construct_event` for exact
parity with real Stripe behavior. Only the secret differs between
stub/test/live -- never hardcoded, always STRIPE_WEBHOOK_SECRET from env.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Optional


def _mode() -> str:
    return os.environ.get("STRIPE_MODE", "stub").strip().lower()


def _sign(payload: bytes, secret: str, timestamp: int) -> str:
    signed_payload = f"{timestamp}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def create_checkout_session(price_cents: int, currency: str, variant_id: str,
                             visitor_id: str, region: str,
                             success_url: Optional[str] = None,
                             cancel_url: Optional[str] = None) -> dict:
    """amount is ALWAYS the caller-supplied price_cents, which main.py
    reads from the stored assignment_event row -- never from a client
    request (F2). Returns {"id": ..., "url": ...}."""
    if price_cents <= 0:
        raise ValueError("price_cents must be positive")

    if _mode() == "stub":
        session_id = f"cs_stub_{uuid.uuid4().hex}"
        return {
            "id": session_id,
            "url": f"https://checkout.stub.local/pay/{session_id}",
        }

    import stripe  # lazy import: not required at all in stub mode

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": currency,
                "unit_amount": price_cents,
                "product_data": {"name": f"Order ({variant_id})"},
            },
            "quantity": 1,
        }],
        metadata={"variant_id": variant_id, "visitor_id": visitor_id, "region": region},
        success_url=success_url or "https://example.com/success",
        cancel_url=cancel_url or "https://example.com/cancel",
    )
    return {"id": session.id, "url": session.url}


def verify_and_construct_event(payload: bytes, sig_header: str, webhook_secret: str,
                                tolerance: int = 300) -> dict:
    """Verify `Stripe-Signature` + timestamp tolerance (F6) and return the
    parsed event dict. Raises ValueError on any verification failure
    (bad/missing signature, expired timestamp, malformed header/payload)
    -- callers must treat that as a rejected webhook, never a partial
    success."""
    if not sig_header:
        raise ValueError("missing Stripe-Signature header")

    if _mode() != "stub":
        import stripe
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret, tolerance=tolerance)
        except Exception as exc:  # stripe.error.SignatureVerificationError et al.
            raise ValueError(f"webhook signature verification failed: {exc}") from exc
        return event if isinstance(event, dict) else event.to_dict()

    # stub mode: verify with the same public HMAC scheme Stripe itself uses.
    try:
        parts = dict(kv.split("=", 1) for kv in sig_header.split(",") if "=" in kv)
        timestamp = int(parts["t"])
        given_sig = parts["v1"]
    except Exception as exc:
        raise ValueError(f"malformed Stripe-Signature header: {exc}") from exc

    if abs(time.time() - timestamp) > tolerance:
        raise ValueError("webhook timestamp outside tolerance (possible replay)")

    expected_sig = hmac.new(
        webhook_secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, given_sig):
        raise ValueError("webhook signature mismatch")

    try:
        return json.loads(payload)
    except Exception as exc:
        raise ValueError(f"malformed webhook payload JSON: {exc}") from exc


def fabricate_signed_event(event_type: str, session_id: str, amount_total: int,
                            metadata: dict, webhook_secret: str,
                            event_id: Optional[str] = None,
                            timestamp: Optional[int] = None,
                            currency: str = "usd") -> tuple[bytes, str]:
    """STUB/TEST HELPER ONLY -- builds a Stripe-shaped event body and a
    validly signed Stripe-Signature header so the /webhook path can be
    exercised offline, end to end. Not used by the app's request path
    itself; used by the runnable check (and by anything standing in for
    "Stripe" in STRIPE_MODE=stub, e.g. a local test-delivery script).
    Returns (payload_bytes, signature_header)."""
    timestamp = timestamp or int(time.time())
    event_id = event_id or f"evt_stub_{uuid.uuid4().hex}"
    body = {
        "id": event_id,
        "object": "event",
        "type": event_type,
        "created": timestamp,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "amount_total": amount_total,
                "currency": currency,
                "metadata": metadata,
                "payment_status": "paid",
                "status": "complete",
            }
        },
    }
    payload = json.dumps(body).encode()
    sig_header = _sign(payload, webhook_secret, timestamp)
    return payload, sig_header
