run-id: 2026-07-19-runnable-pipeline
prompt: "Using the agents continue working on the pipeline. If feasible create
  a real, hostable, and professional deliverable."
agents:
  - backend/backend-dev (sonnet) — MT-23 app service + DAO + learner
  - frontend/react-dev (sonnet) — MT-10 checkout page
  - devops/containerization-engineer (sonnet) — MT-24 Dockerfile + compose wiring
specs: prd.md §1,§4,§5,§8; adr/ADR-0002 Decision 3
verdicts: all deliverables verified by the orchestrator (see Done); the
  build-context seam between agents was closed + re-verified here
commits: (this commit)

# 2026-07-19 — Runnable app service: engine → Postgres → Stripe

**Session/agent**: orchestrator running the Ges-Talt spec-driven flow.
**Issues touched**: MT-10, MT-13, MT-14, MT-23, MT-24 done.

## Done
- **MT-23 app service** (`backend/backend-dev`, `pipeline/app/`): FastAPI
  `/assign` (server-derives region from IP — F1; client `state_code` never
  read), `/create-checkout` (Stripe amount from the stored assignment, not the
  client — F2), `/webhook` (signature + timestamp verified, deduped on
  `event.id`, asserts `amount_total == stored` — F2/F6, outcomes only from
  verified webhooks — F4), a psycopg DAO, and a batch learner (advisory lock,
  writes the *next* epoch's arm, reuses engine v2's selection). **Verified:
  10/10 tests on a live Postgres** incl. state-spoof rejected, tampered amount
  rejected, duplicate delivery → one order, bad signature rejected.
- **MT-10 checkout page** (`frontend/react-dev`, `pipeline/web/`): self-
  contained static page per the designer spec — **28/28 Playwright checks, 0
  axe violations** across 6 state/theme combos, keyboard + 320px reflow passes.
  Refuses to fabricate a fallback price (graceful no-price state) and renders
  the disclosure from the server, leaving the MT-5 go-live gate intact.
- **MT-24 container + integration** (`devops/containerization-engineer` +
  orchestrator): multi-stage non-root Dockerfile + `app` service in the compose
  stack (caught a Kong host-port collision). Orchestrator closed the cross-
  ticket **build-context seam** (`pricing_engine.py` and `web/` sat outside the
  `pipeline/app/` context): widened context to `pipeline/`, fixed the Dockerfile
  COPY/WORKDIR and `.dockerignore`, `app.build.context`. **Verified** by
  mirroring the image FS and booting from `/app/app`: `/healthz` 200 (engine
  import resolves) and `/` serves the real page (web ships), + compose config
  still valid + the 10 app tests still green.

## Decisions
- Money path is one small containerized FastAPI service (ADR-0002 D3); same
  image promotes test→prod, config from env, no secrets baked in.
- Fallback never fabricates a price — server-authoritative or a graceful
  no-price state; disclosure text is always server-sourced (MT-5's home).

## Blocked / carried (go-live gate — NOT shippable yet)
- **MT-5** disclosure/privacy copy (legal sign-off) still blocks the paid page.
- **MT-6/MT-7** re-review of engine v2; **MT-15** (idempotency review),
  **MT-16** (PCI scope) on the payment path; OPSEC F1/F2/F6 are now
  *implemented + tested* but still need `security` re-verification.
- Real run needs a Supabase project + Stripe keys (test then live) supplied via
  env; image build itself couldn't run here (no Docker daemon) — verified via
  FS-mirror instead.
