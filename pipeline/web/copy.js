/**
 * copy.js — structural copy constants for the offer/checkout page.
 *
 * Per docs/sprint-7-26-19-26/design-specs/checkout-offer-page.md §5:
 * "Do not hardcode the copy in [the disclosure component] — source it from
 * wherever MT-5's signed-off disclosure text lands." The regional-pricing
 * disclosure text for the RESOLVED (ready/fallback) states is sourced live
 * from the /assign response's `disclosure` field (server-authoritative) —
 * this file does NOT hardcode that legal copy, by design.
 *
 * This module holds only the copy needed BEFORE any server response exists
 * (loading) or when no server response exists at all (degraded/network
 * failure) plus page chrome that isn't legal disclosure text.
 *
 * FLAGGED — NOT CLEARED FOR SHIP (docs/backlog.md MT-5, status: todo;
 * design-specs/checkout-offer-page.md §6.1, §6.3):
 *   - OFFER_NAME / VALUE_PROP are neutral placeholders. The PRD and issue
 *     spec do not supply product/marketing copy (design spec §6.3) — do
 *     not treat these as final. Replace once the operator supplies real
 *     offer copy.
 *   - DISCLOSURE_LOADING is generic, non-legal copy taken verbatim from
 *     design spec §3.2 ("Prices vary by region. Finding your region's
 *     price…") — same structural shape as the final MT-5 copy but the
 *     specifics (state naming, lawful-basis wording) are MT-5's call, not
 *     baked in here.
 *   - Footer link hrefs (privacy notice, terms) point at routes that do
 *     not exist yet (MT-5 has not shipped the privacy notice page). Left
 *     as real, semantically-correct <a> targets rather than "#" so link
 *     semantics/keyboard behavior are correct now and the page needs no
 *     rework once those routes exist — but they 404 until then.
 *
 * MT-2 (this build) must not go live before MT-5 signs off — see
 * docs/backlog.md ("MT-5 ... todo (blocks MT-2 go-live)") and issue-spec
 * dependency line "#5 blocks #2".
 */

window.OFFER_COPY = Object.freeze({
  // --- Placeholder marketing copy (PM/operator to supply — design spec §6.3) ---
  // Working brand name — coined placeholder, swap before launch (see product-brief.md).
  OFFER_NAME: "Flowmark",
  VALUE_PROP: "One tedious workflow, automated for you — so you get those hours back for good.",

  // --- Structural, non-legal UI copy ---
  CTA_LABEL: "Continue to secure checkout",
  CTA_LOADING_NOTE: "Price is loading",
  STRIPE_NOTE: "Payments handled by Stripe. We never see or store your card details.",
  PRICE_LABEL: "One-time price:",

  // --- Funnel copy (MT-30) — source: docs/sprint-7-26-19-26/content/funnel-copy.md.
  // Verbatim per that doc; bracketed swap points ([a few business days], the
  // SLA/name/policy slots) are left in place intentionally — see the doc's
  // "Summary of swap points" section. Do not invent copy to fill them.

  // Hero (funnel-copy.md "Hero")
  HERO_H1: "Buy back the hours one task is stealing every week.",
  HERO_SUBHEAD:
    "We build one automation — matched to the specific process eating your " +
    "time — and deliver it working within a few business days. Pay once. " +
    "No software for you to learn, no subscription to manage.",
  HERO_CTA: "See your price",
  HERO_MICROTRUST:
    "One-time payment · Stripe secure checkout · Price varies openly by region",
  HEADER_WORDMARK: "Flowmark",
  HEADER_NAV_LINK: "See pricing",
  SKIP_LINK: "Skip to pricing",

  // Problem (funnel-copy.md "The problem, felt")
  PROBLEM_H2: "You already know which task this is.",
  PROBLEM_P1:
    "A lead messages you, and you mean to reply — but the reply waits for a " +
    "free five minutes that doesn't come until tomorrow, by which point " +
    "they've already messaged someone else.",
  PROBLEM_P2:
    "An invoice goes unpaid, not because the client won't pay, but because " +
    "nobody follows up until it's already awkward to bring up.",
  PROBLEM_P3:
    "You write one good post, and it gets used exactly once — when the same " +
    "twenty minutes of rewriting could have turned it into six.",
  PROBLEM_P4:
    "None of these takes long, on its own. That's exactly why it never gets " +
    "fixed. Multiply the five minutes by every lead, every week, and it " +
    "stops being a task — it's a second, unpaid job you never applied for.",

  // Offer (funnel-copy.md "The offer")
  OFFER_H2: "What you get",
  OFFER_ITEMS: [
    "One working automation, built around the tools you already use — your " +
      "CRM, inbox, forms, spreadsheet, or Slack, whatever you've actually " +
      "got, not a tool you have to switch to.",
    "AI handles the reading, drafting, routing, or summarizing; you stay in " +
      "control of what actually sends, or let it run on its own — your call, " +
      "set during intake.",
    "Delivered within a few business days of your intake form.",
    "One price, paid once. No subscription, no seats, no “AI credits” " +
      "to track or run out of.",
  ],
  OFFER_CLOSER:
    "This isn't a course, a template, or a tool you have to configure " +
    "yourself. It's a finished automation, built for your setup, handed to " +
    "you already working.",

  // How it works (funnel-copy.md "How it works (3 steps)")
  HOW_H2: "How it works",
  HOW_STEPS: [
    {
      label: "Pay, then tell us what's eating your time.",
      detail:
        "A short intake form — which task, which tools, and a couple of " +
        "real examples, so what we build fits your business instead of a " +
        "generic case.",
    },
    {
      label: "We build it against your actual tools.",
      detail:
        "The automation is wired to the CRM, inbox, spreadsheet, or Slack " +
        "you told us about — not a demo environment, not a template with " +
        "your logo dropped in.",
    },
    {
      label: "You get a working automation.",
      detail:
        "Delivered within a few business days, tested against the examples " +
        "you gave us, with a short walkthrough so you know how to turn it " +
        "off, adjust it, or ask for a change.",
    },
  ],

  // Trust / credibility (funnel-copy.md "Trust / credibility block")
  TRUST_H2: "Who you're trusting with this",
  TRUST_WHO_LABEL: "Who builds this",
  TRUST_WHO_TEXT:
    "A single operator with hands-on experience building exactly this kind " +
    "of automation — not an agency, not a team you'll get routed through. " +
    "One person, one build, direct communication if you have a question.",
  TRUST_INCLUDED_LABEL: "What's included",
  TRUST_INCLUDED_TEXT:
    "One automation, connected to the tools you specify at intake, " +
    "delivered working, plus a short walkthrough of how it runs.",
  TRUST_NOT_INCLUDED_LABEL: "What's not included",
  TRUST_NOT_INCLUDED_TEXT:
    "Ongoing subscription support, unrelated automations, or an open-ended " +
    "“AI assistant” — this is one workflow, done well, not a " +
    "general-purpose tool.",
  TRUST_PAYMENTS_LABEL: "Payments",
  // Reuses STRIPE_NOTE verbatim per funnel-copy.md — do not duplicate the string.
  TRUST_PRICING_LABEL: "Pricing transparency",
  TRUST_PRICING_TEXT:
    "We publish regional pricing openly instead of guessing what you'll " +
    "pay silently.",
  TRUST_PROCESS_LABEL: "Process transparency",
  TRUST_PROCESS_TEXT:
    "Three steps, start to finish: tell us the workflow, we build it " +
    "against your real tools, you get a working automation — with a " +
    "walkthrough so you know exactly what you're getting.",
  // Social-proof sub-block: structural placeholder only, per funnel-copy.md
  // and brand-guide.md §7.3 — recommended hidden pre-launch. Kept as a real,
  // hideable DOM node (not deleted) so it's a data/CSS change, not a markup
  // change, once real testimonials exist.
  TRUST_SOCIAL_PROOF_LABEL: "What buyers say",
  TRUST_SOCIAL_PROOF_PLACEHOLDER:
    "Real testimonials will appear here once buyers have used their " +
    "automations. We don't publish invented quotes or reviews.",

  // FAQ (funnel-copy.md "Objection-handling FAQ") — SLOT items (refund/revision
  // policy) are intentionally omitted; do not ship until a real policy exists.
  FAQ_H2: "Questions worth asking before you pay",
  FAQ_ITEMS: [
    {
      q: "Will this actually work for my business, or is it generic?",
      a:
        "The intake form asks for your real tools and a couple of real " +
        "examples of the task — the automation is built against those, not " +
        "a one-size-fits-all template. If your process is too unusual to " +
        "automate well, we'll tell you before building rather than deliver " +
        "something that doesn't fit.",
    },
    {
      q: "Is this a subscription? What happens after the automation is delivered?",
      a:
        "No — it's a one-time payment for one automation. There's no " +
        "recurring charge and nothing to cancel later. If the tools it " +
        "connects to change on your end (a new CRM, a new inbox), the " +
        "automation may need adjusting, but that's not a built-in " +
        "subscription.",
    },
    {
      q: "What tools does it actually connect to?",
      a:
        "Whatever you're already using — common CRMs, email/inbox " +
        "providers, form tools, spreadsheets, and Slack are all fair game. " +
        "You tell us your stack at intake; we build to it rather than " +
        "asking you to adopt something new.",
    },
    {
      q: "Who is actually building this — a company, an agency, a person?",
      a:
        "One person, working directly on your build — not a call center, " +
        "not a team you get routed through.",
    },
    {
      q: "Is my information safe? What do you actually collect?",
      // DISCLOSURE — server-sourced text lives on the price card; this
      // answer links out to the privacy notice rather than restating it.
      a: "Full detail on what's collected — including region detection for pricing — lives in the privacy notice:",
      linkText: "PRIVACY_LINK_TEXT",
    },
    {
      q: "How long does delivery actually take?",
      a:
        "A few business days from when you submit the intake form — the " +
        "clock starts at intake, not at payment, since we need your " +
        "specifics before we can start building.",
    },
    {
      q: "Why does the price change depending on where I'm buying from?",
      // DISCLOSURE — server-sourced; do not restate the legal text here.
      a: "The price card below carries the live regional-pricing disclosure. See the full privacy notice for detail:",
      linkText: "PRIVACY_LINK_TEXT",
    },
  ],

  // CTA microcopy (funnel-copy.md "CTA microcopy")
  INTAKE_CTA: "Start your intake form",
  INTAKE_SUBHEAD:
    "Takes about 5 minutes. The more specific your examples, the closer " +
    "the first version will match what you actually need.",

  // Disclosure strip — loading state only (design spec §3.2, generic/true
  // regardless of which price resolves). Ready/fallback states use the
  // server-provided `disclosure` string instead of this file.
  DISCLOSURE_LOADING: "Prices vary by region. Finding your region’s price…",

  // Degraded state: /assign failed outright (network error, non-2xx, or an
  // unparseable response) — no server data at all to render. Per the build
  // brief: never fabricate a price here, show a graceful message instead.
  DISCLOSURE_DEGRADED: "Prices vary by region.",
  DEGRADED_MESSAGE: "We couldn’t load your price just now. Please refresh the page to try again.",

  PRIVACY_LINK_TEXT: "Full privacy notice →",
  PRIVACY_HREF: "/privacy-notice", // MT-5 not shipped yet; route does not exist yet.
  TERMS_HREF: "/terms",
  CONTACT_HREF: "/contact",

  // --- Post-checkout (design spec §3.4) ---
  SUCCESS_HEADING: "You’re all set",
  SUCCESS_RECEIPT_NOTE: "A receipt has been emailed to you.",
  SUCCESS_NEXT_STEPS: "What happens next: we’ll be in touch with setup details shortly.",
  SUCCESS_NO_PRICE_FALLBACK: "Your payment was received.",

  CANCEL_ANNOUNCE: "Checkout was canceled. Your price is unchanged.",
});
