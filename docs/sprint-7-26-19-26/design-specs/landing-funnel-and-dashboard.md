# Design spec — conversion landing funnel + owner analytics dashboard

**Agent**: `agents/frontend/designer` · **Sprint**: sprint-7-26-19-26
**Elevates**: `pipeline/web/` (the shipped MT-10 offer/checkout card) into the
full funnel described in `product-brief.md` §"Vertical scope" item 1. Adds the
owner-only dashboard described in item 2 (maps to backlog `MT-4`, currently
`todo`, assignee `pm/experiment-tracker`; this spec is the layout/interaction
brief that build hands off against — flagged to PM in §7, no dashboard build
sub-issue exists yet).
**Reads honored**: `product-brief.md` (offer, buyer, promise, vertical scope,
hard constraints); `pipeline/web/index.html` + `styles.css` (current single
price card); `checkout-offer-page.md` (prior spec + token table — this spec
**extends** that table, does not replace it); `prd.md` §5,§6; `opsec-gate.md`
F8 (PII aggregation — bears directly on the heatmap design, §6).
**Reuse check**: one prior page exists (`pipeline/web/`). Its token set
(`--bg/--surface/--ink/--ink-muted/--border/--accent/--accent-ink/
--disclosure-bg/--focus-ring`), its card component, its state-machine pattern,
and its "single decision, no dark patterns" posture are reused wholesale
below — every new token is additive, marked `[NEW]` in §1, and justified by a
job the existing eight tokens don't cover. The existing `#offer-view` card
*is* the funnel's final CTA section verbatim; nothing about it changes.

---

## 0. Constraints restated (gates, not preferences — carried from MT-9 §0 + product-brief)

1. **No dark patterns**, funnel-wide: no countdowns, no manufactured scarcity
   ("3 spots left"), no pre-checked upsells, no confirm-shaming, and —
   specific to a *funnel* rather than a bare card — **no fabricated social
   proof**. This product has not launched; it has no customers yet. A trust
   block that invents testimonials, review stars, or "1,200 businesses
   trust us" is a dark pattern (false-proof), not a design shortcut. §4
   defines what trustworthy looks like *without* invented proof.
2. **Regional-pricing disclosure stays first-class** — same placement rule as
   MT-9 §2 (between price and CTA, in reading order, never a tooltip). The
   funnel adds sections *before* the price; it does not touch this rule.
3. **Never a broken page** — same fallback contract as MT-9 §3.3, unchanged.
   The funnel's added sections are static content with no fetch dependency,
   so they cannot fail; only the price block (§4.7, reused verbatim) has
   loading/fallback states.
4. **No price flicker**, unchanged from MT-9 §5.
5. **Heatmap is aggregate, never per-person** (opsec-gate F8, product-brief
   "privacy-safe, no PII, disclosed"). §6.4 is the concrete mechanism: binned
   density over a thumbnail, never a per-session dot or replay.
6. **WCAG 2.2 AA**, both surfaces. §5 (funnel) and §8 (dashboard delta).

---

## 1. Token system — extends `checkout-offer-page.md` §1, does not fork it

Existing eight tokens (`--bg`, `--surface`, `--ink`, `--ink-muted`, `--border`,
`--accent`, `--accent-ink`, `--disclosure-bg`, `--focus-ring`) carry over
**unchanged** — same hex, same job, same both-theme contrast guarantees
already verified in MT-9 §1/§4. They are not repeated here.

New tokens, each computed and validated (`dataviz` skill's
`validate_palette.js` — commands + results below), not eyeballed:

| Token | Light | Dark | Use | Why a new token, not reuse |
|---|---|---|---|---|
| `--surface-2` `[NEW]` | `#F1EFEA` | `#23272C` | nested dashboard tiles (stat tile inside a card) | `--surface` already means "the one card on the page"; a tile-on-tile dashboard needs a second elevation step. Warm-neutral family kept (between `--bg` and `--surface` in light; one step *lighter* than `--surface` in dark, standard dark-mode elevation direction). |
| `--status-good` `[NEW]` | `#0ca30c` | `#0ca30c` | significant winner / delivered | dataviz skill's fixed status palette — same steps both themes, deliberately distinct from `--accent` teal so "the CTA color" and "a green success state" never collide as the same signal. |
| `--status-warning` `[NEW]` | `#fab219` | `#fab219` | trending / below min. sample / in progress | ditto. **Light-surface contrast is 1.79:1 — sub-3:1 by design** (skill's own documented number). Mitigation: always icon + text label, never fill-color-alone (see §7.2 status pill spec). |
| `--status-critical` `[NEW]` | `#d03b3b` | `#d03b3b` | anomaly flag (ties to opsec-gate F4's anomaly monitor) | ditto, reserved — do not reuse for ordinary "down" deltas. |
| `--heat-0…--heat-4` `[NEW]` | `#86b6ef → #5598e7 → #2a78d6 → #1c5cab → #0d366b` | `#184f95 → #2a78d6 → #5598e7 → #9ec5f4 → #cde2fb` | click-density + scroll-depth sequential ramp (§6.4, §6.5) | Deliberately **not** `--accent` (teal). Chart magnitude and brand/CTA color are different jobs (dataviz skill: "assign color by the job it does") — reusing the CTA teal for "click density" would make every heat-mapped screenshot look like a call-to-action heatmap. Sourced from the skill's validated default sequential blue rather than hand-deriving a teal ramp, which would need the same validation work for no visible gain (heatmap sits inside the *owner* dashboard, not the branded funnel, so it never needs to match the funnel's teal). |

**Dark-mode ramp is the light ramp traversed in reverse**, not a separate
palette: in light mode the surface is near-white, so "near zero" should be
the lightest step (recedes into the white thumbnail) and "max density" the
darkest (pops). In dark mode the surface is near-black, so that mapping
would invert the reading — "near zero" needs to stay dark-and-recessive
against a *dark* surface, "max" needs to go light-and-bright to pop. Same
five hexes, opposite order. Validated both ways:

```
node validate_palette.js "#86b6ef,#5598e7,#2a78d6,#1c5cab,#0d366b" \
  --mode light --surface "#FFFFFF" --ordinal
→ ALL CHECKS PASS (light-end contrast 2.11:1, monotone, single hue)

node validate_palette.js "#184f95,#2a78d6,#5598e7,#9ec5f4,#cde2fb" \
  --mode dark --surface "#1C2024" --ordinal
→ ALL CHECKS PASS (light-end contrast 2.02:1, monotone, single hue)
```
(Step 100, `#cde2fb`, was tried as the light-mode zero-point first and
**failed** the 2:1 light-end-contrast check at 1.32:1 — the ramp starts at
step 250 in light mode instead, per the skill's own documented floor. Logged
here so a future palette swap doesn't silently reintroduce that failure.)

Status colors are a **flat semantic layer**, not themed — same hex both
modes, per the skill ("Status palette — fixed, never themed"). Everywhere a
status color is used, an icon + text label carries the meaning too (§7.2),
because `--status-warning` fails plain contrast in light mode by design.

No other new tokens. Section-background rhythm (§3), the trust block, and the
FAQ all reuse `--bg` / `--surface` alternating (see §3) rather than inventing
tint tokens — deliberate: two backgrounds, alternated, is enough rhythm for a
single-column page, and it's free (zero new tokens, zero new failure modes to
re-verify contrast on).

---

## 2. Type + spacing scale (formalizes the ad hoc `clamp()` values already in `styles.css`)

The current stylesheet already uses `clamp()` at point-of-use (h1, price,
skeleton) without a named scale. Funnel adds five more heading/body sizes;
naming them now prevents six more one-off `clamp()` calls with slightly
different breakpoints.

| Token | Value | Reused from | Use |
|---|---|---|---|
| `--text-sm` | `0.875rem` | `.stripe-note`, footer nav (existing, unnamed) | captions, FAQ meta, disclosure fine print |
| `--text-base` | `1rem` | body default (existing, unnamed) | body copy, paragraph |
| `--text-lg` | `1.0625rem` | `.cta-button` (existing, unnamed) | CTA buttons, emphasized body |
| `--text-xl` | `clamp(1.25rem, 4vw, 1.5rem)` | `h1` (existing) | section headings (h2) — the checkout card's `h1` size becomes the funnel's h2 size, since the card is now one section among several, not the page's sole heading |
| `--text-2xl` | `clamp(1.75rem, 5vw, 2.25rem)` `[NEW]` | — | hero subordinate line, trust block heading |
| `--text-3xl` | `clamp(2.25rem, 6vw, 3rem)` `[NEW]` | — | hero `h1` (the page's one true h1) |
| `--price-display` | `clamp(2rem, 8vw, 2.75rem)` | `.price-value` (existing) | **left as its own scale, not folded into `--text-*`** — the price is a hero figure, not a heading; the dataviz skill's own rule ("large standalone numbers use proportional figures, not a heading scale") applies here too. |

Spacing: 4px base unit, named `--space-1` (`0.25rem`) through `--space-8`
(`2rem`) for component-internal spacing (reuses the card's existing padding
rhythm, e.g. `clamp(1.25rem, 5vw, 2.25rem)` ≈ `--space-8` already), plus two
section-level tokens:

| Token | Value | Use |
|---|---|---|
| `--space-section` `[NEW]` | `clamp(3rem, 10vw, 6rem)` | vertical padding between funnel sections (hero excluded) |
| `--space-hero` `[NEW]` | `clamp(4rem, 14vw, 8rem)` | hero top/bottom padding — the one section allowed to breathe more, since it's the page's single first impression |

---

## 3. Part (a) — conversion landing funnel (public)

### 3.1 Section order + rhythm

Exactly the order in `product-brief.md`'s vertical scope, no section added or
reordered:

```
┌─────────────────────────────────────────────┐
│ slim sticky header: wordmark (text, no logo)  │  <- --surface, --border bottom
│                              [See pricing ↓]  │     hairline, always visible
├─────────────────────────────────────────────┤
│                                                │
│              HERO            (h1, --bg)       │  --space-hero padding
│   headline · subhead · primary CTA (anchor)   │
│   micro-trust line under CTA                  │
│                                                │
├─────────────────────────────────────────────┤
│           PROBLEM            (h2, --surface)  │  --space-section padding
│   the felt cost, concrete ("3-5 hrs/week")    │
├─────────────────────────────────────────────┤
│            OFFER             (h2, --bg)       │
│   what you get, what you don't (not a sub)    │
├─────────────────────────────────────────────┤
│        HOW IT WORKS          (h2, --surface)  │
│   3 numbered steps (real sequence — see §3.5) │
├─────────────────────────────────────────────┤
│      TRUST / CREDIBILITY     (h2, --bg)       │  <- §4, the load-bearing
│   process transparency, security, no fake     │     section for a payment
│   proof (§0.1)                                │     page's "assumed as
├─────────────────────────────────────────────┤     good as it looks"
│             FAQ               (h2, --surface) │
│   objection-handling, accordion               │
├─────────────────────────────────────────────┤
│     PRICE + DISCLOSURE + CTA  (h2→"h1" slot)  │  <- verbatim reuse of
│     = the existing #offer-view card, unchanged │     pipeline/web/, §3.6
├─────────────────────────────────────────────┤
│  footer: Privacy · Terms · Contact (existing) │
└─────────────────────────────────────────────┘
```

**Alternating `--bg`/`--surface` band backgrounds** is the entire rhythm
mechanism — no new background tokens, no dividing rules needed between
sections; the color step itself is the divider. Reuses the two colors the
card already established (page ground vs. card surface) and just widens
"card surface" from a 440px card to a full-width band.

**One `<h1>`** — the hero headline. Every other section heading is an `<h2>`.
The reused checkout card's own `<h1>` (per MT-9) is downgraded to `<h2>` in
this context — flagged explicitly since MT-9 §4 hard-required exactly one
`<h1>` *for the card in isolation*; in the funnel, the card is a section, and
the hero owns the page's one `<h1>`. `react-dev`: this is a required markup
change when the card is composed into the funnel, not optional.

**No page nav beyond the sticky header's single anchor link.** This is a
funnel — every exit except "scroll further" or "go to checkout" is a leak.
The header carries a text wordmark (never a logo mark — PRD §6, operator
identity is deliberately unbranded) and exactly one link, "See pricing",
anchor-scrolling to the CTA section. No scroll-hide/reveal behavior on the
header (a header that hides on scroll risks stranding a keyboard-focused
link off-screen — simpler and safer to keep it always visible, low-height).

### 3.2 Hero

- `h1`: the core promise, close to product-brief's own wording — "Pay once.
  Get one workflow off your plate for good." (placeholder pending
  `design/brand-guardian`'s `funnel-copy.md`, see §9 seam note).
- Subhead (`--text-2xl`... no — subhead is body-weight, `--text-lg`, `--ink-
  muted`): one concrete sentence naming a time figure, e.g. "Save the 3–5
  hours a week you lose to [workflow]." — the bracket is real: the specific
  workflow examples are a swap point per product-brief, not invented here.
- Primary CTA: **not a second checkout entry point.** It's a same-page anchor
  link styled as a button (`.cta-button` token reused, `<a href="#price-
  block">`, not a `<button>` — it's real in-page navigation, so anchor
  semantics are correct here, unlike the Stripe-handoff CTA which is
  correctly a `<button>`). Only one place on the page ever shows a price —
  the reused card at the bottom — so the hero CTA cannot duplicate or
  precede that state machine (avoids a second "is this the same price?"
  question the visitor would have to resolve).
- Micro-trust line directly under the CTA, small (`--text-sm`, `--ink-
  muted`): "One-time payment · Stripe secure checkout · Price varies openly
  by region" — three plain facts, not badges/icons, front-loading the
  regional-pricing disclosure's *existence* (not its legal text) as early as
  the hero, so it's never a surprise sprung at the bottom.
- **No hero illustration using real third-party tool logos** (CRM/Slack/
  email-provider marks) without a confirmed integration partnership —
  flagged to PM/legal: implying a specific vendor relationship that doesn't
  exist is a trust *liability*, not a trust signal. If an illustration is
  wanted, use generic abstracted icon shapes (envelope, spreadsheet grid,
  chat bubble) that gesture at "your existing tools" without claiming any
  specific one.

### 3.3 Problem

Single short paragraph or 3 short bullet lines naming the felt cost in the
buyer's own words (per product-brief's buyer profile: lead follow-up, invoice
chasing, content repurposing, appointment reminders — the copy should name
2–3 of these concretely, not "your tedious workflows" abstractly). No chart,
no stat — this section's job is recognition ("that's me"), not data.

### 3.4 Offer

States plainly what is and is not being sold, mirroring product-brief's own
framing: *"A finished, working automation, delivered to you. Not a
subscription. Not a course. Not a template you have to assemble yourself."*
Three short lines is enough; this is the shortest section on the page by
design — it's disambiguating, not persuading (persuasion is the Problem and
Trust sections' job).

### 3.5 How it works (3 steps)

Only place on the page using a numbered sequence — legitimately, since this
*is* a real ordered process (per the `artifact-design` guidance: numbering
should encode something true, not decorate). Three steps, horizontal on
wide viewports / stacked on narrow, each: number badge (`--accent` fill,
`--accent-ink` text — reuses the CTA color for the one other place on the
page that represents forward motion), short label, one-sentence detail.

1. **Tell us the workflow** — short intake form (post-purchase, per
   product-brief — the step happens *after* payment, so this step's copy
   must say "after checkout" plainly, not imply the intake gates the price).
2. **We build it** — "a few business days" (swap point: exact SLA is the
   operator's to set, per product-brief).
3. **It runs** — time back, framed concretely (echo the Problem section's
   named workflow, not a generic "enjoy your time back").

### 3.6 Price + disclosure + CTA

The existing `#offer-view` card from `pipeline/web/index.html`, composed into
the funnel **unchanged** except the `<h1>`→`<h2>` demotion (§3.1). All four
states (default/loading/fallback/post-checkout, MT-9 §3), the disclosure
placement rule (MT-9 §2), and the state machine (MT-9 §5) carry over exactly
— this spec does not reopen any of that. This is the payoff of building the
funnel as an *elevation* rather than a rebuild: the highest-risk component
(the one handling money) is the one component that does not change.

---

## 4. Trust / credibility block — the load-bearing section for a payment page

Product-brief: *"a product is assumed to be as good as it looks."* This
section is where that has to be earned **without invented proof** (§0.1) —
the product has zero customers at launch. Three sub-blocks, each grounded in
something actually true today, not aspirational:

1. **Payment trust** — "Payments processed by Stripe. We never see or store
   your card number." (reuses the existing `.stripe-note` copy verbatim,
   promoted from small print at the bottom of the card into its own visible
   line here — same fact, said twice at two different points in the funnel
   is reinforcement, not redundancy, on a page whose entire job is one
   purchase decision). A small, real Stripe wordmark/badge is appropriate
   here (Stripe provides official marks for exactly this use) — this is the
   one place a third-party mark is legitimate, unlike §3.2's caution about
   tool-integration logos.
2. **Pricing transparency** — restates *why* the price varies (one sentence,
   linking down to the disclosure strip, not duplicating its legal text):
   "We publish regional pricing openly instead of guessing what you'll pay
   silently." This reframes the disclosure from "legal notice you must
   accept" to "a trust signal in its own right" — genuinely true given the
   design intent (MT-9 §2), and costs nothing new to build since it just
   points at the existing disclosure.
3. **Process transparency** — restates the 3-step process as a trust device,
   not just an explainer: what happens, on what timeline, with what you get
   at the end (echo of §3.5, different job — §3.5 explains, this reassures).

**Explicitly not included, flagged to PM**: testimonials, star ratings,
customer logos, "as seen in" press bars, usage counters ("N automations
delivered"). All are standard trust-block content and all require real data
this pre-launch product doesn't have. **Do not backfill with placeholder
numbers that look real** (e.g., a "127 workflows automated" stat with no
real 127) — a fabricated-looking-real number is worse than an honest gap,
since a later discrepancy (real count is much lower) undermines trust more
than never having shown one. Revisit this section once real orders exist
(ties to the dashboard's Orders view, §6.3 — the count becomes available
there first).

---

## 5. Funnel accessibility checklist (WCAG 2.2 AA) — delta from `checkout-offer-page.md` §4

Everything in MT-9 §4 still applies to the reused card verbatim. New items
specific to the multi-section funnel:

- [ ] **Heading structure**: one `<h1>` (hero), `<h2>` per section including
      the demoted card heading (§3.1), `<h3>` for individual FAQ questions.
      No skipped levels.
- [ ] **Landmarks**: `<header>` (sticky bar), `<main>` wrapping all funnel
      sections, one `<section aria-labelledby>` per block, `<footer>`
      unchanged from MT-9.
- [ ] **Skip link** updated: "Skip to pricing" landing on `#price-block`
      (same target as MT-9, now more valuable since there's real content to
      skip past above it).
- [ ] **FAQ accordion**: each question is a real `<button aria-expanded>`
      controlling a panel via `aria-controls`; never a `<summary>` styled to
      look interactive without being one, never hover-only reveal. Closed by
      default except none pre-opened (avoid implying one objection matters
      more). Focus stays on the trigger button after toggle — never moves
      into the panel automatically.
- [ ] **Anchor CTA** (hero → pricing): a real `<a href="#price-block">`
      styled as a button; on activation, moves focus to `#price-block`
      (already `tabindex="-1"` per the existing markup) so keyboard/AT users
      land where sighted users land, not just scroll past it.
- [ ] **Scroll-triggered reveals, if implemented**: respect
      `prefers-reduced-motion: reduce` — content must be present and
      readable with zero animation (fade-in-on-scroll is opacity/transform
      only, never `visibility`/display-gated, so a reduced-motion or
      JS-disabled visitor never sees blank sections).
  <br>
- [ ] **Numbered step badges** (§3.5) are decorative (`aria-hidden`) with the
      ordinal carried in real text ("Step 1: Tell us the workflow"), not
      conveyed by badge shape/color alone.
- [ ] **Contrast**: all new section text pairs re-verified at implemented
      hex values (they're the same `--ink`/`--ink-muted` on `--bg`/`--surface`
      pairs already cleared in MT-9 §4 — no new pairs introduced by the
      funnel sections themselves).
- [ ] **Zoom/reflow at 400%/320px**: single-column already; verify the 3-step
      "how it works" row collapses to stacked, not compressed, below ~600px.

Gate: same as MT-9 — `testing/accessibility-auditor` sign-off required before
this build is considered verified.

---

## 6. Part (b) — owner-only analytics dashboard (private)

### 6.1 Access + shell

Gated behind owner authentication (implementation is `backend/backend-dev`'s
— this spec assumes a login wall exists and only specifies what's behind
it). Four states before any data view renders:

- **Locked** — not authenticated: a plain login form, no dashboard chrome
  visible behind it (no blurred-preview trick — that would leak that data
  exists/its shape to an unauthenticated viewer).
- **Loading** — authenticated, data fetching: skeleton tiles matching the
  populated layout's shape (same "static skeleton, not shimmer, unless
  motion is not reduced" rule as MT-9 §3.2).
- **Populated** — the default described below.
- **Insufficient data** — not an error: the pricing experiment view in
  particular must render an honest "gathering data — N of M minimum samples"
  state rather than a blank chart or (worse) a premature "winner" (ties
  directly to issue-spec MT-4's acceptance criterion: "no winner declared
  below the configured minimum sample" — the *dashboard* is where that rule
  becomes visible, so it needs its own explicit visual state, not just a
  backend guard).

### 6.2 Information architecture — summary before detail

Left rail navigation (desktop) / top tab bar (narrow), four views. Every view
opens with a **KPI row of stat tiles** (`--surface-2` tiles, hero-figure
numerals, `--text-sm` label above, small sparkline where a trend exists) —
summary first — before any table or chart:

```
┌────────────┬──────────────────────────────────────────────┐
│  Overview  │  KPI row: Revenue · Conversion · Orders today  │
│  Pricing   │           · Active experiment state (pill)     │
│  Orders    │  ──────────────────────────────────────────── │
│  Funnel    │  [ detail: table / chart for the active view ] │
│  Heatmap   │                                                │
└────────────┴──────────────────────────────────────────────┘
```

State is encoded **in form, not just number**, throughout (per
`artifact-design`'s dashboard guidance): a status *pill* (color + icon +
text) next to a region's experiment row, not just a conversion-rate number
the owner has to interpret; a severity stripe on the anomaly-flag row, not
just a red number.

### 6.3 Pricing experiment view (MT-4's core acceptance criterion)

Per-region table: state, current price arm, trials, conversion %, expected
revenue, and a status pill using `--status-*` tokens:

| Pill | Meaning | Token |
|---|---|---|
| "Gathering data" | below minimum sample | `--ink-muted` fill, no status color — this is a neutral state, not good/bad, so it deliberately does **not** use `--status-warning` (reserving amber for a state that needs attention, not a normal early-experiment phase) |
| "Trending" | leading but not yet significant | `--status-warning` + trend-up icon + text "trending" |
| "Winner" | statistically significant | `--status-good` + check icon + text "winner" |
| "Anomaly" | anomaly monitor flagged (opsec-gate F4) | `--status-critical` + flag icon + text "review" |

Each row's conversion-rate column carries a small sparkline (`--ink-muted`
line, endpoint dot in the row's status color) — trend at a glance without a
separate chart per region. Expanding a row (or a "view all" link) opens the
full per-arm trial history as a table (satisfies the dataviz skill's "a
table view always exists" rule — the sparkline is a supplement, not the only
way to read the numbers).

### 6.4 Interaction heatmap — click density (aggregate, never per-person)

**Mechanism**: a static thumbnail of the funnel page (a screenshot, refreshed
periodically — not a live iframe) with a **binned density grid** overlaid —
a coarse grid (order of 20–30 columns, proportioned to the thumbnail's
aspect ratio; exact bin count is an implementation call for `react-dev`/
`backend-dev`, not fixed here) where each cell's fill is one of the five
`--heat-*` steps (§1) by the *count of clicks landing in that cell, summed
across all sessions in the selected date range*.

**Why binned cells, not a per-click dot layer** (the concrete mechanism
satisfying the "no per-person tracking" constraint, not just a policy
statement): a scatter of individual click dots — even anonymized — visually
reads as "this is where person X clicked, and here's person Y" the instant
there are few enough dots to eyeball individually. A density grid has no
such reading: a cell's color is inherently a sum, and at low volumes a cell
is either empty or one color-step, never resolvable back to an individual
event. This is a design decision that produces the privacy property, not
just a caption asserting it.

**Legend + disclosure, always visible on the view, not a hover tooltip**:
"Aggregate click density across all sessions in [date range]. Individual
visitors are never shown or tracked here." — stated plainly, same "must not
be buried" posture as the funnel's regional-pricing disclosure (MT-9 §2's
placement principle reapplied to a different disclosure).

**Toggle, not two separate views**: a two-option tab group ("Click density" /
"Scroll depth") switches the same thumbnail's overlay layer — `role="tablist"`
/ `role="tab"` / `role="tabpanel"`, arrow-key operable, one visible focus
state, so a keyboard user can switch layers without tabbing through a whole
new page section.

### 6.5 Scroll depth

Rendered as a **horizontal banded bar**, one band per funnel section from
§3.1 (Hero / Problem / Offer / How it works / Trust / FAQ / Price), width =
% of sessions that scrolled at least into that band, color = the same
`--heat-*` ramp (naturally monotonic decreasing top-to-bottom, which matches
the ramp's own light→dark reading direction — the deepest-reached band is
both the smallest bar *and* the darkest/most-saturated cell, reinforcing
"fewer people got this far" two ways instead of one). Placed directly beside
or below the click-density thumbnail, sharing its legend and date-range
control (one control governs both layers — no duplicate filters).

### 6.6 Accessibility mechanism for the heatmap (the actual hard problem)

A color grid over a screenshot has no meaningful text equivalent
cell-by-cell, and making ~500 grid cells individually focusable would be a
worse keyboard experience than no heatmap at all (a genuine anti-pattern,
not a hypothetical one). Resolution: **the visual grid is decorative**
(`aria-hidden="true"` on the overlay layer, the underlying thumbnail image
has real `alt` text describing what page it is), and it is **never the only
way to access the data** — next to it, always visible (not hidden behind a
disclosure toggle — same "must not be buried" reasoning as the funnel's own
disclosure), a real data table: top 5 highest-density zones by section
label, and the scroll-depth bands as a labeled list with real percentages.
Sighted mouse users get the at-a-glance visual; every user, including
keyboard/AT users, gets the same underlying numbers through the table. This
mirrors the dataviz skill's own rule ("a table view exists") applied to the
one chart type on this page where the visual truly cannot be made
individually accessible.

### 6.7 Orders view

Plain data table: date, region, price paid (`font-variant-numeric: tabular-
nums`, consistent with the price block's existing numeral treatment),
fulfillment status pill (Received → In progress → Delivered, using
`--status-warning`/`--status-good` the same way as §6.3's pills — same three
tokens, same job: "state that needs a glance, not a read"). No PII column
beyond what's operationally necessary (region + price + status) — this view
is downstream of Stripe/the order record (MT-3/MT-14's scope), not a new
data source; this spec doesn't invent new fields to display.

### 6.8 Funnel drop-off view

Stage-ordered horizontal bars (Landed → Viewed offer → Started checkout →
Completed purchase), same `--heat-*` ramp as §6.4/§6.5 (reusing the "ordered,
decreasing, sequential" color job across all three views deliberately —
one visual grammar for "fewer as you go" everywhere it appears on the
dashboard, rather than three different chart-color conventions to relearn).
Each bar labeled with both the raw count and the %-of-previous-stage drop,
since "% of previous stage" is usually the more actionable number for
finding where the funnel leaks.

---

## 7. Dashboard component notes

### 7.1 Stat tile

`--surface-2` background, `--space-4` padding, label (`--text-sm`,
`--ink-muted`, uppercase, slight letter-spacing per artifact-design
guidance), hero figure (`--price-display` scale — reused, since a stat
tile's number is the same "hero figure" job as the funnel's price), optional
sparkline beneath, optional delta line using `--status-good`/`critical` text
color **plus** an up/down glyph (never color-only for a delta, per dataviz
skill's "text wears text tokens" + status-color rules).

### 7.2 Status pill

Fixed shape reused everywhere a status appears (§6.3, §6.7): rounded pill,
`--status-*` background at reduced opacity (not full saturation — keeps text
inside legible without a separate white-text-on-saturated-fill contrast
problem, especially for `--status-warning` which already fails plain
contrast per §1), full-opacity icon + text in the corresponding solid
status color. One component, four semantic uses (good/warning/critical/
neutral-gathering), never a fifth ad hoc color introduced for a one-off
state.

### 7.3 Table

Reuses `--border` for row hairlines and `--ink-muted` for header labels —
no new table-specific tokens. Numeral columns get `tabular-nums`. Sortable
column headers are real `<button>`s inside `<th>`, not a `<div>` with a
click handler.

---

## 8. Dashboard accessibility checklist (WCAG 2.2 AA) — delta from funnel §5

- [ ] **Auth wall**: login form has a real `<h1>`, labeled inputs, and a
      visible error state on failed login that doesn't reveal whether the
      username or password was wrong (security posture, not just a11y, but
      the *error text itself* must still be programmatically associated via
      `aria-describedby` so AT users get it).
- [ ] **Tab group** (§6.4 toggle) is a real `role="tablist"` with arrow-key
      navigation and one visible `aria-selected` state; each panel is
      `role="tabpanel"` and correctly `aria-labelledby` its tab.
- [ ] **Heatmap visual is `aria-hidden`; the adjacent data table is not** —
      the table is the accessible path, per §6.6, and must appear in normal
      document/tab order immediately after (not buried behind an extra
      disclosure toggle of its own).
- [ ] **Status pills**: icon has `aria-hidden` (decorative) and the status
      word is real visible text inside the pill, never `title=` tooltip-only
      or icon-only.
- [ ] **Sortable table headers**: `aria-sort` reflects current state; sort
      action is keyboard-operable via the header button.
- [ ] **Live/refreshing data**: if the dashboard auto-refreshes, use a
      polite, off-screen "Updated N seconds ago" announcement rather than
      silently repainting numbers under a focused/reading user, and never
      steal focus on refresh.
- [ ] **Contrast**: `--status-warning` text/icon combinations are checked at
      their *actual* implemented size/weight against both `--surface` and
      `--surface-2` — given the documented sub-3:1 fill contrast (§1), the
      pill's icon+text must independently clear text contrast; do not rely
      on the fill color for any information.
- [ ] **Empty/insufficient-data state** (§6.1) has real, non-color-coded
      copy ("Gathering data — 340 of 1,000 minimum samples") — not a grayed-
      out chart with no explanation, which reads as broken rather than
      "working as intended, just early."
- [ ] **Zoom/reflow at 400%/320px**: left rail collapses to the top tab bar
      variant already specified in §6.2, not a horizontally-scrolling rail.

Gate: same as the funnel — `testing/accessibility-auditor`.

---

## 9. Handoff notes

**To `agents/frontend/react-dev`** (funnel build):
- Compose the existing `#offer-view` card unchanged into the new page per
  §3.1/§3.6; only markup change is the `<h1>`→`<h2>` demotion (§3.1) plus
  wrapping it in a `<section aria-labelledby>` consistent with the other
  funnel sections.
- New sections (Hero/Problem/Offer/How-it-works/Trust/FAQ) are static markup
  — no state machine, no fetch — except the hero anchor-CTA's focus-move
  behavior (§5).
- Copy seam: this spec uses representative placeholder copy throughout
  (hero headline, problem bullets, FAQ questions, trust-block sentences).
  **Final copy is `design/brand-guardian`'s `funnel-copy.md`** (not yet
  created as of this spec) — same pattern as `copy.js`'s existing
  MT-5-pending seam (source copy from a constants/CMS module, never hardcode
  marketing strings into components), so swapping in real copy later is a
  data change, not a markup change.
- Token additions (§1, §2) go into `styles.css` alongside the existing
  eight — same file, same `:root` / `@media (prefers-color-scheme: dark)`
  pattern already established, no second stylesheet.

**To `agents/backend/backend-dev`** (dashboard data + auth):
- Data contracts for §6.3 (per-region arm/trials/conversion/revenue),
  §6.7 (orders), §6.8 (funnel-stage counts) are read models over data these
  agents' prior work already produces (`pricing_engine.py`'s `Assignment`/
  `PriceArm`, the MT-14 order record, and page-view/click events not yet
  specced — flagged in §10.1). This spec defines the *view*, not the API
  shape; a data-contract pass is needed before `react-dev` can build against
  it (same "handoff, not a finished contract" posture as MT-9 §5 had for the
  checkout card).
- Click/scroll capture (§6.4/§6.5) must land on the anonymous-session-id,
  no-PII, no-raw-IP, no-keystrokes model the product-brief and opsec-gate F8
  already require — this spec's binned-density mechanism (§6.4) is
  compatible with (in fact is *easier* to satisfy privacy-wise with) an
  aggregate-at-write-time pipeline rather than storing raw per-click rows
  and aggregating at read time; flagging that choice to `backend-dev` as a
  design-supports-it note, not a mandate — implementation is theirs.

---

## 10. Open items requiring PM / other agents, not designer judgment

1. **No dashboard-build sub-issue exists in `docs/backlog.md`** — MT-4 is
   assigned to `pm/experiment-tracker` for the analytics/experiment-readout
   *scope*, but this spec also covers heatmap + orders + funnel-drop-off
   views that read like a `frontend/react-dev` build task. PM should decide
   whether MT-4 is decomposed the way MT-2 was (into a design sub-issue,
   already this document, plus a build sub-issue) before work starts.
2. **Click/scroll event capture pipeline is unspecced** — this spec assumes
   the events exist to visualize; no issue currently owns "instrument the
   funnel pages to emit anonymous click/scroll events." Flag to PM against
   opsec-gate F8 (owned by `legal/privacy-engineer`, currently OPEN) so
   instrumentation and its privacy review land together, not instrumentation
   first and privacy review as an afterthought.
3. **Funnel copy** — per §9, `design/brand-guardian`'s `funnel-copy.md` is
   the seam; this spec deliberately does not invent final marketing copy
   (same posture MT-9 §6.3 took for the checkout card's headline).
4. **Trust-block content once real orders exist** (§4) — worth a follow-up
   design pass once the Orders view (§6.7) has real numbers, to decide
   whether/how a real, honest usage figure gets surfaced on the public page
   without it reading as manufactured. Not a decision to make pre-launch.
5. **Stripe trust badge usage** (§4.1) — confirm against Stripe's current
   brand-asset terms before shipping any Stripe mark; flagged, not verified,
   by this spec.

---

## 11. Visual reference

An interactive mockup (theme-aware, keyboard-operable) covering the funnel
hero + trust block and the dashboard's pricing-experiment + heatmap view is
published as an Artifact — see session output for the link. It uses the same
representative placeholder copy referenced in §9, not final copy.
