# Backlog

Rows are added by the spec-driven PM (`agents/pm/project-manager`); one row
per issue. Status: todo / in-progress / blocked / done.

| ID | Item | Assignee (agent) | Sprint | Status | Issue |
|---|---|---|---|---|---|
| MT-1 | Regional price-optimization engine (per-state bandit) | `backend/backend-dev` | sprint-7-26-19-26 | fixed-v2 (re-review pending) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#1-pricing-optimization-engine) |
| MT-2 | Landing + checkout page (own domain) | `frontend/designer` | sprint-7-26-19-26 | in-progress (decomposed → MT-8..MT-12) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-3 | Payments + idempotent webhook (Stripe Checkout) | `backend/payments-billing-engineer` | sprint-7-26-19-26 | in-progress (decomposed → MT-13..MT-17) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-4 | Analytics + experiment readout | `pm/experiment-tracker` | sprint-7-26-19-26 | todo | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#4-analytics--experiment-readout) |
| MT-5 | Privacy notice + regional-pricing disclosure | `legal/product-counsel` | sprint-7-26-19-26 | todo (blocks MT-2 go-live) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#5-privacy-notice--regional-pricing-disclosure) |
| MT-6 | Static review of MT-1 engine | `logicians/code-reviewer` | sprint-7-26-19-26 | FAIL → handed back, v2 pending re-review | [verdicts](sprint-7-26-19-26/reviews/mt1-review-verdicts.md) |
| MT-7 | Statistical-validity gate on the bandit / A-B design | `academic/statistician` | sprint-7-26-19-26 | FAIL → handed back, v2 pending re-review | [verdicts](sprint-7-26-19-26/reviews/mt1-review-verdicts.md) |
| MT-8 | Page↔engine assignment-flow architecture (ADR) | `logicians/software-architect` | sprint-7-26-19-26 | done → [ADR-0001](sprint-7-26-19-26/adr/ADR-0001-pricing-topology.md) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-9 | Offer/checkout page design spec | `frontend/designer` | sprint-7-26-19-26 | done → [design-spec](sprint-7-26-19-26/design-specs/checkout-offer-page.md) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-10 | Landing + checkout page implementation | `frontend/react-dev` | sprint-7-26-19-26 | blocked (MT-8,MT-9,MT-5) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-11 | Accessibility audit of built page | `testing/accessibility-auditor` | sprint-7-26-19-26 | blocked (MT-10) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-12 | Visual evidence: price + disclosure | `testing/evidence-collector` | sprint-7-26-19-26 | blocked (MT-10) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-13 | Stripe hosted Checkout session + handoff | `backend/payments-billing-engineer` | sprint-7-26-19-26 | blocked (MT-8) — F1/F2 controls required | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-14 | Idempotent webhook + order record | `backend/payments-billing-engineer` | sprint-7-26-19-26 | blocked (MT-13) — F6 controls required | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-15 | Idempotency/exactly-once static review | `logicians/distributed-systems-verifier` | sprint-7-26-19-26 | blocked (MT-14) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-16 | PCI-scope confirmation | `security/regulated-data-specialist` | sprint-7-26-19-26 | blocked (MT-13) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-17 | Duplicate-webhook empirical replay | `testing/api-tester` | sprint-7-26-19-26 | blocked (MT-14) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-18 | OPSEC gate: F1/F2/F4/F6 blockers before go-live | `security/appsec-engineer` | sprint-7-26-19-26 | todo (go-live blocker) | [opsec-gate](sprint-7-26-19-26/opsec-gate.md) |
| MT-19 | Operator-identity two-plane register (F9, PRD §6) | `legal/general-counsel` | sprint-7-26-19-26 | todo | [opsec-gate](sprint-7-26-19-26/opsec-gate.md) |
