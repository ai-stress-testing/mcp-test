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
