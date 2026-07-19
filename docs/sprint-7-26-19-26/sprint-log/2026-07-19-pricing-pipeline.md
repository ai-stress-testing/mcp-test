run-id: 2026-07-19-regional-pricing-pipeline
prompt: "A/B-testable sales pipeline that finds optimal price per region from
  per-state baselines; privacy-protecting; use the Ges-Talt agents, funnel
  through OPSEC."
agents:
  - pm/project-manager (opus) — PRD §1–6, issue spec, MT-8..MT-17 decomposition
  - security/architect (opus) — spec-time consult + full threat model (F1–F11)
  - legal/general-counsel (opus) — consult: disparate-impact + surveillance-pricing
  - backend/backend-dev (sonnet) — MT-1 engine v1 + v2 handback fix
  - logicians/code-reviewer (opus) — MT-6 static review → FAIL (3 blockers)
  - academic/statistician (opus) — MT-7 A/B-validity gate → FAIL
  - logicians/software-architect (opus) — ADR-0001 (serving/learning split)
  - frontend/designer (sonnet) — MT-9 checkout page design spec + mockup
specs: prd.md §1–6; issue-specs/pricing-pipeline.md; adr/ADR-0001; opsec-gate.md
verdicts: MT-6 FAIL + MT-7 FAIL → MT-1 v2 fix (self-test PASS, re-review pending);
  OPSEC gate FAIL for go-live (F1/F2/F4/F6 block)
commits: c2d5f92 (MT-1 v1 + tracking); this commit (v2 + agent wave + OPSEC)

# 2026-07-19 — Pricing pipeline: review verdicts, agent wave, OPSEC gate

**Session/agent**: orchestrator (main) running the Ges-Talt spec-driven flow.
**Issues touched**: MT-1 (v2), MT-6/MT-7 (FAIL→handback), MT-8/MT-9 (done),
MT-10..MT-19 (cut/blocked), OPSEC gate.

## Done
- **MT-1 v2** (`pipeline/pricing_engine.py`): fixed every blocker from the two
  review gates — state-VALUE validation (no ZIP pricing), epoch-frozen arm
  (same price per region per epoch), min-sample gate + revenue-CI tie rule
  (defaults to lower price), thread-safe updates, and a self-test that can now
  actually FAIL (multi-seed, continuous true-optimum sweep, off-grid
  detection). Self-test PASS / exit 0. Re-review pending before MT-1 closes.
- **Agent wave** (proper Ges-Talt agents, primed from real personas):
  code-reviewer (MT-6 FAIL), statistician (MT-7 FAIL), software-architect
  (ADR-0001), security-architect (threat model), PM (MT-8..MT-17), designer
  (MT-9 spec + mockup). Deliverables persisted under `adr/`, `reviews/`,
  `design-specs/`.
- **OPSEC funnel** (`opsec-gate.md`): threat-model findings F1–F11 routed
  through the `docs/opsec/` tactic checklists (03 Initial Access, 09 Credential
  Access, 12 Collection, 14 Exfiltration, 15 Impact; 01/02 for identity) with
  control + owner + phase + gate status per row.

## Decisions
- **ADR-0001**: split the serving plane from the learning plane — a single
  offline cron learner owns posteriors (one writer, no atomic-increment race),
  the stateless web tier reads a per-epoch arm-lookup table and appends
  user-level events to SQLite. This is the settled fix for code-reviewer B3.
- **OPSEC gate FAIL for go-live**: F1 (server-derive `state_code`, don't trust
  the client) and F2 (server-authoritative price bound to the charge) are hard
  blockers; F4/F6 (webhook-only outcome feed + signature/idempotency) close
  before real money flows. F3 cleared in v2.
- Device/sub-state pricing remains cut (spec-time, not re-litigated).

## Blocked / carried
- Re-run MT-6/MT-7 gates on engine v2 to close MT-1.
- MT-10 (page build) blocked on MT-5 disclosure copy + MT-8 contract.
- MT-13/MT-14 must implement the F1/F2/F6 controls; MT-18 tracks the OPSEC
  blockers, MT-19 the PRD §6 operator-identity register (F9).
- PM flagged 4 PRD ambiguities for the human: hosting substrate vs "domain +
  Stripe only", arm-refresh interval/stability mechanism, IP→state geo
  provider (a new processor), and order-record datastore (Stripe-native vs
  app-side). These need answers before MT-8/MT-13/MT-14 finalize.
