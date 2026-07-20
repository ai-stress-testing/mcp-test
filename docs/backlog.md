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
| MT-10 | Landing + checkout page implementation | `frontend/react-dev` | sprint-7-26-19-26 | done (`pipeline/web/`, 28/28 Playwright + 0 axe; blocked go-live on MT-5 copy) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-11 | Accessibility audit of built page | `testing/accessibility-auditor` | sprint-7-26-19-26 | blocked (MT-10) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-12 | Visual evidence: price + disclosure | `testing/evidence-collector` | sprint-7-26-19-26 | blocked (MT-10) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#2-landing--checkout-page-own-domain) |
| MT-13 | Stripe hosted Checkout session + handoff | `backend/backend-dev` | sprint-7-26-19-26 | done (`pipeline/app/`, F1+F2 verified on PG) — needs `security` re-verify (MT-16) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-14 | Idempotent webhook + order record | `backend/backend-dev` | sprint-7-26-19-26 | done (`pipeline/app/`, F6 verified: dup→1 order, bad-sig rejected) — needs MT-15 review | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-15 | Idempotency/exactly-once static review | `logicians/distributed-systems-verifier` | sprint-7-26-19-26 | blocked (MT-14) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-16 | PCI-scope confirmation | `security/regulated-data-specialist` | sprint-7-26-19-26 | blocked (MT-13) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-17 | Duplicate-webhook empirical replay | `testing/api-tester` | sprint-7-26-19-26 | blocked (MT-14) | [spec](sprint-7-26-19-26/issue-specs/pricing-pipeline.md#3-payments--webhook) |
| MT-18 | OPSEC gate: F1/F2/F4/F6 blockers before go-live | `security/appsec-engineer` | sprint-7-26-19-26 | todo (go-live blocker) | [opsec-gate](sprint-7-26-19-26/opsec-gate.md) |
| MT-19 | Operator-identity two-plane register (F9, PRD §6) | `legal/general-counsel` | sprint-7-26-19-26 | todo | [opsec-gate](sprint-7-26-19-26/opsec-gate.md) |
| MT-20 | Store & serving topology on Supabase (ADR) | `logicians/software-architect` | sprint-7-26-19-26 | done → [ADR-0002](sprint-7-26-19-26/adr/ADR-0002-supabase-store-environments.md) | [prd §7](sprint-7-26-19-26/prd.md) |
| MT-21 | Test/prod environments (self-hosted Supabase on Docker) | `devops/containerization-engineer` | sprint-7-26-19-26 | done (`environments/`, compose-config verified) | [prd §7](sprint-7-26-19-26/prd.md) |
| MT-22 | Postgres schema + reversible migrations + RLS | `backend/backend-dev` | sprint-7-26-19-26 | done (`pipeline/db/`, up+down verified on PG16) | [prd §4,§7](sprint-7-26-19-26/prd.md) |
| MT-23 | App service (`/assign`,`/create-checkout`,`/webhook`) + learner | `backend/backend-dev` | sprint-7-26-19-26 | done (`pipeline/app/`, 10/10 e2e on PG) | [prd §1,§4,§8](sprint-7-26-19-26/prd.md) |
| MT-24 | Containerize app + wire into compose; fix build-context seam | `devops/containerization-engineer` | sprint-7-26-19-26 | done (orchestrator closed engine/web build-context; image-layout boot verified) | [adr §3](sprint-7-26-19-26/adr/ADR-0002-supabase-store-environments.md) |
| MT-25 | Product brief — define the offer behind the pipeline | `pm/project-manager` | sprint-7-26-19-26 | done → [product-brief](sprint-7-26-19-26/product-brief.md) | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-26 | Brand guide + funnel copy (real content) | `design/brand-guardian` | sprint-7-26-19-26 | done → [brand-guide](sprint-7-26-19-26/content/brand-guide.md), [funnel-copy](sprint-7-26-19-26/content/funnel-copy.md) | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-27 | Landing funnel + owner-dashboard design spec + mockup | `frontend/designer` | sprint-7-26-19-26 | spec done → [design-spec](sprint-7-26-19-26/design-specs/landing-funnel-and-dashboard.md); mockup interrupted (re-do pending) | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-28 | Conversion-psychology + measurement spec | `academic/psychologist` | sprint-7-26-19-26 | done → [psych-spec](sprint-7-26-19-26/content/conversion-psychology-spec.md) | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-29 | Analytics + heatmap capture + owner-only auth/reads | `backend/backend-dev` | sprint-7-26-19-26 | done (`pipeline/app/`, `pipeline/db/migrations/0006`, 6/6 migrations + 10/10 pre-existing + new endpoint checks verified on PG16) — needs `security/senior-secops` review of owner-auth | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-30 | Build the conversion landing funnel | `frontend/react-dev` | sprint-7-26-19-26 | done (`pipeline/web/`, 0 axe light+dark, section order per psych spec, /track wired) | [brief](sprint-7-26-19-26/product-brief.md) |
| MT-31 | Build the owner analytics dashboard UI | `frontend/react-dev` | sprint-7-26-19-26 | blocked (MT-27,MT-29) | [brief](sprint-7-26-19-26/product-brief.md) |
