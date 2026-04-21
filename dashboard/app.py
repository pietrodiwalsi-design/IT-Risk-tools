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

class ITRiskCalculator:
    def __init__(self):
        self.sim_runs = 10000  # Monte Carlo iterations

    def fair_risk_calc(self, lef: float, lm: float) -> float:
        \"\"\"FAIR: Annual Loss Expectancy = LEF * LM\"\"\"
        if lef < 0 or lm < 0:
            raise ValueError(\"Inputs must be non-negative\")
        ale = lef * lm
        logger.info(f\"FAIR ALE calculated: {ale}\")
        return ale

    def monte_carlo_sim(self, lef_mean: float, lef_std: float, lm_mean: float, lm_std: float) -> Dict[str, float]:
        \"\"\"Monte Carlo simulation for risk variability\"\"\"
        lef_samples = np.random.normal(lef_mean, lef_std, self.sim_runs)
        lm_samples = np.random.lognormal(np.log(lm_mean), lm_std, self.sim_runs)  # Log-normal for LM
        lef_samples = np.clip(lef_samples, 0, None)  # Sanitize negative
        lm_samples = np.clip(lm_samples, 0, None)
        ale_samples = lef_samples * lm_samples
        return {
            'mean_ale': np.mean(ale_samples),
            'std_ale': np.std(ale_samples),
            'p95_ale': np.percentile(ale_samples, 95),
            'samples': ale_samples
        }

    def roi_calc(self, current_ale: float, post_control_ale: float, control_cost: float) -> float:
        \"\"\"ROI = (ALE reduction / cost) * 100\"\"\"
        reduction = current_ale - post_control_ale
        if control_cost <= 0:
            raise ValueError(\"Control cost must be positive\")
        roi = (reduction / control_cost) * 100
        logger.info(f\"ROI calculated: {roi}%\")
        return roi

    def lec_score(self, likelihood: int, exposure: int, consequence: int) -> int:
        \"\"\"LEC: Likelihood * Exposure * Consequence (qualitative)\"\"\"
        if not (1 <= likelihood <= 10 and 1 <= exposure <= 10 and 1 <= consequence <= 10):
            raise ValueError(\"LEC inputs must be 1-10\")
        score = likelihood * exposure * consequence
        logger.info(f\"LEC score: {score}\")
        return score

    def generate_charts(self, sim_data: Dict, roi: float, lec: int):
        \"\"\"Generate LEC chart and Monte Carlo plot\"\"\"
        fig = make_subplots(rows=1, cols=2, subplot_titles=('Monte Carlo ALE Distribution', 'ROI & LEC Summary'))
        
        # Monte Carlo histogram
        fig.add_trace(go.Histogram(x=sim_data['samples'], nbinsx=50, name='ALE Samples'), row=1, col=1)
        fig.update_xaxes(title_text=\"Annual Loss Expectancy ($)\", row=1, col=1)
        
        # Summary bar
        categories = ['Mean ALE', 'P95 ALE', 'ROI (%)', 'LEC Score']
        values = [sim_data['mean_ale'], sim_data['p95_ale'], roi, lec]
        fig.add_trace(go.Bar(x=categories, y=values, name='Metrics'), row=1, col=2)
        fig.update_yaxes(title_text=\"Value\", row=1, col=2)
        
        fig.update_layout(title_text=\"IT Risk Dashboard - Phase 1.5\")
        return fig

# Streamlit Dashboard
def main():
    st.title(\"IT Risk Tool - Phase 1.5 Dashboard\")
    
    calc = ITRiskCalculator()
    
    # Inputs (sanitized)
    lef = st.number_input(\"Loss Event Frequency (LEF)\", min_value=0.0, value=1.0)
    lm = st.number_input(\"Loss Magnitude (LM)\", min_value=0.0, value=100000.0)
    lef_std = st.number_input(\"LEF Std Dev\", min_value=0.0, value=0.5)
    lm_std = st.number_input(\"LM Std Dev\", min_value=0.0, value=0.2)
    control_cost = st.number_input(\"Control Cost ($)\", min_value=1.0, value=50000.0)
    post_ale = st.number_input(\"Post-Control ALE\", min_value=0.0, value=50000.0)
    likelihood = st.slider(\"Likelihood (1-10)\", 1, 10, 5)
    exposure = st.slider(\"Exposure (1-10)\", 1, 10, 5)
    consequence = st.slider(\"Consequence (1-10)\", 1, 10, 5)
    
    if st.button(\"Calculate Risk\"):
        try:
            # FAIR
            ale = calc.fair_risk_calc(lef, lm)
            st.write(f\"FAIR ALE: ${ale:,.2f}\")
            
            # Monte Carlo
            sim = calc.monte_carlo_sim(lef, lef_std, lm, lm_std)
            st.write(f\"Monte Carlo Mean ALE: ${sim['mean_ale']:,.2f} (P95: ${sim['p95_ale']:,.2f})\")
            
            # ROI
            roi = calc.roi_calc(ale, post_ale, control_cost)
            st.write(f\"ROI: {roi:.2f}%\")
            
            # LEC
            lec = calc.lec_score(likelihood, exposure, consequence)
            st.write(f\"LEC Score: {lec}\")
            
            # Charts
            fig = calc.generate_charts(sim, roi, lec)
            st.plotly_chart(fig)
            
        except ValueError as e:
            st.error(f\"Input error: {e}\")

if __name__ == \"__main__\":
    main()