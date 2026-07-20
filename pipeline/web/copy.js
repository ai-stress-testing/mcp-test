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
  OFFER_NAME: "[Product name — placeholder pending operator copy]",
  VALUE_PROP: "[One-line value proposition — placeholder pending operator copy]",

  // --- Structural, non-legal UI copy ---
  CTA_LABEL: "Continue to secure checkout",
  CTA_LOADING_NOTE: "Price is loading",
  STRIPE_NOTE: "Payments handled by Stripe. We never see or store your card details.",
  PRICE_LABEL: "One-time price:",

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
