"""
Static content for the IT Risk Quantification Dashboard: example scenarios
and methodology explainer copy. Kept separate from engine.py (stable, tested
math) and app.py (UI) so content edits never risk touching calculation logic.
"""

# ─── Pre-built example scenarios ──────────────────────────────────────────────
EXAMPLES = {
    "— Select a scenario —": None,
    # ── Original scenarios ─────────────────────────────────────────────────
    "🎣 Phishing Attack (Medium Risk)": {
        "lef": 0.2, "lm": 250000.0, "lef_std": 0.1, "lm_std": 0.3,
        "control_cost": 15000.0, "post_ale": 75000.0,
        "likelihood": 6, "exposure": 7, "consequence": 8,
        "description": (
            "An employee clicks a malicious link leading to a data leak. "
            "Frequency is low but impact is significant. "
            "A **$15,000 security awareness training programme** is the proposed control."
        ),
    },
    "💥 DDoS on E-Commerce Site (High Volatility)": {
        "lef": 0.8, "lm": 80000.0, "lef_std": 0.4, "lm_std": 0.5,
        "control_cost": 30000.0, "post_ale": 20000.0,
        "likelihood": 8, "exposure": 9, "consequence": 7,
        "description": (
            "A DDoS attack disrupts online sales. High uncertainty in frequency "
            "due to evolving threat landscape. "
            "A **$30,000 DDoS mitigation service** is evaluated."
        ),
    },
    "🕵️ Insider Threat (Low Freq, High Consequence)": {
        "lef": 0.1, "lm": 500000.0, "lef_std": 0.05, "lm_std": 0.1,
        "control_cost": 50000.0, "post_ale": 100000.0,
        "likelihood": 3, "exposure": 5, "consequence": 10,
        "description": (
            "A rogue employee steals sensitive data. Rare but potentially catastrophic. "
            "**$50,000 in user behaviour analytics & monitoring tools** is the proposed control."
        ),
    },
    # ── Added scenarios (v2.0) ──────────────────────────────────────────────
    "🔐 Ransomware Attack (Medium Enterprise)": {
        "lef": 0.3, "lm": 750000.0, "lef_std": 0.2, "lm_std": 0.4,
        "control_cost": 80000.0, "post_ale": 90000.0,
        "likelihood": 6, "exposure": 8, "consequence": 9,
        "description": (
            "Ransomware encrypts critical systems, causing operational shutdown and extortion demands. "
            "Typical for mid-sized enterprises with mixed patch levels. "
            "**$80,000/year in EDR, backups, and incident response retainer** is evaluated."
        ),
    },
    "☁️ Cloud Misconfiguration / Data Exposure": {
        "lef": 0.5, "lm": 400000.0, "lef_std": 0.3, "lm_std": 0.35,
        "control_cost": 35000.0, "post_ale": 60000.0,
        "likelihood": 7, "exposure": 9, "consequence": 8,
        "description": (
            "A misconfigured S3 bucket or Azure storage account exposes sensitive customer or "
            "financial data to the public internet. GDPR fines and reputational damage are major drivers. "
            "**$35,000/year Cloud Security Posture Management (CSPM) tool** is the proposed control."
        ),
    },
    "🏦 Third-Party / Supplier Failure": {
        "lef": 0.4, "lm": 300000.0, "lef_std": 0.25, "lm_std": 0.3,
        "control_cost": 25000.0, "post_ale": 80000.0,
        "likelihood": 5, "exposure": 7, "consequence": 8,
        "description": (
            "A critical third-party IT or data supplier suffers a breach or outage that cascades "
            "into your organisation. Relevant for insurers with outsourced policy admin or claims systems. "
            "**$25,000/year third-party risk management programme & contractual SLAs** evaluated."
        ),
    },
    "🔑 Privileged Access Compromise": {
        "lef": 0.15, "lm": 600000.0, "lef_std": 0.1, "lm_std": 0.2,
        "control_cost": 60000.0, "post_ale": 80000.0,
        "likelihood": 4, "exposure": 6, "consequence": 10,
        "description": (
            "An attacker gains admin or privileged credentials (via credential stuffing, social engineering, "
            "or stolen tokens) and moves laterally across critical systems. "
            "**$60,000/year Privileged Access Management (PAM) solution + MFA enforcement** evaluated."
        ),
    },
}

# ─── Uncertainty presets (F3) — plain-language Low/Medium/High mapped to numeric std/CV ───
LEF_UNCERTAINTY_PRESETS = {
    "Low — I have solid historical data": 0.1,
    "Medium — I'm estimating from partial data": 0.3,
    "High — this is a new/emerging threat": 0.5,
}

LM_UNCERTAINTY_PRESETS = {
    "Low — I have solid historical data": 0.2,
    "Medium — I'm estimating from partial data": 0.3,
    "High — this is a new/emerging threat": 0.5,
}

# ─── Currency support (F9) ────────────────────────────────────────────────────
CURRENCIES = {
    "€ EUR": "€",
    "$ USD": "$",
    "£ GBP": "£",
}
DEFAULT_CURRENCY = "€ EUR"

# ─── Sidebar methodology explainer copy ───────────────────────────────────────
METHODOLOGY_FAIR = """
**Factor Analysis of Information Risk**

Converts risk to a dollar value:

> **ALE = LEF × LM**

- **LEF** — how often the event occurs per year
- **LM** — average financial impact per event
- **ALE** — expected annual loss in dollars

Used in board reports, insurance pricing, and cyber budgets.
"""

METHODOLOGY_MONTE_CARLO = """
**Why not just use the formula?**

Real risk is uncertain. Monte Carlo runs the FAIR formula 10,000 times
with slightly different random inputs each time (based on your std dev values),
producing a *distribution* of possible outcomes.

- **Mean ALE** — the average outcome across all runs
- **P95 ALE** — 95% of outcomes fall below this value (tail risk / worst-case planning)

The wider the distribution → the more uncertain your risk estimate.
"""

METHODOLOGY_LEC = """
**Likelihood × Exposure × Consequence**

A quick qualitative scoring method — no dollar values needed.

| Score | Band | Action |
|-------|------|--------|
| 1–99 | 🟢 Low | Monitor |
| 100–499 | 🟡 Medium | Mitigate |
| 500–1000 | 🔴 High | Act Now |

Useful when you don't have enough data for FAIR,
or as a first-pass prioritisation across many risks.
"""

METHODOLOGY_ROI = """
**Return on Investment**

> **ROI = (ALE reduction ÷ Control cost) × 100**

- **ALE reduction** = Current ALE − Post-control ALE
- **>100%** = control saves more than it costs ✅
- **<0%** = control costs more than the risk itself ❌

Use this to justify security spend to management.
"""

HOW_TO_USE_MD = """
---

## Step 1 — Load an Example (Optional but Recommended)

At the top of the **Risk Calculator** tab, use the **scenario dropdown** to pre-load a real-world example:

- **🎣 Phishing Attack** — medium risk, high ROI training scenario
- **💥 DDoS on E-Commerce** — high volatility, urgent action
- **🕵️ Insider Threat** — rare but catastrophic

Once loaded, all input fields fill automatically. You can then tweak values for your own situation.

---

## Step 2 — Fill In the FAIR Inputs

These four fields drive the quantitative dollar calculation:

| Field | What to enter | Example |
|-------|--------------|---------|
| **LEF** (Loss Event Frequency) | How often per year | 0.5 = once every 2 years |
| **LM** (Loss Magnitude) | $ cost when it happens | $150,000 |
| **LEF uncertainty** | How uncertain is the frequency? | Low / Medium / High preset, or Advanced |
| **LM uncertainty** | How uncertain is the loss amount? | Low / Medium / High preset, or Advanced |

> 💡 **Not sure?** Pick "Medium" if you're estimating from partial data. Use the **Advanced** expander if you want to enter exact std dev / CV numbers.

---

## Step 3 — Fill In the Control ROI Inputs

| Field | What to enter | Example |
|-------|--------------|----------|
| **Control Cost** | Annual cost of the mitigation | $20,000/year for a firewall service |
| **Post-Control ALE** | Expected ALE *after* the control | $30,000 (if control halves the risk) |

> 💡 **Tip**: If your control eliminates the risk entirely, set Post-Control ALE to 0. But be realistic — very few controls offer 100% protection.

---

## Step 4 — Set the LEC Sliders

Three sliders from 1 to 10:

- **Likelihood**: How probable is this threat?
  - 1 = virtually impossible (comet strike)
  - 5 = plausible (could happen this year)
  - 10 = almost certain (you're under active attack)
- **Exposure**: How exposed is the asset?
  - 1 = air-gapped, isolated system
  - 5 = internal network access
  - 10 = public internet, enterprise-wide
- **Consequence**: How bad if it happens?
  - 1 = minor inconvenience, quickly recovered
  - 5 = significant disruption, days of downtime
  - 10 = catastrophic — regulatory fines, data breach, business continuity threat

---

## Step 5 — Click Calculate and Read the Results

After clicking **⚡ Calculate Risk**, you'll see:

1. **FAIR ALE** — your baseline annual loss
2. **Monte Carlo results** — mean + worst-case (P95)
3. **Control ROI** — is the mitigation worth it?
4. **LEC Score** — qualitative risk band (Low / Medium / High)
5. **Charts** — visual distribution of outcomes + summary metrics
6. **Scenario summary table** — screenshot-ready for reports

Results now **stay visible** while you keep adjusting inputs — if your inputs
have changed since the last calculation, you'll see a "stale results" notice
instead of the results disappearing. Click **Calculate Risk** again to refresh.

Use the **expandable "What does this mean?"** sections under each result for interpretation guidance.

---

## Example: Phishing Attack Walkthrough

**Situation**: You want to evaluate a $15,000 security awareness training programme to reduce phishing risk.

**Inputs**:
- LEF: 0.2 (one phishing incident every 5 years)
- LM: $250,000 (data breach cost)
- LEF uncertainty: Low | LM uncertainty: Medium
- Control Cost: $15,000 | Post-Control ALE: $75,000 (training reduces exposure)
- Likelihood: 6 | Exposure: 7 | Consequence: 8

**Expected Results**:
- FAIR ALE: $50,000
- Monte Carlo Mean: ~$48,500 | P95: ~$120,000
- ROI: ~200% ✅ (training saves $35k, costs $15k)
- LEC: 336 → 🟡 Medium Risk

**Conclusion**: Training is a clear win — high ROI and medium priority escalation.

---

## Tips for Getting Better Results

- **Use real data** where possible: incident logs → LEF, breach cost studies → LM
- **Sensitivity analysis**: run the tool 3 times with low / medium / high inputs to see the range
- **P95 for budgets**: use the 95th percentile when sizing cyber insurance or emergency reserves
- **ROI >100% = invest**: if the control saves more than it costs, the business case is made
- **LEC for prioritisation**: when you have 10 risks to rank and no dollar data, LEC gives you a quick order

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Input error" message | Check for zero/negative values in LEF, LM, or Control Cost |
| Charts not loading | Refresh the page; ensure JavaScript is enabled |
| Page loads slowly | Free hosting sleeps after 15 min — wait 10 seconds and reload |
| Unexpected ROI | Check Post-Control ALE isn't higher than current ALE |
| Results disappeared | They shouldn't anymore (Phase 1 fix) — if they do, please report this as a bug |

---

## What's Coming Next (Phase 2)

- 🧭 Guided 4-step flow (Scenario → Inputs → Results → Report)
- 💾 Save and load scenarios as JSON
- 📄 One-click Markdown/HTML report export
- 🔐 User authentication for team use
- 🗺️ STRIDE threat model integration (import threats → pre-filled scenarios)
- 📊 Risk heatmap / portfolio view across multiple scenarios

---
*Built for IT Risk professionals. Questions? Contact Peter Van Walsem.*
"""
