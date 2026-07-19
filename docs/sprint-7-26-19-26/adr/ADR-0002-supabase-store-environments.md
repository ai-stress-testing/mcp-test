# ADR-0002 — Store & serving topology on Supabase

**Status**: Proposed (PM to route flagged items) · **Author**: `logicians/software-architect` (opus, read-only) · **Sprint**: sprint-7-26-19-26
**Supersedes**: ADR-0001 §"State store: SQLite on the one host" only.
**Retains from ADR-0001**: serving/learning split, batch-epoch learner,
region-epoch invariant, user-level analysis. This ADR changes only *where
state lives* and *where the request path runs*, now that infra budget exists.

## Decision 1 — Store = Supabase Postgres (behind the `store.py` DAO)

SQLite retired as prod store. Unlocks: concurrent multi-worker serving without
divergence (closes code-reviewer B3), a real test↔prod schema-parity split
(PRD §7), RLS + separate schemas to physically partition analytics from
order/PII (F8), managed backups/PITR/HA, and advisory-lock/SERIALIZABLE
primitives for the learner.
**Gives up**: a managed third-party **sub-processor** enters the trust boundary
(new privacy-notice entry + DPA → DPO), network egress + pooling now mandatory,
recurring cost + lock-in. **Guardrail**: DAO speaks plain Postgres; no Supabase
client libs / PostgREST / Realtime in `pricing_core.py` — the exit stays open.

## Decision 2 — Posterior concurrency: KEEP the batch-epoch learner

Postgres makes per-outcome atomic `alpha += 1` viable — **we decline it.**
Atomicity was never the reason for the batch design; **experiment validity was**:
- The region-epoch invariant (PRD §1 / F3) needs one frozen arm per region per
  epoch; per-outcome re-selection reintroduces refresh-shopping.
- Analysis unit is the **user** (`DISTINCT visitor_id`) over an attribution-
  windowed append-only log — an atomic per-event counter silently makes the
  *event* the unit and corrupts the significance math (MIN_CONVERSIONS, CI, tie).
- Append-only + batch recompute is auditable/replayable; a lossy counter isn't.

**Single-writer mechanism (preferred)**: a scheduled learner that takes
`pg_try_advisory_lock(<learner_key>)` first and exits if it can't — smallest
boring guarantee of exactly one writer, survives duplicate schedulers. Fallback:
`SERIALIZABLE` epoch-close txn (only if folded into the request path — it
shouldn't be). **Trade-off**: keeps epoch-latency adaptation and forgoes
real-time updates — responsiveness we deliberately don't want, for an invariant
true by construction and auditable stats.

## Decision 3 — Request path = a small containerized app service (not Edge Functions)

`/assign` + `/webhook` run as the same image that promotes test→prod, talking
to Postgres via the DAO. Edge Functions rejected: image parity is a hard PRD
constraint and is native to a container; the reviewed engine is framework-free
Python (don't port a passing engine to Deno); a single small service is the
simplest place for server authority + Stripe signature verification.
**How the two authoritative properties land**:
- **F1 server-derived `state_code`**: derived from the trusted connecting IP at
  the service edge; only `{"state_code": <derived>}` passed to `assign_price`;
  client state is a non-authoritative hint; raw IP discarded post-derivation.
- **F2 server-authoritative price**: `assign_price` writes the assignment
  (`session_id → variant_id, price_cents`) to Postgres in-request; Checkout
  amount is read back from that row; `/webhook` verifies signature + timestamp,
  dedupes on `event.id`, asserts `amount_total == stored_cents` before recording;
  only a verified `checkout.session.completed` may append a `converted` outcome
  (F4). Order write idempotent on the Stripe event id (unique constraint).
**Gives up**: a host/service surface to run and patch — the opsec tactics
deferred as "revisit when real server infra exists" (Execution/Persistence/
PrivEsc) now partially come into scope; **this ADR is that trigger.**

## Decision 4 — The test↔prod boundary

**Identical (must not drift)**: schema (one migration set applies to both —
self-hosted and managed Supabase are the same Postgres), the app image
(byte-for-byte digest promotes), engine/core + DAO.
**Differs (env-supplied, never baked)**: data (test = synthetic; never copy
prod PII down — F8), secrets (**Stripe test-mode keys in test vs live in prod**;
DB creds; Supabase service key — from secret manager, CI secret-scans), and
domain/webhook URL/rate-limits/`EPOCH_HOURS`.
**Promotion**: build once → migrate test's self-hosted Supabase → verdict-loop
+ opsec re-verify (F1/F2/F4/F6) against test-mode Stripe → promote the same
image digest to prod → apply the same migrations to managed Supabase → swap
env config + live keys. Only config and data change at the boundary.

## Items to route

- **PM**: managed-Supabase cost/billing + "or equivalent" exit criteria;
  ownership of the new host/service surface (→ `devops/sre` + security); a
  standing test↔prod parity release-gate; F5 now spans two key sets.
- **`academic/statistician`**: sign off that batch-derived posteriors from
  `DISTINCT visitor_id` over the windowed log preserve the significance/tie/
  min-sample guarantees on Postgres (no drift toward per-event increments).
- **`legal/data-protection-officer`**: Supabase + its cloud host as a new
  sub-processor (privacy notice + DPA + US residency); analytics/order-PII
  schema separation satisfies F8; raw-IP discard enforceable in the new topology.
