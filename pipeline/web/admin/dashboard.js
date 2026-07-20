/**
 * dashboard.js — owner-only analytics dashboard state machine.
 * Design spec: docs/sprint-7-26-19-26/design-specs/landing-funnel-and-dashboard.md §6-8.
 * Backend contract (pipeline/app/main.py):
 *   POST /admin/login {passcode}   -> 200 {status:"ok"} + owner_session cookie, or 401
 *   GET  /admin/metrics            -> {regions: [...], funnel: {...}}, 401 if unauthenticated
 *   GET  /admin/heatmap?path=/     -> {path, bin_size_pct, click_bins, scroll_depth_histogram}, 401 if unauthenticated
 *
 * States: locked -> (login) -> loading -> populated | insufficient-data | error.
 * No /admin/logout route exists in the current contract, so this build does
 * not offer a logout affordance that would silently fail to end the
 * httponly session cookie — flagged as a seam, not silently faked.
 */
(function () {
  "use strict";

  // Mirrors pricing_engine.py's MIN_CONVERSIONS gate (per-arm minimum
  // before a region can be read as anything but "gathering data"). This
  // view does NOT reimplement the engine's posterior/statistical-
  // significance test — it only enforces the sample-size floor, and never
  // renders a "winner" pill (see #view-pricing caveat copy).
  var MIN_CONVERSIONS = 50;

  var el = {
    loginView: document.getElementById("login-view"),
    loginForm: document.getElementById("login-form"),
    passcodeInput: document.getElementById("passcode-input"),
    loginError: document.getElementById("login-error"),
    loginSubmit: document.getElementById("login-submit"),
    loginSubmitLabel: document.getElementById("login-submit-label"),
    loginSpinner: document.getElementById("login-spinner"),

    dashboardShell: document.getElementById("dashboard-shell"),
    lastUpdated: document.getElementById("last-updated"),
    mainContent: document.getElementById("main-content"),

    railLinks: Array.prototype.slice.call(document.querySelectorAll(".rail-link")),

    viewLoading: document.getElementById("view-loading"),
    viewError: document.getElementById("view-error"),
    viewErrorMessage: document.getElementById("view-error-message"),
    retryButton: document.getElementById("retry-button"),

    viewOverview: document.getElementById("view-overview"),
    overviewEmpty: document.getElementById("overview-empty"),
    kpiRow: document.getElementById("kpi-row"),
    overviewRegions: document.getElementById("overview-regions"),

    viewPricing: document.getElementById("view-pricing"),
    pricingEmpty: document.getElementById("pricing-empty"),
    pricingTableWrap: document.getElementById("pricing-table-wrap"),

    viewFunnel: document.getElementById("view-funnel"),
    funnelEmpty: document.getElementById("funnel-empty"),
    funnelBars: document.getElementById("funnel-bars"),

    viewHeatmap: document.getElementById("view-heatmap"),
    heatmapPathForm: document.getElementById("heatmap-path-form"),
    heatmapPathInput: document.getElementById("heatmap-path-input"),
    heatmapEmpty: document.getElementById("heatmap-empty"),
    heatmapContent: document.getElementById("heatmap-content"),
    tabClick: document.getElementById("tab-click"),
    tabScroll: document.getElementById("tab-scroll"),
    panelClick: document.getElementById("panel-click"),
    panelScroll: document.getElementById("panel-scroll"),
    clickGrid: document.getElementById("click-grid"),
    scrollBands: document.getElementById("scroll-bands"),
    clickTableWrap: document.getElementById("click-table-wrap"),
    scrollTableWrap: document.getElementById("scroll-table-wrap"),
  };

  var allViews = [el.viewOverview, el.viewPricing, el.viewFunnel, el.viewHeatmap];
  var currentViewName = "overview";
  var latestMetrics = null;

  // --- helpers --------------------------------------------------------------

  function formatCurrency(cents) {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(
        cents / 100
      );
    } catch (e) {
      return "$" + (cents / 100).toFixed(2);
    }
  }

  function formatPct(n) {
    if (n === null || n === undefined || !isFinite(n)) return "—";
    return (n * 100).toFixed(1) + "%";
  }

  function el_(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  // --- LOGIN ------------------------------------------------------------

  function setLoginBusy(busy) {
    el.loginSubmit.disabled = busy;
    el.loginSpinner.hidden = !busy;
    el.loginSubmitLabel.textContent = busy ? "Signing in…" : "Sign in";
  }

  function showLoginError(message) {
    el.loginError.textContent = message;
    el.loginError.hidden = false;
  }

  function clearLoginError() {
    el.loginError.hidden = true;
    el.loginError.textContent = "";
  }

  function handleLoginSubmit(evt) {
    evt.preventDefault();
    clearLoginError();
    var passcode = el.passcodeInput.value;
    if (!passcode) {
      showLoginError("Enter the operator passcode.");
      return;
    }
    setLoginBusy(true);
    fetch("/admin/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ passcode: passcode }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("unauthorized");
        return res.json();
      })
      .then(function () {
        setLoginBusy(false);
        el.passcodeInput.value = "";
        enterDashboard();
      })
      .catch(function () {
        setLoginBusy(false);
        // Same message regardless of failure reason (bad passcode vs.
        // server misconfiguration) — mirrors owner_auth.py's own posture
        // of not signaling which is which.
        showLoginError("Invalid passcode. Try again.");
        el.passcodeInput.focus();
      });
  }

  // --- VIEW SWITCHING ---------------------------------------------------

  function showView(name) {
    currentViewName = name;
    allViews.forEach(function (v) {
      v.hidden = v.id !== "view-" + name;
    });
    el.railLinks.forEach(function (btn) {
      if (btn.dataset.view === name) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });
    if (name === "heatmap" && latestMetrics) {
      loadHeatmap(el.heatmapPathInput.value || "/");
    }
  }

  el.railLinks.forEach(function (btn) {
    btn.addEventListener("click", function () {
      showView(btn.dataset.view);
    });
  });

  // --- DASHBOARD DATA LOAD ------------------------------------------------

  function setLoadingState() {
    el.viewLoading.hidden = false;
    el.viewError.hidden = true;
    allViews.forEach(function (v) {
      v.hidden = true;
    });
  }

  function setErrorState(message) {
    el.viewLoading.hidden = true;
    el.viewError.hidden = false;
    el.viewErrorMessage.textContent = message;
    allViews.forEach(function (v) {
      v.hidden = true;
    });
  }

  function setPopulatedState() {
    el.viewLoading.hidden = true;
    el.viewError.hidden = true;
    showView(currentViewName);
  }

  function enterDashboard() {
    el.loginView.hidden = true;
    el.dashboardShell.hidden = false;
    el.mainContent.focus();
    fetchMetrics();
  }

  function fetchMetrics() {
    setLoadingState();
    fetch("/admin/metrics")
      .then(function (res) {
        if (res.status === 401) throw new Error("unauthorized");
        if (!res.ok) throw new Error("http-" + res.status);
        return res.json();
      })
      .then(function (data) {
        latestMetrics = data;
        renderOverview(data);
        renderPricing(data);
        renderFunnel(data);
        setPopulatedState();
        el.lastUpdated.textContent = "Updated " + new Date().toLocaleTimeString();
        if (currentViewName === "heatmap") loadHeatmap(el.heatmapPathInput.value || "/");
      })
      .catch(function (err) {
        if (err.message === "unauthorized") {
          // Session expired mid-visit: fall back to the login wall rather
          // than a confusing error banner.
          el.dashboardShell.hidden = true;
          el.loginView.hidden = false;
          return;
        }
        setErrorState(
          "Could not load dashboard data. Check your connection and try again."
        );
      });
  }

  el.retryButton.addEventListener("click", fetchMetrics);

  // --- OVERVIEW -----------------------------------------------------------

  function regionRollup(regions) {
    // Groups the flat (region, price_cents) rows the API returns into one
    // entry per region, since region_metrics() can return multiple arms
    // (price points) tried in the same region over time.
    var byRegion = {};
    regions.forEach(function (row) {
      if (!byRegion[row.region]) byRegion[row.region] = [];
      byRegion[row.region].push(row);
    });
    return byRegion;
  }

  function regionStatus(arms) {
    var trials = 0,
      conversions = 0,
      revenue = 0;
    arms.forEach(function (a) {
      trials += a.trials;
      conversions += a.conversions;
      revenue += a.revenue_cents;
    });
    // Below the pricing engine's own minimum-conversion gate: neutral
    // "gathering data" state, deliberately not a status-warning color
    // (design spec §6.3 — this is normal early-experiment phase, not a
    // state that needs attention).
    var belowMinSample = conversions < MIN_CONVERSIONS;
    return { trials: trials, conversions: conversions, revenue: revenue, belowMinSample: belowMinSample };
  }

  function renderStatusPill(belowMinSample) {
    var pill = el_("span", "status-pill " + (belowMinSample ? "status-neutral" : "status-warning"));
    var icon = el_("span", "status-icon", belowMinSample ? "○" : "▲");
    icon.setAttribute("aria-hidden", "true");
    var label = el_("span", null, belowMinSample ? "Gathering data" : "Trending");
    pill.appendChild(icon);
    pill.appendChild(label);
    return pill;
  }

  function isEmptyMetrics(data) {
    var noRegionTraffic = !data.regions || data.regions.every(function (r) {
      return r.trials === 0;
    });
    var noFunnelTraffic = !data.funnel || data.funnel.pageview === 0;
    return noRegionTraffic && noFunnelTraffic;
  }

  function renderOverview(data) {
    el.kpiRow.innerHTML = "";
    el.overviewRegions.innerHTML = "";

    if (isEmptyMetrics(data)) {
      el.overviewEmpty.hidden = false;
      el.overviewEmpty.innerHTML =
        "<strong>Not enough traffic yet.</strong> No pageviews or price assignments have been recorded. Once visitors start arriving, KPIs and region status will appear here — this is an honest empty state, not an error.";
      return;
    }
    el.overviewEmpty.hidden = true;

    var byRegion = regionRollup(data.regions || []);
    var totalRevenue = 0,
      totalTrials = 0,
      totalConversions = 0,
      gatheringCount = 0,
      trendingCount = 0;
    Object.keys(byRegion).forEach(function (region) {
      var status = regionStatus(byRegion[region]);
      totalRevenue += status.revenue;
      totalTrials += status.trials;
      totalConversions += status.conversions;
      if (status.belowMinSample) gatheringCount++;
      else trendingCount++;
    });

    var funnel = data.funnel || { pageview: 0, cta_view: 0, cta_click: 0, order: 0 };

    var tiles = [
      { label: "Revenue collected", value: formatCurrency(totalRevenue) },
      {
        label: "Overall conversion",
        value: totalTrials > 0 ? formatPct(totalConversions / totalTrials) : "—",
        sub: totalTrials + " trials",
      },
      { label: "Orders", value: String(funnel.order) },
      {
        label: "Regions",
        value: String(gatheringCount + trendingCount),
        sub: gatheringCount + " gathering data · " + trendingCount + " trending",
      },
    ];
    tiles.forEach(function (t) {
      var tile = el_("div", "stat-tile");
      tile.appendChild(el_("span", "stat-label", t.label));
      tile.appendChild(el_("p", "stat-figure", t.value));
      if (t.sub) tile.appendChild(el_("p", "stat-sub", t.sub));
      el.kpiRow.appendChild(tile);
    });

    var heading = el_("h3", null, "Regions at a glance");
    el.overviewRegions.appendChild(heading);
    var list = el_("div");
    Object.keys(byRegion)
      .sort()
      .forEach(function (region) {
        var status = regionStatus(byRegion[region]);
        var row = el_("div", "funnel-stage-label");
        var label = el_("span", null, region + " — " + status.trials + " trials, " + formatCurrency(status.revenue));
        row.appendChild(label);
        row.appendChild(renderStatusPill(status.belowMinSample));
        list.appendChild(row);
      });
    el.overviewRegions.appendChild(list);
  }

  // --- PRICING --------------------------------------------------------------

  function renderPricing(data) {
    el.pricingTableWrap.innerHTML = "";
    var regions = data.regions || [];
    if (regions.length === 0 || regions.every(function (r) { return r.trials === 0; })) {
      el.pricingEmpty.hidden = false;
      el.pricingEmpty.innerHTML =
        "<strong>Not enough traffic yet.</strong> No visitor has been assigned a price in any region, so there is nothing to compare — this is expected before launch traffic arrives.";
      return;
    }
    el.pricingEmpty.hidden = true;

    var byRegion = regionRollup(regions);
    var table = document.createElement("table");
    var thead = document.createElement("thead");
    thead.innerHTML =
      "<tr><th>Region</th><th>Status</th><th class=\"numeral\">Trials</th><th class=\"numeral\">Conversions</th><th class=\"numeral\">Conversion rate</th><th class=\"numeral\">Revenue</th></tr>";
    table.appendChild(thead);
    var tbody = document.createElement("tbody");

    Object.keys(byRegion)
      .sort()
      .forEach(function (region) {
        var arms = byRegion[region].slice().sort(function (a, b) {
          return a.price_cents - b.price_cents;
        });
        var status = regionStatus(arms);
        var primary = arms[0];
        var tr = document.createElement("tr");
        var rate = primary.trials > 0 ? primary.conversions / primary.trials : null;
        tr.innerHTML =
          "<td>" +
          region +
          "</td><td></td><td class=\"numeral\">" +
          status.trials +
          "</td><td class=\"numeral\">" +
          status.conversions +
          "</td><td class=\"numeral\">" +
          formatPct(status.trials > 0 ? status.conversions / status.trials : null) +
          "</td><td class=\"numeral\">" +
          formatCurrency(status.revenue) +
          "</td>";
        tr.children[1].appendChild(renderStatusPill(status.belowMinSample));
        tbody.appendChild(tr);

        if (arms.length > 0) {
          var detailsRow = document.createElement("tr");
          var detailsCell = document.createElement("td");
          detailsCell.colSpan = 6;
          var details = document.createElement("details");
          details.className = "arm-history";
          var summary = document.createElement("summary");
          summary.textContent = "View all price points tested (" + arms.length + ")";
          details.appendChild(summary);
          var innerTable = document.createElement("table");
          innerTable.innerHTML =
            "<thead><tr><th class=\"numeral\">Price</th><th class=\"numeral\">Trials</th><th class=\"numeral\">Conversions</th><th class=\"numeral\">Revenue</th></tr></thead>";
          var innerBody = document.createElement("tbody");
          arms.forEach(function (arm) {
            var row = document.createElement("tr");
            row.innerHTML =
              "<td class=\"numeral\">" +
              formatCurrency(arm.price_cents) +
              "</td><td class=\"numeral\">" +
              arm.trials +
              "</td><td class=\"numeral\">" +
              arm.conversions +
              "</td><td class=\"numeral\">" +
              formatCurrency(arm.revenue_cents) +
              "</td>";
            innerBody.appendChild(row);
          });
          innerTable.appendChild(innerBody);
          details.appendChild(innerTable);
          detailsCell.appendChild(details);
          detailsRow.appendChild(detailsCell);
          tbody.appendChild(detailsRow);
        }
      });

    table.appendChild(tbody);
    el.pricingTableWrap.appendChild(table);
  }

  // --- FUNNEL ---------------------------------------------------------------

  function renderFunnel(data) {
    el.funnelBars.innerHTML = "";
    var funnel = data.funnel || { pageview: 0, cta_view: 0, cta_click: 0, order: 0 };
    if (funnel.pageview === 0) {
      el.funnelEmpty.hidden = false;
      el.funnelEmpty.innerHTML =
        "<strong>Not enough traffic yet.</strong> No pageviews recorded, so there is no funnel to show.";
      return;
    }
    el.funnelEmpty.hidden = true;

    var stages = [
      { label: "Pageview", count: funnel.pageview },
      { label: "CTA viewed", count: funnel.cta_view },
      { label: "CTA clicked", count: funnel.cta_click },
      { label: "Order completed", count: funnel.order },
    ];
    var max = stages[0].count || 1;
    var prev = null;
    stages.forEach(function (stage) {
      var row = el_("div", "funnel-stage");
      var labelRow = el_("div", "funnel-stage-label");
      labelRow.appendChild(el_("span", null, stage.label));
      labelRow.appendChild(el_("strong", null, String(stage.count)));
      row.appendChild(labelRow);

      var track = el_("div", "funnel-bar-track");
      var fill = el_("div", "funnel-bar-fill");
      var pct = max > 0 ? Math.max(0, Math.min(100, (stage.count / max) * 100)) : 0;
      fill.style.width = pct + "%";
      track.appendChild(fill);
      row.appendChild(track);

      if (prev !== null) {
        var dropPct = prev > 0 ? (1 - stage.count / prev) * 100 : null;
        var dropText =
          dropPct === null
            ? "no prior-stage sessions to compare"
            : dropPct.toFixed(1) + "% drop from previous stage";
        row.appendChild(el_("p", "funnel-drop", dropText));
      }
      prev = stage.count;
      el.funnelBars.appendChild(row);
    });
  }

  // --- HEATMAP ----------------------------------------------------------

  function heatColorIndex(value, max) {
    if (max <= 0) return 0;
    var ratio = value / max;
    return Math.min(4, Math.round(ratio * 4));
  }

  function loadHeatmap(path) {
    el.heatmapContent.hidden = true;
    el.heatmapEmpty.hidden = true;
    fetch("/admin/heatmap?path=" + encodeURIComponent(path))
      .then(function (res) {
        if (res.status === 401) throw new Error("unauthorized");
        if (!res.ok) throw new Error("http-" + res.status);
        return res.json();
      })
      .then(renderHeatmap)
      .catch(function (err) {
        if (err.message === "unauthorized") {
          el.dashboardShell.hidden = true;
          el.loginView.hidden = false;
          return;
        }
        el.heatmapEmpty.hidden = false;
        el.heatmapEmpty.innerHTML =
          "<strong>Could not load heatmap data.</strong> Try again, or check the path.";
      });
  }

  function renderHeatmap(data) {
    var clickBins = data.click_bins || [];
    var scrollHist = data.scroll_depth_histogram || [];

    if (clickBins.length === 0 && scrollHist.length === 0) {
      el.heatmapEmpty.hidden = false;
      el.heatmapEmpty.innerHTML =
        "<strong>Not enough interaction data yet for " +
        (data.path || "this path") +
        ".</strong> No click or scroll events have been captured on this path yet.";
      el.heatmapContent.hidden = true;
      return;
    }
    el.heatmapEmpty.hidden = true;
    el.heatmapContent.hidden = false;

    renderClickGrid(data, clickBins);
    renderScrollBands(scrollHist);
    renderClickTable(clickBins);
    renderScrollTable(scrollHist);
  }

  function renderClickGrid(data, clickBins) {
    var binSize = data.bin_size_pct || 10;
    var cols = Math.max(1, Math.round(100 / binSize));
    var rows = cols;
    el.clickGrid.style.gridTemplateColumns = "repeat(" + cols + ", 1fr)";
    el.clickGrid.style.gridTemplateRows = "repeat(" + rows + ", 1fr)";
    el.clickGrid.innerHTML = "";

    var counts = {};
    var max = 0;
    clickBins.forEach(function (b) {
      counts[b.x_bin + "," + b.y_bin] = b.count;
      if (b.count > max) max = b.count;
    });

    for (var y = 0; y < rows; y++) {
      for (var x = 0; x < cols; x++) {
        var count = counts[x + "," + y] || 0;
        var cell = el_("div", "click-cell");
        if (count > 0) {
          cell.classList.add("heat-" + heatColorIndex(count, max));
        }
        el.clickGrid.appendChild(cell);
      }
    }
  }

  function renderScrollBands(scrollHist) {
    el.scrollBands.innerHTML = "";
    if (scrollHist.length === 0) return;
    var max = 0;
    scrollHist.forEach(function (b) {
      if (b.sessions > max) max = b.sessions;
    });
    var sorted = scrollHist.slice().sort(function (a, b) {
      return a.bucket_pct - b.bucket_pct;
    });
    sorted.forEach(function (bucket) {
      var row = el_("div", "scroll-band-row");
      row.appendChild(el_("span", "scroll-band-label", bucket.bucket_pct + "%+"));
      var track = el_("div", "scroll-band-track");
      var fill = el_("div", "scroll-band-fill");
      var pct = max > 0 ? (bucket.sessions / max) * 100 : 0;
      fill.style.width = pct + "%";
      // Fewer sessions reaching this depth => darker/more-saturated
      // (design spec §6.5: deepest-reached band both smallest AND darkest).
      var idx = max > 0 ? Math.round((1 - bucket.sessions / max) * 4) : 0;
      fill.classList.add("heat-" + idx);
      track.appendChild(fill);
      row.appendChild(track);
      el.scrollBands.appendChild(row);
    });
  }

  function renderClickTable(clickBins) {
    el.clickTableWrap.innerHTML = "";
    if (clickBins.length === 0) {
      el.clickTableWrap.appendChild(el_("p", "view-caveat", "No click events recorded on this path yet."));
      return;
    }
    var top = clickBins
      .slice()
      .sort(function (a, b) {
        return b.count - a.count;
      })
      .slice(0, 5);
    var table = document.createElement("table");
    table.innerHTML =
      "<thead><tr><th>Zone (x, y bin)</th><th class=\"numeral\">Clicks</th></tr></thead>";
    var tbody = document.createElement("tbody");
    top.forEach(function (bin) {
      var row = document.createElement("tr");
      row.innerHTML =
        "<td>col " + bin.x_bin + ", row " + bin.y_bin + "</td><td class=\"numeral\">" + bin.count + "</td>";
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    el.clickTableWrap.appendChild(table);
  }

  function renderScrollTable(scrollHist) {
    el.scrollTableWrap.innerHTML = "";
    if (scrollHist.length === 0) {
      el.scrollTableWrap.appendChild(el_("p", "view-caveat", "No scroll events recorded on this path yet."));
      return;
    }
    // Percent-of-sessions-reaching is approximated against the shallowest
    // bucket present (best available proxy for "sessions who loaded the
    // page" from this endpoint — true top-of-page session count is not a
    // separate field in this contract).
    var sorted = scrollHist.slice().sort(function (a, b) {
      return a.bucket_pct - b.bucket_pct;
    });
    var base = sorted[0].sessions || 1;
    var table = document.createElement("table");
    table.innerHTML =
      "<thead><tr><th>Depth</th><th class=\"numeral\">Sessions</th><th class=\"numeral\">% of shallowest bucket</th></tr></thead>";
    var tbody = document.createElement("tbody");
    sorted.forEach(function (bucket) {
      var row = document.createElement("tr");
      row.innerHTML =
        "<td>" +
        bucket.bucket_pct +
        "%+ scrolled</td><td class=\"numeral\">" +
        bucket.sessions +
        "</td><td class=\"numeral\">" +
        formatPct(bucket.sessions / base) +
        "</td>";
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    el.scrollTableWrap.appendChild(table);
  }

  function switchHeatmapLayer(layer) {
    var isClick = layer === "click";
    el.tabClick.setAttribute("aria-selected", isClick ? "true" : "false");
    el.tabClick.tabIndex = isClick ? 0 : -1;
    el.tabScroll.setAttribute("aria-selected", isClick ? "false" : "true");
    el.tabScroll.tabIndex = isClick ? -1 : 0;
    el.panelClick.hidden = !isClick;
    el.panelScroll.hidden = isClick;
  }

  [el.tabClick, el.tabScroll].forEach(function (tab) {
    tab.addEventListener("click", function () {
      switchHeatmapLayer(tab.dataset.layer);
      tab.focus();
    });
  });

  var tablistEl = document.querySelector(".tablist");
  tablistEl.addEventListener("keydown", function (evt) {
    if (evt.key !== "ArrowLeft" && evt.key !== "ArrowRight") return;
    evt.preventDefault();
    var next = evt.key === "ArrowLeft" ? el.tabClick : el.tabScroll;
    switchHeatmapLayer(next.dataset.layer);
    next.focus();
  });

  el.heatmapPathForm.addEventListener("submit", function (evt) {
    evt.preventDefault();
    var path = el.heatmapPathInput.value.trim() || "/";
    if (!path.startsWith("/")) path = "/" + path;
    el.heatmapPathInput.value = path;
    loadHeatmap(path);
  });

  // --- boot -------------------------------------------------------------

  el.loginForm.addEventListener("submit", handleLoginSubmit);

  function boot() {
    // No session-check endpoint exists in the contract (only /admin/login
    // and 401-gated reads), so this build always starts at the login wall
    // rather than guessing whether a prior cookie is still valid — an
    // unnecessary /admin/metrics probe on every page load would also be a
    // needless authenticated read against a state we can't yet render
    // anything from.
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
