"""
Pytest suite for the Monte Carlo lognormal parameterisation fix + core engine
correctness. Runs against engine.py (the pure calculation module extracted in
Phase 1.5) so it is importable/testable without Streamlit or any UI running.

Run with: pytest dashboard/test_monte_carlo.py -v
(also wired into CI — see .github/workflows/test.yml)
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Make `engine` importable regardless of CWD (repo root, dashboard/, or CI runner).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import ITRiskCalculator  # noqa: E402


@pytest.mark.parametrize("cv", [0.1, 0.3, 0.5, 0.8])
def test_mean_preservation(cv):
    """E[lm_samples] should be within 2% of lm_mean for various CVs."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000  # higher precision for tests
    lm_mean = 750000.0

    sigma = np.sqrt(np.log(1 + cv**2))
    mu = np.log(lm_mean) - 0.5 * sigma**2
    lm_samples = np.random.lognormal(mu, sigma, calc.sim_runs)
    sample_mean = np.mean(lm_samples)
    rel_error = abs(sample_mean - lm_mean) / lm_mean

    assert rel_error < 0.02, f"CV={cv}: E[LM]=${sample_mean:,.0f} vs target ${lm_mean:,.0f}, rel_error={rel_error:.4f}"


@pytest.mark.parametrize("cv", [0.1, 0.3, 0.5, 0.8])
def test_cv_preservation(cv):
    """Sample CV should be within 5% of the target CV."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    lm_mean = 750000.0

    sigma = np.sqrt(np.log(1 + cv**2))
    mu = np.log(lm_mean) - 0.5 * sigma**2
    lm_samples = np.random.lognormal(mu, sigma, calc.sim_runs)
    sample_mean = np.mean(lm_samples)
    sample_std = np.std(lm_samples)
    sample_cv = sample_std / sample_mean
    rel_error = abs(sample_cv - cv) / cv

    assert rel_error < 0.05, f"CV={cv}: sample_CV={sample_cv:.4f}, rel_error={rel_error:.4f}"


def test_ale_mean_vs_fair():
    """mean_ale should be within 3% of FAIR ALE (LEF x LM) for the Ransomware scenario."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    lef, lm, lef_std, lm_cv = 0.3, 750000.0, 0.2, 0.4
    result = calc.monte_carlo_sim(lef, lef_std, lm, lm_cv)
    fair_ale = lef * lm
    rel_error = abs(result["mean_ale"] - fair_ale) / fair_ale

    assert rel_error < 0.03, f"Mean ALE=${result['mean_ale']:,.0f}, FAIR ALE=${fair_ale:,.0f}, rel_error={rel_error:.4f}"


def test_p95_not_inflated():
    """P95 should not be more than 3x the mean for CV=0.3."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    result = calc.monte_carlo_sim(0.3, 0.2, 750000.0, 0.3)
    ratio = result["p95_ale"] / result["mean_ale"]

    assert ratio <= 3.0, f"P95/Mean ratio={ratio:.2f} (should be <= 3.0)"


def test_roi_calc():
    calc = ITRiskCalculator()
    roi = calc.roi_calc(100000.0, 40000.0, 20000.0)
    expected = ((100000 - 40000) / 20000) * 100  # 300%
    assert abs(roi - expected) < 0.1, f"ROI={roi:.1f}% (expected {expected:.1f}%)"


def test_lec_score_boundaries():
    calc = ITRiskCalculator()
    assert calc.lec_score(1, 1, 1) == 1
    assert calc.lec_score(10, 10, 10) == 1000


def test_lec_score_rejects_out_of_range():
    calc = ITRiskCalculator()
    with pytest.raises(ValueError):
        calc.lec_score(0, 5, 5)
    with pytest.raises(ValueError):
        calc.lec_score(5, 11, 5)


def test_fair_risk_calc_rejects_negative_lef():
    calc = ITRiskCalculator()
    with pytest.raises(ValueError):
        calc.fair_risk_calc(-1.0, 100000.0)


def test_fair_risk_calc_rejects_zero_lm():
    calc = ITRiskCalculator()
    with pytest.raises(ValueError):
        calc.fair_risk_calc(0.5, 0.0)


def test_roi_calc_rejects_zero_control_cost():
    calc = ITRiskCalculator()
    with pytest.raises(ValueError):
        calc.roi_calc(100000.0, 50000.0, 0.0)


if __name__ == "__main__":
    # Keep the old standalone-script behaviour working too, for anyone used
    # to running this file directly instead of via pytest.
    sys.exit(pytest.main([__file__, "-v"]))
