"""
Pure calculation engine for the IT Risk Quantification Dashboard.

No Streamlit imports here — this module must be importable and testable
without a running Streamlit app (see test_monte_carlo.py). UI code lives
in app.py; example/explainer copy lives in content.py.

Methods implemented:
- FAIR (Factor Analysis of Information Risk): ALE = LEF x LM
- Monte Carlo simulation over FAIR inputs (lognormal LM, normal LEF)
- Control ROI = (ALE reduction / control cost) x 100
- LEC (Likelihood x Exposure x Consequence) qualitative scoring
"""

import logging
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


class ITRiskCalculator:
    def __init__(self):
        self.sim_runs = 10000  # Monte Carlo iterations

    # Hard limits — prevent numerical overflow and DoS via extreme inputs
    MAX_LEF = 1000.0          # >1000 events/year is not a meaningful risk scenario
    MAX_LM = 1_000_000_000.0  # $1 billion cap
    MAX_STD = 10.0            # std dev sanity cap
    MAX_COST = 1_000_000_000.0

    def _validate_fair_inputs(self, lef: float, lm: float, lef_std: float = 0, lm_std: float = 0):
        """Centralised server-side validation — independent of UI constraints"""
        if not (0 <= lef <= self.MAX_LEF):
            raise ValueError(f"LEF must be between 0 and {self.MAX_LEF}")
        if not (0 < lm <= self.MAX_LM):
            raise ValueError(f"Loss Magnitude must be > 0 and ≤ ${self.MAX_LM:,.0f}")
        if not (0 <= lef_std <= self.MAX_STD):
            raise ValueError(f"LEF Std Dev must be between 0 and {self.MAX_STD}")
        if not (0 <= lm_std <= 2.0):
            raise ValueError("LM CV must be between 0 and 2.0")

    def fair_risk_calc(self, lef: float, lm: float) -> float:
        """FAIR: Annual Loss Expectancy = LEF * LM"""
        self._validate_fair_inputs(lef, lm)
        ale = lef * lm
        logger.info("FAIR ALE calculated")  # no raw values in logs
        return ale

    def monte_carlo_sim(self, lef_mean: float, lef_std: float, lm_mean: float, lm_std: float) -> Dict[str, float]:
        """Monte Carlo simulation for risk variability"""
        self._validate_fair_inputs(lef_mean, lm_mean, lef_std, lm_std)
        lef_samples = np.random.normal(lef_mean, lef_std, self.sim_runs)
        # Correct lognormal parameterisation for CV (coefficient of variation)
        cv = lm_std
        if cv > 0:
            sigma = np.sqrt(np.log(1 + cv**2))
            mu = np.log(lm_mean) - 0.5 * sigma**2
        else:
            sigma = 0.0
            mu = np.log(lm_mean)
        lm_samples = np.random.lognormal(mu, sigma, self.sim_runs)
        lef_samples = np.clip(lef_samples, 0, None)
        lm_samples = np.clip(lm_samples, 0, None)
        ale_samples = lef_samples * lm_samples
        # Guard against NaN/Inf from numerical edge cases
        if not np.isfinite(ale_samples).all():
            ale_samples = np.nan_to_num(ale_samples, nan=0.0, posinf=self.MAX_LM, neginf=0.0)
        return {
            'mean_ale': float(np.mean(ale_samples)),
            'std_ale': float(np.std(ale_samples)),
            'p95_ale': float(np.percentile(ale_samples, 95)),
            'samples': ale_samples,
        }

    def roi_calc(self, current_ale: float, post_control_ale: float, control_cost: float) -> float:
        """ROI = (ALE reduction / cost) * 100"""
        if not (0 < control_cost <= self.MAX_COST):
            raise ValueError(f"Control cost must be > 0 and ≤ ${self.MAX_COST:,.0f}")
        if post_control_ale < 0:
            raise ValueError("Post-control ALE cannot be negative")
        reduction = current_ale - post_control_ale
        roi = (reduction / control_cost) * 100
        logger.info("ROI calculated")
        return roi

    def lec_score(self, likelihood: int, exposure: int, consequence: int) -> int:
        """LEC: Likelihood * Exposure * Consequence (qualitative)"""
        if not (1 <= likelihood <= 10 and 1 <= exposure <= 10 and 1 <= consequence <= 10):
            raise ValueError("LEC inputs must be 1-10")
        score = likelihood * exposure * consequence
        logger.info(f"LEC score: {score}")
        return score

    def generate_charts(self, sim_data: Dict, roi: float, lec: int, ale: float):
        """Generate Monte Carlo histogram and summary bar chart.

        Imports plotly lazily so this module stays importable in
        environments that only need the pure math (e.g. CI running
        test_monte_carlo.py without the full dashboard dependency set).
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

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
