# OPSEC gate — regional-pricing pipeline

Per `ORCHESTRATION.md` ("every major output passes through OPSEC") and
`docs/opsec/README.md` (the gate): the `security/architect` threat model is
funneled through the MITRE-tactic checklists it flagged. Each row ties a
threat-model finding to the OPSEC technique + control + owner + phase, and a
**gate status**. OPSEC is a design-time gate here (proximity edge #1) — the
pipeline is a thin public endpoint + Stripe + a datastore, so only the tactics
with a real surface are run; listing the rest would be unjustified defense
depth (itself attack surface).

**Gate verdict: FAIL for go-live.** Blockers **F1, F2, F4, F6** must close
before any paid page ships. **F3 cleared** in engine v2 (epoch-frozen arm).
The rest are OPEN with named owners — a control with no owner is not a control.

| Finding | Tactic | Technique (ID) | OPSEC control (checklist) | Owner | Phase | Gate |
|---|---|---|---|---|---|---|
| **F1** client-supplied `state_code` is authoritative → state-spoof to cheapest tier | 03 Initial Access | public-app input abuse | Strict input validation at the trust boundary; derive state server-side from trusted IP geo, treat client value as non-authoritative hint; WAF/rate-limit | `security/appsec-engineer` + `backend/backend-dev` | prevent | **BLOCK** |
| **F2** no crypto binding of shown price to charge → client edits amount | 03 Initial Access / 15 Impact | T1565 Data Manipulation (Financial Theft) | Server-authoritative assignment store; Checkout amount from store not client; webhook asserts `amount_total == stored`; transaction limits | `backend/payments-billing-engineer` | prevent | **BLOCK** |
| F3 per-request resampling → refresh-shopping / non-uniform price | 15 Impact | T1565 Data Manipulation | Epoch-frozen arm per (region, epoch) | `backend/backend-dev` | prevent | **CLEARED (v2)** |
| **F4** bandit outcome feed steerable → poison published price to floor/ceiling | 15 Impact | T1565 Data Manipulation | Only signature-verified `checkout.session.completed` may set `converted=True`; FIM/hashing on posteriors; anomaly monitor on per-arm inflow (rate, IP diversity) | `security/threat-detection-engineer` + `pm/experiment-tracker` | detect | **BLOCK** |
| **F6** unsigned/replayed webhook → fake orders + bandit poison | 09 Credential Access | T1606 Forge Web Credentials | Verify `Stripe-Signature` + timestamp tolerance (~5 min); dedupe on `event.id`; reject unsigned/expired | `backend/payments-billing-engineer` + `security/appsec-engineer` | prevent | **BLOCK** |
| F5 Stripe secret / signing secret handling | 09 Credential Access | T1552 Unsecured Credentials | No secrets in repo/JS; secret manager/env; restricted Stripe key; CI secret-scanning | `devops/gitops-engineer` + `security/appsec-engineer` | prevent | OPEN |
| F5 stolen app token | 09 Credential Access | T1528 Steal Application Access Token | Token binding; short lifetimes; monitor unusual token usage | `security/appsec-engineer` | prevent | OPEN |
| F8 PII aggregation (IP/geo/device/analytics) | 12 Collection | T1213 / T1530 Data from Repositories/Cloud | Access controls + DLP; discard raw IP after state-derivation; separate analytics store from order/PII store | `legal/privacy-engineer` | prevent | OPEN |
| F8 PII egress | 14 Exfiltration | T1567 Exfil over Web Service / T1020 Automated | Allowlist approved services; monitor bulk outbound; enforce retention deletion | `legal/privacy-engineer` | detect | OPEN |
| F7 VPN/geo arbitrage → data pollution | 12 Collection | T1213 (learning-set integrity) | Serve proxied/foreign traffic but exclude it from the bandit learning set (tag non-US/known-proxy IP) | `backend/backend-dev` | prevent | OPEN |
| F9 operator-identity OSINT leak | 01 Recon / 02 Resource Dev | operator OSINT | Brand-only statement descriptor / WHOIS / email headers; two-plane identity register; truthful KYC | `pm/project-manager` + `legal/general-counsel` | prevent | OPEN |
| F11 endpoint DoS / KYC-freeze availability | 15 Impact | Endpoint Denial of Service | Auto-scaling + rate limiting + WAF on `/assign` and `/webhook`; pre-clear KYC | `devops/sre` + `networking/network-engineer` | prevent | OPEN |

## Tactics deliberately out of scope (state-and-move-on)

04 Execution · 05 Persistence · 06 Privilege Escalation · 07 Defense Evasion ·
08 Defense Impairment · 10 Discovery · 11 Lateral Movement · 13 Command &
Control. All presuppose a compromised host or internal network; this pipeline
has no such surface until real server infrastructure exists. Revisit then.

## Gate outcome

- **Do not ship a paid page** until F1, F2, F4, F6 close (design-level, owned
  by the MT-3 / MT-8 implementers) and are re-verified.
- F5/F7/F8/F9/F11 are OPEN with owners and must be tracked to closure but do
  not individually block the first live test if F1/F2/F4/F6 are shut.
- Detection controls (F4 anomaly monitor, F8 egress monitor) hand to
  `security/threat-detection-engineer` once serving infra exists.
