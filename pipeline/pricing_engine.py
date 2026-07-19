"""
Transparent regional price-optimization engine (v2 — post-review).

Design goal (from the user): "start with per-state baselines and
algorithmically find the middle ground" — discover the revenue-maximizing
price per U.S. state via online experimentation, without hand-tuning.

This v2 addresses the two Ges-Talt review-gate FAILs on v1:
  logicians/code-reviewer:
    B1  state_code VALUE was unvalidated -> a ZIP/city string minted its own
        arm set = sub-state pricing. FIXED: values validated against US_STATES;
        anything else collapses to one shared "__default__" bucket.
    B2  price was resampled per request -> two same-region users could see
        different prices at once. FIXED: one CURRENT arm per region per epoch;
        all region visitors in an epoch see it. Randomization unit is
        region-epoch, analysis unit is the user.
    B3  in-process, non-atomic state. PARTIAL: a lock makes single-process
        updates atomic and all mutable state lives behind `_lock` in
        `_arms`/`_current` so it externalizes to a shared store cleanly. The
        multi-worker topology decision is the software-architect ADR (MT-2).
  academic/statistician:
    - best_price reported a winner on n=0 (0.5 prior mean). FIXED: decisive
      only past a minimum-conversion gate, with a revenue CI and a TIE rule
      that defaults to the LOWER price.
    - early exploration over-charged (flat prior). FIXED: forced round-robin
      until each arm is explored, then Thompson sampling.
    - self-test was circular and could not fail. FIXED: multi-seed,
      CONTINUOUS true-optimum sweep, an off-grid case that must trip a
      boundary warning, and hard assertions (non-zero exit on failure).
    - non-stationarity: optional `decay` discounts stale counts.

WHAT THIS STILL DELIBERATELY DOES NOT DO (enforced in code): price on device,
price below STATE granularity, or charge two same-region visitors different
prices in the same epoch.

Self-test:  python3 pricing_engine.py   (exits non-zero on failure)
"""
from __future__ import annotations

import math
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# --- Guardrails (the "line", enforced) --------------------------------------

# Only U.S. state may influence price. Both the KEY and its VALUE are checked
# (v1 checked the key only — the B1 hole).
ALLOWED_PRICING_INPUTS = frozenset({"state_code"})
US_STATES = frozenset({
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
})
DEFAULT_REGION = "__default__"

PRICE_FLOOR = 20.0
PRICE_CEIL = 400.0

# Published per-state purchasing-power baseline (illustrative subset; 1.00 ==
# national average). Lower-income states get a LOWER baseline — the move is
# toward affordability, not extraction. Unknown state -> national baseline.
STATE_PPP_INDEX = {
    "CA": 1.34, "NY": 1.28, "FL": 1.03, "ME": 0.98, "NM": 0.88,
    "MS": 0.85, "TX": 0.98, "WA": 1.18, "MA": 1.30, "OH": 0.92,
}
DEFAULT_PPP = 1.00

# Statistics gates (statistician).
MIN_CONVERSIONS = 50   # per arm before it can be reported a decisive winner
Z = 1.96               # ~95% normal-approx interval


def canonical_region(raw: object) -> str:
    """Normalize any caller-supplied state value to a valid region or the
    shared default bucket. This is the single choke point that keeps
    sub-state strings (ZIPs, cities, lat/long) from ever minting their own
    price."""
    if not isinstance(raw, str):
        return DEFAULT_REGION
    code = raw.strip().upper()
    return code if code in US_STATES else DEFAULT_REGION


@dataclass
class PriceArm:
    region: str
    price: float
    alpha: float = 1.0
    beta: float = 1.0

    def sample_conversion(self) -> float:
        return random.betavariate(self.alpha, self.beta)

    def p_hat(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def p_var(self) -> float:
        a, b = self.alpha, self.beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    def expected_revenue(self) -> float:
        return self.price * self.p_hat()

    def revenue_ci(self) -> tuple[float, float]:
        se = self.price * math.sqrt(self.p_var())
        m = self.expected_revenue()
        return (m - Z * se, m + Z * se)

    def update(self, converted: bool, decay: float = 1.0) -> None:
        if decay != 1.0:  # discount stale evidence toward the prior
            self.alpha = 1.0 + (self.alpha - 1.0) * decay
            self.beta = 1.0 + (self.beta - 1.0) * decay
        if converted:
            self.alpha += 1
        else:
            self.beta += 1

    @property
    def conversions(self) -> int:
        return int(self.alpha - 1)

    @property
    def trials(self) -> int:
        return int(self.alpha + self.beta - 2)


@dataclass
class Assignment:
    session_id: str
    region: str
    baseline: float
    price: float
    variant_id: str
    device_class: Optional[str] = None  # logged for UX analytics; NEVER priced
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PriceDecision:
    price: float
    expected_revenue: float
    ci: tuple[float, float]
    decisive: bool          # False => below sample gate or a statistical tie
    reason: str


class PricingEngine:
    def __init__(self, base_price: float, spread: float = 0.25, steps: int = 5,
                 epoch_size: int = 50, decay: float = 1.0):
        if steps < 2:
            raise ValueError("steps must be >= 2 (need a price range to test)")
        self.base_price = base_price
        self.spread = spread
        self.steps = steps
        self.epoch_size = epoch_size
        self.decay = decay
        self._arms: dict[str, list[PriceArm]] = {}
        self._current: dict[str, PriceArm] = {}
        self._epoch_n: dict[str, int] = {}
        self._lock = threading.Lock()

    # --- pricing model ------------------------------------------------------

    def baseline_for(self, region: str) -> float:
        ppp = STATE_PPP_INDEX.get(region, DEFAULT_PPP)
        return round(min(max(self.base_price * ppp, PRICE_FLOOR), PRICE_CEIL), 2)

    def _arms_for(self, region: str) -> list[PriceArm]:
        if region not in self._arms:
            base = self.baseline_for(region)
            lo, hi = base * (1 - self.spread), base * (1 + self.spread)
            prices = sorted({
                round(min(max(lo + (hi - lo) * i / (self.steps - 1), PRICE_FLOOR), PRICE_CEIL), 2)
                for i in range(self.steps)
            })  # dedupe collapses arms that clamp to the same bound
            self._arms[region] = [PriceArm(region, p) for p in prices]
        return self._arms[region]

    def _select_arm(self, region: str) -> PriceArm:
        """Forced round-robin until every arm is explored, then Thompson
        sampling on expected revenue (price x sampled conversion)."""
        arms = self._arms_for(region)
        unexplored = [a for a in arms if a.trials == 0]
        if unexplored:
            return min(unexplored, key=lambda a: a.price)  # cheapest-first probe
        return max(arms, key=lambda a: a.price * a.sample_conversion())

    def assign_price(self, session_id: str, signals: Optional[dict]) -> Assignment:
        signals = signals or {}
        pricing_view = {k: v for k, v in signals.items() if k in ALLOWED_PRICING_INPUTS}
        region = canonical_region(pricing_view.get("state_code"))

        with self._lock:
            arm = self._current.get(region)
            if arm is None:
                arm = self._current[region] = self._select_arm(region)
                self._epoch_n.setdefault(region, 0)
            price = arm.price

        return Assignment(
            session_id=session_id,
            region=region,
            baseline=self.baseline_for(region),
            price=price,
            variant_id=f"{region}@{price:.2f}",
            device_class=signals.get("device_class"),
        )

    def record_outcome(self, assignment: Assignment, converted: bool) -> bool:
        """Update the posterior for the arm the buyer actually saw. Returns
        False (and drops nothing silently) if the price no longer maps to an
        arm — the caller can log it."""
        region = assignment.region
        with self._lock:
            match = next((a for a in self._arms_for(region)
                          if abs(a.price - assignment.price) < 1e-9), None)
            if match is None:
                return False
            match.update(converted, decay=self.decay)
            self._epoch_n[region] = self._epoch_n.get(region, 0) + 1
            if self._epoch_n[region] >= self.epoch_size:
                self._current[region] = self._select_arm(region)
                self._epoch_n[region] = 0
        return True

    # --- decision readout (gated) ------------------------------------------

    def best_price(self, region: str) -> PriceDecision:
        """Revenue-maximizing price WITH a minimum-sample gate and a tie rule.
        Never declares a decisive winner on thin data; on a statistical tie it
        defaults to the LOWER price (better conversion, fairness-aligned)."""
        region = canonical_region(region)
        arms = sorted(self._arms_for(region), key=lambda a: a.expected_revenue(), reverse=True)
        top = arms[0]
        if top.conversions < MIN_CONVERSIONS:
            return PriceDecision(top.price, round(top.expected_revenue(), 2),
                                 top.revenue_ci(), False,
                                 f"below sample gate ({top.conversions}/{MIN_CONVERSIONS} conv)")
        runner = arms[1] if len(arms) > 1 else None
        if runner is not None and top.revenue_ci()[0] <= runner.revenue_ci()[1]:
            lo_price = min(top.price, runner.price)
            m = next(a for a in arms if abs(a.price - lo_price) < 1e-9)
            return PriceDecision(lo_price, round(m.expected_revenue(), 2),
                                 m.revenue_ci(), False,
                                 "revenue CIs overlap — tie, defaulting to lower price")
        return PriceDecision(top.price, round(top.expected_revenue(), 2),
                             top.revenue_ci(), True, "decisive")

    def at_boundary(self, region: str) -> bool:
        """True if the current best arm is the cheapest or dearest candidate —
        a signal the true optimum may be OFF the tested grid and `spread`
        should be widened (the range-validation guard the statistician asked
        for)."""
        region = canonical_region(region)
        arms = sorted(self._arms_for(region), key=lambda a: a.price)
        best = max(arms, key=lambda a: a.expected_revenue())
        return best.price in (arms[0].price, arms[-1].price)


# --- Self-test: a real test that can FAIL (non-zero exit) -------------------

def _true_conversion(ceiling: float, price: float) -> float:
    return 1 / (1 + math.exp((price - ceiling) / 12))


def _continuous_optimum(ceiling: float) -> float:
    """Brute-force the revenue-maximizing price over a CONTINUOUS sweep — not
    over the engine's own candidate grid (the v1 circularity)."""
    grid = [PRICE_FLOOR + i * 0.5 for i in range(int((PRICE_CEIL - PRICE_FLOOR) / 0.5))]
    return max(grid, key=lambda p: p * _true_conversion(ceiling, p))


def _run(seed: int, ceiling_factor: float, region: str = "CA", n: int = 12000):
    random.seed(seed)
    engine = PricingEngine(base_price=60.0, spread=0.30, steps=6, epoch_size=40)
    base = engine.baseline_for(region)
    ceiling = base * ceiling_factor  # ground truth NOT tied to the grid center
    for i in range(n):
        a = engine.assign_price(f"s{i}", {
            "state_code": region,
            "device_class": random.choice(["mac", "windows", "mobile"]),
        })
        engine.record_outcome(a, random.random() < _true_conversion(ceiling, a.price))
    return engine, base, ceiling


def _selftest() -> int:
    failures = []

    # 1) On-grid optimum: multi-seed, must land within one arm of the BEST
    #    CANDIDATE, and must NOT trip the boundary warning.
    for seed in (1, 2, 3, 4, 5):
        engine, base, ceiling = _run(seed, ceiling_factor=1.0)
        arms = sorted(engine._arms_for("CA"), key=lambda a: a.price)
        best_candidate = max(arms, key=lambda a: a.price * _true_conversion(ceiling, a.price))
        chosen = max(arms, key=lambda a: a.expected_revenue())
        idx_c = arms.index(chosen)
        idx_b = arms.index(best_candidate)
        if abs(idx_c - idx_b) > 1:
            failures.append(f"seed {seed}: chose {chosen.price} vs best candidate "
                            f"{best_candidate.price} (>1 arm off)")
        if engine.at_boundary("CA"):
            failures.append(f"seed {seed}: on-grid run tripped boundary warning")

    # 2) B1 — value validation: a ZIP string must NOT mint its own arm set;
    #    it collapses to the shared default region.
    engine, *_ = _run(7, 1.0)
    zip_asg = engine.assign_price("z", {"state_code": "90210"})
    if zip_asg.region != DEFAULT_REGION:
        failures.append(f"ZIP '90210' minted region {zip_asg.region!r} (sub-state pricing leak)")

    # 3) B2 — same region+epoch => identical price regardless of device.
    engine2 = PricingEngine(base_price=60.0, spread=0.3, steps=6)
    p_mac = engine2.assign_price("u1", {"state_code": "CA", "device_class": "mac"}).price
    p_win = engine2.assign_price("u2", {"state_code": "CA", "device_class": "windows"}).price
    if p_mac != p_win:
        failures.append(f"device changed price within an epoch: mac={p_mac} win={p_win}")

    # 4) Statistician gate — a winner must NOT be declared on thin data.
    thin = PricingEngine(base_price=60.0, spread=0.3, steps=6)
    a = thin.assign_price("t", {"state_code": "CA"})
    thin.record_outcome(a, True)  # one conversion
    if thin.best_price("CA").decisive:
        failures.append("best_price declared decisive on ~1 conversion (sample gate failed)")

    # 5) Off-grid optimum MUST be detected: true optimum well above the grid,
    #    so the engine should settle on the dearest arm AND flag the boundary.
    engine3, base3, ceiling3 = _run(9, ceiling_factor=1.9)
    if not engine3.at_boundary("CA"):
        failures.append("off-grid optimum did NOT trip the boundary warning (test blind spot)")
    cont_opt = _continuous_optimum(ceiling3)
    top_candidate = max(engine3._arms_for("CA"), key=lambda a: a.price).price
    if cont_opt <= top_candidate:
        failures.append("off-grid scenario mis-constructed (optimum not actually off-grid)")

    # --- report -------------------------------------------------------------
    print("Self-test — regional price optimization (v2)\n")
    for region in ("CA", "ME", "NM"):
        e, b, c = _run(1, 1.0, region=region)
        d = e.best_price(region)
        print(f"  {region}: baseline {b:.2f} -> price {d.price:.2f} "
              f"(exp.rev {d.expected_revenue:.2f}, decisive={d.decisive}, "
              f"boundary={e.at_boundary(region)})")

    print()
    if failures:
        print(f"RESULT: FAIL — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS — on-grid convergence, value validation, device-"
          "independence, sample gate, and off-grid detection all hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
