# Issue: A/B-testable regional price-optimization pipeline

**Sprint**: sprint-7-26-19-26 · **Source**: user goal — "A/B testable sales
pipeline that finds optimal pricing per region, starting from per-state
baselines and algorithmically finding the middle ground."
**Assignee (parent)**: `agents/pm/project-manager`
**Goal**: let a solo operator sell a productized service from their own
domain at a price that is optimized per U.S. state via online experimentation,
without incurring the legal exposure of surveillance/device pricing.

## Consultation record (proximity order, per ORCHESTRATION.md)

Constraints entered at spec time, not after. Quoted verdicts:

- `security/architect` (opus) — threat/abuse model: **"Per-person price
  extraction keyed to device or sub-state location is the surveillance-pricing
  pattern under active FTC 6(b) scrutiny. Cut it. Price on state granularity
  only, identical price per region per interval, shown openly."** → **FAIL** on
  any device/ZIP pricing input; **PASS** on transparent state-tier + A/B.
- `legal/general-counsel` (opus) — **"Location-as-wealth-proxy carries
  disparate-impact exposure (ProPublica / Princeton Review ZIP precedent).
  State-level PPP tiers applied uniformly, framed as affordability, are
  defensible. Device-based surcharge is not — it's the Orbitz cautionary
  tale."** → risk register owner assigned.
- `legal/data-protection-officer` (sonnet) — **"Coarse IP→state geolocation
  and a device_class flag are personal data. Need a privacy notice, a lawful
  basis, retention limit, and the device flag structurally barred from
  pricing."**
- `academic/statistician` (opus) — **"A revenue-objective Thompson-sampling
  bandit is sound for this; guard the floor/ceiling and log per-arm trials so
  significance is auditable. Don't switch winners before minimum-sample."**

## Spec

What must be true when this issue closes — falsifiable:

1. Price shown to a visitor is a pure function of `{state_code}` plus the
   region's current bandit arm. Given the same state and RNG state, the price
   is identical regardless of device, browser, OS, or IP beyond state.
2. No pricing input is finer-grained than U.S. state. ZIP, city, lat/long,
   and device are never read by the pricing path (enforced in code:
   `ALLOWED_PRICING_INPUTS == {"state_code"}`).
3. Every price stays within `[PRICE_FLOOR, PRICE_CEIL]`.
4. Each region's price converges toward its revenue-maximizing candidate as
   outcomes accumulate (demonstrated by `pricing_engine.py` self-test).
5. A public privacy notice discloses IP→state geolocation and analytics; the
   pricing page states that price varies by region.
6. Payment capture is idempotent and PCI scope is minimized (hosted Stripe
   Checkout — no raw card data touches the app).

## Sub-issues

### 1. Pricing-optimization engine
- **Assignee**: `agents/backend/backend-dev` (design reviewed by
  `agents/logicians/software-architect`)
- **Scope**: the region-tier + Thompson-sampling revenue bandit.
- **Acceptance criteria**:
  - [x] `pricing_engine.py` converges each of ≥3 test states to within one
        price step of the true revenue optimum (self-test prints PASS).
  - [x] Device class is captured but structurally excluded from pricing.
  - [x] Prices bounded by floor/ceiling; unknown state → national baseline,
        never a penalty.
- **Negative prompt (do NOT)**: read device/ZIP/lat-long for pricing; let the
  bandit exceed bounds; charge two same-region visitors different prices at the
  same instant.
- **Verify**: `python3 pricing_engine.py` → prints PASS. ✅ done (this commit).

### 2. Landing + checkout page (own domain)
- **Assignee**: `agents/frontend/designer` (build) + `agents/frontend/react-dev`
- **Scope**: one-page offer + Stripe Checkout handoff; renders the assigned
  region price and a visible "prices vary by region" line.
- **Acceptance criteria**:
  - [ ] Page calls the engine, renders one price, logs the assignment event.
  - [ ] Regional-pricing disclosure visible before payment.
  - [ ] Accessible (labels, focus, contrast) — `testing/accessibility-auditor`.
- **Negative prompt**: no dark-pattern countdowns; no collecting card data
  directly; no per-visitor price flicker on reload within a session.
- **Verify**: `evidence-collector` screenshots price + disclosure on the built page.

### 3. Payments + webhook
- **Assignee**: `agents/backend/payments-billing-engineer`
- **Scope**: Stripe hosted Checkout, idempotent `checkout.session.completed`
  webhook, order record keyed to the assignment's `variant_id`.
- **Acceptance criteria**:
  - [ ] Duplicate webhook delivery creates exactly one order (idempotency key).
  - [ ] Recorded sale price == price the engine assigned for that session.
- **Negative prompt**: no card PAN stored; no price recomputed server-side that
  could differ from what the buyer saw.
- **Verify**: `api-tester` replays a duplicate webhook; one order results.

### 4. Analytics + experiment readout
- **Assignee**: `agents/pm/experiment-tracker` (validity gate:
  `agents/academic/statistician`)
- **Scope**: per-arm trials/conversions/revenue table + go/no-go on price moves.
- **Acceptance criteria**:
  - [ ] Dashboard shows per-state per-arm trials, conversion, exp. revenue.
  - [ ] No winner declared below the configured minimum sample.
- **Negative prompt**: no PII in analytics rows; device_class present but
  flagged non-pricing.
- **Verify**: statistician confirms the significance guard fires on thin data.

### 5. Privacy notice + regional-pricing disclosure
- **Assignee**: `agents/legal/product-counsel` (privacy verify:
  `agents/legal/privacy-engineer`)
- **Scope**: privacy policy (geolocation + analytics + retention) and the
  on-page regional-pricing statement.
- **Acceptance criteria**:
  - [ ] Notice names IP→state geolocation, analytics, retention window.
  - [ ] `privacy-engineer` traces device_class and confirms no pricing use
        (file:line evidence).
- **Verify**: privacy-engineer report shows device_class → analytics only.

## Dependencies

`#1 blocks #2` · `#1 blocks #3` · `#2 blocks #4` · `#5 blocks #2`
(disclosure must exist before the paid page goes live).
