# Design spec — offer + checkout (single page, hands off to Stripe Checkout)

**Agent**: `agents/frontend/designer` · **Sprint**: sprint-7-26-19-26 · **Issue**: MT-2
(`docs/sprint-7-26-19-26/issue-specs/pricing-pipeline.md` §2)
**Reads honored**: `prd.md` §1, §5, §6; issue spec MT-2 acceptance criteria + negative prompt.
**Reuse check**: no prior frontend work exists in this repo (`agents/frontend/*` is
empty, `agents/INDEX.md` lists 0 agents, no design system or prior page). There is
nothing to reuse — every visual decision below is new and is flagged as such. This
spec becomes the pattern future pages in this repo should reuse.

---

## 0. Constraints this build must not violate (restated up front, per charter)

These are gates, not preferences. `testing/accessibility-auditor` and the verdict
loop check them; do not let implementation drift from them for conversion reasons.

1. **No dark patterns** — no fake countdowns, no fake scarcity ("3 left!"), no
   pre-checked upsells/add-ons, no confirm-shaming copy on any decline/cancel
   path ("No thanks, I don't want to save money" is banned). One price, one
   honest CTA.
2. **Disclosure must not be buried.** "Prices vary by region" is a first-class
   element in the reading order between the price and the pay button — not a
   footer link, not a tooltip, not collapsed behind a "details" toggle.
3. **Never a broken page.** If geolocation or price-fetch fails, the page
   renders the national baseline price with the *same* layout used for the
   success path. No error banner, no blank price, no retry wall.
4. **No price flicker within a session** (issue spec negative prompt). Once a
   price is assigned it is stable for the session — this is a state-persistence
   requirement for react-dev, noted again in §5.
5. **WCAG 2.2 AA.**

---

## 1. Layout + visual hierarchy

Single column, single card, centered — this is a one-decision page (buy / don't
buy), so the layout should not introduce a second decision. No nav bar, no
multi-product grid.

```
┌───────────────────────────────────────────┐
│  (skip-to-content target)                  │
│  Product name / one-line offer   [h1]      │
│  One-sentence value proposition  [p]       │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │  PRICE  (large, tabular numerals)  │ ← aria-live region
│  │  billing cadence, if any           │     │
│  └───────────────────────────────────┘     │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │  ⓘ Prices vary by region.          │ ← disclosure strip
│  │    You're seeing the [State] price.│     │
│  │    Full privacy notice →           │     │
│  └───────────────────────────────────┘     │
│                                             │
│  [   Continue to secure checkout   ]  ← CTA (button, not link)
│  Payments handled by Stripe. We never      │
│  see or store your card details.           │
│                                             │
│  footer: Privacy notice · Terms · Contact  │
└───────────────────────────────────────────┘
```

Reading order = visual order = DOM order = tab order (§4). The disclosure strip
sits **between** the price and the CTA specifically so a screen-reader user
tabbing forward, or a sighted user scanning down, cannot reach "pay" without
passing it.

**Visual weight**, largest to smallest: price → headline → CTA button →
disclosure strip text → value-prop sentence → footer. The disclosure is not the
loudest element on the page (that would read as alarming, itself a mild dark
pattern in reverse — manufactured anxiety), but it is not quiet either: same
body-text size as the value proposition, set in a tinted, bordered strip so it
reads as a distinct, deliberate block rather than incidental copy.

**Card**: max-width ~440px, centered, generous padding (not a dense commerce
layout — this is a single SKU). Rounded corners, one soft border/shadow, on a
calm neutral page background.

**Type**: system-ui font stack (San Francisco / Segoe UI / Roboto / etc.), not
a custom webfont. This is a deliberate choice, not a default: a payment page's
job is to paint the price and the pay button as fast as possible with zero
FOIT/FOUT risk, and a system font reads as platform-native and trustworthy on a
checkout screen — the same reasoning Stripe's own Checkout uses. Numerals in
the price use `font-variant-numeric: tabular-nums`.

**Color**: no design system exists yet in this repo, so this spec establishes
a provisional one — flagged for react-dev to treat as a starting token set,
not a locked brand (PRD §6: the operator's identity is deliberately
unbranded/shielded, so this page should read as a plain, professional,
low-personality product page, not a "brand" with a logo and voice).

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#F6F5F2` | `#14171A` | page ground (warm-neutral paper / near-black, not pure white/black) |
| `--surface` | `#FFFFFF` | `#1C2024` | card |
| `--ink` | `#1B1F23` | `#EDEFF1` | headings, price |
| `--ink-muted` | `#5B6370` | `#9AA4AF` | body copy, footer |
| `--border` | `#E2DFD9` | `#2A2F35` | card border, disclosure strip border |
| `--accent` | `#1F6F5C` | `#3FA98A` | CTA button — deep teal, reads as "confirm/go," deliberately not the red/orange of urgency-driven commerce UI |
| `--disclosure-bg` | `#FBF3E3` | `#2B2416` | disclosure strip fill — warm parchment tint, informational, not alarm-yellow |

All pairs below are checked for AA at the sizes they're used at (verify again
once real type sizes are implemented — see §4 checklist):
- `--ink` on `--surface`/`--bg`: >7:1 both themes (AAA).
- `--ink-muted` on `--surface`/`--bg`: ≥4.5:1 both themes (body text minimum).
- white text on `--accent` button: ≥4.5:1 both themes.
- `--ink` on `--disclosure-bg`: ≥4.5:1 both themes.

---

## 2. The disclosure treatment (PRD §5, the load-bearing requirement)

**Placement**: its own visually distinct strip, directly below the price
block, directly above the CTA button. Never in a footer-only link, never
collapsed.

**Copy pattern** (plain language, per PRD; exact legal wording is MT-5's,
see §6 — this is the *shape* the copy should take):

> ⓘ **Prices vary by region.** You're seeing the **[State]** price. This price
> is the same for everyone in your region right now. [Full privacy notice →]

Three sentences, each doing one job: (1) the disclosure itself, in the
plain language the PRD asks for; (2) which region price the visitor is
seeing, naming the state — more transparent than a generic "your region,"
and consistent with "identical price per region per interval, shown openly"
from the security consult; (3) a link out to the full privacy notice
(MT-5) for anyone who wants the geolocation/analytics/retention detail.

**Icon**: a plain "ⓘ" info glyph or equivalent, not a warning triangle — this
is a factual disclosure, not an error. Decorative, `aria-hidden="true"`; the
information is carried entirely by the text next to it.

**Why a strip, not a tooltip/accordion**: anything that requires an extra
click or hover to reveal fails "must not be buried" outright, and fails
keyboard/screen-reader-first users doubly. The strip costs one extra glance,
always visible, no interaction required.

**Open decision flagged to `pm/project-manager` / legal**: naming the specific
state to the visitor (option chosen here) is the most transparent reading of
"shown openly," but it's a legal/DPO call whether stating the detected state
back to the visitor changes anything about the privacy-notice lawful-basis
language (MT-5, still `todo` per `docs/backlog.md`). Do not have react-dev
build against this copy as final — treat §2's copy as a structural
placeholder until `legal/product-counsel` + `legal/privacy-engineer` sign off
under MT-5. MT-5 blocks MT-2 per the issue spec's dependency line; this page
should not go live with placeholder disclosure copy.

---

## 3. States

One component, four states, same layout shell in all four — only the price
block and (for post-checkout) the card body change. This is deliberate: a
visitor who lands mid-fallback should not be able to tell anything went wrong.

### 3.1 Default (price resolved)
- Price block shows the resolved regional price, large, tabular numerals.
- Disclosure strip shows the resolved state name.
- CTA enabled: "Continue to secure checkout."

### 3.2 Loading (price resolving)
- Disclosure strip renders immediately with generic copy — it does not wait
  on the price fetch, since "prices vary by region" is true regardless of
  which price resolves: *"Prices vary by region. Finding your region's
  price…"*
- Price block shows a skeleton placeholder (a static muted block, not a
  shimmering animation, to respect `prefers-reduced-motion` by default —
  animate only if reduced-motion is not requested, and keep it subtle even
  then).
- CTA is present but disabled (`aria-disabled="true"`, not removed from the
  DOM) with label unchanged — do not swap it to "Loading…" text that a
  screen-reader user tabbing past would announce as if it were the permanent
  label; instead pair it with an `aria-describedby` note ("Price is loading")
  and a visible spinner glyph next to it.
- This state should resolve in low hundreds of ms in the common case; if it
  runs long, it still must not time out into an error UI — see 3.3.

### 3.3 Error / fallback (geolocation or price fetch fails)
- **Visually identical to Default**, showing the national baseline price from
  `pricing_engine.py` (`DEFAULT_PPP` / unknown-state path, PRD: "unknown
  state → national baseline, never a penalty").
- Disclosure strip copy adjusts only the state clause: drop the "You're
  seeing the [State] price" sentence (there is no resolved state) and keep
  the rest: *"Prices vary by region. You're seeing our standard price."*
- No error banner, no red state, no retry button surfaced to the visitor —
  the failure is logged for analytics/ops, not shown. This satisfies "must
  degrade to a sensible default price, never a broken page" literally: the
  visitor experience is the same page, just the baseline price.
- CTA behaves exactly as Default once the fallback price is set (this is not
  a degraded/disabled state from the visitor's point of view).

### 3.4 Post-checkout return
Stripe hosted Checkout redirects back to `success_url` / `cancel_url` on your
domain. Two sub-states, both reachable only via those redirect URLs (not
by direct navigation with a guessable path):

- **Success**: replace the card body (same shell, same max-width) with a
  confirmation: what was purchased, the price paid (must equal the price
  shown pre-checkout — MT-3's job to guarantee, this page just displays it),
  a note that a receipt was emailed, and a plain next-step ("What happens
  next" — one or two sentences, not a marketing upsell). No "you saved $X"
  framing (nothing was discounted; avoid inventing anchor-price psychology
  that wasn't part of the original offer).
- **Cancel / return without completing**: the visitor lands back on the
  *same* Default-state offer page, price unchanged (must reuse the same
  session assignment — see §5, no re-roll). Absolutely no confirm-shaming
  interstitial ("Wait — are you sure?", exit-intent modal, "here's a
  discount to stay"). If Stripe's cancel redirect fires, just show the offer
  page again, unmodified.

---

## 4. Accessibility checklist (WCAG 2.2 AA)

- [ ] **Contrast**: all text/background and UI-component/background pairs
      ≥4.5:1 (normal text) / ≥3:1 (large text ≥24px or 19px bold, and
      non-text UI like the button border/focus ring) in both themes. Verify
      the actual implemented hex values, not just the token table above.
- [ ] **Focus order** = DOM order = visual order: skip link → h1 → (price
      region is not independently focusable, it's not interactive) →
      disclosure strip link → CTA button → footer links. No positive
      `tabindex`.
- [ ] **Visible focus indicator** on every interactive element (CTA button,
      disclosure's privacy-notice link, footer links) — a focus ring that
      meets the 3:1 non-text contrast minimum against both `--surface` and
      `--accent`, in both themes. Never `outline: none` without a
      replacement.
- [ ] **Keyboard operability**: entire flow (including the Stripe handoff)
      operable with Tab/Shift+Tab/Enter/Space alone. No hover-only or
      click-only affordance carries information the keyboard path lacks.
- [ ] **Skip link**: "Skip to offer" landing on the price block, for screen
      reader / keyboard users to bypass any header chrome.
- [ ] **Landmarks + heading structure**: single `<h1>` (offer name), `<main>`
      wrapping the card, `<footer>` for legal links. No skipped heading
      levels.
- [ ] **Price is a real label, not implied by position**: visually-hidden
      label text ("One-time price:") precedes the numeral for screen readers,
      so "$65.93" is never announced context-free.
- [ ] **`aria-live="polite"` on the price container** so assistive tech
      announces the transition loading → resolved/fallback without the user
      having to re-navigate to it. Do not use `aria-live="assertive"` — this
      is not urgent/interrupting information.
- [ ] **CTA button is `aria-describedby` the disclosure strip's id** — so a
      screen-reader user focusing "Continue to secure checkout" hears the
      regional-pricing disclosure immediately as part of the button's
      accessible description, even though it's also independently readable
      in document order above it. Belt-and-suspenders for the "must not be
      buried" requirement specifically for AT users who navigate by
      form-control/button lists rather than linearly.
- [ ] **Real `<button>`/`<a>` elements**, never a `<div onclick>`; CTA is a
      `<button>` (it triggers navigation to Stripe via JS/form submit, not a
      plain same-tab link, so button semantics are correct) with an
      accessible name matching its visible text exactly.
- [ ] **Disabled-during-loading CTA** uses `aria-disabled="true"` (kept
      focusable, announced as unavailable) rather than the `disabled`
      attribute, which would pull it out of the tab order and could strand a
      keyboard user's expected tab stop — but do not let it be *activatable*
      while `aria-disabled`; the click/keydown handler must no-op so a
      double-activation (e.g. a fast double Enter) cannot fire two Checkout
      Session creations — pairs with `pricing_engine.py`'s idempotency
      guarantee on the backend so there's no double-charge risk either way.
- [ ] **Motion**: any skeleton-loading animation respects
      `prefers-reduced-motion: reduce` (fall back to a static skeleton).
- [ ] **Color is never the only signal**: the fallback/default states are
      distinguished (for analytics/ops, not the visitor) by data, not by a
      color change the visitor would see and have to interpret.
- [ ] **Zoom/reflow**: layout holds at 400% zoom / 320px CSS width without
      horizontal scroll or clipped content (single-column design should pass
      this by construction — verify anyway).
- [ ] **Language + region text is real text**, not an image of text (state
      name, price, disclosure — all must be selectable/readable by AT and
      by browser translation tools).

Gate: `testing/accessibility-auditor` must sign off against this checklist
before MT-2 verify (`evidence-collector` screenshots) is considered
satisfied.

---

## 5. Handoff notes to `agents/frontend/react-dev`

**Data contract** (from `pipeline/pricing_engine.py::Assignment`):
```
session_id, region (state_code or "__default__"), baseline, price,
variant_id ("{state}@{price}"), device_class (analytics-only, never
rendered/branched-on for price logic), ts
```
`region == "__default__"` (or an unrecognized state) is the signal to render
the **3.3 Error/fallback** copy variant — this is a data-driven state, not a
try/catch around a render failure. Treat "fetch succeeded but returned the
default-baseline arm" and "fetch failed outright" the same way in the UI:
both render 3.3.

**State machine** (suggest exactly these four, matching §3):
`loading → ready | fallback`, plus an orthogonal `post_checkout: success |
cancel` route reached only via the Stripe redirect URLs. Do not add a fifth
"hard error" visual state — per PRD, there is no such state on this page;
network/geo failure always resolves to `fallback`, never to a broken render.
If the pricing engine call itself throws, catch it client-side and treat it
identically to `fallback` with the compiled-in national baseline price as a
last-resort static value, so the page never renders with no price at all.

**No price flicker within a session** (issue-spec negative prompt): persist
the `Assignment` (or at minimum `variant_id` + `price`) for the session —
`sessionStorage` keyed by `session_id`, or a server-set session cookie if
`session_id` is server-issued — and reuse it on reload rather than
re-calling `assign_price`. Re-assigning per page-load would (a) visually
flicker the price and (b) let a single visitor roll multiple bandit arms,
which the engine's docstring explicitly rules out ("never charges two
people in the same region different prices at the same time" generalizes to
not re-rolling the same person either).

**Suggested component boundaries**:
- `OfferPage` — layout shell, owns state machine.
- `PriceDisplay` — the `aria-live` region, tabular-nums, renders skeleton in
  `loading`.
- `RegionDisclosure` — the strip; takes `state | null` prop, renders 3.1/3.3
  copy variants; owns the id that `CheckoutButton`'s `aria-describedby`
  points to. **Do not hardcode the copy in this component** — source it from
  wherever MT-5's signed-off disclosure text lands (a shared copy/constants
  module or CMS field), since that copy is still pending legal sign-off as
  of this spec.
- `CheckoutButton` — posts to your backend to create the Stripe Checkout
  Session (never calls Stripe client-side with raw card fields — PRD §4,
  MT-3's scope), then redirects.
- `PostCheckoutReturn` — handles `success_url`/`cancel_url` query params,
  renders 3.4.

**Explicit build constraints to carry into code review** (restating §0 as
acceptance-test fodder for `logicians/` static review and
`testing/accessibility-auditor`):
- No countdown timer, no "X people bought this today," no pre-checked
  checkbox of any kind, no dismiss-with-shame copy anywhere in the cancel
  path.
- Disclosure strip is not removable by any A/B/growth experiment on this
  page — pricing experimentation is scoped to the price value only
  (`pricing_engine.py`), never to whether the disclosure renders.

---

## 6. Open items requiring PM / legal, not designer judgment

1. **Final disclosure + privacy-notice copy** — MT-5 (`legal/product-counsel`,
   verified by `legal/privacy-engineer`) is still `todo`. This spec's §2 copy
   is a structural placeholder (correct length, tone, and information
   content) but is not cleared for ship. MT-5 blocks MT-2 per the issue
   spec's dependency line — flagging so the PM doesn't let MT-2 implementation
   outrun MT-5 sign-off.
2. **Whether to name the visitor's specific state** in the disclosure (this
   spec's recommendation, §2) vs. a generic "your region" — recommend the
   named-state version for transparency but defer final call to
   `legal/product-counsel` given it interacts with the geolocation
   disclosure's lawful-basis wording.
3. **Product name / one-line value proposition copy** for the h1 and
   value-prop line are not specified anywhere in the PRD or issue spec —
   PM or the operator needs to supply real offer copy before this ships;
   this spec deliberately does not invent product marketing copy.

---

## 7. Visual reference

An interactive mockup covering all four states (theme-aware, keyboard-
operable) is published as an Artifact for `react-dev` to check hierarchy and
disclosure placement against: see session output.
