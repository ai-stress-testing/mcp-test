# Funnel copy — offer page, final-quality draft

**Agent**: `design/brand-guardian` · **Sprint**: sprint-7-26-19-26
**Companion doc**: `brand-guide.md` (voice rules this copy follows — read
that first for the *why*).
**Reads honored**: `product-brief.md`, `prd.md` §5, `pipeline/web/copy.js`,
`design-specs/checkout-offer-page.md`.

## How this relates to `pipeline/web/copy.js`

`copy.js` already ships real, load-bearing structural strings for the
single-card checkout component: `CTA_LABEL`, `STRIPE_NOTE`, `PRICE_LABEL`,
the loading/degraded disclosure fallbacks, and the success/cancel strings.
**This document does not duplicate or diverge from those** — where the
funnel below reaches the same moment `copy.js` already covers (the final
buy button, the Stripe reassurance line, the success screen), it reuses the
exact `copy.js` string verbatim and says so, so `frontend/react-dev` has one
source of truth per string instead of two slightly different versions to
reconcile. New copy below is for the parts of the funnel `copy.js`
deliberately doesn't own: hero, problem, offer, how-it-works, trust/FAQ, and
the *intake* step after purchase (which `copy.js`'s generic
`SUCCESS_NEXT_STEPS` line gestures at but doesn't spell out).

**Legal/disclosure text is explicitly out of scope here** — per `prd.md` §5
and `copy.js`'s own header comment, the regional-pricing disclosure is
server-sourced from the `/assign` response and is MT-5's (legal) call. Every
place this copy needs that text, it's marked `[DISCLOSURE — server-sourced,
do not hardcode]` rather than drafted.

**Bracketed items are swap points**, not filler: workflow examples, the
price band, and the delivery SLA are the operator's to finalize per
`product-brief.md` §"Swap points." Everything else below is ready to ship
as final copy once "Flowmark" is replaced with the real name.

---

## Hero

> **H1**: Buy back the hours one task is stealing every week.
>
> **Subhead**: We build one automation — matched to the specific process
> eating your time — and deliver it working within [a few business days].
> Pay once. No software for you to learn, no subscription to manage.
>
> **CTA (anchor, scrolls to the price card)**: See your price

Note: this hero CTA is distinct from the final purchase button. The final
button's label is already defined in `copy.js` as `CTA_LABEL: "Continue to
secure checkout"` — reuse that string verbatim on the price card itself.
"See your price" here is a lower-commitment anchor link for visitors
scrolling from the top of a longer landing page, not a second checkout
button.

---

## The problem, felt

> **H2**: You already know which task this is.
>
> A lead messages you, and you mean to reply — but the reply waits for a
> free five minutes that doesn't come until tomorrow, by which point
> they've already messaged someone else.
>
> An invoice goes unpaid, not because the client won't pay, but because
> nobody follows up until it's already awkward to bring up.
>
> You write one good post, and it gets used exactly once — when the same
> twenty minutes of rewriting could have turned it into six.
>
> None of these takes long, on its own. That's exactly why it never gets
> fixed. Multiply the five minutes by every lead, every week, and it stops
> being a task — it's a second, unpaid job you never applied for.

(Workflow examples used per the operator's three named use cases — lead
follow-up, invoice chasing, content repurposing — swap or extend once real
buyer verticals are known.)

---

## The offer

> **H2**: What you get
>
> - One working automation, built around the tools you already use — your
>   CRM, inbox, forms, spreadsheet, or Slack, whatever you've actually got,
>   not a tool you have to switch to.
> - AI handles the reading, drafting, routing, or summarizing; you stay in
>   control of what actually sends, or let it run on its own — your call,
>   set during intake.
> - Delivered within [a few business days] of your intake form.
> - One price, paid once. No subscription, no seats, no "AI credits" to
>   track or run out of.
>
> This isn't a course, a template, or a tool you have to configure
> yourself. It's a finished automation, built for your setup, handed to you
> already working.

---

## How it works (3 steps)

> **1. Pay, then tell us what's eating your time.**
> A short intake form — which task, which tools, and a couple of real
> examples, so what we build fits your business instead of a generic case.
>
> **2. We build it against your actual tools.**
> The automation is wired to the CRM, inbox, spreadsheet, or Slack you told
> us about — not a demo environment, not a template with your logo dropped
> in.
>
> **3. You get a working automation.**
> Delivered within [a few business days], tested against the examples you
> gave us, with a short walkthrough so you know how to turn it off, adjust
> it, or ask for a change.

---

## Trust / credibility block

Two parts — one is real content that's true from day one, the other is an
explicitly labeled placeholder for social proof that doesn't exist yet.
**See the open flag in `brand-guide.md` §7.3**: recommend hiding the social-
proof sub-block entirely pre-launch rather than shipping a visible
"coming soon" placeholder, but that's a PM/growth call, laid out here as an
option, not decided by this doc.

### Always-true process content (ship now, no placeholder needed)

> **Who builds this**: a single operator with hands-on experience building
> exactly this kind of automation — not an agency, not a team you'll get
> routed through. One person, one build, direct communication if you have a
> question.
>
> **What's included**: one automation, connected to the tools you specify at
> intake, delivered working, plus a short walkthrough of how it runs.
>
> **What's not included**: ongoing subscription support, unrelated
> automations, or an open-ended "AI assistant" — this is one workflow, done
> well, not a general-purpose tool.
>
> **Payments**: [reuse `copy.js` `STRIPE_NOTE` verbatim] "Payments handled
> by Stripe. We never see or store your card details."
>
> **If it doesn't fit your process**: [SLOT — revision/refund policy not
> yet defined; do not ship this section until the operator supplies a real
> policy. Placeholder question for the FAQ below marks the same gap.]

### Social proof (structural placeholder — do not populate with invented content)

> **What buyers say**
> *[Placeholder — real testimonials go here once buyers have used their
> automations. Do not fill this with invented quotes, review counts, or
> customer logos. Recommended default: hide this block entirely until real
> testimonials exist, rather than showing a "reviews coming soon" state to
> visitors — see brand-guide.md §7.3 for the tradeoff.]*

---

## Objection-handling FAQ

> **Will this actually work for my business, or is it generic?**
> The intake form asks for your real tools and a couple of real examples of
> the task — the automation is built against those, not a one-size-fits-all
> template. If your process is too unusual to automate well, we'll tell you
> before building rather than deliver something that doesn't fit.
>
> **What if I don't like what you build?**
> [SLOT — revision or refund policy not yet defined. Do not publish this
> answer, or this FAQ item, until the operator supplies real terms. A
> payment page cannot promise a policy that isn't decided.]
>
> **Is this a subscription? What happens after the automation is delivered?**
> No — it's a one-time payment for one automation. There's no recurring
> charge and nothing to cancel later. If the tools it connects to change on
> your end (a new CRM, a new inbox), the automation may need adjusting, but
> that's not a built-in subscription.
>
> **What tools does it actually connect to?**
> Whatever you're already using — common CRMs, email/inbox providers, form
> tools, spreadsheets, and Slack are all fair game. You tell us your stack
> at intake; we build to it rather than asking you to adopt something new.
>
> **Who is actually building this — a company, an agency, a person?**
> One person, working directly on your build — not a call center, not a
> team you get routed through. [Do not add unverifiable credentials or
> years-of-experience claims here — keep this line honestly generic per
> brand-guide.md §1's anonymity constraint.]
>
> **Is my information safe? What do you actually collect?**
> [DISCLOSURE — server-sourced, do not hardcode] Full detail on what's
> collected (including region detection for pricing) lives in the privacy
> notice: reuse `copy.js` `PRIVACY_LINK_TEXT` / `PRIVACY_HREF` ("Full privacy
> notice →" / `/privacy-notice`) as the link out from this FAQ answer rather
> than restating the disclosure text here.
>
> **How long does delivery actually take?**
> [a few business days] from when you submit the intake form — the clock
> starts at intake, not at payment, since we need your specifics before we
> can start building. [SLA is a swap point per product-brief.md — confirm
> exact day count before this ships as final copy.]
>
> **What if my process changes later and I need a tweak?**
> [SLOT — same open policy question as "what if I don't like what you
> build?" above; needs one real answer that covers both pre- and
> post-delivery changes before either FAQ item ships.]
>
> **Why does the price change depending on where I'm buying from?**
> [DISCLOSURE — server-sourced, do not hardcode] This is the regional-pricing
> disclosure itself; do not draft it here. The price card above already
> carries the live disclosure text from the `/assign` response — this FAQ
> item should link to the same privacy notice rather than re-explain the
> mechanism in different words that could drift out of sync with the legal
> copy.

---

## CTA microcopy

Reuse `copy.js` verbatim wherever the funnel reaches that exact moment —
listed here for completeness, not redefined:

- Price-card buy button: `CTA_LABEL` — "Continue to secure checkout"
- While price is resolving: `CTA_LOADING_NOTE` — "Price is loading"
- Below the buy button: `STRIPE_NOTE` — "Payments handled by Stripe. We
  never see or store your card details."
- Price label for screen readers: `PRICE_LABEL` — "One-time price:"

New microcopy for moments `copy.js` doesn't cover:

> **Hero anchor CTA**: See your price
> **Intake form entry CTA (post-purchase)**: Start your intake form
> **Intake form subhead**: Takes about [5] minutes. The more specific your
> examples, the closer the first version will match what you actually need.

---

## Post-purchase: success + intake next step

`copy.js` already defines the always-shown structural strings
(`SUCCESS_HEADING`, `SUCCESS_RECEIPT_NOTE`, `CANCEL_ANNOUNCE`, etc.) — reuse
those verbatim for their moments. The copy below fills in the one part the
product brief requires that `copy.js`'s generic `SUCCESS_NEXT_STEPS` line
doesn't spell out: the actual next action (submit the intake form), since
the offer's fulfillment depends on it.

> **Success heading**: [reuse `copy.js` `SUCCESS_HEADING`] "You're all set"
>
> **Receipt note**: [reuse `copy.js` `SUCCESS_RECEIPT_NOTE`] "A receipt has
> been emailed to you."
>
> **What happens next** (expands on `copy.js`'s generic
> `SUCCESS_NEXT_STEPS` — this is the version to ship once the intake form
> exists; keep the generic line only as a fallback if the intake form isn't
> ready to link yet):
> One step left: tell us which task to automate and which tools it touches.
> The intake form takes about [5] minutes — the more specific your
> examples, the closer the first build will match what you need. We'll
> confirm receipt of your intake and follow up with any questions before we
> start building.
>
> **Intake CTA button**: Start your intake form
>
> **No-price fallback** (edge case, `copy.js` `SUCCESS_NO_PRICE_FALLBACK`):
> reuse verbatim — "Your payment was received." — pair with the same intake
> CTA above; the intake step is unaffected by whether the price could be
> re-displayed.
>
> **Cancel path** (reuse `copy.js` `CANCEL_ANNOUNCE` verbatim — "Checkout
> was canceled. Your price is unchanged.") — no additional copy needed; per
> `design-specs/checkout-offer-page.md` §3.4, no exit-intent modal, no
> discount offer, no "are you sure" interstitial. This document adds nothing
> here deliberately, to avoid reintroducing confirm-shaming through a
> back door.

---

## Summary of swap points left open in this copy

Per `product-brief.md` §"Swap points" plus gaps this draft surfaced:

1. **Name**: "Flowmark" throughout — none of this copy names it directly
   except implicitly via "the automation"/"your automation," so a rename
   touches page titles/metadata, not this body copy.
2. **Delivery SLA**: "[a few business days]" appears in hero, offer,
   how-it-works, and FAQ — currently consistent placeholder language, needs
   one real number before ship.
3. **Price band**: not written into this copy at all (the price card owns
   the number, server-sourced) — no action needed here.
4. **Revision/refund policy**: two FAQ items and one trust-block line are
   marked `[SLOT]` and should not ship until the operator supplies real
   terms — publishing a payment page that promises an undefined policy is a
   trust risk in the opposite direction from having no policy line at all.
5. **Workflow examples**: hero/problem section uses lead follow-up, invoice
   chasing, and content repurposing per the product brief; swap or add
   verticals as real buyer segments emerge.
