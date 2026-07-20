# Conversion-psychology + measurement spec

**Author**: `academic/psychologist` (read-only; mechanism-naming, no UI/copy). **For**: the full funnel (MT-30) + owner analytics (MT-29/MT-31).

Governing fact: the buyer pays **a stranger, online, once, upfront**, for fulfillment that happens **after** payment, with **no brand to borrow trust from** (identity shielded, PRD §6). Every trust signal must be earned in-page; none can be borrowed.

## 1. Persuasion architecture (ABI trust model, serial resolution)

A first-time buyer can't resolve ability/benevolence/integrity simultaneously — that exceeds working memory (~4 chunks) and shows up as silent bounce, not a legible objection. Resolve one dominant question per section:

| Section | Mechanism it discharges |
|---|---|
| **Hero** | Relevance filter (System-1, <1s). No trust copy here — it adds load before the visitor has decided the page is about them. |
| **Problem, felt** | Schema activation — recognize an existing pain (lead follow-up, invoice chasing, content repurposing), don't manufacture one. |
| **Offer** | Close the gap schema→product: picture the *specific* deliverable (one automation, delivered — not a course/template/subscription). |
| **How it works (3 steps)** | **Ability** — concreteness is the only evidence a stranger can execute (no case-study history to lean on). Genuinely hard to explain; don't over-simplify (integrity debt paid at fulfillment). |
| **Proof/trust** | **Benevolence + Integrity** — evaluated by the ELM *central route*: substantive checkable claims, not badges/star-cues a skeptic discounts. Anonymity removes peripheral cues, so substance must carry it. |
| **Objection FAQ** | Resolve *residual* doubts after proof — placed after, not before, so it doesn't introduce new doubts early. |
| **CTA / price** | Only here — price is judged against accumulated risk assessment; showing it earlier forces "is it worth it?" before the info to answer exists → reflexive no. |
| **Checkout handoff** | One further action; Stripe's familiar UI is itself a real trust signal. |

Stated as a hypothesis, not validated truth — §5's instrumentation checks whether real drop-off matches this ordering; contradicting data revises the sequence.

## 2. Objection sequence (fires in this order; resolve where noted)

1 "Is this for a business like mine?" → Hero+Problem · 2 "What am I getting?" → Offer · 3 "Can a solo op actually build this?" → How-it-works · 4 "Will it work with *my* tools?" → FAQ (honest scope disclosure) · 5 "Is paying a stranger safe?" → Proof + Stripe handoff · 6 "Refund if it fails?" → **needs a real policy, not reassurance copy (operator/PM call)** · 7 "How long?" → explicit SLA (a swap-point still unset) · 8 "Why does price differ by region?" → inline disclosure between price and CTA (must resolve without a click, or it poisons the page) · 9 "Did payment go through?" → success state.

Objection #4 ethics: if the automation can't support every tool combo, **say so** — a mismatch discovered post-payment is far more damaging (and refund-inducing) than a self-selected-out non-buyer.

## 3. Cognitive-load minimization (checkout path)

Already right, keep it: single isolated decision (one CTA, no tier/add-on selector — Hick's Law); price legibility (one big tabular number, no compound math); disclosure inline in reading order (gated-behind-a-click info is systematically underweighted); skeleton over shimmer (avoids layout-jump re-orientation, reduced-motion-gated).
**As the funnel grows, do NOT** add a second/sticky "buy now" CTA above the fold — a second decision point reached before ABI is addressed pulls impulsive clicks that reverse (cancel-and-return), which is worse when fulfillment is manual per-sale labor. A "jump to pricing" affordance should be a plain anchor, not a second payment button.

## 4. Ethical line — persuasion vs. manipulation (all OUT)

False scarcity/countdowns (forces System-1 before ABI evaluation completes) · confirm-shaming (poisons future reconsideration) · drip-priced surprises (attacks Integrity, the hardest ABI dim to repair; also barred by PRD §5) · fake/struck-through anchor pricing (fabricated reference — no real prior price exists) · fabricated/vague social proof (ELM central-route buyers discount or catch it).

**Why honesty is the durable choice *here specifically***: (1) no brand to absorb a spotted dark pattern — a detected trick raises fraud-suspicion priors across the *entire* remaining page; the page's only trust capital is its real-time honesty. (2) The relationship continues after payment (intake + days of manual delivery) — a manipulated buyer arrives primed to regret, churn intake, or dispute; an honestly-converted buyer is worth more than an extra manipulated one when labor is the cost center.

## 5. Measurement (privacy-safe: anon session id only, no PII/IP/keystrokes/replay)

**Capture**: scroll-depth at each section boundary (% reaching each); dwell per section (ambiguous alone — see below); clicks on *non-interactive* elements (false-affordance signal — e.g. tapping the price hoping for a breakdown); **CTA reached-but-not-clicked** (isolates "saw the ask and declined" from "never got there"); the 3-stage funnel (load → price shown → checkout clicked → Stripe done), each gap a different diagnosis; rage-clicks on the disabled (loading) CTA (a latency UX issue, not unwillingness).

**Read without over-claiming**:
- Hold funnel/heatmap conclusions to the **same minimum-sample discipline** the pricing engine uses for declaring an arm winner.
- **Region and price arm are confounders** — segment by arm before comparing, never pool (a content problem and price-sensitivity look identical pooled).
- **Device class** is a structural confounder (scroll behavior differs for viewport reasons).
- **Returning-in-session visitors** (Stripe-cancel returners reuse `sessionStorage`, re-enter mid-funnel) are a different population — don't pool with fresh loads.
- **Correlation≠causation**: a scroll-stall is equally consistent with friction, satisfaction-then-leave, or interruption — require **convergent** signals (stall + back-nav + low CTA-reach together) before treating a section as a confirmed problem.
- **Dwell is fundamentally ambiguous** (engaged reading vs confused re-reading); privacy-safe capture *cannot* disambiguate it — resolve with a few moderated user-research sessions, not a confident heatmap read.
- Segment by date/arm-state (day-of-week effects; convergence-phase non-comparability).

Bottom line: every funnel-section conclusion is a hypothesis until it replicates across independent sessions, >1 traffic day, and ideally >1 price arm — the same posture this repo applies to the pricing experiment itself.
