# ADR-0001 — Pricing pipeline: state topology & experiment plane

**Status**: Proposed (PM to route flagged items) · **Author**: `logicians/software-architect` (opus, read-only) · **Sprint**: sprint-7-26-19-26

## Context

Solo operator, own domain, infra budget = domain + Stripe only. Engine exists
but two review gates block it: code-reviewer (in-process posteriors diverge
across web workers; `alpha += 1` non-atomic) and statistician (randomization
must be region-epoch level AND sticky per user; analysis unit = user).

## Decision

**Decouple the serving plane from the learning plane.** Arm selection stops
being per-request and becomes a per-epoch batch decision made by a single
offline cron **learner**. The web tier only *reads* the current epoch's arm and
*appends* user-level events. One move dissolves both blockers:

- Hot path is stateless → no cross-worker divergence, no non-atomic increment
  (posteriors are single-writer, batch-derived from an append-only log).
- One arm per region per epoch → region-epoch invariant holds by construction;
  users pinned at first assignment (sticky); posteriors from `DISTINCT
  visitor_id` (user is the analysis unit); decay λ + baseline control arm for
  non-stationarity.

**State store: SQLite on the one host** (ACID appends, zero extra infra, swap
to Postgres later behind a DAO). Chosen over atomic-increment Postgres (keeps
serving simple; epoch design doesn't want real-time updates) and over a
bespoke stateful learner process (hot-path SPOF, against YAGNI).

## Module layout (framework-free inner core)

`pricing_core.py` (pure stdlib decision fns) · `store.py` (SQLite DAO) ·
`web.py` (endpoint) · `webhook.py` · `learner.py` (cron). SQLite/web
framework/Stripe SDK are adapters around the core, never imported by it.

## Consequences (what it gives up)

Learning latency (adapts once per epoch, low-traffic regions may never reach
significance — dashboard correctly withholds a winner); less data-efficient
exploration (deliberate, for the invariant); no real-time posterior updates;
sticky-first pins a bounced user's price for the attribution window; single
host / SQLite gives up HA (DAO is the migration seam). Closing the door on
per-impression/contextual bandits is aligned with the security+legal boundary,
not a regret.

## Flagged to `pm/project-manager`

1. Statistical knobs (EPOCH_HOURS, attribution window, decay λ, min-sample) →
   `academic/statistician`.
2. Sticky-vs-region-epoch precedence rule → `academic/statistician`.
3. `visitor_id` cookie + derived `state_code` persistence → `legal/data-protection-officer` + `product-counsel`.
4. Price-integrity handoff (persist price at assignment; webhook reconciles) →
   `backend/payments-billing-engineer`.
