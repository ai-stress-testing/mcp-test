run-id: 2026-07-19-regional-pricing-pipeline
prompt: "A/B-testable sales pipeline that finds optimal price per region from
  per-state baselines; privacy-protecting; use the Ges-Talt agents."
agents:
  - pm/project-manager (opus) — PRD §1–6, issue spec, backlog rows
  - security/architect (opus) — consult: cut device/sub-state pricing
  - legal/general-counsel (opus) — consult: disparate-impact + surveillance-pricing risk
  - backend/backend-dev (sonnet) — MT-1 engine implementation
  - logicians/code-reviewer (opus) — MT-6 static review (running)
  - academic/statistician (opus) — MT-7 A/B-validity gate (running)
specs: docs/sprint-7-26-19-26/prd.md §1–6; issue-specs/pricing-pipeline.md
verdicts: MT-1 self-test PASS; MT-6/MT-7 in flight
commits: (this commit)

# 2026-07-19 — Regional price-optimization pipeline: spec + engine landed

**Session/agent**: orchestrator (main) running the Ges-Talt spec-driven flow.
**Issues touched**: MT-1 (done), MT-2..MT-5 (todo), MT-6/MT-7 (in-progress).

## Done
- PRD written for sprint-7-26-19-26 (§1–6) and 7 backlog rows cut (MT-1..MT-7).
- Issue spec `pricing-pipeline.md` with 5 build sub-issues + real assignees,
  acceptance criteria, negative prompts, dependency order.
- MT-1 engine (`pipeline/pricing_engine.py`) implemented and self-test PASS:
  per-state Thompson-sampling revenue bandit converged CA→$65.93, ME→$48.22,
  NM→$43.30 from published PPP baselines; device-independence demonstrated.
- MT-6/MT-7 review agents (code-reviewer, statistician) dispatched against the
  committed engine.

## Decisions
- **Device-based and sub-state (ZIP/geo) pricing are cut** — not deferred.
  Security + legal consult at spec time flagged the surveillance-pricing
  pattern (FTC 6(b) scrutiny) and location-as-wealth-proxy disparate-impact
  exposure (ProPublica / Princeton Review precedent). Pricing granularity is
  capped at U.S. state, enforced in code (`ALLOWED_PRICING_INPUTS`), not just
  documented. Not to be re-litigated.
- Optimization objective is **expected revenue** (price × conversion), not
  conversion alone — otherwise the bandit races to the price floor.
- Tracking lives in **mcp-test** (the convention-adopting repo); Ges-Talt
  remains the source of the agents + convention, not a host for this product.

## Blocked / carried
- MT-2 (checkout page) is gated on MT-5 (disclosure copy) before any paid
  go-live, per the dependency order.
- Fold MT-6/MT-7 verdicts into this entry + issue spec when they return; a
  FAIL hands back to `backend/backend-dev` per the verdict loop.
