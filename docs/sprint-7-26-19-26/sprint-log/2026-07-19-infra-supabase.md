run-id: 2026-07-19-supabase-two-environments
prompt: "I can host a proper Supabase instance. I like a test version and a
  production version; self-hosted Supabase on Docker for test. Keep iterating."
agents:
  - logicians/software-architect (opus) — ADR-0002 (store + serving topology)
  - devops/containerization-engineer (sonnet) — MT-21 test/prod environments
  - backend/backend-dev (sonnet) — MT-22 Postgres schema + migrations + RLS
specs: prd.md §1,§4,§7,§8 (updated); adr/ADR-0002
verdicts: all three deliverables verified by the orchestrator (see Done)
commits: (this commit)

# 2026-07-19 — Supabase store + test/prod environments

**Session/agent**: orchestrator running the Ges-Talt spec-driven flow.
**Issues touched**: PRD infra forks resolved; MT-20/MT-21/MT-22 done.

## Done
- **ADR-0002** (`logicians/software-architect`): Supabase Postgres behind the
  `store.py` DAO (supersedes ADR-0001's SQLite). Keeps the batch-epoch learner
  (experiment validity, not atomicity, was its reason — declines per-outcome
  atomic increments). Money path = a small containerized service (not Edge
  Functions) so the image promotes test→prod and the framework-free engine
  stays put; F1 (server-derived state) and F2 (server-authoritative price) land
  there.
- **MT-21 environments** (`devops/containerization-engineer`): `environments/`
  with a self-hosted Supabase test stack (6 pinned services, healthchecks),
  test/prod `.env.example` (Stripe test vs live, no secrets), a `.gitignore`
  that tracks only `.example`, and `check-compose.sh`. **Verified**: `docker
  compose config` PASS in my hands (daemon not needed).
- **MT-22 schema** (`backend/backend-dev`): `pipeline/db/migrations/` — 5
  reversible migrations for the ADR event model. **Verified on a live PG16**:
  up ×5 → 5 tables → down ×5 → 0 tables; F6 = two UNIQUE constraints; F2 = two
  BEFORE-INSERT price-integrity triggers; RLS enabled on all 5 tables; F10 =
  all price columns `integer` cents; F8 = no raw-IP/zip column (the "ip"
  substring hits were `stripe_*`). Agent also caught+fixed a real RLS bug
  (trigger fns needed `SECURITY DEFINER`) by testing.

## Decisions
- Store = Supabase Postgres; two environments (test = self-hosted Docker, prod
  = managed), image parity, config from env, no committed secrets. (ADR-0002.)
- Batch-epoch learner retained; single-writer via `pg_try_advisory_lock`.
- `order` table renamed `orders` (reserved keyword) — same columns/semantics.

## Blocked / carried
- New host/service surface (ADR-0002 Decision 3) re-opens opsec tactics
  deferred as "revisit when real server infra exists" (Execution/Persistence/
  PrivEsc) → route to `devops/sre` + security.
- Still open before go-live: re-run MT-6/MT-7 gates on engine v2; build the
  `/assign` + `/webhook` service (MT-13/MT-14) against this schema with F1/F2/F6
  controls; MT-5 disclosure copy; statistician sign-off that Postgres batch
  posteriors preserve the significance guarantees (ADR-0002 routing).
