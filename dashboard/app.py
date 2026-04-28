import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Tuple, Dict
import logging

# Setup logging (sanitized, no PII)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IT Risk Tool",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Pre-built example scenarios ──────────────────────────────────────────────
EXAMPLES = {
    "— Select a scenario —": None,
    "🎣 Phishing Attack (Medium Risk)": {
        "lef": 0.2, "lm": 250000.0, "lef_std": 0.1, "lm_std": 0.3,
        "control_cost": 15000.0, "post_ale": 75000.0,
        "likelihood": 6, "exposure": 7, "consequence": 8,
        "description": (
            "An employee clicks a malicious link leading to a data leak. "
            "Frequency is low but impact is significant. "
            "A **$15,000 security training programme** is the proposed control."
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
            "**$50,000 in monitoring tools** is the proposed control."
        ),
    },
}


# ─── Risk calculator ──────────────────────────────────────────────────────────
class ITRiskCalculator:
    def __init__(self):
        self.sim_runs = 10000  # Monte Carlo iterations

    def fair_risk_calc(self, lef: float, lm: float) -> float:
        """FAIR: Annual Loss Expectancy = LEF * LM"""
        if lef < 0 or lm < 0:
            raise ValueError("Inputs must be non-negative")
        ale = lef * lm
        logger.info(f"FAIR ALE calculated: {ale}")
        return ale

    def monte_carlo_sim(self, lef_mean: float, lef_std: float, lm_mean: float, lm_std: float) -> Dict[str, float]:
        """Monte Carlo simulation for risk variability"""
        lef_samples = np.random.normal(lef_mean, lef_std, self.sim_runs)
        lm_samples = np.random.lognormal(np.log(lm_mean), lm_std, self.sim_runs)
        lef_samples = np.clip(lef_samples, 0, None)
        lm_samples = np.clip(lm_samples, 0, None)
        ale_samples = lef_samples * lm_samples
        return {
            'mean_ale': np.mean(ale_samples),
            'std_ale': np.std(ale_samples),
            'p95_ale': np.percentile(ale_samples, 95),
            'samples': ale_samples
        }

    def roi_calc(self, current_ale: float, post_control_ale: float, control_cost: float) -> float:
        """ROI = (ALE reduction / cost) * 100"""
        reduction = current_ale - post_control_ale
        if control_cost <= 0:
            raise ValueError("Control cost must be positive")
        roi = (reduction / control_cost) * 100
        logger.info(f"ROI calculated: {roi}%")
        return roi

    def lec_score(self, likelihood: int, exposure: int, consequence: int) -> int:
        """LEC: Likelihood * Exposure * Consequence (qualitative)"""
        if not (1 <= likelihood <= 10 and 1 <= exposure <= 10 and 1 <= consequence <= 10):
            raise ValueError("LEC inputs must be 1-10")
        score = likelihood * exposure * consequence
        logger.info(f"LEC score: {score}")
        return score

    def generate_charts(self, sim_data: Dict, roi: float, lec: int, ale: float):
        """Generate Monte Carlo histogram and summary bar chart"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Monte Carlo ALE Distribution (10,000 runs)', 'Risk Metrics Summary'),
            column_widths=[0.6, 0.4],
        )

        # ── Monte Carlo histogram ──────────────────────────────────────────
        samples = sim_data['samples']
        fig.add_trace(
            go.Histogram(
                x=samples, nbinsx=60, name='ALE Samples',
                marker_color='steelblue', opacity=0.75,
                hovertemplate='ALE: $%{x:,.0f}<br>Count: %{y}<extra></extra>',
            ),
            row=1, col=1,
        )
        # Mean & P95 lines
        fig.add_vline(
            x=sim_data['mean_ale'], line_dash='dash', line_color='orange',
            annotation_text=f"Mean ${sim_data['mean_ale']:,.0f}",
            annotation_position='top right', row=1, col=1,
        )
        fig.add_vline(
            x=sim_data['p95_ale'], line_dash='dot', line_color='red',
            annotation_text=f"P95 ${sim_data['p95_ale']:,.0f}",
            annotation_position='top right', row=1, col=1,
        )
        fig.update_xaxes(title_text='Annual Loss Expectancy ($)', tickprefix='$', tickformat=',.0f', row=1, col=1)
        fig.update_yaxes(title_text='Frequency', row=1, col=1)

        # ── Summary bars ──────────────────────────────────────────────────
        lec_color = 'green' if lec < 100 else ('orange' if lec < 500 else 'red')
        roi_color = 'green' if roi >= 100 else ('orange' if roi >= 0 else 'red')

        categories = ['FAIR ALE ($)', 'Mean ALE ($)', 'P95 ALE ($)', 'ROI (%)', 'LEC Score']
        values = [ale, sim_data['mean_ale'], sim_data['p95_ale'], roi, lec]
        colors = ['steelblue', 'steelblue', 'indianred', roi_color, lec_color]

        fig.add_trace(
            go.Bar(
                x=categories, y=values, name='Metrics',
                marker_color=colors, opacity=0.85,
                hovertemplate='%{x}: %{y:,.2f}<extra></extra>',
            ),
            row=1, col=2,
        )
        fig.update_yaxes(title_text='Value', row=1, col=2)

        fig.update_layout(
            title_text='IT Risk Dashboard — Phase 1.5',
            showlegend=False,
            height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        return fig


# ─── Helpers ──────────────────────────────────────────────────────────────────
def lec_band(score: int) -> tuple:
    if score < 100:
        return "🟢 Low Risk", "green", "Monitor — acceptable risk level. Document and review annually."
    elif score < 500:
        return "🟡 Medium Risk", "orange", "Mitigate — implement controls within 90 days."
    else:
        return "🔴 High Risk", "red", "Act Now — escalate immediately and implement emergency controls."


def roi_band(roi: float) -> tuple:
    if roi >= 200:
        return "🟢 Excellent", "green", "Control is highly cost-effective. Implement."
    elif roi >= 100:
        return "🟡 Good", "orange", "Control pays back. Justified investment."
    elif roi >= 0:
        return "🟠 Marginal", "darkorange", "Break-even or marginal. Consider alternatives."
    else:
        return "🔴 Negative ROI", "red", "Control costs more than it saves. Reassess control design."


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/cyber-security.png", width=64)
    st.title("🛡️ IT Risk Tool")
    st.caption("Phase 1.5 — Quantitative Risk Dashboard")

    st.divider()

    st.markdown("### 📖 Methodologies")
    with st.expander("FAIR (Quantitative)"):
        st.markdown(
            """
            **Factor Analysis of Information Risk**

            Converts risk to a dollar value:

            > **ALE = LEF × LM**

            - **LEF** — how often the event occurs per year
            - **LM** — average financial impact per event
            - **ALE** — expected annual loss in dollars

            Used in board reports, insurance pricing, and cyber budgets.
            """
        )
    with st.expander("Monte Carlo Simulation"):
        st.markdown(
            """
            **Why not just use the formula?**

            Real risk is uncertain. Monte Carlo runs the FAIR formula 10,000 times
            with slightly different random inputs each time (based on your std dev values),
            producing a *distribution* of possible outcomes.

            - **Mean ALE** — the average outcome across all runs
            - **P95 ALE** — 95% of outcomes fall below this value (tail risk / worst-case planning)

            The wider the distribution → the more uncertain your risk estimate.
            """
        )
    with st.expander("LEC (Qualitative)"):
        st.markdown(
            """
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
        )
    with st.expander("ROI of Controls"):
        st.markdown(
            """
            **Return on Investment**

            > **ROI = (ALE reduction ÷ Control cost) × 100**

            - **ALE reduction** = Current ALE − Post-control ALE
            - **>100%** = control saves more than it costs ✅
            - **<0%** = control costs more than the risk itself ❌

            Use this to justify security spend to management.
            """
        )

    st.divider()
    st.markdown("### 💡 Tips")
    st.info(
        "Start with an example scenario, then tweak the inputs for your own case. "
        "Use the **P95 ALE** figure for pessimistic/worst-case planning."
    )
    st.markdown("**LEC Interpretation**")
    st.markdown("🟢 1–99 → Low | 🟡 100–499 → Medium | 🔴 500+ → High")

    st.divider()
    st.caption("Built with Python + Streamlit | [Source code](https://github.com/pietrodiwalsi-design/IT-Risk-tools)")


# ─── Main area ────────────────────────────────────────────────────────────────
tab_calc, tab_guide = st.tabs(["📊 Risk Calculator", "📋 How to Use"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
with tab_calc:
    st.header("IT Risk Calculator")
    st.markdown(
        "Quantify your IT risks using **FAIR** and **LEC** methodologies, "
        "with **Monte Carlo simulation** for uncertainty modelling. "
        "Fill in the inputs below and click **Calculate Risk**."
    )

    # ── Example scenario loader ────────────────────────────────────────────
    st.subheader("🚀 Quick Start — Load an Example Scenario")
    selected_example = st.selectbox(
        "Choose a pre-built scenario to auto-fill inputs, or enter your own values below:",
        options=list(EXAMPLES.keys()),
        index=0,
    )

    ex = EXAMPLES[selected_example]
    if ex:
        st.info(f"**Scenario:** {ex['description']}")

    # Default values — use example if selected
    def val(key, default):
        return ex[key] if ex else default

    st.divider()

    # ── Input columns ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("#### 📐 FAIR / Monte Carlo Inputs")
        st.caption("These drive the quantitative (dollar) risk calculation.")

        lef = st.number_input(
            "Loss Event Frequency (LEF) — events per year",
            min_value=0.0, value=float(val("lef", 1.0)), step=0.1,
            help=(
                "How often do you expect this risk event to occur per year? "
                "Use decimals for less-than-annual events: "
                "0.1 = once every 10 years, 0.5 = once every 2 years, 2.0 = twice per year."
            ),
        )
        lm = st.number_input(
            "Loss Magnitude (LM) — $ impact per event",
            min_value=0.0, value=float(val("lm", 100000.0)), step=5000.0,
            help=(
                "What is the average financial impact when this event occurs? "
                "Include direct costs (recovery, fines, legal) and indirect costs "
                "(reputational damage, lost revenue). Use your incident history or insurance data."
            ),
        )

        st.markdown("**Uncertainty (for Monte Carlo)**")
        lef_std = st.number_input(
            "LEF Std Dev — frequency uncertainty",
            min_value=0.0, value=float(val("lef_std", 0.5)), step=0.05,
            help=(
                "How uncertain are you about the frequency? "
                "Low certainty (new threat) → higher value (e.g. 0.4). "
                "Historical data available → lower value (e.g. 0.1). "
                "Rule of thumb: ~30–50% of LEF for moderate uncertainty."
            ),
        )
        lm_std = st.number_input(
            "LM Std Dev — loss uncertainty",
            min_value=0.0, value=float(val("lm_std", 0.2)), step=0.05,
            help=(
                "How uncertain are you about the loss magnitude? "
                "Cyber losses are often skewed (small events common, huge events rare). "
                "0.2 = moderate uncertainty, 0.5 = high uncertainty. "
                "Loss magnitude uses a log-normal distribution to model skewness."
            ),
        )

    with col_right:
        st.markdown("#### 💰 Control ROI Inputs")
        st.caption("Evaluate whether a security control is worth the investment.")

        control_cost = st.number_input(
            "Control Cost ($) — annual cost of the mitigation",
            min_value=1.0, value=float(val("control_cost", 50000.0)), step=1000.0,
            help=(
                "Total annual cost to implement and run the control. "
                "Include licensing, staff time, training, and maintenance. "
                "One-off costs can be amortised over expected lifetime."
            ),
        )
        post_ale = st.number_input(
            "Post-Control ALE ($) — expected ALE after control is applied",
            min_value=0.0, value=float(val("post_ale", 50000.0)), step=5000.0,
            help=(
                "What will the Annual Loss Expectancy be *after* the control is in place? "
                "If the control eliminates the risk entirely, enter 0. "
                "Be realistic — controls rarely eliminate 100% of risk. "
                "This is compared against your FAIR ALE to calculate savings."
            ),
        )

        st.markdown("#### 🎯 LEC Qualitative Inputs")
        st.caption("Quick risk prioritisation without needing dollar values.")

        likelihood = st.slider(
            "Likelihood (1–10)",
            1, 10, int(val("likelihood", 5)),
            help="1 = virtually impossible, 5 = possible, 10 = almost certain. Based on threat intelligence and historical data.",
        )
        exposure = st.slider(
            "Exposure (1–10)",
            1, 10, int(val("exposure", 5)),
            help="1 = isolated/air-gapped system, 5 = internal network, 10 = internet-facing enterprise-wide asset.",
        )
        consequence = st.slider(
            "Consequence (1–10)",
            1, 10, int(val("consequence", 5)),
            help="1 = minor inconvenience, 5 = significant disruption, 10 = catastrophic / business-ending impact.",
        )

    # ── Calculate button ───────────────────────────────────────────────────
    st.divider()
    calc_col, _ = st.columns([1, 3])
    with calc_col:
        calculate = st.button("⚡ Calculate Risk", type="primary", use_container_width=True)

    if calculate:
        calc = ITRiskCalculator()
        try:
            # ── Compute ───────────────────────────────────────────────────
            ale = calc.fair_risk_calc(lef, lm)
            sim = calc.monte_carlo_sim(lef, lef_std, lm, lm_std)
            roi = calc.roi_calc(ale, post_ale, control_cost)
            lec = calc.lec_score(likelihood, exposure, consequence)

            # ── Results header ────────────────────────────────────────────
            st.divider()
            st.subheader("📈 Results")

            # KPI row
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("FAIR ALE", f"${ale:,.0f}", help="Deterministic annual loss expectancy")
            k2.metric("Monte Carlo Mean ALE", f"${sim['mean_ale']:,.0f}", help="Average across 10,000 simulations")
            k3.metric("P95 ALE (Tail Risk)", f"${sim['p95_ale']:,.0f}", help="Worst-case: 5% of scenarios exceed this")
            k4.metric("LEC Score", f"{lec}", help="Qualitative risk score (L × E × C)")

            # ── FAIR ALE ──────────────────────────────────────────────────
            st.markdown("---")
            st.markdown(f"### 💵 FAIR Annual Loss Expectancy: **${ale:,.2f}**")
            with st.expander("What does this mean?"):
                st.markdown(
                    f"""
                    The **FAIR ALE of ${ale:,.2f}** is your expected financial loss per year from this risk.
                    It's calculated as:

                    > **ALE = LEF × LM = {lef} × ${lm:,.0f} = ${ale:,.2f}**

                    This is a *deterministic* figure — a single point estimate. It's useful for
                    quick comparisons, but doesn't capture uncertainty. That's what Monte Carlo is for.

                    **Use this for**: Board presentations, insurance discussions, budget justifications.
                    """
                )

            # ── Monte Carlo ───────────────────────────────────────────────
            st.markdown(f"### 🎲 Monte Carlo: Mean **${sim['mean_ale']:,.0f}** | P95 **${sim['p95_ale']:,.0f}**")
            with st.expander("What does this mean?"):
                st.markdown(
                    f"""
                    Running 10,000 simulations with your uncertainty inputs produced:

                    - **Mean ALE: ${sim['mean_ale']:,.0f}** — average outcome across all scenarios
                    - **Std Dev: ${sim['std_ale']:,.0f}** — spread / volatility of outcomes
                    - **P95 ALE: ${sim['p95_ale']:,.0f}** — only 5% of scenarios are *worse* than this

                    {"⚠️ **High uncertainty**: Your P95 is more than 3× the mean. Consider tightening your std dev estimates once you have better data." if sim["p95_ale"] > 3 * sim["mean_ale"] else ""}

                    **Use the P95 for pessimistic planning** (worst-case budgets, cyber insurance limits).
                    **Use the Mean for expected-case planning** (annual risk register, ROI analysis).
                    """
                )

            # ── ROI ───────────────────────────────────────────────────────
            roi_label, roi_color, roi_advice = roi_band(roi)
            st.markdown(f"### 📊 Control ROI: **{roi:.1f}%** {roi_label}")
            with st.expander("What does this mean?"):
                savings = ale - post_ale
                st.markdown(
                    f"""
                    Your proposed control costs **${control_cost:,.0f}/year** and is projected to
                    reduce ALE from **${ale:,.0f}** to **${post_ale:,.0f}** — a saving of **${savings:,.0f}/year**.

                    > **ROI = (${savings:,.0f} ÷ ${control_cost:,.0f}) × 100 = {roi:.1f}%**

                    **Rating: {roi_label}** — {roi_advice}

                    {"💡 Tip: If ROI is negative, consider whether the control is right-sized. Could a cheaper alternative achieve similar reduction?" if roi < 0 else ""}
                    {"💡 Tip: ROI >200% is strong. Consider whether the Post-Control ALE estimate is realistic — make sure you're not underestimating residual risk." if roi > 200 else ""}
                    """
                )

            # ── LEC ───────────────────────────────────────────────────────
            lec_label, lec_col, lec_advice = lec_band(lec)
            st.markdown(f"### 🎯 LEC Score: **{lec}** {lec_label}")
            with st.expander("What does this mean?"):
                st.markdown(
                    f"""
                    **LEC = Likelihood ({likelihood}) × Exposure ({exposure}) × Consequence ({consequence}) = {lec}**

                    | Band | Score Range | Action |
                    |------|-------------|--------|
                    | 🟢 Low | 1–99 | Monitor, review annually |
                    | 🟡 Medium | 100–499 | Implement controls within 90 days |
                    | 🔴 High | 500–1000 | Escalate immediately, emergency controls |

                    **Your score of {lec} = {lec_label}**

                    {lec_advice}

                    **Key driver**: {"Consequence is dominant — focus controls on impact reduction (backup, DR, insurance)." if consequence >= max(likelihood, exposure) else "Likelihood is dominant — focus on prevention (access controls, patching, training)." if likelihood >= max(exposure, consequence) else "Exposure is dominant — focus on reducing attack surface (network segmentation, least privilege)."}
                    """
                )

            # ── Charts ────────────────────────────────────────────────────
            st.divider()
            st.subheader("📉 Visualisations")
            fig = calc.generate_charts(sim, roi, lec, ale)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "**Left chart**: Distribution of 10,000 simulated ALE outcomes. "
                "Orange dashed line = Mean. Red dotted line = P95 (tail risk). "
                "**Right chart**: Summary metrics — red = high risk / negative ROI, green = low risk / good ROI."
            )

            # ── Scenario summary ──────────────────────────────────────────
            st.divider()
            st.subheader("📋 Scenario Summary")
            summary_md = f"""
| Metric | Value |
|--------|-------|
| Loss Event Frequency | {lef} events/year |
| Loss Magnitude | ${lm:,.0f} per event |
| **FAIR ALE** | **${ale:,.0f}/year** |
| Monte Carlo Mean ALE | ${sim['mean_ale']:,.0f}/year |
| Monte Carlo P95 ALE | ${sim['p95_ale']:,.0f}/year |
| Control Cost | ${control_cost:,.0f}/year |
| Post-Control ALE | ${post_ale:,.0f}/year |
| **Control ROI** | **{roi:.1f}% — {roi_label}** |
| LEC Score | {lec} — {lec_label} |
            """
            st.markdown(summary_md)
            st.caption("💡 Tip: Take a screenshot of this table for your risk register or board report.")

        except ValueError as e:
            st.error(f"⚠️ Input error: {e}")
            st.info("Check that all fields have valid values and try again.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HOW TO USE
# ══════════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.header("📋 How to Use This Tool")
    st.markdown(
        "This guide walks you through each step of running a risk calculation. "
        "You don't need a background in risk management — just follow the steps."
    )

    st.markdown("""
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
| **LEF Std Dev** | How uncertain is the frequency? | 0.2 (low uncertainty) |
| **LM Std Dev** | How uncertain is the loss amount? | 0.3 (moderate) |

> 💡 **Not sure about std deviations?** Use 0.3–0.5 for most scenarios if you're guessing. Lower values (0.1) mean you're confident; higher (0.5+) means high uncertainty.

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

1. **FAIR ALE** — your baseline annual loss in dollars
2. **Monte Carlo results** — mean + worst-case (P95)
3. **Control ROI** — is the mitigation worth it?
4. **LEC Score** — qualitative risk band (Low / Medium / High)
5. **Charts** — visual distribution of outcomes + summary metrics
6. **Scenario summary table** — screenshot-ready for reports

Use the **expandable "What does this mean?"** sections under each result for interpretation guidance.

---

## Example: Phishing Attack Walkthrough

**Situation**: You want to evaluate a $15,000 security awareness training programme to reduce phishing risk.

**Inputs**:
- LEF: 0.2 (one phishing incident every 5 years)
- LM: $250,000 (data breach cost)
- LEF Std Dev: 0.1 | LM Std Dev: 0.3
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

---

## What's Coming Next (Phase 2)

- 📥 CSV / Excel import for bulk scenario analysis
- 💾 Save and compare multiple scenarios
- 📄 PDF export for board reports
- 🔐 User authentication for team use
- 🗺️ OCTAVE / STRIDE threat model integration
- 📊 Risk heatmap view

---
*Built for IT Risk professionals. Questions? Contact Peter Van Walsem.*
    """)
