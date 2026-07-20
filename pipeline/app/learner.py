"""
pipeline/app/learner.py -- the offline batch epoch-close job (ADR-0001 /
ADR-0002 Decision 2). Single writer of posterior + epoch_assignment,
enforced by a `pg_try_advisory_lock` taken up front: if another instance
already holds it, this run exits immediately rather than racing it
(idempotent no-op, not an error -- survives duplicate schedulers).

Per (region, price arm): derives posteriors from DISTINCT visitor_id over
assignment_event LEFT JOINed to orders (analysis unit is the user, not
the event -- ADR-0002 Decision 2), then reuses pricing_engine.py's own
Thompson-sampling selection (`_select_arm`) to pick the next arm, and
writes it to epoch_assignment for the next epoch id.

Run as a cron / scheduled job, NOT in the request path:
    python3 pipeline/app/learner.py
Exits 0 whether it did work or lost the advisory-lock race; exits
non-zero only on an actual failure (DB error, etc.), so a scheduler can
alert on real breakage without false-positiving on "someone else already
has the lock."
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Optional

_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)
from pricing_engine import PricingEngine  # noqa: E402

import store  # sibling module, flat import (see main.py's note)


def _epoch_hours() -> float:
    return float(os.environ.get("EPOCH_HOURS", "24"))


def _base_price_cents() -> int:
    return int(os.environ.get("BASE_PRICE_CENTS", "6000"))


def current_epoch_id(epoch_hours: Optional[float] = None, now: Optional[datetime] = None) -> int:
    epoch_hours = epoch_hours if epoch_hours is not None else _epoch_hours()
    now = now or datetime.now(timezone.utc)
    return int(now.timestamp() // (epoch_hours * 3600))


def close_epoch(conn, base_price_dollars: float, target_epoch_id: int) -> dict:
    """Recompute posteriors for every region with recorded activity and
    write the Thompson-selected next arm for target_epoch_id. Returns a
    small summary dict for logging/tests: {region: {price_cents, variant_id}}."""
    engine = PricingEngine(base_price=base_price_dollars)
    summary: dict[str, dict] = {}

    for region in store.regions_with_activity(conn):
        stats_by_price_cents = {
            row["price_cents"]: row for row in store.arm_stats_for_region(conn, region)
        }
        if not stats_by_price_cents:
            continue

        # The canonical price grid for this region (same one /assign's
        # bootstrap path and the engine's own arm derivation use) --
        # reusing engine internals is the "reuse engine v2 selection
        # logic" the ticket asks for, not a reimplementation of Thompson
        # sampling here.
        arms = engine._arms_for(region)  # noqa: SLF001 -- intentional reuse, not a public API misuse

        # A posterior row must exist for EVERY grid arm, not just the ones
        # with observed trials: _select_arm()'s forced-round-robin phase
        # picks the cheapest UNEXPLORED arm first, and epoch_assignment's
        # FK (epoch_assignment_arm_fkey) requires whatever it picks to
        # already be a posterior row. An arm with no observations gets
        # the uniform Beta(1,1) prior, same default PriceArm starts with.
        for arm in arms:
            price_cents = round(arm.price * 100)
            row = stats_by_price_cents.get(price_cents)
            conversions = int(row["conversions"]) if row else 0
            trials = int(row["trials"]) if row else 0
            arm.alpha = 1.0 + conversions
            arm.beta = 1.0 + max(trials - conversions, 0)
            store.upsert_posterior(conn, region, price_cents, arm.alpha, arm.beta, target_epoch_id)

        # Any observed price OUTSIDE the current grid (e.g. base price /
        # spread changed since it was served) has nothing to attribute to
        # and is intentionally not folded in -- it stays in assignment_event/
        # orders for audit, it just doesn't feed today's grid's posteriors.

        chosen = engine._select_arm(region)  # noqa: SLF001 -- see note above
        price_cents = round(chosen.price * 100)
        variant_id = f"{region}@{chosen.price:.2f}"
        store.upsert_epoch_assignment(conn, region, target_epoch_id, price_cents, variant_id)
        summary[region] = {"price_cents": price_cents, "variant_id": variant_id}

    return summary


def main() -> int:
    # Target NEXT epoch, not the current one: the region-epoch invariant
    # (ADR-0001) requires the CURRENT epoch's arm to stay frozen for
    # every visitor already in it. Writing next epoch's row in advance
    # means /assign's bootstrap fallback (store.ensure_bootstrap_arm)
    # only ever fires for a region with no traffic yet, not as a race
    # against this job for an epoch already being served. epoch_assign-
    # ment writes are ON CONFLICT DO NOTHING (see store.py) specifically
    # so neither writer can clobber a price already live for an epoch.
    target_epoch_id = current_epoch_id() + 1
    base_price_dollars = _base_price_cents() / 100.0

    conn = store.get_conn()
    try:
        if not store.try_advisory_lock(conn):
            print("learner: advisory lock held elsewhere, exiting (no-op)")
            return 0
        try:
            summary = close_epoch(conn, base_price_dollars, target_epoch_id)
            conn.commit()
            print(f"learner: epoch {target_epoch_id} closed for {len(summary)} region(s): {summary}")
        finally:
            store.advisory_unlock(conn)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
