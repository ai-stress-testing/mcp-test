# Security threat model — regional-pricing pipeline

**Author**: `security/architect` (opus, read-only, design-time gate) · **Posture: CONDITIONAL FAIL** — F1 & F2 (Critical) block go-live. Full OPSEC-tactic mapping in `../opsec-gate.md`.

## Trust boundaries

Untrusted browser → pricing endpoint (all of `signals` is attacker-controlled) →
IP→state geo (must be server-derived). Assignment (`session_id → variant_id,
price`) must be **server-authoritative**, never round-tripped through the client
unbound. Card data never touches the app (Stripe hosted Checkout — keep it).
Webhook URL is public; nothing trusted until the signature verifies, and only
verified events may move money or steer the bandit. Operator identity: truthful
to the rail (KYC), brand-only to the public.

## Findings

| ID | Sev | Finding | Boring control | Owner |
|---|---|---|---|---|
| F1 | CRIT | `state_code` client-supplied & authoritative → spoof a cheap state, no VPN | derive state server-side from trusted IP; reject/hint-only client value | appsec + backend-dev |
| F2 | CRIT | no crypto binding of shown price to charge → client edits amount | server-side assignment store; Checkout amount from store; webhook asserts `amount_total == stored` | payments-billing-engineer |
| F3 | HIGH | per-request Thompson sampling breaks "same price per region", enables refresh-shopping | **FIXED in engine v2** — epoch-frozen arm | backend-dev |
| F4 | HIGH | bandit outcome feed steerable → poison published price to floor/ceiling | only signature-verified webhook sets `converted`; anomaly monitor on inflow | payments + threat-detection |
| F5 | HIGH | Stripe secret / signing-secret handling | secrets in manager/env not repo/JS; restricted key; CI secret-scan | appsec + gitops |
| F6 | HIGH | webhook signature/replay/idempotency | verify signature + timestamp tolerance; dedupe on `event.id` | payments + appsec |
| F7 | MED | VPN/geo arbitrage → data pollution | serve proxied traffic but exclude from learning set | pm (accept/doc) + backend-dev |
| F8 | MED | PII collection/retention/re-identification (IP+geo+device+analytics) | discard raw IP post-derivation; separate analytics from order store; enforce retention | privacy-engineer + DPO |
| F9 | MED | operator-identity leak (statement descriptor, WHOIS, controller contact) vs rail KYC | brand-only descriptor/contact; KYC truthful & early; two-plane identity register | pm + legal |
| F10 | LOW | float→cents drift fails the F2 amount check | canonicalize arms to integer cents | appsec |
| F11 | LOW→MED | public endpoint has no rate limit → bandit-poison + DoS; KYC-freeze | rate-limit `/assign` & `/webhook`; pre-clear KYC | networking + senior-secops |

## Gate

Do not ship a paid page until **F1 and F2 close and F3's epoch-freeze is
verified** (v2 addresses F3; re-review pending). F4/F6 close before real money
flows.
