import logging

import streamlit as st

from engine import ITRiskCalculator, lec_band, roi_band
from content import (
    EXAMPLES,
    LEF_UNCERTAINTY_PRESETS,
    LM_UNCERTAINTY_PRESETS,
    CURRENCIES,
    DEFAULT_CURRENCY,
    METHODOLOGY_FAIR,
    METHODOLOGY_MONTE_CARLO,
    METHODOLOGY_LEC,
    METHODOLOGY_ROI,
    HOW_TO_USE_MD,
)

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

# ─── Session state defaults (F1, F4) ──────────────────────────────────────────
# F1: computed results persist across reruns instead of living only inside
# `if calculate:` — this is what stopped results from vanishing on any
# widget interaction (e.g. clicking the CSV download button).
if "results" not in st.session_state:
    st.session_state["results"] = None          # dict of computed outputs, or None
if "results_inputs" not in st.session_state:
    st.session_state["results_inputs"] = None    # snapshot of inputs used to compute results
if "loaded_example" not in st.session_state:
    st.session_state["loaded_example"] = "— Select a scenario —"
if "currency_label" not in st.session_state:
    st.session_state["currency_label"] = DEFAULT_CURRENCY


def _current_input_snapshot(lef, lm, lef_std, lm_std, control_cost, post_ale, likelihood, exposure, consequence):
    """Cheap tuple snapshot of all calculation inputs, used to detect staleness (F1)."""
    return (lef, lm, lef_std, lm_std, control_cost, post_ale, likelihood, exposure, consequence)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def lec_label_word(label: str) -> str:
    """'🟡 Medium Risk' -> 'Medium Risk'"""
    return label.split(" ", 1)[-1]


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/cyber-security.png", width=64)
    st.title("🛡️ IT Risk Tool")
    st.caption("Phase 1.5 — Quantitative Risk Dashboard")

    st.divider()

    # F9: currency selector — applies to all $ labels/outputs on the page.
    # Uses a stable widget key ("currency_select") bound one-way into
    # session_state, instead of index=... derived from the same state key
    # being written back into on every rerun — avoids a fragile
    # self-referencing widget pattern that can desync under AppTest/reruns.
    st.markdown("### 💱 Currency")
    selected_currency = st.selectbox(
        "Report currency",
        options=list(CURRENCIES.keys()),
        key="currency_select",
        index=list(CURRENCIES.keys()).index(st.session_state["currency_label"]),
        help="Changes the currency symbol shown in results, charts, and exports. Does not convert values.",
    )
    st.session_state["currency_label"] = selected_currency
    CUR = CURRENCIES[selected_currency]

    st.divider()

    st.markdown("### 📖 Methodologies")
    with st.expander("FAIR (Quantitative)"):
        st.markdown(METHODOLOGY_FAIR)
    with st.expander("Monte Carlo Simulation"):
        st.markdown(METHODOLOGY_MONTE_CARLO)
    with st.expander("LEC (Qualitative)"):
        st.markdown(METHODOLOGY_LEC)
    with st.expander("ROI of Controls"):
        st.markdown(METHODOLOGY_ROI)

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

    # ── Example scenario loader (F4: explicit Load + Reset, no lying dropdown) ──
    st.subheader("🚀 Quick Start — Load an Example Scenario")
    ex_col1, ex_col2, ex_col3 = st.columns([3, 1, 1])
    with ex_col1:
        selected_example = st.selectbox(
            "Choose a pre-built scenario, then click Load — or enter your own values below:",
            options=list(EXAMPLES.keys()),
            index=list(EXAMPLES.keys()).index(st.session_state["loaded_example"])
            if st.session_state["loaded_example"] in EXAMPLES else 0,
        )
    with ex_col2:
        st.markdown("&nbsp;")
        load_clicked = st.button("📥 Load", use_container_width=True, disabled=(selected_example == "— Select a scenario —"))
    with ex_col3:
        st.markdown("&nbsp;")
        reset_clicked = st.button("↺ Reset", use_container_width=True)

    if load_clicked:
        st.session_state["loaded_example"] = selected_example
        ex_to_load = EXAMPLES[selected_example]
        for field in ("lef", "lm", "lef_std", "lm_std", "control_cost", "post_ale",
                      "likelihood", "exposure", "consequence"):
            st.session_state[f"field_{field}"] = ex_to_load[field]
        st.rerun()

    if reset_clicked:
        st.session_state["loaded_example"] = "— Select a scenario —"
        for field in ("lef", "lm", "lef_std", "lm_std", "control_cost", "post_ale",
                      "likelihood", "exposure", "consequence"):
            st.session_state.pop(f"field_{field}", None)
        st.session_state["results"] = None
        st.session_state["results_inputs"] = None
        st.rerun()

    # Whether the currently loaded example still matches (F4: no more lying dropdown)
    is_example_loaded = st.session_state["loaded_example"] != "— Select a scenario —"
    if is_example_loaded:
        ex = EXAMPLES[st.session_state["loaded_example"]]
        st.info(f"**Scenario loaded:** {ex['description']}")
    else:
        st.caption("No example loaded — using your own values (or the defaults below).")

    def field_default(key: str, fallback):
        return st.session_state.get(f"field_{key}", fallback)

    st.divider()

    # ── Input columns ──────────────────────────────────────────────────────
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("#### 📐 FAIR / Monte Carlo Inputs")
        st.caption("These drive the quantitative (dollar) risk calculation.")

        lef = st.number_input(
            "Loss Event Frequency (LEF) — events per year",
            min_value=0.0, max_value=1000.0, value=float(field_default("lef", 1.0)), step=0.1,
            help=(
                "How often do you expect this risk event to occur per year? "
                "Use decimals for less-than-annual events: "
                "0.1 = once every 10 years, 0.5 = once every 2 years, 2.0 = twice per year."
            ),
        )
        lm = st.number_input(
            f"Loss Magnitude (LM) — {CUR} impact per event",
            min_value=1.0, max_value=1_000_000_000.0, value=float(field_default("lm", 100000.0)), step=5000.0,
            help=(
                "What is the average financial impact when this event occurs? "
                "Include direct costs (recovery, fines, legal) and indirect costs "
                "(reputational damage, lost revenue). Use your incident history or insurance data."
            ),
        )

        # F3: plain-language uncertainty presets as the primary control, with an
        # Advanced expander underneath for power users who want exact numbers.
        st.markdown("**Uncertainty (for Monte Carlo)**")

        default_lef_std = float(field_default("lef_std", 0.3))
        default_lm_std = float(field_default("lm_std", 0.3))

        def _closest_preset(value, presets):
            return min(presets, key=lambda k: abs(presets[k] - value))

        lef_preset_choice = st.radio(
            "How uncertain is your frequency estimate?",
            options=list(LEF_UNCERTAINTY_PRESETS.keys()),
            index=list(LEF_UNCERTAINTY_PRESETS.keys()).index(_closest_preset(default_lef_std, LEF_UNCERTAINTY_PRESETS)),
            help="Low = you have solid historical data. High = new/emerging threat, mostly guessing.",
        )
        lef_std = LEF_UNCERTAINTY_PRESETS[lef_preset_choice]

        lm_preset_choice = st.radio(
            "How uncertain is your loss-magnitude estimate?",
            options=list(LM_UNCERTAINTY_PRESETS.keys()),
            index=list(LM_UNCERTAINTY_PRESETS.keys()).index(_closest_preset(default_lm_std, LM_UNCERTAINTY_PRESETS)),
            help="A log-normal distribution models the typically skewed nature of cyber losses.",
        )
        lm_std = LM_UNCERTAINTY_PRESETS[lm_preset_choice]

        with st.expander("⚙️ Advanced — enter exact std dev / CV values"):
            lef_std = st.number_input(
                "LEF Std Dev — frequency uncertainty",
                min_value=0.0, max_value=10.0, value=float(lef_std), step=0.05,
                help="Overrides the Low/Medium/High preset above. Rule of thumb: ~30–50% of LEF for moderate uncertainty.",
            )
            lm_std = st.number_input(
                "Loss Magnitude CV — coefficient of variation (uncertainty as % of mean)",
                min_value=0.0, max_value=2.0, value=float(lm_std), step=0.05,
                help="Overrides the Low/Medium/High preset above. 0.2 = 20% uncertainty, 0.5 = 50% uncertainty.",
            )

    with col_right:
        st.markdown("#### 💰 Control ROI Inputs")
        st.caption("Evaluate whether a security control is worth the investment.")

        control_cost = st.number_input(
            f"Control Cost ({CUR}) — annual cost of the mitigation",
            min_value=1.0, max_value=1_000_000_000.0, value=float(field_default("control_cost", 50000.0)), step=1000.0,
            help=(
                "Total annual cost to implement and run the control. "
                "Include licensing, staff time, training, and maintenance. "
                "One-off costs can be amortised over expected lifetime."
            ),
        )
        post_ale = st.number_input(
            f"Post-Control ALE ({CUR}) — expected ALE after control is applied",
            min_value=0.0, max_value=1_000_000_000.0, value=float(field_default("post_ale", 50000.0)), step=5000.0,
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
            1, 10, int(field_default("likelihood", 5)),
            help="1 = virtually impossible, 5 = possible, 10 = almost certain. Based on threat intelligence and historical data.",
        )
        exposure = st.slider(
            "Exposure (1–10)",
            1, 10, int(field_default("exposure", 5)),
            help="1 = isolated/air-gapped system, 5 = internal network, 10 = internet-facing enterprise-wide asset.",
        )
        consequence = st.slider(
            "Consequence (1–10)",
            1, 10, int(field_default("consequence", 5)),
            help="1 = minor inconvenience, 5 = significant disruption, 10 = catastrophic / business-ending impact.",
        )

    # ── Calculate button ───────────────────────────────────────────────────
    st.divider()
    calc_col, _ = st.columns([1, 3])
    with calc_col:
        calculate = st.button("⚡ Calculate Risk", type="primary", use_container_width=True)

    current_snapshot = _current_input_snapshot(
        lef, lm, lef_std, lm_std, control_cost, post_ale, likelihood, exposure, consequence
    )

    if calculate:
        calc = ITRiskCalculator()
        try:
            ale = calc.fair_risk_calc(lef, lm)
            sim = calc.monte_carlo_sim(lef, lef_std, lm, lm_std)
            roi = calc.roi_calc(ale, post_ale, control_cost)
            lec = calc.lec_score(likelihood, exposure, consequence)

            # F1: store results in session_state instead of only using them
            # inline — this is what keeps them visible across reruns caused
            # by any later widget interaction (including the CSV download).
            st.session_state["results"] = {
                "ale": ale, "sim": sim, "roi": roi, "lec": lec,
                "lef": lef, "lm": lm, "lef_std": lef_std, "lm_std": lm_std,
                "control_cost": control_cost, "post_ale": post_ale,
                "likelihood": likelihood, "exposure": exposure, "consequence": consequence,
                "scenario_name": (
                    st.session_state["loaded_example"]
                    if st.session_state["loaded_example"] != "— Select a scenario —"
                    else "This risk scenario"
                ),
            }
            st.session_state["results_inputs"] = current_snapshot
        except ValueError as e:
            st.error(f"⚠️ Input error: {e}")
            st.info("Check that all fields have valid values and try again.")

    # ── Render results whenever present (F1) ───────────────────────────────
    results = st.session_state["results"]
    if results is not None:
        is_stale = st.session_state["results_inputs"] != current_snapshot

        st.divider()
        if is_stale:
            st.warning(
                "⚠️ **Inputs changed since this calculation.** The results below are from your "
                "*previous* inputs. Click **⚡ Calculate Risk** again to refresh them."
            )
        st.subheader("📈 Results")

        ale = results["ale"]
        sim = results["sim"]
        roi = results["roi"]
        lec = results["lec"]
        lef_r, lm_r = results["lef"], results["lm"]
        control_cost_r, post_ale_r = results["control_cost"], results["post_ale"]
        likelihood_r, exposure_r, consequence_r = results["likelihood"], results["exposure"], results["consequence"]
        scenario_name = results["scenario_name"]

        # KPI row
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("FAIR ALE", f"{CUR}{ale:,.0f}", help="Deterministic annual loss expectancy")
        k2.metric("Monte Carlo Mean ALE", f"{CUR}{sim['mean_ale']:,.0f}", help="Average across 10,000 simulations")
        k3.metric("P95 ALE (Tail Risk)", f"{CUR}{sim['p95_ale']:,.0f}", help="Worst-case: 5% of scenarios exceed this")
        k4.metric("LEC Score", f"{lec}", help="Qualitative risk score (L × E × C)")

        # ── FAIR ALE ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"### 💵 FAIR Annual Loss Expectancy: **{CUR}{ale:,.2f}**")
        with st.expander("What does this mean?"):
            st.markdown(
                f"""
                The **FAIR ALE of {CUR}{ale:,.2f}** is your expected financial loss per year from this risk.
                It's calculated as:

                > **ALE = LEF × LM = {lef_r} × {CUR}{lm_r:,.0f} = {CUR}{ale:,.2f}**

                This is a *deterministic* figure — a single point estimate. It's useful for
                quick comparisons, but doesn't capture uncertainty. That's what Monte Carlo is for.

                **Use this for**: Board presentations, insurance discussions, budget justifications.
                """
            )

        # ── Monte Carlo ───────────────────────────────────────────────
        st.markdown(f"### 🎲 Monte Carlo: Mean **{CUR}{sim['mean_ale']:,.0f}** | P95 **{CUR}{sim['p95_ale']:,.0f}**")
        with st.expander("What does this mean?"):
            st.markdown(
                f"""
                Running 10,000 simulations with your uncertainty inputs produced:

                - **Mean ALE: {CUR}{sim['mean_ale']:,.0f}** — average outcome across all scenarios
                - **Std Dev: {CUR}{sim['std_ale']:,.0f}** — spread / volatility of outcomes
                - **P95 ALE: {CUR}{sim['p95_ale']:,.0f}** — only 5% of scenarios are *worse* than this

                {"⚠️ **High uncertainty**: Your P95 is more than 3× the mean. Consider tightening your std dev estimates once you have better data." if sim["p95_ale"] > 3 * sim["mean_ale"] else ""}

                **Use the P95 for pessimistic planning** (worst-case budgets, cyber insurance limits).
                **Use the Mean for expected-case planning** (annual risk register, ROI analysis).
                """
            )

        # ── ROI ───────────────────────────────────────────────────────
        roi_label, roi_color, roi_advice = roi_band(roi)
        st.markdown(f"### 📊 Control ROI: **{roi:.1f}%** {roi_label}")
        with st.expander("What does this mean?"):
            savings = ale - post_ale_r
            st.markdown(
                f"""
                Your proposed control costs **{CUR}{control_cost_r:,.0f}/year** and is projected to
                reduce ALE from **{CUR}{ale:,.0f}** to **{CUR}{post_ale_r:,.0f}** — a saving of **{CUR}{savings:,.0f}/year**.

                > **ROI = ({CUR}{savings:,.0f} ÷ {CUR}{control_cost_r:,.0f}) × 100 = {roi:.1f}%**

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
                **LEC = Likelihood ({likelihood_r}) × Exposure ({exposure_r}) × Consequence ({consequence_r}) = {lec}**

                | Band | Score Range | Action |
                |------|-------------|--------|
                | 🟢 Low | 1–99 | Monitor, review annually |
                | 🟡 Medium | 100–499 | Implement controls within 90 days |
                | 🔴 High | 500–1000 | Escalate immediately, emergency controls |

                **Your score of {lec} = {lec_label}**

                {lec_advice}

                **Key driver**: {"Consequence is dominant — focus controls on impact reduction (backup, DR, insurance)." if consequence_r >= max(likelihood_r, exposure_r) else "Likelihood is dominant — focus on prevention (access controls, patching, training)." if likelihood_r >= max(exposure_r, consequence_r) else "Exposure is dominant — focus on reducing attack surface (network segmentation, least privilege)."}
                """
            )

        # ── Charts ────────────────────────────────────────────────────
        st.divider()
        st.subheader("📉 Visualisations")
        calc_for_charts = ITRiskCalculator()
        fig = calc_for_charts.generate_charts(sim, roi, lec, ale)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "**Left chart**: Distribution of 10,000 simulated ALE outcomes. "
            "Orange dashed line = Mean. Red dotted line = P95 (tail risk). "
            "**Right chart**: Summary metrics — red = high risk / negative ROI, green = low risk / good ROI."
        )

        # ── Inherent vs Residual Risk ──────────────────────────────────
        st.divider()
        st.subheader("⚖️ Inherent vs. Residual Risk")
        st.caption("Inherent = risk before any controls. Residual = risk after the proposed control is applied.")

        residual_lef = lef_r * (post_ale_r / ale) if ale > 0 else lef_r
        residual_lef = max(residual_lef, 0.0)
        ale_reduction_pct = ((ale - post_ale_r) / ale * 100) if ale > 0 else 0
        p95_residual_estimate = sim['p95_ale'] * (post_ale_r / ale) if ale > 0 else sim['p95_ale']
        lec_residual = max(1, round(lec * (post_ale_r / ale))) if ale > 0 else lec
        lec_residual_label, _, _ = lec_band(lec_residual)

        ir_col1, ir_col2, ir_col3 = st.columns([2, 1, 2])
        with ir_col1:
            st.markdown("**🔴 Inherent Risk** *(no controls)*")
            st.metric("ALE", f"{CUR}{ale:,.0f}")
            st.metric("P95 ALE", f"{CUR}{sim['p95_ale']:,.0f}")
            st.metric("LEC Score", f"{lec} — {lec_label_word(lec_label)}")
        with ir_col2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            st.markdown("&nbsp;", unsafe_allow_html=True)
            st.markdown("&nbsp;", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;font-size:2rem;padding-top:1.5rem'>→</div>", unsafe_allow_html=True)
            delta_color = "green" if ale_reduction_pct > 0 else "red"
            st.markdown(f"<div style='text-align:center;color:{delta_color};font-weight:bold'>▼ {ale_reduction_pct:.0f}%</div>", unsafe_allow_html=True)
        with ir_col3:
            st.markdown("**🟢 Residual Risk** *(after control)*")
            st.metric("ALE", f"{CUR}{post_ale_r:,.0f}", delta=f"-{CUR}{ale - post_ale_r:,.0f}")
            st.metric("P95 ALE (est.)", f"{CUR}{p95_residual_estimate:,.0f}", delta=f"-{CUR}{sim['p95_ale'] - p95_residual_estimate:,.0f}")
            st.metric("LEC Score (est.)", f"{lec_residual} — {lec_label_word(lec_residual_label)}")

        # ── Auto-generated narrative ───────────────────────────────────
        st.divider()
        st.subheader("📝 Executive Summary")
        severity_word = "low" if lec < 100 else ("medium" if lec < 500 else "high")
        roi_word = "strong" if roi >= 200 else ("good" if roi >= 100 else ("marginal" if roi >= 0 else "negative"))
        control_verdict = (
            "The proposed control is a clear investment — it saves significantly more than it costs."
            if roi >= 100 else (
                "The proposed control shows marginal return. Consider whether a more cost-effective alternative exists."
                if roi >= 0 else
                "The proposed control costs more than the risk it addresses. Reassess control design or scope."
            )
        )
        narrative = (
            f"**{scenario_name.strip('🎣💥🕵️🔐☁️🏦🔑 ')}** carries an expected annual loss of "
            f"**{CUR}{ale:,.0f}**, with a 5% chance of losses exceeding **{CUR}{sim['p95_ale']:,.0f}** in any given year "
            f"(Monte Carlo mean: {CUR}{sim['mean_ale']:,.0f}). "
            f"Overall risk severity is rated **{severity_word.upper()}** (LEC score: {lec}). "
            f"The proposed control requires an annual investment of **{CUR}{control_cost_r:,.0f}** and is projected to "
            f"reduce expected annual losses by **{ale_reduction_pct:.0f}%**, from {CUR}{ale:,.0f} to {CUR}{post_ale_r:,.0f}, "
            f"delivering a **{roi:.0f}% ROI** ({roi_word} return). "
            f"{control_verdict}"
        )
        st.info(narrative)
        if st.button("📋 Copy to clipboard", key="copy_narrative"):
            st.code(narrative.replace("**", ""), language=None)
            st.caption("Select all and copy the text above.")

        # ── Scenario summary + export ──────────────────────────────────
        st.divider()
        st.subheader("📋 Scenario Summary")
        summary_md = f"""
| Metric | Value |
|--------|-------|
| Loss Event Frequency | {lef_r} events/year |
| Loss Magnitude | {CUR}{lm_r:,.0f} per event |
| **FAIR ALE (Inherent)** | **{CUR}{ale:,.0f}/year** |
| Monte Carlo Mean ALE | {CUR}{sim['mean_ale']:,.0f}/year |
| Monte Carlo P95 ALE | {CUR}{sim['p95_ale']:,.0f}/year |
| Control Cost | {CUR}{control_cost_r:,.0f}/year |
| **Post-Control ALE (Residual)** | **{CUR}{post_ale_r:,.0f}/year** |
| ALE Reduction | {ale_reduction_pct:.0f}% |
| **Control ROI** | **{roi:.1f}% — {roi_label}** |
| LEC Score (Inherent) | {lec} — {lec_label} |
| LEC Score (Residual est.) | {lec_residual} — {lec_residual_label} |
        """
        st.markdown(summary_md)

        # ── CSV Export (F1: this button no longer wipes the results above) ──
        import csv
        import io

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["IT Risk Tool — Scenario Export", ""])
        writer.writerow(["Scenario", scenario_name.replace('**', '')])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Loss Event Frequency (LEF)", lef_r])
        writer.writerow(["Loss Magnitude (LM)", f"{CUR}{lm_r:,.0f}"])
        writer.writerow(["FAIR ALE (Inherent)", f"{CUR}{ale:,.0f}"])
        writer.writerow(["Monte Carlo Mean ALE", f"{CUR}{sim['mean_ale']:,.0f}"])
        writer.writerow(["Monte Carlo P95 ALE", f"{CUR}{sim['p95_ale']:,.0f}"])
        writer.writerow(["Monte Carlo Std Dev", f"{CUR}{sim['std_ale']:,.0f}"])
        writer.writerow(["Control Cost", f"{CUR}{control_cost_r:,.0f}"])
        writer.writerow(["Post-Control ALE (Residual)", f"{CUR}{post_ale_r:,.0f}"])
        writer.writerow(["ALE Reduction", f"{ale_reduction_pct:.0f}%"])
        writer.writerow(["Control ROI", f"{roi:.1f}%"])
        writer.writerow(["ROI Rating", roi_label])
        writer.writerow(["LEC Score (Inherent)", lec])
        writer.writerow(["LEC Rating (Inherent)", lec_label])
        writer.writerow(["LEC Score (Residual est.)", lec_residual])
        writer.writerow(["LEC Rating (Residual est.)", lec_residual_label])
        writer.writerow([])
        writer.writerow(["Executive Summary", narrative.replace('**', '')])
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="⬇️ Download Results as CSV",
            data=csv_data,
            file_name="it_risk_scenario_export.csv",
            mime="text/csv",
            help="Download a CSV summary of this scenario — import into Excel or your risk register.",
            key="csv_download",
        )
        st.caption("💡 Tip: Use the CSV export to build a risk register in Excel, or paste the executive summary into a board report.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HOW TO USE
# ══════════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.header("📋 How to Use This Tool")
    st.markdown(
        "This guide walks you through each step of running a risk calculation. "
        "You don't need a background in risk management — just follow the steps."
    )
    st.markdown(HOW_TO_USE_MD)
