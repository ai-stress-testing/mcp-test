# MT-1 engine — review verdicts & v2 resolution

Two Ges-Talt gates reviewed `pipeline/pricing_engine.py` v1. Both returned
**FAIL**; MT-1 handed back to `backend/backend-dev`; v2 addresses every
blocker. Re-review of v2 is pending (status: fixed, not yet re-verified).

## `logicians/code-reviewer` (opus) — VERDICT: FAIL → resolved in v2

| # | Blocker (v1) | v2 fix |
|---|---|---|
| B1 | `ALLOWED_PRICING_INPUTS` whitelisted the KEY not the VALUE — a ZIP/city string as `state_code` minted its own arm set = sub-state pricing | `canonical_region()` validates the value against `US_STATES`; anything else → shared `__default__`. Self-test asserts ZIP `"90210"` collapses to default. |
| B2 | fresh Thompson sample per request → two same-region users see different prices at once | one CURRENT arm per region per epoch; all region visitors in an epoch see it. Self-test asserts device/2-call price equality within an epoch. |
| B3 | in-process dict, non-atomic `alpha += 1` — multi-worker diverges | lock makes single-process updates atomic; state isolated behind `_lock` for a shared-store swap. Multi-worker topology = ADR-0001 (split serving/learning, one cron learner). |

Also flagged (fixed): `steps>=2` guard, dedupe clamped arms, `record_outcome`
returns False on no-match (no silent drop), `None` signals guard, state-case
normalization.

## `academic/statistician` (opus) — VERDICT: FAIL → resolved in v2

| Blocker (v1) | v2 fix |
|---|---|
| `best_price` reported a winner on n=0 (0.5 prior mean) | min-conversion gate (`MIN_CONVERSIONS=50`) + revenue CI; `decisive=False` until met |
| no effect size / interval; no tie rule | `revenue_ci()`; on overlapping CIs → **tie, default to the LOWER price** (fairness-aligned) |
| self-test circular (true optimum = grid center) & couldn't fail | ground truth decoupled; **continuous** true-optimum sweep; off-grid case must trip `at_boundary()`; hard assertions → non-zero exit |
| wrong randomization unit (per-impression, pseudo-replication) | region-epoch assignment; ADR event schema analyzes at `DISTINCT visitor_id` |
| no non-stationarity handling | optional `decay` discounts stale counts; baseline retained as control arm |
| early exploration over-charged (flat prior) | forced round-robin until every arm explored, then Thompson |

Bandit math itself was confirmed **sound** by both reviewers (revenue-objective
Thompson sampling is valid; price never enters the posterior).

## v2 status

`python3 pipeline/pricing_engine.py` → **PASS** (exit 0), and now genuinely
fails on regression. Re-review by both gates is the next verdict-loop step
before MT-1 closes.
