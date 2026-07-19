# PRD — sprint-7-26-19-26

**User goal**: a privacy-conscious solo operator wants a sales pipeline for a
productized tech service that A/B-tests price to find the revenue-optimal
point per U.S. state — "start with per-state baselines and algorithmically
find the middle ground" — sold from their own domain.
**Out of scope**: per-person / device-based pricing, sub-state (ZIP/city/geo)
pricing, and any covert individualized willingness-to-pay extraction — cut at
spec time by the security + legal consult (see issue spec). Also out of scope
this sprint: multi-currency / non-US regions.

## Requirements

Numbered, so issues can cite `prd.md §n`.

1. Price shown is a pure function of `{state_code}` + the region's current
   experiment arm — identical for all visitors in a state at a given time,
   regardless of device, browser, OS, or finer-grained location. `state_code`
   is **server-derived from the connecting IP**, never trusted from the client
   (threat-model F1).
7. Two environments with byte-for-byte image parity: a **test** environment on
   self-hosted Supabase (Docker) and a **production** environment on a managed
   Supabase (or equivalent Postgres). Config comes from the environment, not a
   rebuild; no secrets in the repo or images.
8. The assigned price is **server-authoritative** and bound to the charge: the
   Checkout amount is read from the store, not the client, and the webhook
   asserts it matches before fulfilling (threat-model F2).
2. Pricing inputs are capped at U.S. state granularity; device is captured for
   UX/conversion analytics only and is structurally barred from the price path.
3. Each region converges toward its revenue-maximizing candidate price via
   online experimentation, within published floor/ceiling bounds.
4. Checkout uses a hosted payment page (Stripe Checkout) — no raw card data
   touches the app; sale is recorded idempotently against the assigned variant.
5. A public privacy notice discloses IP→state geolocation + analytics +
   retention; the offer page states that price varies by region.
6. Operator identity is shielded from the public (brand name, WHOIS privacy,
   registered-agent/anonymous LLC, virtual mailbox) while remaining compliant
   with platform KYC and tax obligations.

## Constraints

- Infra: domain + Stripe + **Supabase (Postgres)**. Test = self-hosted
  Supabase on Docker (free); prod = managed Supabase or equivalent. (Supersedes
  the earlier "domain + Stripe only" — see ADR-0002.)
- Transparent-by-construction: no dark patterns, no hidden surcharges.
- Same image promotes test → prod; environment supplies config; no secrets
  committed.
- Must pass the Ges-Talt verdict loop (static review + statistical validity +
  reality-check) and the OPSEC gate (F1/F2/F4/F6 closed) before any paid page
  goes live.

## Success criteria

- [x] Pricing engine converges each of ≥3 test states to its revenue optimum
      and proves device-independence (`pipeline/pricing_engine.py` self-test).
- [ ] Live checkout on own domain renders the regional price + disclosure.
- [ ] Duplicate payment webhook yields exactly one order at the shown price.
- [ ] Experiment dashboard withholds a "winner" below minimum sample.
- [ ] Privacy notice + regional-pricing disclosure published before go-live.
