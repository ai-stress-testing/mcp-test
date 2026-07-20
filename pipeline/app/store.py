"""
pipeline/app/store.py -- DAO for the pricing/checkout app (ADR-0002
Decision 1 guardrail: plain Postgres via psycopg v3, no Supabase client
libs). Every function here takes an already-open connection so callers
control the transaction boundary (main.py commits per-request; learner.py
commits once at epoch-close under its advisory lock).

Connects as the `service_role` database role (DATABASE_URL), which
carries BYPASSRLS in Supabase (and is configured that way for the local
runnable check -- see pipeline/db/README.md "Roles & RLS"). The anon-role
RLS posture on assignment_event/impression is irrelevant to this service:
it never connects as anon.
"""
from __future__ import annotations

import os
from typing import Optional

import psycopg
from psycopg.rows import dict_row

# Fixed key for the learner's single-writer advisory lock (ADR-0002
# Decision 2). Arbitrary but must stay constant across processes/deploys
# for the lock to mean anything.
LEARNER_ADVISORY_LOCK_KEY = 727001


def get_conn() -> psycopg.Connection:
    """Open a new connection as the service-role identity. Autocommit is
    OFF -- callers must conn.commit() explicitly after a successful
    request so a mid-request failure rolls back cleanly (e.g. a bootstrap
    arm insert followed by an assignment insert that then fails the F2
    trigger)."""
    dsn = os.environ["DATABASE_URL"]
    return psycopg.connect(dsn, row_factory=dict_row, autocommit=False)


# --- epoch_assignment -------------------------------------------------------

def get_epoch_arm(conn: psycopg.Connection, region: str, epoch_id: int) -> Optional[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "select price_cents, variant_id from public.epoch_assignment "
            "where region = %s and epoch_id = %s",
            (region, epoch_id),
        )
        return cur.fetchone()


def ensure_bootstrap_arm(conn: psycopg.Connection, region: str, epoch_id: int,
                          price_cents: int, variant_id: str) -> dict:
    """Fallback path when a region has no live arm yet for this epoch:
    seed a posterior row (uniform Beta(1,1) prior) and an epoch_assignment
    row at the engine's baseline price, then return whatever is live for
    (region, epoch_id) -- which may be a different bootstrap that won a
    concurrent race, not necessarily this call's own values. Idempotent
    via ON CONFLICT DO NOTHING; safe under concurrent /assign requests."""
    with conn.cursor() as cur:
        cur.execute(
            "insert into public.posterior (region, price_cents, alpha, beta, updated_epoch) "
            "values (%s, %s, 1.0, 1.0, %s) "
            "on conflict (region, price_cents) do nothing",
            (region, price_cents, epoch_id),
        )
        cur.execute(
            "insert into public.epoch_assignment (region, epoch_id, price_cents, variant_id) "
            "values (%s, %s, %s, %s) "
            "on conflict (region, epoch_id) do nothing",
            (region, epoch_id, price_cents, variant_id),
        )
        cur.execute(
            "select price_cents, variant_id from public.epoch_assignment "
            "where region = %s and epoch_id = %s",
            (region, epoch_id),
        )
        row = cur.fetchone()
    if row is None:
        # Should be unreachable (we just inserted or someone else did),
        # but never silently return None to a caller expecting a price.
        raise RuntimeError(f"bootstrap failed to produce an arm for region={region} epoch_id={epoch_id}")
    return row


# --- assignment_event --------------------------------------------------------

def upsert_first_assignment(conn: psycopg.Connection, visitor_id: str, region: str,
                             epoch_id: int, variant_id: str, price_cents: int,
                             device_class: Optional[str]) -> dict:
    """Sticky first-assignment-wins, enforced by the visitor_id PK (see
    migration 0003 comment): insert-or-noop, then re-read on conflict so a
    returning visitor always gets back their ORIGINAL price, never a
    freshly recomputed one."""
    with conn.cursor() as cur:
        cur.execute(
            "insert into public.assignment_event "
            "(visitor_id, region, epoch_id, variant_id, price_cents, device_class) "
            "values (%s, %s, %s, %s, %s, %s) "
            "on conflict (visitor_id) do nothing "
            "returning visitor_id, region, epoch_id, variant_id, price_cents",
            (visitor_id, region, epoch_id, variant_id, price_cents, device_class),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "select visitor_id, region, epoch_id, variant_id, price_cents "
                "from public.assignment_event where visitor_id = %s",
                (visitor_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"upsert_first_assignment: no row for visitor_id={visitor_id} after upsert")
    return row


def get_assignment_for_visitor(conn: psycopg.Connection, visitor_id: str) -> Optional[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "select visitor_id, region, epoch_id, variant_id, price_cents "
            "from public.assignment_event where visitor_id = %s",
            (visitor_id,),
        )
        return cur.fetchone()


# --- orders -------------------------------------------------------------

def order_exists_by_event_id(conn: psycopg.Connection, stripe_event_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("select 1 from public.orders where stripe_event_id = %s", (stripe_event_id,))
        return cur.fetchone() is not None


def insert_order(conn: psycopg.Connection, stripe_session_id: str, stripe_event_id: str,
                  visitor_id: str, region: str, epoch_id: int, variant_id: str,
                  price_paid_cents: int) -> bool:
    """F6 idempotency backstop: ON CONFLICT on stripe_event_id (the
    dedupe key) means a race between a pre-check and a concurrent
    duplicate delivery still yields exactly one row. Returns True iff
    THIS call actually inserted the row (False = a duplicate, no-op)."""
    with conn.cursor() as cur:
        cur.execute(
            "insert into public.orders "
            "(stripe_session_id, stripe_event_id, visitor_id, region, epoch_id, variant_id, price_paid_cents) "
            "values (%s, %s, %s, %s, %s, %s, %s) "
            "on conflict (stripe_event_id) do nothing "
            "returning id",
            (stripe_session_id, stripe_event_id, visitor_id, region, epoch_id, variant_id, price_paid_cents),
        )
        row = cur.fetchone()
    return row is not None


# --- learner (epoch close) -----------------------------------------------

def try_advisory_lock(conn: psycopg.Connection, key: int = LEARNER_ADVISORY_LOCK_KEY) -> bool:
    with conn.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s) as locked", (key,))
        return bool(cur.fetchone()["locked"])


def advisory_unlock(conn: psycopg.Connection, key: int = LEARNER_ADVISORY_LOCK_KEY) -> None:
    with conn.cursor() as cur:
        cur.execute("select pg_advisory_unlock(%s)", (key,))


def regions_with_activity(conn: psycopg.Connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("select distinct region from public.assignment_event")
        return [r["region"] for r in cur.fetchall()]


def arm_stats_for_region(conn: psycopg.Connection, region: str) -> list[dict]:
    """Per (region, price_cents) arm: DISTINCT-visitor trials and
    conversions, joining the append-only assignment_event log to orders
    (ADR-0002 Decision 2: analysis unit is the user, not the event; no
    attribution-window filter yet -- EPOCH_HOURS/window cadence is the
    open item ADR-0001 flagged to academic/statistician, kept out of this
    ticket's scope rather than guessed at)."""
    with conn.cursor() as cur:
        cur.execute(
            "select ae.price_cents as price_cents, "
            "count(distinct ae.visitor_id) as trials, "
            "count(distinct o.visitor_id) as conversions "
            "from public.assignment_event ae "
            "left join public.orders o on o.visitor_id = ae.visitor_id "
            "where ae.region = %s "
            "group by ae.price_cents",
            (region,),
        )
        return cur.fetchall()


def upsert_posterior(conn: psycopg.Connection, region: str, price_cents: int,
                      alpha: float, beta: float, epoch_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "insert into public.posterior (region, price_cents, alpha, beta, updated_epoch) "
            "values (%s, %s, %s, %s, %s) "
            "on conflict (region, price_cents) do update set "
            "alpha = excluded.alpha, beta = excluded.beta, updated_epoch = excluded.updated_epoch",
            (region, price_cents, alpha, beta, epoch_id),
        )


def upsert_epoch_assignment(conn: psycopg.Connection, region: str, epoch_id: int,
                             price_cents: int, variant_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "insert into public.epoch_assignment (region, epoch_id, price_cents, variant_id) "
            "values (%s, %s, %s, %s) "
            "on conflict (region, epoch_id) do nothing",
            (region, epoch_id, price_cents, variant_id),
        )
