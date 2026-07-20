# Product brief — the offer behind the pipeline

Working name: **Flowmark** (placeholder — swap before launch; the machinery
doesn't depend on the name). This brief defines what the regional-pricing
pipeline actually sells, so the funnel content, design, and analytics are
built around a real offer instead of `[placeholder]`.

## The offer (one-time, self-serve, regionally priced)

**One tedious workflow, automated for you.** The operator (a solo builder with
coding/AI skills) builds *one* done-for-you automation that connects a small
business's existing tools — CRM, email, forms, spreadsheets, Slack — with AI
handling the routing, drafting, and summarizing. Buyer pays once at the
region-optimized price ($40–$150 by state via the pipeline), fills a short
intake, and receives the working automation within a few business days.

- **Not** a subscription, not a course, not a template dump. A finished,
  working automation delivered to the buyer.
- Fits self-serve Stripe checkout: the purchase is the commitment + payment;
  fulfillment follows via a short intake form.

## Who buys it

A small-business owner or solopreneur losing hours every week to one
repetitive manual process — lead follow-up, invoice chasing, content
repurposing, appointment reminders — who wants it gone but won't hire a
developer or learn n8n/Zapier themselves.

## The core promise (value prop)

**"Pay once. Get one workflow off your plate for good."** Time saved, not
software delivered. Concrete: "Save the 3–5 hours a week you spend on <the
thing>."

## Vertical scope (this build — funnel + instrumentation)

1. **A real conversion funnel** on the landing page (not a bare price card):
   hero → the problem, felt → the offer → how it works (3 steps) → proof/trust
   → objection-handling FAQ → the regional-priced CTA → checkout. Real copy,
   ethically persuasive, **no dark patterns**.
2. **Owner-only analytics** ("only I can view data"): the pricing experiment
   (per-region arm, conversion, revenue), orders, funnel drop-off, and
   **interaction heatmaps** (clicks + scroll depth) — privacy-safe, no PII,
   disclosed, and gated behind owner authentication.
3. **Design quality is a feature, not polish** — research says a product is
   assumed to be as good as it looks. The visual system must read as
   trustworthy on a payment page.

## Hard constraints (carried from the whole project)

- Transparent regional pricing only; no device/per-person pricing (cut at spec
  time). No dark patterns anywhere in the funnel.
- Heatmap/analytics capture: anonymous session id only, **no PII, no raw IP,
  no keystrokes/text**; disclosed in the privacy notice; owner-authenticated
  read path; aligns with the existing threat model + OPSEC gate.
- Disclosure/legal copy stays server-sourced and gated on MT-5 (legal).

## Swap points (before launch)

Brand name, the specific workflow examples, price band, and delivery SLA are
the operator's to set. Everything downstream is built to make those easy to
change, not hardcoded.
