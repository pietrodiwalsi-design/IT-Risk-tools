"""
IT Risk Quantification Dashboard — UI layer.

Phase 2 flow redesign (docs/ux-review-and-improvement-plan.md, section 3):
Tab 1 restructured from one long scrolling page into a 4-step stepper:
  1. Scenario   - name/description, example load, method choice (F5, F8)
  2. Inputs     - only fields for the chosen method, plain-language labels (F3)
  3. Results    - KPI row pinned on top, inherent-vs-residual toggle (F2)
  4. Report     - executive summary + one-click Markdown download + CSV (F7)

Post-preview feedback (2026-07-07) folded in:
  - Sidebar removed entirely; Currency selector moved into a top bar next
    to the tab strip (nothing left worth a persistent side panel once the
    methodology theory moved to How to Use).
  - New "Saved Assessments" tab: lightweight dashboard of previously saved
    calculations (storage.py), with a delete button per row.

Engine (engine.py) and content (content.py) are unchanged in behaviour --
only the UI/flow around them was rebuilt, per the Phase 1.5 module split
that exists specifically to de-risk this kind of UI rewrite.
"""
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
import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="IT Risk Tool",
    page_icon="\U0001F6E1\uFE0F",
    layout="wide",
)

STEPS = ["1. Scenario", "2. Inputs", "3. Results", "4. Report"]
METHODS = ["Quick scan (LEC)", "Full quantification (FAIR + Monte Carlo)"]

# --- Session state defaults --------------------------------------------------
if "step" not in st.session_state:
    st.session_state["step"] = 0
if "method" not in st.session_state:
    st.session_state["method"] = METHODS[1]
if "results" not in st.session_state:
    st.session_state["results"] = None
if "results_inputs" not in st.session_state:
    st.session_state["results_inputs"] = None
if "loaded_example" not in st.session_state:
    st.session_state["loaded_example"] = "— Select a scenario —"
if "custom_scenario_text" not in st.session_state:
    st.session_state["custom_scenario_text"] = ""
if "currency_label" not in st.session_state:
    st.session_state["currency_label"] = DEFAULT_CURRENCY


def _current_input_snapshot(lef, lm, lef_std, lm_std, control_cost, post_ale,
                             likelihood, exposure, consequence, method):
    return (lef, lm, lef_std, lm_std, control_cost, post_ale, likelihood, exposure, consequence, method)


def lec_label_word(label: str) -> str:
    return label.split(" ", 1)[-1]


def is_quick_scan() -> bool:
    return st.session_state["method"] == METHODS[0]


def goto_step(index: int) -> None:
    st.session_state["step"] = index


def field_default(key: str, fallback):
    return st.session_state.get(f"field_{key}", fallback)


def resolve_scenario_name() -> str:
    """Custom free-text description (if provided) takes precedence over a
    loaded example name; falls back to a generic label if neither is set."""
    custom_text = st.session_state.get("custom_scenario_text", "").strip()
    if custom_text:
        return custom_text
    if st.session_state["loaded_example"] != "— Select a scenario —":
        return st.session_state["loaded_example"]
    return "This risk scenario"


# --- Top bar: title + currency selector (sidebar removed entirely -- ------
# nothing left in it justified a persistent side panel once the F6 fix
# moved all methodology theory into the How to Use tab). -------------------
title_col, currency_col = st.columns([4, 1])
with title_col:
    st.title("\U0001F6E1️ IT Risk Tool")
    st.caption("Phase 2 — Guided Risk Assessment | [Source code](https://github.com/pietrodiwalsi-design/IT-Risk-tools)")
with currency_col:
    selected_currency = st.selectbox(
        "\U0001F4B1 Currency",
        options=list(CURRENCIES.keys()),
        key="currency_select",
        index=list(CURRENCIES.keys()).index(st.session_state["currency_label"]),
        help="Changes the currency symbol shown in results, charts, and exports. Does not convert values.",
    )
    st.session_state["currency_label"] = selected_currency
CUR = CURRENCIES[selected_currency]

# Note: the Tips box and the "See How to Use for FAIR/Monte Carlo/LEC/ROI
# theory" pointer that used to live in the sidebar (Phase 1.5) are gone
# along with the sidebar itself in Phase 2 -- there is no longer a
# persistent side panel to put them in. The How to Use tab remains the
# single source of truth for methodology theory (F6).


# --- Main area -----------------------------------------------------------------
tab_calc, tab_saved, tab_guide = st.tabs([
    "\U0001F4CA Risk Calculator", "\U0001F4C1 Saved Assessments", "\U0001F4CB How to Use",
], key="main_tabs", on_change="rerun")

with tab_calc:
    if tab_calc.open:
        st.header("IT Risk Calculator")

        step_cols = st.columns(4)
        for i, (col, label) in enumerate(zip(step_cols, STEPS)):
            with col:
                if i < st.session_state["step"]:
                    st.success(label)
                elif i == st.session_state["step"]:
                    st.info(f"**{label}**")
                else:
                    st.caption(label)

        st.divider()

        current_step = st.session_state["step"]

        # =========================================================================
        # STEP 1 - SCENARIO
        # =========================================================================
        if current_step == 0:
            st.subheader("Step 1 — Describe Your Scenario")
            st.markdown(
                "Start from a real-world example, or go straight to entering your own values. "
                "Then choose how deep you want to go."
            )

            st.markdown("#### \U0001F680 Load an Example (optional)")
            ex_col1, ex_col2 = st.columns([3, 1])
            with ex_col1:
                selected_example = st.selectbox(
                    "Choose a pre-built scenario:",
                    options=list(EXAMPLES.keys()),
                    index=list(EXAMPLES.keys()).index(st.session_state["loaded_example"])
                    if st.session_state["loaded_example"] in EXAMPLES else 0,
                    label_visibility="collapsed",
                    key="step1_example_select",
                )
            with ex_col2:
                load_clicked = st.button(
                    "\U0001F4E5 Load", use_container_width=True,
                    disabled=(selected_example == "— Select a scenario —"),
                    key="step1_load_btn",
                )

            if load_clicked:
                st.session_state["loaded_example"] = selected_example
                st.session_state["custom_scenario_text"] = ""
                ex_to_load = EXAMPLES[selected_example]
                for field in ("lef", "lm", "lef_std", "lm_std", "control_cost", "post_ale",
                              "likelihood", "exposure", "consequence"):
                    st.session_state[f"field_{field}"] = ex_to_load[field]
                st.rerun()

            is_example_loaded = st.session_state["loaded_example"] != "— Select a scenario —"
            if is_example_loaded:
                ex = EXAMPLES[st.session_state["loaded_example"]]
                loaded_col1, loaded_col2 = st.columns([4, 1])
                with loaded_col1:
                    st.success(f"**Loaded:** {ex['description']}")
                with loaded_col2:
                    if st.button("↺ Reset", use_container_width=True, key="step1_reset_btn"):
                        st.session_state["loaded_example"] = "— Select a scenario —"
                        for field in ("lef", "lm", "lef_std", "lm_std", "control_cost", "post_ale",
                                      "likelihood", "exposure", "consequence"):
                            st.session_state.pop(f"field_{field}", None)
                        st.session_state["results"] = None
                        st.session_state["results_inputs"] = None
                        st.rerun()
            else:
                st.caption("No example loaded — you'll enter your own values in the next step.")

            st.divider()

            # --- Free-text scenario description (own risk, no preset needed) ---
            st.markdown("#### \u270D\uFE0F Or Describe Your Own Risk")
            st.caption(
                "Not one of the examples above? Write your own scenario in plain language — "
                "it will be used as the scenario name/description on Results and in the Report/export, "
                "instead of an example name."
            )
            custom_text = st.text_area(
                "Describe your risk scenario:",
                value=st.session_state["custom_scenario_text"],
                placeholder=(
                    "e.g. A third-party payroll vendor suffers a breach exposing employee bank details, "
                    "triggering mandatory notification costs and reputational damage."
                ),
                height=100,
                label_visibility="collapsed",
                key="step1_custom_scenario_text",
            )
            if custom_text != st.session_state["custom_scenario_text"]:
                st.session_state["custom_scenario_text"] = custom_text
                if custom_text.strip():
                    # A custom description takes precedence over any loaded example name.
                    st.session_state["loaded_example"] = "— Select a scenario —"

            if st.session_state["custom_scenario_text"].strip():
                st.info(f"**Your scenario:** {st.session_state['custom_scenario_text'].strip()}")

            st.divider()

            st.markdown("#### \U0001F3AF Choose Your Method")
            method_choice = st.radio(
                "How deep do you want to go?",
                options=METHODS,
                index=METHODS.index(st.session_state["method"]),
                help=(
                    "**Quick scan**: 3 sliders (Likelihood x Exposure x Consequence), no dollar values needed — "
                    "good for a first-pass ranking across many risks, in about 30 seconds.\n\n"
                    "**Full quantification**: FAIR + Monte Carlo simulation, produces a dollar-based Annual Loss "
                    "Expectancy and Control ROI — good for board reports and budget justification."
                ),
                key="step1_method_radio",
            )
            st.session_state["method"] = method_choice

            if is_quick_scan():
                st.caption("✅ You'll only see the 3 LEC sliders next — no financial data required.")
            else:
                st.caption("✅ You'll enter frequency/impact figures plus a proposed control cost next.")

            st.divider()
            _, nav_col = st.columns([3, 1])
            with nav_col:
                if st.button("Next: Inputs →", type="primary", use_container_width=True, key="step1_next_btn"):
                    goto_step(1)
                    st.rerun()

        # =========================================================================
        # STEP 2 - INPUTS
        # =========================================================================
        elif current_step == 1:
            st.subheader("Step 2 — Enter Your Inputs")
            quick = is_quick_scan()

            if quick:
                st.markdown("#### \U0001F3AF Quick Scan — Likelihood x Exposure x Consequence")
                st.caption("Three sliders, no dollar values needed. Good for ranking many risks quickly.")

                likelihood = st.slider(
                    "Likelihood — how probable is this threat? (1–10)",
                    1, 10, int(field_default("likelihood", 5)),
                    help="1 = virtually impossible, 5 = possible, 10 = almost certain. Based on threat intel and history.",
                    key="step2_quick_likelihood",
                )
                exposure = st.slider(
                    "Exposure — how exposed is the asset? (1–10)",
                    1, 10, int(field_default("exposure", 5)),
                    help="1 = isolated/air-gapped system, 5 = internal network, 10 = internet-facing enterprise-wide asset.",
                    key="step2_quick_exposure",
                )
                consequence = st.slider(
                    "Consequence — how bad if it happens? (1–10)",
                    1, 10, int(field_default("consequence", 5)),
                    help="1 = minor inconvenience, 5 = significant disruption, 10 = catastrophic / business-ending impact.",
                    key="step2_quick_consequence",
                )
                # Quick scan doesn't need FAIR/ROI fields — keep last-known or sane
                # defaults so downstream code (shared with Full quantification)
                # always has a value to work with.
                lef = float(field_default("lef", 1.0))
                lm = float(field_default("lm", 100000.0))
                lef_std = float(field_default("lef_std", 0.3))
                lm_std = float(field_default("lm_std", 0.3))
                control_cost = float(field_default("control_cost", 50000.0))
                post_ale = float(field_default("post_ale", 50000.0))

            else:
                st.markdown("#### \U0001F4D0 FAIR / Monte Carlo Inputs")
                st.caption("These drive the quantitative (dollar) risk calculation.")

                in_col1, in_col2 = st.columns(2, gap="large")

                with in_col1:
                    lef = st.number_input(
                        "Loss Event Frequency (LEF) — events per year",
                        min_value=0.0, max_value=1000.0, value=float(field_default("lef", 1.0)), step=0.1,
                        help=(
                            "How often do you expect this risk event to occur per year? "
                            "Use decimals for less-than-annual events: "
                            "0.1 = once every 10 years, 0.5 = once every 2 years, 2.0 = twice per year."
                        ),
                        key="step2_full_lef",
                    )
                    lm = st.number_input(
                        f"Loss Magnitude (LM) — {CUR} impact per event",
                        min_value=1.0, max_value=1_000_000_000.0, value=float(field_default("lm", 100000.0)), step=5000.0,
                        help=(
                            "What is the average financial impact when this event occurs? "
                            "Include direct costs (recovery, fines, legal) and indirect costs "
                            "(reputational damage, lost revenue). Use your incident history or insurance data."
                        ),
                        key="step2_full_lm",
                    )

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
                        key="step2_lef_preset",
                    )
                    lef_std = LEF_UNCERTAINTY_PRESETS[lef_preset_choice]

                    lm_preset_choice = st.radio(
                        "How uncertain is your loss-magnitude estimate?",
                        options=list(LM_UNCERTAINTY_PRESETS.keys()),
                        index=list(LM_UNCERTAINTY_PRESETS.keys()).index(_closest_preset(default_lm_std, LM_UNCERTAINTY_PRESETS)),
                        help="A log-normal distribution models the typically skewed nature of cyber losses.",
                        key="step2_lm_preset",
                    )
                    lm_std = LM_UNCERTAINTY_PRESETS[lm_preset_choice]

                    with st.expander("\u2699️ Advanced — enter exact std dev / CV values"):
                        lef_std = st.number_input(
                            "LEF Std Dev — frequency uncertainty",
                            min_value=0.0, max_value=10.0, value=float(lef_std), step=0.05,
                            help="Overrides the Low/Medium/High preset above. Rule of thumb: ~30–50% of LEF for moderate uncertainty.",
                            key="step2_lef_std_advanced",
                        )
                        lm_std = st.number_input(
                            "Loss Magnitude CV — coefficient of variation (uncertainty as % of mean)",
                            min_value=0.0, max_value=2.0, value=float(lm_std), step=0.05,
                            help="Overrides the Low/Medium/High preset above. 0.2 = 20% uncertainty, 0.5 = 50% uncertainty.",
                            key="step2_lm_std_advanced",
                        )

                with in_col2:
                    st.markdown("#### \U0001F4B0 Control ROI Inputs")
                    st.caption("Evaluate whether a security control is worth the investment.")

                    control_cost = st.number_input(
                        f"Control Cost ({CUR}) — annual cost of the mitigation",
                        min_value=1.0, max_value=1_000_000_000.0, value=float(field_default("control_cost", 50000.0)), step=1000.0,
                        help=(
                            "Total annual cost to implement and run the control. "
                            "Include licensing, staff time, training, and maintenance. "
                            "One-off costs can be amortised over expected lifetime."
                        ),
                        key="step2_control_cost",
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
                        key="step2_post_ale",
                    )

                    st.markdown("#### \U0001F3AF LEC Qualitative Inputs")
                    st.caption("Also captured, for a quick qualitative cross-check alongside the dollar figures.")

                    likelihood = st.slider(
                        "Likelihood (1–10)",
                        1, 10, int(field_default("likelihood", 5)),
                        help="1 = virtually impossible, 5 = possible, 10 = almost certain.",
                        key="step2_full_likelihood",
                    )
                    exposure = st.slider(
                        "Exposure (1–10)",
                        1, 10, int(field_default("exposure", 5)),
                        help="1 = isolated/air-gapped system, 5 = internal network, 10 = internet-facing enterprise-wide asset.",
                        key="step2_full_exposure",
                    )
                    consequence = st.slider(
                        "Consequence (1–10)",
                        1, 10, int(field_default("consequence", 5)),
                        help="1 = minor inconvenience, 5 = significant disruption, 10 = catastrophic / business-ending impact.",
                        key="step2_full_consequence",
                    )

            # Persist current widget values so they survive step navigation
            for key, val in (
                ("lef", lef), ("lm", lm), ("lef_std", lef_std), ("lm_std", lm_std),
                ("control_cost", control_cost), ("post_ale", post_ale),
                ("likelihood", likelihood), ("exposure", exposure), ("consequence", consequence),
            ):
                st.session_state[f"field_{key}"] = val

            st.divider()
            back_col, calc_col = st.columns([1, 1])
            with back_col:
                if st.button("← Back: Scenario", use_container_width=True, key="step2_back_btn"):
                    goto_step(0)
                    st.rerun()
            with calc_col:
                calculate = st.button("\u26a1 Calculate Risk", type="primary", use_container_width=True, key="step2_calculate_btn")

            if calculate:
                calc = ITRiskCalculator()
                try:
                    if quick:
                        lec = calc.lec_score(likelihood, exposure, consequence)
                        st.session_state["results"] = {
                            "quick_scan": True,
                            "lec": lec,
                            "likelihood": likelihood, "exposure": exposure, "consequence": consequence,
                            "scenario_name": resolve_scenario_name(),
                        }
                    else:
                        ale = calc.fair_risk_calc(lef, lm)
                        sim = calc.monte_carlo_sim(lef, lef_std, lm, lm_std)
                        roi = calc.roi_calc(ale, post_ale, control_cost)
                        lec = calc.lec_score(likelihood, exposure, consequence)

                        st.session_state["results"] = {
                            "quick_scan": False,
                            "ale": ale, "sim": sim, "roi": roi, "lec": lec,
                            "lef": lef, "lm": lm, "lef_std": lef_std, "lm_std": lm_std,
                            "control_cost": control_cost, "post_ale": post_ale,
                            "likelihood": likelihood, "exposure": exposure, "consequence": consequence,
                            "scenario_name": resolve_scenario_name(),
                        }
                    st.session_state["results_inputs"] = _current_input_snapshot(
                        lef, lm, lef_std, lm_std, control_cost, post_ale, likelihood, exposure, consequence,
                        st.session_state["method"],
                    )
                    goto_step(2)
                    st.rerun()
                except ValueError as e:
                    st.error(f"\u26a0️ Input error: {e}")
                    st.info("Check that all fields have valid values and try again.")

        # =========================================================================
        # STEP 3 - RESULTS
        # =========================================================================
        elif current_step == 2:
            results = st.session_state["results"]

            if results is None:
                st.warning("No results yet — go to Step 2 and click **Calculate Risk** first.")
                if st.button("← Back: Inputs", key="step3_empty_back_btn"):
                    goto_step(1)
                    st.rerun()
            else:
                st.subheader("Step 3 — Results")
                st.caption(f"\U0001F4CB Scenario: **{results['scenario_name']}**")

                current_snapshot = _current_input_snapshot(
                    float(field_default("lef", 1.0)), float(field_default("lm", 100000.0)),
                    float(field_default("lef_std", 0.3)), float(field_default("lm_std", 0.3)),
                    float(field_default("control_cost", 50000.0)), float(field_default("post_ale", 50000.0)),
                    int(field_default("likelihood", 5)), int(field_default("exposure", 5)),
                    int(field_default("consequence", 5)), st.session_state["method"],
                )
                is_stale = st.session_state["results_inputs"] != current_snapshot
                if is_stale:
                    st.warning(
                        "\u26a0️ **Inputs changed since this calculation.** These results are from your "
                        "*previous* inputs. Go back to Step 2 and click **Calculate Risk** again to refresh."
                    )

                scenario_name = results["scenario_name"]
                quick = results.get("quick_scan", False)
                lec = results["lec"]
                lec_label, lec_col, lec_advice = lec_band(lec)

                # --- KPI row, pinned at the top regardless of method (F2) ---------
                if quick:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Likelihood", results["likelihood"])
                    k2.metric("Exposure", results["exposure"])
                    k3.metric("Consequence", results["consequence"])
                    st.markdown(f"### \U0001F3AF LEC Score: **{lec}** {lec_label}")
                else:
                    ale = results["ale"]
                    sim = results["sim"]
                    roi = results["roi"]
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("FAIR ALE", f"{CUR}{ale:,.0f}", help="Deterministic annual loss expectancy")
                    k2.metric("Monte Carlo Mean ALE", f"{CUR}{sim['mean_ale']:,.0f}", help="Average across 10,000 simulations")
                    k3.metric("P95 ALE (Tail Risk)", f"{CUR}{sim['p95_ale']:,.0f}", help="Worst-case: 5% of scenarios exceed this")
                    k4.metric("LEC Score", f"{lec}", help="Qualitative risk score (L x E x C)")

                st.divider()

                if quick:
                    st.markdown(f"### \U0001F3AF LEC Score: **{lec}** {lec_label}")
                    likelihood_r, exposure_r, consequence_r = results["likelihood"], results["exposure"], results["consequence"]
                    with st.expander("What does this mean?", expanded=True):
                        st.markdown(
                            f"""
    **LEC = Likelihood ({likelihood_r}) x Exposure ({exposure_r}) x Consequence ({consequence_r}) = {lec}**

    | Band | Score Range | Action |
    |------|-------------|--------|
    | \U0001F7E2 Low | 1–99 | Monitor, review annually |
    | \U0001F7E1 Medium | 100–499 | Implement controls within 90 days |
    | \U0001F534 High | 500–1000 | Escalate immediately, emergency controls |

    **Your score of {lec} = {lec_label}**

    {lec_advice}

    **Key driver**: {"Consequence is dominant — focus controls on impact reduction (backup, DR, insurance)." if consequence_r >= max(likelihood_r, exposure_r) else "Likelihood is dominant — focus on prevention (access controls, patching, training)." if likelihood_r >= max(exposure_r, consequence_r) else "Exposure is dominant — focus on reducing attack surface (network segmentation, least privilege)."}

    \U0001F4A1 **Want a dollar figure too?** Go back to Step 1 and switch to **Full quantification**.
                            """
                        )
                else:
                    ale = results["ale"]
                    sim = results["sim"]
                    roi = results["roi"]
                    lef_r, lm_r = results["lef"], results["lm"]
                    control_cost_r, post_ale_r = results["control_cost"], results["post_ale"]
                    likelihood_r, exposure_r, consequence_r = results["likelihood"], results["exposure"], results["consequence"]

                    st.markdown(f"### \U0001F4B5 FAIR Annual Loss Expectancy: **{CUR}{ale:,.2f}**")
                    with st.expander("What does this mean?"):
                        st.markdown(
                            f"""
    The **FAIR ALE of {CUR}{ale:,.2f}** is your expected financial loss per year from this risk.
    It's calculated as:

    > **ALE = LEF x LM = {lef_r} x {CUR}{lm_r:,.0f} = {CUR}{ale:,.2f}**

    This is a *deterministic* figure — a single point estimate. It's useful for
    quick comparisons, but doesn't capture uncertainty. That's what Monte Carlo is for.

    **Use this for**: Board presentations, insurance discussions, budget justifications.
                            """
                        )

                    st.markdown(f"### \U0001F3B2 Monte Carlo: Mean **{CUR}{sim['mean_ale']:,.0f}** | P95 **{CUR}{sim['p95_ale']:,.0f}**")
                    with st.expander("What does this mean?"):
                        high_uncertainty_note = (
                            "\u26a0️ **High uncertainty**: Your P95 is more than 3x the mean. "
                            "Consider tightening your std dev estimates once you have better data."
                            if sim["p95_ale"] > 3 * sim["mean_ale"] else ""
                        )
                        st.markdown(
                            f"""
    Running 10,000 simulations with your uncertainty inputs produced:

    - **Mean ALE: {CUR}{sim['mean_ale']:,.0f}** — average outcome across all scenarios
    - **Std Dev: {CUR}{sim['std_ale']:,.0f}** — spread / volatility of outcomes
    - **P95 ALE: {CUR}{sim['p95_ale']:,.0f}** — only 5% of scenarios are *worse* than this

    {high_uncertainty_note}

    **Use the P95 for pessimistic planning** (worst-case budgets, cyber insurance limits).
    **Use the Mean for expected-case planning** (annual risk register, ROI analysis).
                            """
                        )

                    roi_label, roi_color, roi_advice = roi_band(roi)
                    st.markdown(f"### \U0001F4CA Control ROI: **{roi:.1f}%** {roi_label}")
                    with st.expander("What does this mean?"):
                        savings = ale - post_ale_r
                        roi_negative_tip = (
                            "\U0001F4A1 Tip: If ROI is negative, consider whether the control is right-sized. "
                            "Could a cheaper alternative achieve similar reduction?" if roi < 0 else ""
                        )
                        roi_high_tip = (
                            "\U0001F4A1 Tip: ROI >200% is strong. Consider whether the Post-Control ALE estimate "
                            "is realistic — make sure you're not underestimating residual risk." if roi > 200 else ""
                        )
                        st.markdown(
                            f"""
    Your proposed control costs **{CUR}{control_cost_r:,.0f}/year** and is projected to
    reduce ALE from **{CUR}{ale:,.0f}** to **{CUR}{post_ale_r:,.0f}** — a saving of **{CUR}{savings:,.0f}/year**.

    > **ROI = ({CUR}{savings:,.0f} / {CUR}{control_cost_r:,.0f}) x 100 = {roi:.1f}%**

    **Rating: {roi_label}** — {roi_advice}

    {roi_negative_tip}
    {roi_high_tip}
                            """
                        )

                    st.markdown(f"### \U0001F3AF LEC Score: **{lec}** {lec_label}")
                    with st.expander("What does this mean?"):
                        st.markdown(
                            f"""
    **LEC = Likelihood ({likelihood_r}) x Exposure ({exposure_r}) x Consequence ({consequence_r}) = {lec}**

    | Band | Score Range | Action |
    |------|-------------|--------|
    | \U0001F7E2 Low | 1–99 | Monitor, review annually |
    | \U0001F7E1 Medium | 100–499 | Implement controls within 90 days |
    | \U0001F534 High | 500–1000 | Escalate immediately, emergency controls |

    **Your score of {lec} = {lec_label}**

    {lec_advice}

    **Key driver**: {"Consequence is dominant — focus controls on impact reduction (backup, DR, insurance)." if consequence_r >= max(likelihood_r, exposure_r) else "Likelihood is dominant — focus on prevention (access controls, patching, training)." if likelihood_r >= max(exposure_r, consequence_r) else "Exposure is dominant — focus on reducing attack surface (network segmentation, least privilege)."}
                            """
                        )

                    st.divider()
                    st.subheader("\U0001F4C9 Visualisations")
                    calc_for_charts = ITRiskCalculator()
                    fig = calc_for_charts.generate_charts(sim, roi, lec, ale)
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(
                        "**Left chart**: Distribution of 10,000 simulated ALE outcomes. "
                        "Orange dashed line = Mean. Red dotted line = P95 (tail risk). "
                        "**Right chart**: Summary metrics — red = high risk / negative ROI, green = low risk / good ROI."
                    )

                    # --- Inherent vs Residual Risk, as a toggle instead of a
                    # second always-visible table (F2) ---------------------------
                    st.divider()
                    st.subheader("\u2696️ Inherent vs. Residual Risk")
                    show_residual = st.toggle(
                        "Show residual risk (after the proposed control is applied)",
                        value=True,
                        help="Inherent = risk before any controls. Residual = risk after the proposed control.",
                        key="step3_show_residual_toggle",
                    )

                    residual_lef = lef_r * (post_ale_r / ale) if ale > 0 else lef_r
                    residual_lef = max(residual_lef, 0.0)
                    ale_reduction_pct = ((ale - post_ale_r) / ale * 100) if ale > 0 else 0
                    p95_residual_estimate = sim['p95_ale'] * (post_ale_r / ale) if ale > 0 else sim['p95_ale']
                    lec_residual = max(1, round(lec * (post_ale_r / ale))) if ale > 0 else lec
                    lec_residual_label, _, _ = lec_band(lec_residual)

                    if not show_residual:
                        st.markdown("**\U0001F534 Inherent Risk** *(no controls)*")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("ALE", f"{CUR}{ale:,.0f}")
                        m2.metric("P95 ALE", f"{CUR}{sim['p95_ale']:,.0f}")
                        m3.metric("LEC Score", f"{lec} — {lec_label_word(lec_label)}")
                    else:
                        ir_col1, ir_col2, ir_col3 = st.columns([2, 1, 2])
                        with ir_col1:
                            st.markdown("**\U0001F534 Inherent Risk** *(no controls)*")
                            st.metric("ALE", f"{CUR}{ale:,.0f}")
                            st.metric("P95 ALE", f"{CUR}{sim['p95_ale']:,.0f}")
                            st.metric("LEC Score", f"{lec} — {lec_label_word(lec_label)}")
                        with ir_col2:
                            st.markdown("&nbsp;", unsafe_allow_html=True)
                            st.markdown("&nbsp;", unsafe_allow_html=True)
                            st.markdown("&nbsp;", unsafe_allow_html=True)
                            st.markdown("<div style='text-align:center;font-size:2rem;padding-top:1.5rem'>\u2192</div>", unsafe_allow_html=True)
                            delta_color = "green" if ale_reduction_pct > 0 else "red"
                            st.markdown(f"<div style='text-align:center;color:{delta_color};font-weight:bold'>\u25bc {ale_reduction_pct:.0f}%</div>", unsafe_allow_html=True)
                        with ir_col3:
                            st.markdown("**\U0001F7E2 Residual Risk** *(after control)*")
                            st.metric("ALE", f"{CUR}{post_ale_r:,.0f}", delta=f"-{CUR}{ale - post_ale_r:,.0f}")
                            st.metric("P95 ALE (est.)", f"{CUR}{p95_residual_estimate:,.0f}", delta=f"-{CUR}{sim['p95_ale'] - p95_residual_estimate:,.0f}")
                            st.metric("LEC Score (est.)", f"{lec_residual} — {lec_label_word(lec_residual_label)}")

                st.divider()
                back_col, next_col = st.columns([1, 1])
                with back_col:
                    if st.button("← Back: Inputs", use_container_width=True, key="step3_back_btn"):
                        goto_step(1)
                        st.rerun()
                with next_col:
                    if st.button("Next: Report →", type="primary", use_container_width=True, key="step3_next_btn"):
                        goto_step(3)
                        st.rerun()

        # =========================================================================
        # STEP 4 - REPORT
        # =========================================================================
        elif current_step == 3:
            results = st.session_state["results"]

            if results is None:
                st.warning("No results yet — go to Step 2 and click **Calculate Risk** first.")
                if st.button("← Back: Inputs", key="step4_empty_back_btn"):
                    goto_step(1)
                    st.rerun()
            else:
                st.subheader("Step 4 — Report")
                scenario_name = results["scenario_name"]
                quick = results.get("quick_scan", False)
                lec = results["lec"]
                lec_label, _, _ = lec_band(lec)
                clean_scenario_name = scenario_name.strip("\U0001F3A3\U0001F4A5\U0001F575\ufe0f\U0001F510\u2601\ufe0f\U0001F3E6\U0001F511 ")

                if quick:
                    likelihood_r, exposure_r, consequence_r = results["likelihood"], results["exposure"], results["consequence"]
                    narrative = (
                        f"**{clean_scenario_name}** scored **{lec}** on the LEC scale "
                        f"(Likelihood {likelihood_r} x Exposure {exposure_r} x Consequence {consequence_r}), "
                        f"rated **{lec_label}**. This is a qualitative quick-scan result — "
                        f"run a Full quantification for a dollar-based Annual Loss Expectancy and Control ROI."
                    )
                else:
                    ale = results["ale"]
                    sim = results["sim"]
                    roi = results["roi"]
                    control_cost_r, post_ale_r = results["control_cost"], results["post_ale"]
                    severity_word = "low" if lec < 100 else ("medium" if lec < 500 else "high")
                    roi_word = "strong" if roi >= 200 else ("good" if roi >= 100 else ("marginal" if roi >= 0 else "negative"))
                    ale_reduction_pct = ((ale - post_ale_r) / ale * 100) if ale > 0 else 0
                    control_verdict = (
                        "The proposed control is a clear investment — it saves significantly more than it costs."
                        if roi >= 100 else (
                            "The proposed control shows marginal return. Consider whether a more cost-effective alternative exists."
                            if roi >= 0 else
                            "The proposed control costs more than the risk it addresses. Reassess control design or scope."
                        )
                    )
                    narrative = (
                        f"**{clean_scenario_name}** carries an expected annual loss of "
                        f"**{CUR}{ale:,.0f}**, with a 5% chance of losses exceeding **{CUR}{sim['p95_ale']:,.0f}** in any given year "
                        f"(Monte Carlo mean: {CUR}{sim['mean_ale']:,.0f}). "
                        f"Overall risk severity is rated **{severity_word.upper()}** (LEC score: {lec}). "
                        f"The proposed control requires an annual investment of **{CUR}{control_cost_r:,.0f}** and is projected to "
                        f"reduce expected annual losses by **{ale_reduction_pct:.0f}%**, from {CUR}{ale:,.0f} to {CUR}{post_ale_r:,.0f}, "
                        f"delivering a **{roi:.0f}% ROI** ({roi_word} return). "
                        f"{control_verdict}"
                    )

                top_row_col1, top_row_col2 = st.columns([4, 1])
                with top_row_col1:
                    st.subheader("\U0001F4DD Executive Summary")
                with top_row_col2:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    if st.button("\U0001F4BE Save Assessment", use_container_width=True, key="save_assessment_btn"):
                        saved_id = storage.save_assessment(
                            scenario_name=clean_scenario_name,
                            method=st.session_state["method"],
                            results=results,
                            currency_label=st.session_state["currency_label"],
                        )
                        st.session_state["last_saved_id"] = saved_id
                        st.toast("Assessment saved — see the **Saved Assessments** tab.", icon="\U0001F4BE")
                st.info(narrative)

                # --- F7: one-click Markdown report download (new in Phase 2) ------
                report_lines = [
                    f"# IT Risk Assessment — {clean_scenario_name}",
                    "",
                    f"**Method:** {'Quick scan (LEC)' if quick else 'Full quantification (FAIR + Monte Carlo)'}",
                    "",
                    "## Executive Summary",
                    "",
                    narrative.replace("**", ""),
                    "",
                    "## Scenario Details",
                    "",
                ]
                if quick:
                    report_lines += [
                        f"| Metric | Value |",
                        f"|--------|-------|",
                        f"| Likelihood | {results['likelihood']} |",
                        f"| Exposure | {results['exposure']} |",
                        f"| Consequence | {results['consequence']} |",
                        f"| **LEC Score** | **{lec} — {lec_label_word(lec_label)}** |",
                    ]
                else:
                    ale = results["ale"]
                    sim = results["sim"]
                    roi = results["roi"]
                    lef_r, lm_r = results["lef"], results["lm"]
                    control_cost_r, post_ale_r = results["control_cost"], results["post_ale"]
                    roi_label, _, _ = roi_band(roi)
                    ale_reduction_pct = ((ale - post_ale_r) / ale * 100) if ale > 0 else 0
                    report_lines += [
                        "| Metric | Value |",
                        "|--------|-------|",
                        f"| Loss Event Frequency | {lef_r} events/year |",
                        f"| Loss Magnitude | {CUR}{lm_r:,.0f} per event |",
                        f"| **FAIR ALE (Inherent)** | **{CUR}{ale:,.0f}/year** |",
                        f"| Monte Carlo Mean ALE | {CUR}{sim['mean_ale']:,.0f}/year |",
                        f"| Monte Carlo P95 ALE | {CUR}{sim['p95_ale']:,.0f}/year |",
                        f"| Control Cost | {CUR}{control_cost_r:,.0f}/year |",
                        f"| **Post-Control ALE (Residual)** | **{CUR}{post_ale_r:,.0f}/year** |",
                        f"| ALE Reduction | {ale_reduction_pct:.0f}% |",
                        f"| **Control ROI** | **{roi:.1f}% — {roi_label}** |",
                        f"| LEC Score | {lec} — {lec_label_word(lec_label)} |",
                    ]
                report_lines += ["", "---", f"*Generated by IT Risk Tool.*"]
                report_md = "\n".join(report_lines)

                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button(
                        label="\U0001F4C4 Download Report (Markdown)",
                        data=report_md,
                        file_name="it_risk_report.md",
                        mime="text/markdown",
                        help="One-click report: executive summary + full scenario table. Paste into a board deck or wiki.",
                        key="md_download",
                        use_container_width=True,
                    )

                if not quick:
                    st.divider()
                    st.subheader("\U0001F4CB Scenario Summary")
                    ale = results["ale"]
                    sim = results["sim"]
                    roi = results["roi"]
                    lef_r, lm_r = results["lef"], results["lm"]
                    control_cost_r, post_ale_r = results["control_cost"], results["post_ale"]
                    roi_label, _, _ = roi_band(roi)
                    ale_reduction_pct = ((ale - post_ale_r) / ale * 100) if ale > 0 else 0

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
    | LEC Score | {lec} — {lec_label_word(lec_label)} |
                    """
                    st.markdown(summary_md)

                    import csv
                    import io

                    csv_buffer = io.StringIO()
                    writer = csv.writer(csv_buffer)
                    writer.writerow(["IT Risk Tool — Scenario Export", ""])
                    writer.writerow(["Scenario", clean_scenario_name])
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
                    writer.writerow(["LEC Score", lec])
                    writer.writerow(["LEC Rating", lec_label])
                    writer.writerow([])
                    writer.writerow(["Executive Summary", narrative.replace("**", "")])
                    csv_data = csv_buffer.getvalue()

                    with dl_col2:
                        st.download_button(
                            label="\u2b07️ Download Results as CSV",
                            data=csv_data,
                            file_name="it_risk_scenario_export.csv",
                            mime="text/csv",
                            help="Download a CSV summary of this scenario — import into Excel or your risk register.",
                            key="csv_download",
                            use_container_width=True,
                        )
                    st.caption("\U0001F4A1 Tip: Use the CSV export to build a risk register in Excel, or the Markdown report for a board deck.")

                st.divider()
                back_col2, new_col = st.columns([1, 1])
                with back_col2:
                    if st.button("← Back: Results", use_container_width=True, key="step4_back_btn"):
                        goto_step(2)
                        st.rerun()
                with new_col:
                    if st.button("\U0001F504 Start a New Assessment", use_container_width=True, key="step4_new_assessment_btn"):
                        for field in ("lef", "lm", "lef_std", "lm_std", "control_cost", "post_ale",
                                      "likelihood", "exposure", "consequence"):
                            st.session_state.pop(f"field_{field}", None)
                        st.session_state["loaded_example"] = "— Select a scenario —"
                        st.session_state["custom_scenario_text"] = ""
                        st.session_state["results"] = None
                        st.session_state["results_inputs"] = None
                        st.session_state["step"] = 0
                        st.rerun()


with tab_saved:
    if tab_saved.open:
        st.header("\U0001F4C1 Saved Assessments")
        st.markdown(
            "Assessments you've explicitly saved from Step 4 (Report), for quick reference "
            "or re-use later in this session or a future one."
        )
        st.caption(
            "\u2139️ Saved on this server's disk, not in a database. If this app is redeployed "
            "or restarted, previously saved assessments will be lost — download the Markdown/CSV "
            "report from Step 4 for anything you need to keep long-term."
        )
        st.divider()

        saved_records = storage.list_assessments()

        if not saved_records:
            st.info("No saved assessments yet. Run a calculation, then click **Save Assessment** in Step 4 (Report).")
        else:
            for record in saved_records:
                r = record["results"]
                is_quick_record = r.get("quick_scan", False)
                saved_at_display = record["saved_at"].replace("T", " ").split(".")[0] + " UTC"
                rec_currency = CURRENCIES.get(record.get("currency_label", DEFAULT_CURRENCY), "\u20ac")

                with st.container(border=True):
                    row_col1, row_col2, row_col3 = st.columns([3, 2, 1])
                    with row_col1:
                        st.markdown(f"**{record['scenario_name']}**")
                        st.caption(f"Saved {saved_at_display} · {record['method']}")
                    with row_col2:
                        if is_quick_record:
                            lec_label, _, _ = lec_band(r["lec"])
                            st.metric("LEC Score", f"{r['lec']} — {lec_label_word(lec_label)}")
                        else:
                            st.metric("FAIR ALE", f"{rec_currency}{r['ale']:,.0f}")
                    with row_col3:
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                        if st.button("\U0001F5D1️ Delete", key=f"delete_{record['id']}", use_container_width=True):
                            storage.delete_assessment(record["id"])
                            st.rerun()


with tab_guide:
    if tab_guide.open:
        st.header("\U0001F4CB How to Use This Tool")
        st.markdown(
            "This guide walks you through each step of running a risk calculation. "
            "You don't need a background in risk management — just follow the steps."
        )
        st.markdown(HOW_TO_USE_MD)

        # F6: methodology theory lives here (single source), not duplicated in
        # the sidebar on every tab. See docs/ux-review-and-improvement-plan.md.
        st.divider()
        st.subheader("\U0001F4D6 Methodology Reference")
        with st.expander("FAIR (Quantitative)"):
            st.markdown(METHODOLOGY_FAIR)
        with st.expander("Monte Carlo Simulation"):
            st.markdown(METHODOLOGY_MONTE_CARLO)
        with st.expander("LEC (Qualitative)"):
            st.markdown(METHODOLOGY_LEC)
        with st.expander("ROI of Controls"):
            st.markdown(METHODOLOGY_ROI)
