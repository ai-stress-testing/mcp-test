run-id: 2026-07-20-analytics-backend
prompt: "MT-29 — owner-only analytics + interaction-capture backend."
agents:
  - backend/backend-dev (sonnet) — MT-29 interaction capture + owner auth + reads
specs: product-brief.md §2 ("owner-only analytics"); threat-model.md F8;
  opsec-gate.md F8
verdicts: runnable check below, self-verified by the implementing agent —
  not yet reviewed by security/senior-secops (owner-auth is security-
  sensitive, flagged for that review, see Blocked / carried)
commits: (this commit)

# 2026-07-20 — Owner-only analytics + interaction-capture backend

**Session/agent**: `backend/backend-dev` (sonnet).
**Issues touched**: MT-29 done (backend only — UI is `frontend/react-dev`'s
next ticket).

## Done
- **`pipeline/db/migrations/0006_interaction_event.{up,down}.sql`**: new
  `interaction_event` table — anonymous `session_id` (opaque, deliberately
  never `assignment_event.visitor_id`, never FK'd to it), closed
  `event_type` enum (`pageview|click|scroll|cta_view|cta_click`), bounded
  `x_pct`/`y_pct`/`scroll_pct` (0-100, nullable), `viewport_w` (0-20000),
  `occurred_at`. No raw IP, no text/keystroke column (F8). RLS: `anon`
  INSERT-only, with the CHECK bounds duplicated into the RLS policy itself
  (defense-in-depth against a client using the anon key directly, not just
  the app). No SELECT grant/policy for anyone but `service_role`.
- **`pipeline/app/owner_auth.py`** (new): single-owner gate. `check_passcode`
  compares against `OWNER_PASSCODE` via HMAC-SHA256 digests +
  `hmac.compare_digest` (constant-time, and avoids leaking the configured
  passcode's length the way a raw `compare_digest(candidate, expected)`
  would on early length-mismatch). `issue_session_token`/
  `verify_session_token` mint/check a `{expiry}.{hmac-sha256 sig}` token
  signed with `OWNER_SESSION_SECRET` — no secret material embedded in the
  token itself. `require_owner` is the FastAPI dependency gating every
  `/admin/*` route; fails closed (401) on missing/expired/tampered cookie
  or an unconfigured `OWNER_SESSION_SECRET`.
- **`pipeline/app/main.py`**: `POST /track` (public, bounded — chunked body
  read capped at 4096 bytes so an attacker can't bypass a Content-Length
  check; unknown `event_type` rejected, percentages clamped not rejected,
  `session_id` sourced only from a dedicated `session_id` cookie the
  server mints, never trusted from the client body); `POST /admin/login`
  (issues the owner cookie, `Secure`/`httponly`/`SameSite=strict`);
  `GET /admin/metrics` (per-region arm/conversion/revenue +
  pageview→cta_view→cta_click→order funnel counts); `GET /admin/heatmap`
  (click-density bins + scroll-depth histogram, aggregate counts only —
  no endpoint returns a raw `interaction_event` row). All three `/admin/*`
  routes 401 via `Depends(owner_auth.require_owner)`.
- **`pipeline/app/store.py`**: `insert_interaction_event`,
  `region_metrics`, `funnel_counts`, `heatmap_bins` — every read helper
  returns counts/bins, never per-session rows.

## Decisions
- Analytics `session_id` lives on its own cookie (`session_id`, distinct
  from the pricing `visitor_id` cookie) and is never joined to
  `assignment_event`/`orders` anywhere in the schema or the DAO — this is
  the F8 control, not an incidental gap. The funnel counts in
  `/admin/metrics` are therefore independent per-stage counts
  (pageview/cta_view/cta_click distinct-session counts, `order` a plain
  row count), not a single joined cohort — a deliberate trade against
  re-identification risk.
- Owner-auth uses only stdlib `hmac`/`hashlib`/`secrets` per the ticket's
  constraint; no invented password hashing (single operator credential,
  not stored at rest beyond the `OWNER_PASSCODE` env var).

## Runnable check (this session, local Postgres 16 via `sudo -u postgres`)
- Applied all 6 `.up.sql` migrations in order on a scratch DB with
  `anon`/`authenticated`/`service_role` stand-in roles — clean.
- RLS spot-check as `anon` (via `SET ROLE`): valid `interaction_event`
  insert succeeds; an out-of-enum `event_type` is rejected by the RLS
  policy itself (not just app validation); `SELECT` denied.
- `pipeline/app/tests/test_app.py` — all 10 pre-existing tests still pass
  unmodified (STRIPE_MODE=stub).
- Ad-hoc script (not committed) against a live `TestClient`: `/track`
  accepts a bounded click/scroll event and sets the `session_id` cookie;
  rejects an unknown `event_type` (400) and a non-integer `viewport_w`
  (400); clamps out-of-range percentages instead of rejecting (200); rejects
  an oversized `path` (400, chunked-read cap). `/admin/metrics` and
  `/admin/heatmap` both 401 with no cookie and with a tampered
  `owner_session` cookie; `/admin/login` 401 on a wrong passcode (no
  cookie set); 200 + valid cookie on the correct `OWNER_PASSCODE`; then
  both admin reads return 200 with correct owner session, `/admin/heatmap`
  response contains no `session_id` field anywhere (aggregate-only
  confirmed by string search on the response body).
- Full down-migration chain (`0006` → `0001`) verified reversible back to
  an empty `public` schema.
- Cleanup: scratch DB and the three stand-in roles dropped; scratch venv
  and the ad-hoc check script removed after the run.

## Blocked / carried
- **`security/senior-secops` review requested**: owner-auth is
  security-sensitive (session-cookie signing, passcode comparison,
  fail-closed behavior when `OWNER_SESSION_SECRET`/`OWNER_PASSCODE` are
  unset). Flagging `pipeline/app/owner_auth.py` + the `/admin/login`
  handler in `main.py` for that review before go-live, per this repo's
  security-sensitive-change convention.
- No rate limiting on `/admin/login` (brute-force passcode guessing) or
  `/track` — out of this ticket's scope, same F11 (endpoint DoS/rate-limit)
  finding already OPEN in `opsec-gate.md`, owned by
  `devops/sre` + `networking/network-engineer`.
- UI for the owner dashboard is `frontend/react-dev`'s next ticket
  (MT-31, blocked on this + MT-27) — this ticket returns JSON only, no
  templates/pages touched.
- `environments/*/.env.example` were NOT touched (out of this ticket's
  scope) — they'll need `OWNER_PASSCODE` and `OWNER_SESSION_SECRET`
  placeholders added by whoever owns those files before this ships to the
  test/prod compose stacks.
