run-id: 2026-07-20-owner-dashboard-ui
prompt: "MT-31 — owner-only analytics dashboard UI."
agents:
  - frontend/react-dev (sonnet) — MT-31 dashboard build
specs: docs/sprint-7-26-19-26/design-specs/landing-funnel-and-dashboard.md
  §6-8; docs/sprint-7-26-19-26/content/conversion-psychology-spec.md §5;
  pipeline/app/main.py + store.py (backend contract, read-only reference)
verdicts: self-verified by the implementing agent (Playwright + axe-core,
  see below) — not yet reviewed by testing/accessibility-auditor per the
  design spec's gate (§5/§8), flagged in Blocked / carried
commits: (this commit)

# 2026-07-20 — Owner-only analytics dashboard UI (MT-31)

**Session/agent**: `frontend/react-dev` (sonnet).
**Issues touched**: MT-31 done (UI only, against the existing MT-29 backend
contract — no backend files touched).

## Done
- **`pipeline/web/admin/index.html`**: login view (locked state, no
  dashboard chrome visible behind it) + dashboard shell with a left-rail
  nav (Overview / Pricing / Funnel / Heatmap), each opening with
  summary-before-detail per design spec §6.2. Loading (static skeleton),
  error, and per-view empty states are separate DOM nodes, not CSS
  overlays, so screen readers never see stale content underneath.
- **`pipeline/web/admin/dashboard.css`**: adds only the design spec's
  §1/§2 `[NEW]` tokens (`--surface-2`, `--status-good/warning/critical`,
  `--heat-0..4`, `--text-*`/`--space-*` scale) on top of the unmodified
  `../styles.css` — the existing eight funnel tokens are reused verbatim,
  not touched.
- **`pipeline/web/admin/dashboard.js`**: state machine (locked → login →
  loading → populated/insufficient-data/error), region status pills,
  funnel bars with drop-off %, and the heatmap's click-density grid +
  scroll-depth bands with `role="tablist"` arrow-key layer toggle. A real
  data table always accompanies the `aria-hidden` heatmap grid (design
  spec §6.6).

## Decisions
- **No "winner" pill is ever rendered.** `/admin/metrics` exposes trial/
  conversion counts but not the pricing engine's posterior/statistical-
  significance computation (`pricing_engine.py`'s `best_price`/`decisive`
  is internal, not surfaced via this endpoint). Reimplementing a
  parallel significance test client-side risked silently diverging from
  the real one, so the UI only distinguishes **Gathering data** (region's
  summed conversions < `MIN_CONVERSIONS`=50, mirroring
  `pricing_engine.py`'s own gate) vs. **Trending** (past that floor,
  currently leading) — satisfies MT-4's "no winner declared below the
  configured minimum sample" acceptance criterion by construction, and is
  flagged in-view as a data-contract gap for `backend-dev` (design spec
  §9) rather than papered over.
- **No Orders view built.** Design spec §6.7 describes one, but no
  `/admin/orders` (or equivalent) route exists in the current backend
  contract — inventing one was out of this ticket's scope (backend files
  are off-limits). Flagging to PM/backend-dev alongside the winner-pill
  gap above.
- **No logout affordance.** No `/admin/logout` route exists to actually
  invalidate the httponly `owner_session` cookie; a client-side-only
  "log out" button would silently not end the session, so none was
  built rather than shipping a control that lies about what it does.
- Pricing table rows are grouped by region but labeled "price points
  tested," not "current vs. historical arm" — `region_metrics()` doesn't
  return which `(region, price_cents)` row is the live epoch's arm, so
  claiming one is "current" would be an unverified assertion. Full
  per-arm history is still available via an expandable `<details>` row.
- Scroll-depth table's "% of shallowest bucket" is an explicit
  approximation (baseline = the 0%-bucket's session count, not a true
  "sessions who loaded the page" figure not present in the contract) —
  labeled as such in the column header rather than presented as exact.

## Runnable check (this session)
- Dev-only stub server (`admin_stub_server.py`, not committed) fakes
  `/admin/login`, `/admin/metrics`, `/admin/heatmap` against three
  scenarios (`populated`, `empty`, `error`) and serves the static tree
  from `pipeline/web/` so `../styles.css` resolves exactly as it would
  under the real app.
- Playwright (chromium at `/opt/pw-browsers/chromium-1194/...`) drove:
  login (wrong passcode → honest non-revealing error; correct passcode →
  dashboard), all four populated views, the heatmap tab/keyboard toggle,
  the empty-data state (all four views individually confirmed to show
  "not enough traffic yet" copy, zero fabricated numbers, no KPI tiles
  rendered), and the authenticated-but-failing-fetch error state with
  Retry. Screenshots captured light + dark for login/overview/heatmap.
- axe-core run against every captured state (login ×2 themes,
  overview ×2, heatmap ×2): **0 violations** across all six runs.
- Bug found and fixed during verification: `dashboard.css`'s own header
  comment contained the literal substring `text-*/space-*`, whose `*/`
  prematurely closed the file's first comment block and silently
  corrupted the parse of the `--heat-0..4` custom properties (they
  computed to `''`, so the click-density grid rendered with no fill and
  the density legend was blank) while every other token in the same
  `:root` block kept working. Fixed by inserting a space
  (`text-* / space-*`); reran the full Playwright + axe suite after the
  fix to confirm the grid renders and no new violations were introduced.
  Also tightened `.region-summary-list` row spacing (rows read
  print-spread-thin at full container width before this pass).

## Blocked / carried
- **`testing/accessibility-auditor` sign-off still required** before this
  build is considered verified per the design spec's own gate (§5/§8) —
  this session's axe-core run is a strong self-check, not a substitute
  for that review.
- **Backend data-contract gaps flagged to `backend/backend-dev` + PM**:
  (1) no decisive/winner computation exposed via `/admin/metrics` (design
  spec §9 already flagged this seam); (2) no `/admin/orders` route for
  design spec §6.7's Orders view; (3) no `/admin/logout` route.
- **Serving-seam note for the orchestrator**: this build assumes
  `pipeline/app/main.py` will serve `pipeline/web/admin/index.html` (and
  its sibling `dashboard.css`/`dashboard.js`) at `/admin`, gated so an
  unauthenticated request still gets the login page's static HTML (the
  page itself handles the locked state client-side; only the `/admin/*`
  JSON reads are 401-gated per the existing `require_owner` dependency).
  No route currently in `main.py` serves this directory — wiring that up
  is backend-dev's, not touched here (public `pipeline/web/` funnel files
  and everything under `pipeline/app/` were out of this ticket's scope).
