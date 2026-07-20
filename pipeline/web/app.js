/**
 * app.js — offer/checkout page state machine.
 * Implements docs/sprint-7-26-19-26/design-specs/checkout-offer-page.md §3/§5
 * against the fixed interface contract:
 *   POST /assign (no body)         -> { variant_id, price_cents, currency, region, disclosure }
 *   POST /create-checkout (no body) -> { checkout_url }
 * States: loading -> ready | fallback | degraded, plus post_checkout: success | cancel.
 */
(function () {
  "use strict";

  var COPY = window.OFFER_COPY;
  var STORAGE_KEY = "offerAssignment.v1";

  // --- element refs ---------------------------------------------------------
  var el = {
    offerView: document.getElementById("offer-view"),
    successView: document.getElementById("success-view"),
    offerHeading: document.getElementById("offer-heading"),
    valueProp: document.querySelector(".value-prop"),
    priceBlock: document.getElementById("price-block"),
    priceLabel: document.getElementById("price-label"),
    priceNumber: document.getElementById("price-number"),
    priceSkeleton: document.getElementById("price-skeleton"),
    degradedMessage: document.getElementById("degraded-message"),
    disclosureText: document.getElementById("disclosure-text-content"),
    privacyLink: document.getElementById("privacy-link"),
    ctaButton: document.getElementById("cta-button"),
    ctaLabel: document.getElementById("cta-label"),
    ctaSpinner: document.getElementById("cta-spinner"),
    ctaLoadingNote: document.getElementById("cta-loading-note"),
    stripeNote: document.getElementById("stripe-note"),
    footerPrivacy: document.getElementById("footer-privacy"),
    footerTerms: document.getElementById("footer-terms"),
    footerContact: document.getElementById("footer-contact"),
    cancelAnnouncement: document.getElementById("cancel-announcement"),
    successHeading: document.getElementById("success-heading"),
    successPurchaseLine: document.getElementById("success-purchase-line"),
    successPriceLine: document.getElementById("success-price-line"),
    successReceiptNote: document.getElementById("success-receipt-note"),
    successNextSteps: document.getElementById("success-next-steps"),

    // --- funnel (MT-30) ---
    skipLink: document.getElementById("skip-link"),
    headerWordmark: document.getElementById("header-wordmark"),
    headerNavLink: document.getElementById("header-nav-link"),
    heroHeading: document.getElementById("hero-heading"),
    heroSubhead: document.getElementById("hero-subhead"),
    heroCta: document.getElementById("hero-cta"),
    heroMicrotrust: document.getElementById("hero-microtrust"),
    problemHeading: document.getElementById("problem-heading"),
    problemBody: document.getElementById("problem-body"),
    offerValueHeading: document.getElementById("offer-value-heading"),
    offerItems: document.getElementById("offer-items"),
    offerCloser: document.getElementById("offer-closer"),
    howHeading: document.getElementById("how-heading"),
    howSteps: document.getElementById("how-steps"),
    trustHeading: document.getElementById("trust-heading"),
    trustGrid: document.getElementById("trust-grid"),
    trustSocialProof: document.getElementById("trust-social-proof"),
    socialProofHeading: document.getElementById("social-proof-heading"),
    socialProofText: document.getElementById("social-proof-text"),
    faqHeading: document.getElementById("faq-heading"),
    faqList: document.getElementById("faq-list"),
  };

  var submitting = false; // guards against double checkout-session creation

  // --- static copy (loaded once, independent of fetch state) ---------------
  function paintStaticCopy() {
    el.offerHeading.textContent = COPY.OFFER_NAME;
    el.valueProp.textContent = COPY.VALUE_PROP;
    el.ctaLabel.textContent = COPY.CTA_LABEL;
    el.ctaLoadingNote.textContent = COPY.CTA_LOADING_NOTE;
    el.stripeNote.textContent = COPY.STRIPE_NOTE;
    el.priceLabel.textContent = COPY.PRICE_LABEL;
    el.privacyLink.textContent = COPY.PRIVACY_LINK_TEXT;
    el.privacyLink.href = COPY.PRIVACY_HREF;
    el.footerPrivacy.href = COPY.PRIVACY_HREF;
    el.footerTerms.href = COPY.TERMS_HREF;
    el.footerContact.href = COPY.CONTACT_HREF;
  }

  // --- funnel sections (MT-30) — static markup, no fetch, no state machine.
  // Content sourced from copy.js (single source of truth) per the design
  // spec's handoff note: never hardcode marketing strings into components.
  function paintFunnelCopy() {
    // Header + skip link
    el.headerWordmark.textContent = COPY.HEADER_WORDMARK;
    el.headerNavLink.textContent = COPY.HEADER_NAV_LINK;
    el.skipLink.textContent = COPY.SKIP_LINK;

    // Hero
    el.heroHeading.textContent = COPY.HERO_H1;
    el.heroSubhead.textContent = COPY.HERO_SUBHEAD;
    el.heroCta.textContent = COPY.HERO_CTA;
    el.heroMicrotrust.textContent = COPY.HERO_MICROTRUST;

    // Problem
    el.problemHeading.textContent = COPY.PROBLEM_H2;
    [COPY.PROBLEM_P1, COPY.PROBLEM_P2, COPY.PROBLEM_P3, COPY.PROBLEM_P4].forEach(
      function (text) {
        var p = document.createElement("p");
        p.textContent = text;
        el.problemBody.appendChild(p);
      }
    );

    // Offer
    el.offerValueHeading.textContent = COPY.OFFER_H2;
    COPY.OFFER_ITEMS.forEach(function (text) {
      var li = document.createElement("li");
      li.textContent = text;
      el.offerItems.appendChild(li);
    });
    el.offerCloser.textContent = COPY.OFFER_CLOSER;

    // How it works — numbered badges are decorative (aria-hidden); the
    // ordinal is carried in real text ("Step N: ...") per the a11y
    // checklist, never conveyed by badge shape/color alone.
    el.howHeading.textContent = COPY.HOW_H2;
    COPY.HOW_STEPS.forEach(function (step, idx) {
      var li = document.createElement("li");
      li.className = "how-step";

      var badge = document.createElement("span");
      badge.className = "how-step-badge";
      badge.setAttribute("aria-hidden", "true");
      badge.textContent = String(idx + 1);
      li.appendChild(badge);

      var label = document.createElement("p");
      label.className = "how-step-label";
      label.textContent = "Step " + (idx + 1) + ": " + step.label;
      li.appendChild(label);

      var detail = document.createElement("p");
      detail.className = "how-step-detail";
      detail.textContent = step.detail;
      li.appendChild(detail);

      el.howSteps.appendChild(li);
    });

    // Trust / credibility
    el.trustHeading.textContent = COPY.TRUST_H2;
    var trustPairs = [
      [COPY.TRUST_WHO_LABEL, COPY.TRUST_WHO_TEXT],
      [COPY.TRUST_INCLUDED_LABEL, COPY.TRUST_INCLUDED_TEXT],
      [COPY.TRUST_NOT_INCLUDED_LABEL, COPY.TRUST_NOT_INCLUDED_TEXT],
      // Payments line reuses STRIPE_NOTE verbatim (funnel-copy.md) — same
      // fact said twice at two points in the funnel is reinforcement, not
      // redundancy, on a page whose entire job is one purchase decision.
      [COPY.TRUST_PAYMENTS_LABEL, COPY.STRIPE_NOTE],
      [COPY.TRUST_PRICING_LABEL, COPY.TRUST_PRICING_TEXT],
      [COPY.TRUST_PROCESS_LABEL, COPY.TRUST_PROCESS_TEXT],
    ];
    trustPairs.forEach(function (pair) {
      // dt/dd wrapped in a div (valid per the HTML5 <dl> content model) so
      // each label+text pair stays together as one grid cell instead of
      // the grid auto-placing dt/dd as separate flow items.
      var item = document.createElement("div");
      item.className = "trust-item";
      var dt = document.createElement("dt");
      dt.textContent = pair[0];
      var dd = document.createElement("dd");
      dd.textContent = pair[1];
      item.appendChild(dt);
      item.appendChild(dd);
      el.trustGrid.appendChild(item);
    });

    // Social proof — structural placeholder, hidden by default (§0.1,
    // brand-guide.md §7.3). Left in the DOM (not deleted) so populating it
    // later is a data/CSS change, not a markup change.
    el.socialProofHeading.textContent = COPY.TRUST_SOCIAL_PROOF_LABEL;
    el.socialProofText.textContent = COPY.TRUST_SOCIAL_PROOF_PLACEHOLDER;

    // FAQ — real accordion: <h3><button aria-expanded aria-controls></button></h3>
    // + a panel via aria-labelledby. Closed by default, none pre-opened.
    el.faqHeading.textContent = COPY.FAQ_H2;
    COPY.FAQ_ITEMS.forEach(function (item, idx) {
      var wrapper = document.createElement("div");
      wrapper.className = "faq-item";

      var h3 = document.createElement("h3");
      h3.className = "faq-question";

      var triggerId = "faq-trigger-" + idx;
      var panelId = "faq-panel-" + idx;

      var trigger = document.createElement("button");
      trigger.type = "button";
      trigger.className = "faq-trigger";
      trigger.id = triggerId;
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-controls", panelId);

      var triggerText = document.createElement("span");
      triggerText.textContent = item.q;
      trigger.appendChild(triggerText);

      var triggerIcon = document.createElement("span");
      triggerIcon.className = "faq-trigger-icon";
      triggerIcon.setAttribute("aria-hidden", "true");
      triggerIcon.textContent = "+";
      trigger.appendChild(triggerIcon);

      h3.appendChild(trigger);
      wrapper.appendChild(h3);

      var panel = document.createElement("div");
      panel.className = "faq-panel";
      panel.id = panelId;
      panel.setAttribute("role", "region");
      panel.setAttribute("aria-labelledby", triggerId);
      panel.hidden = true;

      var answerP = document.createElement("p");
      answerP.textContent = item.a;
      panel.appendChild(answerP);

      if (item.linkText === "PRIVACY_LINK_TEXT") {
        var link = document.createElement("a");
        link.href = COPY.PRIVACY_HREF;
        link.textContent = COPY.PRIVACY_LINK_TEXT;
        answerP.appendChild(document.createTextNode(" "));
        answerP.appendChild(link);
      }

      wrapper.appendChild(panel);
      el.faqList.appendChild(wrapper);

      trigger.addEventListener("click", function () {
        var expanded = trigger.getAttribute("aria-expanded") === "true";
        trigger.setAttribute("aria-expanded", expanded ? "false" : "true");
        panel.hidden = expanded;
        // Focus stays on the trigger after toggle (a11y checklist §5) —
        // no explicit focus() call needed since the click already left
        // focus there; this comment documents the intentional no-op.
      });
    });

    // Anchor CTAs (hero → pricing, header → pricing): real in-page
    // navigation styled as buttons. After activation, move focus to
    // #price-block so keyboard/AT users land where sighted users land
    // (a11y checklist §5), not just scroll past it.
    [el.heroCta, el.headerNavLink].forEach(function (anchor) {
      anchor.addEventListener("click", function () {
        window.requestAnimationFrame(function () {
          el.priceBlock.focus();
        });
      });
    });
  }

  function formatPrice(priceCents, currency) {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: currency || "USD",
      }).format(priceCents / 100);
    } catch (e) {
      // Unknown/invalid currency code from the server — fall back to a
      // plain numeral rather than crashing the render.
      return (priceCents / 100).toFixed(2) + " " + (currency || "");
    }
  }

  // --- state renderers -------------------------------------------------------

  function renderLoading() {
    el.priceNumber.textContent = "";
    el.priceSkeleton.hidden = false;
    el.degradedMessage.hidden = true;
    el.disclosureText.textContent = COPY.DISCLOSURE_LOADING;
    setCtaEnabled(false, /*loading=*/ true);
  }

  function renderReady(assignment) {
    el.priceSkeleton.hidden = true;
    el.degradedMessage.hidden = true;
    el.priceNumber.textContent = formatPrice(assignment.price_cents, assignment.currency);
    el.disclosureText.textContent = assignment.disclosure;
    setCtaEnabled(true, /*loading=*/ false);
  }

  function renderDegraded() {
    el.priceSkeleton.hidden = true;
    el.priceNumber.textContent = "";
    el.degradedMessage.hidden = false;
    el.degradedMessage.textContent = COPY.DEGRADED_MESSAGE;
    el.disclosureText.textContent = COPY.DISCLOSURE_DEGRADED;
    setCtaEnabled(false, /*loading=*/ false);
  }

  function setCtaEnabled(enabled, loading) {
    el.ctaButton.setAttribute("aria-disabled", enabled ? "false" : "true");
    el.ctaSpinner.hidden = !loading;
    el.ctaButton.setAttribute(
      "aria-describedby",
      loading ? "disclosure-strip cta-loading-note" : "disclosure-strip"
    );
  }

  // --- persistence (no price flicker within a session; no re-roll) --------

  function loadPersisted() {
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function persist(assignment) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(assignment));
    } catch (e) {
      // sessionStorage unavailable (private mode, quota) — degrade to
      // re-fetching on reload rather than breaking the page.
    }
  }

  // --- /assign -----------------------------------------------------------

  function fetchAssignment() {
    renderLoading();
    fetch("/assign", { method: "POST" })
      .then(function (res) {
        if (!res.ok) throw new Error("assign: HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        if (
          !data ||
          typeof data.price_cents !== "number" ||
          typeof data.disclosure !== "string"
        ) {
          throw new Error("assign: malformed response");
        }
        persist(data);
        renderReady(data);
      })
      .catch(function () {
        // Network failure, non-2xx, or unparseable body: no server data to
        // render at all. Never fabricate a price — show the graceful
        // degraded state instead (never a broken page either).
        renderDegraded();
      });
  }

  // --- /create-checkout ----------------------------------------------------

  function startCheckout() {
    if (submitting || el.ctaButton.getAttribute("aria-disabled") === "true") {
      return; // no-op while loading/degraded/already-submitting — no double session
    }
    submitting = true;
    setCtaEnabled(false, /*loading=*/ true);

    fetch("/create-checkout", { method: "POST" })
      .then(function (res) {
        if (!res.ok) throw new Error("create-checkout: HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        if (!data || typeof data.checkout_url !== "string") {
          throw new Error("create-checkout: malformed response");
        }
        window.location = data.checkout_url;
      })
      .catch(function () {
        // Re-enable so the visitor can try again; no error banner, no
        // confirm-shaming, just return them to the same actionable state.
        submitting = false;
        var cached = loadPersisted();
        if (cached) {
          renderReady(cached);
        } else {
          renderDegraded();
        }
      });
  }

  el.ctaButton.addEventListener("click", startCheckout);
  el.ctaButton.addEventListener("keydown", function (evt) {
    if (
      (evt.key === "Enter" || evt.key === " ") &&
      el.ctaButton.getAttribute("aria-disabled") === "true"
    ) {
      evt.preventDefault(); // aria-disabled stays focusable; keep it inert
    }
  });

  // --- post-checkout return (§3.4) ------------------------------------------

  function renderSuccess() {
    el.offerView.hidden = true;
    el.successView.hidden = false;
    el.successHeading.textContent = COPY.SUCCESS_HEADING;
    el.successReceiptNote.textContent = COPY.SUCCESS_RECEIPT_NOTE;
    el.successNextSteps.textContent = COPY.SUCCESS_NEXT_STEPS;

    var cached = loadPersisted();
    if (cached && typeof cached.price_cents === "number") {
      el.successPurchaseLine.textContent = COPY.OFFER_NAME;
      el.successPriceLine.textContent =
        "Price paid: " + formatPrice(cached.price_cents, cached.currency);
    } else {
      // No persisted assignment for this session (e.g. cleared storage) —
      // never invent a price; show a generic, still-honest confirmation.
      el.successPurchaseLine.textContent = COPY.SUCCESS_NO_PRICE_FALLBACK;
      el.successPriceLine.textContent = "";
    }
  }

  function renderCancelReturn() {
    // Same Default-state offer page, no interstitial — reuse the session's
    // existing assignment rather than re-rolling (design spec §3.4/§5).
    el.cancelAnnouncement.textContent = COPY.CANCEL_ANNOUNCE;
    var cached = loadPersisted();
    if (cached) {
      renderReady(cached);
    } else {
      fetchAssignment();
    }
  }

  // --- boot ------------------------------------------------------------------

  function boot() {
    paintStaticCopy();
    paintFunnelCopy();

    var params = new URLSearchParams(window.location.search);
    var checkoutParam = params.get("checkout");

    if (checkoutParam === "success") {
      renderSuccess();
      return;
    }

    if (checkoutParam === "cancel") {
      renderCancelReturn();
      return;
    }

    var cached = loadPersisted();
    if (cached) {
      renderReady(cached); // reuse session assignment — no re-fetch, no flicker
    } else {
      fetchAssignment();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
