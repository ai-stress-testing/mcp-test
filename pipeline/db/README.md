# pipeline/db — database layer

Scope of this directory: **schema only** (Supabase Postgres), as reversible
migrations under `migrations/`. No endpoints, no learner cron, no web app —
those are other tickets (see "Seams" below). Does not touch `environments/`
(containerization-engineer's ticket).

Source of truth for the model: `docs/sprint-7-26-19-26/adr/ADR-0001-pricing-topology.md`
(event schema / serving-learning split), `docs/sprint-7-26-19-26/reviews/security-threat-model.md`
and `opsec-gate.md` (F1/F2/F4/F6/F8/F10 controls this schema bakes in),
`pipeline/pricing_engine.py` (`Assignment` / `PriceArm` shapes this schema
persists).

## Tables

| Table | Writer | Purpose |
|---|---|---|
| `posterior` | learner cron only (service_role) | Beta(alpha, beta) per (region, price_cents) arm — the bandit's belief state. |
| `epoch_assignment` | learner cron only (service_role) | The one live (price, variant) per region per epoch — what the web tier reads. |
| `assignment_event` | anon (insert-only) | One row per visitor's **first** assignment (sticky, PK = `visitor_id`). |
| `impression` | anon (insert-only) | Page-view/impression telemetry. Analytics only. |
| `orders` | webhook handler only (service_role) | One row per fulfilled Stripe Checkout session. Ticket calls this `order`; renamed to avoid the `ORDER` reserved keyword — see "Naming note". |

Migration order matters (FK dependencies): `posterior` → `epoch_assignment`
→ `assignment_event` → `impression` / `orders`.

## Single-writer rule (ADR-0001)

`posterior` and `epoch_assignment` have exactly one writer: the offline
learner cron, running as `service_role`. This is what makes the region-epoch
invariant hold by construction (ADR-0001) — the web/serving tier never
mutates bandit state, it only reads `epoch_assignment` (via `service_role`,
server-side — see "Roles & RLS") and appends events. `orders` likewise has
exactly one writer: the signature-verified Stripe webhook handler
(`service_role`) — never the browser, never a client-supplied amount.

## Naming note

The ticket and ADR call the sales table `order`. `ORDER` is a reserved
SQL keyword; every reference to an unquoted `order` table breaks, and
quoting `"order"` in every query forever is unnecessary attack surface for
a typo. The migration creates `orders` instead — same entity, same columns,
same constraints the ticket specifies.

## F2 — price-integrity: schema seam + app-layer enforcement

F2 (threat model, CRITICAL) is "no crypto binding of shown price to
charge → client edits amount." The **primary control is application-layer**
and is *not* built in this ticket — it's the seam for
`backend/payments-billing-engineer` (ADR-0001 flagged item 4):

1. The Checkout Session must be created server-side with `amount` read from
   the visitor's `assignment_event.price_cents` row (never from a client
   parameter).
2. The webhook handler must verify the signature (F6), then assert
   `event.data.object.amount_total == assignment_event.price_cents` for
   that visitor **before** it writes to `orders`.

The schema backs that app-layer control with a **database-level backstop**,
not a substitute for it: `orders_price_matches_assignment()` (trigger,
`0005_orders.up.sql`) re-derives the visitor's assignment on every insert
and raises if `region` / `epoch_id` / `variant_id` / `price_paid_cents`
don't match `assignment_event` exactly. An app bug that skips the
`amount_total` check therefore fails loudly as a rejected insert instead of
silently writing an under-priced order. The same pattern polices
`assignment_event` itself against `epoch_assignment`
(`assignment_event_matches_epoch()`, `0003_assignment_event.up.sql`), so a
sticky assignment can't be written for a price that isn't the live arm.

Postgres `CHECK` constraints cannot reference another table, which is why
this is a trigger rather than a `CHECK` — the FK-only piece (an order must
point at a real `assignment_event` row) *is* a plain FK
(`orders_visitor_fkey`); the equality piece needs the trigger.

## F10 — integer cents

Every price column (`posterior.price_cents`, `epoch_assignment.price_cents`,
`assignment_event.price_cents`, `impression`'s `variant_id` text encodes it
but doesn't store it separately, `orders.price_paid_cents`) is `integer`
cents, never `numeric`/`float` dollars. This is what makes the F2 equality
check in the trigger exact instead of epsilon-comparison-prone.
`pipeline/pricing_engine.py` currently computes float dollar prices
(`PriceArm.price`) — converting to integer cents at the point of persistence
is the app-layer seam for whoever builds the learner/web writer path; it is
not done in `pricing_engine.py` by this ticket (out of scope: engine
changes).

## F8 — no raw IP, ever

No table in this schema has an IP address column, and none should ever be
added. Geolocation happens upstream (the F1 control: derive `state_code`
server-side from the connecting IP); only its derived output — `region` — is
persisted anywhere here. `device_class` is present (PRD req. 2) strictly for
UX/conversion analytics and is structurally never joined into a pricing
query, FK, or trigger in this schema — pricing reads only
`posterior`/`epoch_assignment`.

## Roles & RLS

Supabase ships three relevant roles: `anon` (public API key, e.g. from the
browser), `authenticated` (unused here — visitors don't log in), and
`service_role` (secret key, server-side only, carries `BYPASSRLS`).

- `assignment_event`, `impression`: RLS enabled, **`anon` may `INSERT`
  only** (`with check (true)` — every insert is a visitor's own event, there
  is nothing to scope by owner). No `SELECT`/`UPDATE`/`DELETE` policy exists
  for `anon`, so those commands are default-denied even though the base
  `GRANT`s are also explicitly revoked (belt-and-suspenders). A visitor
  cannot read or tamper with another visitor's row.
- `posterior`, `epoch_assignment`, `orders`: RLS enabled with **zero**
  policies and an explicit `REVOKE ALL ... FROM anon, authenticated`. Only
  `service_role` can touch them, via its `BYPASSRLS` attribute — no policy
  is defined *for* `service_role` because none is needed.
- The pricing-read path (server reads `epoch_assignment` to price a
  visitor) runs **server-side using the `service_role` key**, never the
  `anon` key from the browser. This is deliberate, not an oversight: if
  `anon` could `SELECT epoch_assignment`, any client could enumerate every
  region's live price, and the F1/F2 boundary (price is server-computed,
  never client-readable-then-trusted) gets weaker. The public-facing pricing
  endpoint is a server route, not a direct Supabase client call.

## Applying / verifying

Against a local Supabase (`supabase start`, Docker-based self-hosted per PRD
§7 test environment) or a bare Postgres with the Supabase roles created:

```bash
# apply, in order
for f in pipeline/db/migrations/*.up.sql; do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done

# roll back, in reverse order
for f in $(ls -r pipeline/db/migrations/*.down.sql); do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
```

If using the Supabase CLI instead of raw `psql`, drop these files (renamed
`<timestamp>_<name>.sql`, up only — Supabase CLI migrations are forward-only
by convention) into `supabase/migrations/` and run `supabase db push` /
`supabase migration up`; the `.down.sql` files remain the source of truth
for manual rollback since the CLI has no built-in `down`.

**Runnable check performed for this ticket**: applied every `.up.sql` in
order against a scratch database on the sandbox's local Postgres 16
(`createdb ges_talt_db_check`, with `anon`/`authenticated`/`service_role`
roles created to stand in for Supabase's), confirmed the RLS posture
(`anon` can `INSERT` into `assignment_event`/`impression`, cannot read or
write `posterior`/`epoch_assignment`/`orders`; the F2 triggers reject a
mismatched price), then applied every `.down.sql` in reverse order back to
an empty schema. See the sprint log for the transcript. To re-run:

```bash
createdb ges_talt_db_check
psql ges_talt_db_check -c "create role anon; create role authenticated; create role service_role;"
for f in pipeline/db/migrations/*.up.sql; do psql ges_talt_db_check -v ON_ERROR_STOP=1 -f "$f"; done
# ... exercise / inspect ...
for f in $(ls -r pipeline/db/migrations/*.down.sql); do psql ges_talt_db_check -v ON_ERROR_STOP=1 -f "$f"; done
dropdb ges_talt_db_check
```

## Seams left for other tickets

- **Learner cron** (writes `posterior` + `epoch_assignment`, `service_role`):
  converts `pricing_engine.py` float dollars → integer cents at write time.
- **Web/serving endpoint** (reads `epoch_assignment`, `service_role`,
  server-side): the F1 server-side IP→state derivation happens here, not in
  this schema.
- **Assignment-event / impression writer**: whatever writes the visitor's
  first assignment must do `insert into assignment_event ... on conflict
  (visitor_id) do nothing returning *`, then re-read on conflict — sticky
  pinning is enforced by the `visitor_id` primary key, not by app logic
  alone.
- **Payments/webhook handler** (`backend/payments-billing-engineer`,
  ADR-0001 flagged item 4): signature verification (F6), the
  `amount_total == assignment_event.price_cents` assertion (F2, primary
  control — see above), and the `orders` insert.
- **Retention/deletion jobs** (F8, `legal/privacy-engineer` + DPO): this
  schema does not implement a retention window or delete job; `assigned_at`
  / `occurred_at` / `created_at` timestamps are there for one to be built
  against.
