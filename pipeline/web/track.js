/**
 * track.js — privacy-safe funnel instrumentation (MT-30 §2).
 *
 * Contract (POST /track, see pipeline/app/main.py):
 *   { event_type, path, x_pct, y_pct, scroll_pct, viewport_w }
 *   event_type in {"pageview","click","scroll","cta_view","cta_click"}
 *
 * Hard rules, restated from conversion-psychology-spec.md §5 and
 * opsec-gate F8:
 *   - No PII, no raw text, no keystrokes, no per-person replay. Only
 *     coordinates (as page-relative percentages), scroll depth, viewport
 *     width, and which page. The session identity is a cookie minted
 *     SERVER-SIDE (never sent by this script, never read by it) — this
 *     file has no notion of who a visitor is.
 *   - Must never block or break the funnel. Every send is best-effort;
 *     failures (network, /track unreachable, blocked by an extension)
 *     are swallowed silently, never surfaced to the visitor.
 */
(function () {
  "use strict";

  var ENDPOINT = "/track";
  var sectionsFired = Object.create(null);
  var ctaViewFired = false;

  function currentPath() {
    return window.location && window.location.pathname ? window.location.pathname : "/";
  }

  function docHeight() {
    var de = document.documentElement;
    var body = document.body;
    return Math.max(
      de ? de.scrollHeight : 0,
      de ? de.offsetHeight : 0,
      de ? de.clientHeight : 0,
      body ? body.scrollHeight : 0,
      body ? body.offsetHeight : 0,
      1
    );
  }

  function clampPct(n) {
    if (typeof n !== "number" || isNaN(n)) return 0;
    return Math.max(0, Math.min(100, Math.round(n)));
  }

  function scrollPct() {
    var doc = docHeight();
    var viewport = window.innerHeight || document.documentElement.clientHeight || 0;
    var scrollable = Math.max(doc - viewport, 1);
    var y = window.scrollY || window.pageYOffset || 0;
    return clampPct((y / scrollable) * 100);
  }

  // --- transport: best-effort, never throws, never blocks -----------------
  function send(eventType, extra) {
    var payload = {
      event_type: eventType,
      path: currentPath(),
      viewport_w: Math.round(window.innerWidth || document.documentElement.clientWidth || 0),
    };
    if (extra) {
      for (var key in extra) {
        if (Object.prototype.hasOwnProperty.call(extra, key)) {
          payload[key] = extra[key];
        }
      }
    }

    var body;
    try {
      body = JSON.stringify(payload);
    } catch (e) {
      return; // never let a serialization edge case throw into the funnel
    }

    try {
      if (navigator && typeof navigator.sendBeacon === "function") {
        var blob = new Blob([body], { type: "application/json" });
        var queued = navigator.sendBeacon(ENDPOINT, blob);
        if (queued) return;
      }
    } catch (e) {
      // fall through to fetch
    }

    try {
      if (typeof fetch === "function") {
        fetch(ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: body,
          credentials: "same-origin",
          keepalive: true,
        }).catch(function () {
          // /track unreachable or non-2xx — fail silently, never block
          // the funnel on analytics (MT-30 §2).
        });
      }
    } catch (e) {
      // fetch unavailable/blocked — fail silently.
    }
  }

  // --- pageview -------------------------------------------------------------
  function trackPageview() {
    send("pageview", { scroll_pct: 0 });
  }

  // --- scroll checkpoints at section boundaries (design spec §5, §6.5) -----
  function trackScrollCheckpoints() {
    if (typeof IntersectionObserver !== "function") return;
    var sections = document.querySelectorAll("[data-track-section]");
    if (!sections.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var name = entry.target.getAttribute("data-track-section");
          if (!name || sectionsFired[name]) return;
          sectionsFired[name] = true;
          send("scroll", { scroll_pct: scrollPct() });
        });
      },
      { threshold: 0 }
    );

    Array.prototype.forEach.call(sections, function (section) {
      observer.observe(section);
    });
  }

  // --- CTA view (fires once, when the purchase CTA enters view) -----------
  function trackCtaView() {
    var cta = document.getElementById("cta-button");
    if (!cta || typeof IntersectionObserver !== "function") return;

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !ctaViewFired) {
            ctaViewFired = true;
            send("cta_view", { scroll_pct: scrollPct() });
            obs.disconnect();
          }
        });
      },
      { threshold: 0.5 }
    );
    observer.observe(cta);
  }

  // --- CTA click ------------------------------------------------------------
  function trackCtaClick() {
    var cta = document.getElementById("cta-button");
    if (!cta) return;
    cta.addEventListener(
      "click",
      function () {
        send("cta_click", { scroll_pct: scrollPct() });
      },
      { passive: true }
    );
  }

  // --- click coordinates (aggregate density input; never per-element text) -
  function trackClicks() {
    document.addEventListener(
      "click",
      function (evt) {
        var vw = window.innerWidth || document.documentElement.clientWidth || 1;
        var doc = docHeight();
        var y = (window.scrollY || window.pageYOffset || 0) + evt.clientY;
        send("click", {
          x_pct: clampPct((evt.clientX / vw) * 100),
          y_pct: clampPct((y / doc) * 100),
          scroll_pct: scrollPct(),
        });
      },
      { passive: true }
    );
  }

  function boot() {
    try {
      trackPageview();
      trackScrollCheckpoints();
      trackCtaView();
      trackCtaClick();
      trackClicks();
    } catch (e) {
      // Instrumentation must never break the funnel it's watching.
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
