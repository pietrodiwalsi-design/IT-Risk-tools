# Model Assumptions — IT Risk Quantification Dashboard

**Scope:** `dashboard/engine.py` · Written 2026-07-07 as part of Phase 1.5
(structure work, per `docs/ux-review-and-improvement-plan.md`).

Every number this tool shows to a stakeholder (board, CISO, auditor) needs a
defensible method behind it. This document is that defence: which
distributions are used, why, what their parameters mean, and where the hard
limits come from.

---

## 1. FAIR (Factor Analysis of Information Risk)

**Formula:** `ALE = LEF × LM`

- **LEF (Loss Event Frequency)** — expected number of loss events per year.
  A rate, not a probability; can exceed 1 (e.g. 2.0 = twice a year).
- **LM (Loss Magnitude)** — average financial impact per event, in the
  scenario's currency.
- **ALE (Annual Loss Expectancy)** — the deterministic point estimate of
  expected annual loss. This is FAIR's headline number, widely used in
  board reporting and insurance pricing.

This is the standard FAIR formulation (Open FAIR / The Open Group risk
taxonomy). It intentionally does not decompose into Threat Event Frequency ×
Vulnerability or Primary/Secondary Loss — that finer-grained FAIR
decomposition is out of scope for this tool's current MVP; LEF and LM are
taken as already-elicited top-level estimates (from incident history,
industry benchmarks such as Verizon DBIR, or subject-matter-expert
judgement).

## 2. Monte Carlo simulation

**Why:** a single ALE point estimate hides uncertainty. Real-world loss
frequency and magnitude both vary; Monte Carlo runs the FAIR formula many
times with randomly sampled inputs to produce a *distribution* of possible
annual outcomes, from which we read off the mean and a tail-risk percentile.

**Sample size:** `sim_runs = 10000` in the UI (100,000 in the test suite for
tighter statistical tolerance). 10,000 runs is enough for stable mean/P95
estimates at these input scales (see §5, empirically verified) while keeping
UI response time interactive.

### 2.1 LEF sampling — Normal distribution

```
lef_samples = Normal(mean=lef, std=lef_std)
lef_samples = clip(lef_samples, min=0)
```

LEF is modelled as normally distributed around the point estimate, clipped
at zero (frequency cannot be negative). Normal is a reasonable default for a
rate estimate with moderate relative uncertainty; it is *not* a claim that
event frequency is exactly Gaussian in reality — it is a pragmatic choice
that is symmetric, well-understood by reviewers, and matches how the
uncertainty input (`lef_std`) is elicited from users ("how many standard
deviations of doubt do you have around this frequency estimate").

**Known limitation:** for very high `lef_std` relative to `lef`, the normal
distribution puts nonzero probability mass below zero (handled via clipping,
which slightly inflates the effective mean above the theoretical normal
mean for high-uncertainty cases). This is a known, accepted approximation —
not a defect — documented here so it is never a surprise finding later.

### 2.2 LM sampling — Lognormal distribution, CV-parameterised

```
cv = lm_std                                  # coefficient of variation
sigma = sqrt(log(1 + cv^2))
mu = log(lm_mean) - 0.5 * sigma^2
lm_samples = Lognormal(mu, sigma)
```

Loss magnitude is modelled as **lognormal**, not normal. This matches how
cyber/operational losses actually behave: they are bounded below by zero,
right-skewed (many small-to-medium losses, a long tail of rare catastrophic
ones), and multiplicative in nature (a breach that's "twice as bad" often
means twice the records exposed, not a fixed dollar increment). Lognormal is
the standard choice in actuarial and FAIR-adjacent quantitative risk
literature for this reason.

**Parameterisation — the "CV, not sigma" fix (2026-05-20, `c576ccc`):** the
UI input `lm_std` is exposed to the user as a **coefficient of variation**
(CV = std/mean, "uncertainty as % of mean"), not as the lognormal `sigma`
parameter directly. Naively passing CV in as if it were `sigma` is a common
bug — it does not preserve the intended mean or CV of the sampled
distribution. The formulas above derive the correct `(mu, sigma)` pair from
`(lm_mean, cv)` so that:

- `E[lm_samples] ≈ lm_mean` (verified within 2% in
  `test_monte_carlo.py::test_mean_preservation`, for CV ∈ {0.1, 0.3, 0.5, 0.8})
- `CV(lm_samples) ≈ cv` (verified within 5% in
  `test_monte_carlo.py::test_cv_preservation`)

This is the single most important correctness property of the whole engine:
if a user says "my average loss is €750k with 30% uncertainty," the
simulation must actually produce samples averaging ~€750k with ~30% CV —
not some other, silently-wrong number. Both are covered by automated tests
and must stay green through any future refactor.

### 2.3 Output statistics

- **`mean_ale`** — average of `lef_samples × lm_samples` across all runs.
  Should track the deterministic FAIR ALE closely (verified within 3% in
  `test_ale_mean_vs_fair`) — Monte Carlo mean and the FAIR point formula are
  two views of the same expectation and must agree.
- **`std_ale`** — standard deviation of the ALE samples; a volatility
  measure, shown to give a sense of "how wide is the range of outcomes."
- **`p95_ale`** — 95th percentile of ALE samples. 5% of simulated years
  exceed this value. Used for pessimistic / worst-case planning (cyber
  insurance limit sizing, emergency reserve budgeting). Sanity-checked to
  not exceed 3× the mean for a moderate-uncertainty scenario
  (`test_p95_not_inflated`, CV=0.3) — a much higher ratio would indicate a
  parameterisation regression, not a legitimate fat-tail finding.

**Numerical safety:** samples are clipped to `[0, ∞)` and any resulting
`NaN`/`Inf` (which can appear at extreme input combinations near the hard
limits below) are replaced with `0` or the configured `MAX_LM` cap via
`np.nan_to_num`. This is a defensive guard, not expected to trigger for
realistic inputs — it exists so the app degrades to a bounded number instead
of crashing or silently propagating `NaN` into a chart.

## 3. Control ROI

**Formula:** `ROI = (current_ALE − post_control_ALE) / control_cost × 100`

A standard security-investment ROI framing: how much expected annual loss is
avoided, per unit of annual control spend. `current_ALE` is always the
*deterministic* FAIR ALE (not the Monte Carlo mean) for this calculation —
the two are close by construction (§2.3) and the deterministic figure is
easier for a reader to trace back to the two raw inputs (LEF × LM).

**Bands** (`roi_band()` in `engine.py`):
| ROI | Band | Rationale |
|---|---|---|
| ≥200% | 🟢 Excellent | Control returns 2x+ its cost in avoided loss — strong case |
| ≥100% | 🟡 Good | Control pays for itself at least once over |
| ≥0% | 🟠 Marginal | Break-even or thin margin — defensible but not compelling alone |
| <0% | 🔴 Negative | Control costs more than the risk it addresses |

These thresholds are a practical rule of thumb (common in security-business-case
literature), not a formally derived optimum — documented here so a reviewer
knows they are a judgement call, open to recalibration if Peter's stakeholder
audience uses different internal hurdle rates.

## 4. LEC (Likelihood × Exposure × Consequence)

**Formula:** `LEC = Likelihood × Exposure × Consequence`, each factor scored
1–10 by the user via qualitative anchors shown in the UI help text (e.g.
Exposure: 1 = air-gapped, 10 = internet-facing enterprise-wide asset).

This is a simple **qualitative multiplicative risk matrix**, not a
statistical model — it exists as a fast, no-dollar-values-needed
prioritisation method for when FAIR-quality data isn't available yet, or for
ranking many risks quickly (see UX review finding F5). Range is 1–1000.

**Bands** (`lec_band()` in `engine.py`):
| Score | Band | Action guidance |
|---|---|---|
| 1–99 | 🟢 Low | Monitor, review annually |
| 100–499 | 🟡 Medium | Mitigate within 90 days |
| 500–1000 | 🔴 High | Escalate immediately, emergency controls |

These bandwidth thresholds are a pragmatic convention (roughly log-spaced
across the 1–1000 range), consistent with common qualitative risk-matrix
practice, and should be treated as a starting point for calibration against
Peter's organisation's actual risk appetite statement, not as a
universally-derived constant.

## 5. Hard input limits (`engine.py` constants)

| Limit | Value | Purpose |
|---|---|---|
| `MAX_LEF` | 1000 events/year | Above this, "annual frequency" stops being a meaningful FAIR framing (essentially continuous/ambient) — also bounds Monte Carlo runtime |
| `MAX_LM` | €1,000,000,000 (1bn) | Sanity cap — prevents accidental overflow / unrealistic single-event magnitude entries; also used as the `nan_to_num` posinf replacement |
| `MAX_STD` (LEF std dev) | 10 | Prevents pathological normal-distribution inputs that would push most sampled mass below zero |
| LM CV | 0–2.0 | CV=2.0 already implies extreme skew (std = 2x the mean); higher values make the lognormal fit numerically unstable and are not realistic for the loss types this tool targets |
| `MAX_COST` (control cost) | €1,000,000,000 (1bn) | Same sanity-cap rationale as `MAX_LM` |

All limits are enforced server-side in `_validate_fair_inputs()` /
`roi_calc()` / `lec_score()`, independent of the Streamlit widget
`min_value`/`max_value` constraints — the engine must reject invalid input
even if called directly (e.g. from a future API, or the golden-set-style
test harness pattern used in `eu-ai-act-compliance-checker`), not only when
routed through the current UI.

## 6. What this tool does *not* model (explicitly out of scope)

- Full FAIR decomposition (Threat Event Frequency, Vulnerability, Primary/
  Secondary Loss as separate elicited inputs) — LEF/LM are taken as already
  top-level estimates.
- Correlation between LEF and LM (sampled independently) — a "bad year" that
  increases both frequency and magnitude simultaneously (e.g. a systemic
  attack wave) is not modelled.
- Multi-year discounting / time value of money on ALE or control cost.
- Portfolio-level aggregation across multiple simultaneous risk scenarios
  (Phase 3 / STRIDE-import roadmap item, not yet built).

---
*This document should be reviewed whenever `engine.py`'s formulas, sampling
distributions, or hard limits change — it is the "why" behind every number
the UI shows, and needs to stay in sync with the code it describes.*
