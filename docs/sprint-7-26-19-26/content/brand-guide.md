# Brand guide — voice, naming, color/type direction

**Agent**: `design/brand-guardian` · **Sprint**: sprint-7-26-19-26
**Reads honored**: `product-brief.md` (the offer), `prd.md` §5 (disclosure is
server-sourced — this guide does not write legal copy), `pipeline/web/copy.js`
(existing structural copy this guide's companion `funnel-copy.md` extends,
not replaces), `design-specs/checkout-offer-page.md` (existing provisional
color tokens + "unbranded, low-personality" framing this guide inherits and
gives the rationale for).

North star for every rule below: **this is a payment page a stranger is
about to trust with their card.** Every voice and color/type call is judged
against whether it raises or lowers that stranger's confidence that this is
real, competent, and safe to pay right now — not against whether it's
memorable, delightful, or distinctive for its own sake.

---

## 1. A constraint that shapes everything else: identity is deliberately shielded

PRD §6 shields the operator's identity from the public (brand name privacy,
anonymous LLC, virtual mailbox) while staying KYC/tax-compliant. The design
spec already reads this correctly for visuals ("this page should read as a
plain, professional, low-personality product page, not a 'brand' with a
logo and voice" — `design-specs/checkout-offer-page.md` §1).

The same logic has to hold for *voice*, and that's a real constraint on
normal brand-guardian work: the usual move here would be to build a
distinctive human voice (founder story, personality, "meet the builder"
photo). That move is off the table on this build — not because it's bad
practice generally, but because it works against the anonymity requirement
this project was scoped around. So this guide defines a voice that reads as
**competent and trustworthy without surfacing a persona.** Think: the way a
well-run utility, a payment processor's own docs, or a solo engineer's
changelog reads — precise, calm, un-performed — rather than a DTC startup's
landing page.

**Flagging this explicitly for `pm/project-manager`**: confirm this reading
of "shielded identity" is meant to extend to marketing tone and not just
legal-entity/WHOIS information. If the operator *wants* some personality later
(a named "who builds this" bio, for instance), that's a scope change against
PRD §6 worth a deliberate call, not something to drift into during copywriting.

---

## 2. Naming

**"Flowmark" is a placeholder.** Per `product-brief.md`: "Working name:
Flowmark (placeholder — swap before launch; the machinery doesn't depend on
the name)." Nothing in this guide or in `funnel-copy.md` treats it as final.
Both documents are written so a name swap is a find-and-replace, not a
rewrite — the voice rules below are name-agnostic by design.

Guidance for whoever picks the real name:

- **Read as a tool, not a lifestyle brand.** Literal, short, no forced
  acronym. This is closer to naming a utility than naming a consumer app.
- **Don't anthropomorphize it** ("Aiden," "Sage," anything that implies a
  persona/assistant with a face). The product is one delivered automation,
  not an ongoing relationship with a character — and a named "personality"
  cuts against the anonymity requirement in §1.
- **Avoid AI-generic naming filler** ("-AI," "-ly," "-Flow" stacked with
  another buzzword) — it reads as a category-of-the-month product, which
  undercuts the "finished, working thing" positioning.
- In copy, don't refer to the product as "your AI assistant" — it's one
  specific automation. Always name the job it does ("your lead follow-up
  workflow," "your invoice chasing automation"), never a vague AI-agent
  framing. This is also a scope-clarity point: buyers are purchasing one
  automation, not an open-ended assistant, and the copy should never imply
  otherwise.

---

## 3. Voice: 3–5 adjectives, with do/don't

### Direct
- **Do**: lead with the concrete fact — price, timeline, what's included —
  in the first sentence of a section.
- **Don't**: open with scene-setting or a rhetorical question ("Imagine
  never chasing an invoice again...").

### Competent
- **Do**: use exact, checkable specifics ("delivered within a few business
  days," "one workflow," "connects to your CRM, inbox, or spreadsheet").
- **Don't**: reach for unearned superlatives ("revolutionary,"
  "game-changing," "world-class").

### Plain-spoken
- **Do**: write the way a builder would explain what they made — short
  sentences, ordinary words.
- **Don't**: stack marketing adjectives ("seamless, cutting-edge,
  best-in-class solution").

### Respectful of skepticism
- **Do**: name the buyer's actual doubt and answer it head-on (this is the
  whole job of the FAQ in `funnel-copy.md`).
- **Don't**: pressure, guilt, or rush ("Don't miss out," "Other businesses
  are already ahead of you").

### Calm
- **Do**: one clear ask per screen, steady pacing, minimal punctuation
  emphasis.
- **Don't**: urgency devices of any kind — see §6, these are hard-banned,
  not just off-voice.

---

## 4. Tone by funnel stage

| Stage | Register |
|---|---|
| Hero | Confident, spare — fewest words that still land the offer. |
| Problem | Specific and empathetic, not melodramatic — name the actual task and the actual hours, don't manufacture dread. |
| Offer | Matter-of-fact — a list of what's true, not a pitch. |
| How it works | Procedural — numbered, short, no adjectives doing persuasion work. |
| Trust/credibility | Quiet and evidence-first; where there's no evidence yet, say so plainly (see §6). |
| FAQ | Conversational but precise — answer in the first sentence, elaborate after. |
| CTA microcopy | Short, no exclamation points, no invented urgency. |
| Post-purchase | Relief and clarity — confirm what happened and what's next, nothing upsell-shaped. |

---

## 5. Color & type direction (brand-level mood — tokens stay with the designer)

This section is *not* new design direction — `design-specs/checkout-offer-page.md`
§1 already established a provisional token set, and it already reads as the
right mood. This section names *why* it's right, as the brand-level
rationale for `design/designer` (or whoever owns tokens) to keep tracking as
the page evolves, not a competing set of decisions.

- **Warm-neutral, not stark.** Paper-toned background over pure white,
  near-black over pure black. Stark black/white on a payment page reads
  either clinical (SaaS-dashboard cold) or unfinished (template default).
  Warm neutral reads considered.
- **One ink color, one accent — no gradient, no neon, no multi-color
  accent system.** A single deliberate accent used *only* for the action
  (the existing deep-teal "confirm/go" choice is correct) keeps the page
  reading as one decision, matching the funnel's actual structure (buy /
  don't buy).
- **No urgency palette anywhere** — no bright red/orange used
  decoratively or for emphasis. Reserve any red/orange entirely for genuine
  error states (network failure, form validation), never for persuasion.
  This is a color-level restatement of the no-dark-patterns rule in §6.
- **Type: system-ui stack, not a custom or display webfont.** This is a
  trust decision as much as a performance one: the fastest-painting,
  most platform-native font is also the one least likely to read as "someone
  picked a font to seem trustworthy" — invisible craft beats visible
  personality here. No rounded "friendly consumer app" geometric sans; no
  script/display anywhere.
- **Imagery: none by default.** No stock photography (people in a meeting,
  handshake, laptop-in-a-cafe) — it's the fastest way to make an honest page
  feel like a template. If imagery is added later, it should be product
  truth (an actual before/after of the automation running — a cluttered
  inbox next to a sorted one) never generic lifestyle stock.
- Net mood in one line: **this should feel like a well-built internal tool
  or Stripe's own Checkout, not a DTC subscription-box landing page.**

---

## 6. Trust-element rules (hard constraint — restated here as the brand-level policy)

No fabricated testimonials, fake customer logos, fake user/customer counts,
fake scarcity or countdown timers, and no confirm-shaming copy on any
decline/cancel path, anywhere in the funnel. This isn't a style preference —
it's the load-bearing trust mechanism for a page asking a stranger to pay a
solo, deliberately-anonymous operator before seeing the product work.

Where a testimonial, logo, or usage-count element would normally sit,
`funnel-copy.md`'s trust/credibility block writes it as an explicit
**structural placeholder** labeled for the operator to fill with real
material once it exists — never as invented content dressed up to look
real. See `funnel-copy.md` §Trust/credibility block for the actual copy and
a flagged recommendation on whether to render or hide that block pre-launch.

---

## 7. Open items flagged to `pm/project-manager`

1. **Voice-vs-anonymity reading** (§1): confirm PRD §6's identity-shielding
   intent extends to tone, not just legal-entity disclosure — this guide
   assumed yes and designed around it.
2. **Name lock**: `funnel-copy.md` is written to be a clean find-and-replace
   once a real name is chosen; nothing here should block on the name being
   finalized, but PM should track it before go-live copy is frozen (design
   spec §6 open item 3 flags the same gap from the designer's side).
3. **Trust-block render decision**: `funnel-copy.md` gives two honest
   options — ship the real, always-true process/security content now and
   *hide* the social-proof sub-block entirely until real testimonials exist,
   versus shipping a visibly-labeled "reviews coming soon" placeholder.
   Recommendation: hide until populated (a visible "coming soon" placeholder
   on a payment page reads as "nobody has bought this yet," which is its own
   small trust cost) — but this is a PM/growth call, not mine to force.
4. **SLA and price-band swap points**: `funnel-copy.md` uses bracketed
   slots (`[a few / N business days]`, the price band) per `product-brief.md`
   §"Swap points" — operator needs to confirm the real delivery SLA before
   this ships as final copy, not just the name.
5. **Guarantee/revision policy**: the FAQ in `funnel-copy.md` includes an
   objection ("what if I don't like what you build?") that needs a real
   policy answer (revision count, refund terms, or neither) — this guide
   left it as a slot rather than inventing a policy that would then be a
   binding commitment nobody signed off on.
