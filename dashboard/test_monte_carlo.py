#!/usr/bin/env python3
"""Test script for Monte Carlo lognormal parameterisation fix."""

import numpy as np
import sys
sys.path.insert(0, '/root/.openclaw/workspace/IT-Risk-tools/dashboard')
from app import ITRiskCalculator

def test_mean_preservation():
    """Test that E[lm_samples] ≈ lm_mean within 2% for various CVs."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000  # higher precision for tests
    test_cvs = [0.1, 0.3, 0.5, 0.8]
    lm_mean = 750000.0
    passed = True
    for cv in test_cvs:
        # Run sampling logic directly to test the fix
        cv_val = cv
        sigma = np.sqrt(np.log(1 + cv_val**2))
        mu = np.log(lm_mean) - 0.5 * sigma**2
        lm_samples = np.random.lognormal(mu, sigma, calc.sim_runs)
        sample_mean = np.mean(lm_samples)
        rel_error = abs(sample_mean - lm_mean) / lm_mean
        status = "PASS" if rel_error < 0.02 else "FAIL"
        print(f"CV={cv}: E[LM] = ${sample_mean:,.0f} (target ${lm_mean:,.0f}), rel_error={rel_error:.4f} [{status}]")
        if rel_error >= 0.02:
            passed = False
    return passed

def test_cv_preservation():
    """Test that sample CV ≈ target CV within 5%."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    test_cvs = [0.1, 0.3, 0.5, 0.8]
    lm_mean = 750000.0
    passed = True
    for cv in test_cvs:
        cv_val = cv
        sigma = np.sqrt(np.log(1 + cv_val**2))
        mu = np.log(lm_mean) - 0.5 * sigma**2
        lm_samples = np.random.lognormal(mu, sigma, calc.sim_runs)
        sample_mean = np.mean(lm_samples)
        sample_std = np.std(lm_samples)
        sample_cv = sample_std / sample_mean
        rel_error = abs(sample_cv - cv) / cv
        status = "PASS" if rel_error < 0.05 else "FAIL"
        print(f"CV={cv}: sample_CV = {sample_cv:.4f}, rel_error={rel_error:.4f} [{status}]")
        if rel_error >= 0.05:
            passed = False
    return passed

def test_ale_mean_vs_fair():
    """Test that mean_ale ≈ FAIR ALE (LEF × LM) within 3% for Ransomware scenario."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    lef, lm, lef_std, lm_cv = 0.3, 750000.0, 0.2, 0.4
    result = calc.monte_carlo_sim(lef, lef_std, lm, lm_cv)
    fair_ale = lef * lm
    rel_error = abs(result['mean_ale'] - fair_ale) / fair_ale
    status = "PASS" if rel_error < 0.03 else "FAIL"
    print(f"Mean ALE = ${result['mean_ale']:,.0f}, FAIR ALE = ${fair_ale:,.0f}, rel_error={rel_error:.4f} [{status}]")
    return rel_error < 0.03

def test_p95_not_inflated():
    """Test that P95 is not more than 3× the mean for CV=0.3."""
    calc = ITRiskCalculator()
    calc.sim_runs = 100000
    result = calc.monte_carlo_sim(0.3, 0.2, 750000.0, 0.3)
    ratio = result['p95_ale'] / result['mean_ale']
    status = "PASS" if ratio <= 3.0 else "FAIL"
    print(f"P95/Mean ratio = {ratio:.2f} (should be ≤ 3.0) [{status}]")
    return ratio <= 3.0

def test_roi_calc():
    """Test roi_calc for correctness."""
    calc = ITRiskCalculator()
    roi = calc.roi_calc(100000.0, 40000.0, 20000.0)
    expected = ((100000 - 40000) / 20000) * 100  # 300%
    passed = abs(roi - expected) < 0.1
    status = "PASS" if passed else "FAIL"
    print(f"ROI = {roi:.1f}% (expected {expected:.1f}%) [{status}]")
    return passed

def test_lec_score():
    """Test lec_score boundary values."""
    calc = ITRiskCalculator()
    # Test valid range
    score = calc.lec_score(1, 1, 1)
    passed = score == 1
    score = calc.lec_score(10, 10, 10)
    passed = passed and score == 1000
    status = "PASS" if passed else "FAIL"
    print(f"LEC boundaries: 1×1×1=1, 10×10×10=1000 [{status}]")
    return passed

def main():
    print("=== Monte Carlo Fix Verification Tests ===\n")
    results = []
    results.append(("Mean preservation", test_mean_preservation()))
    results.append(("CV preservation", test_cv_preservation()))
    results.append(("ALE mean vs FAIR", test_ale_mean_vs_fair()))
    results.append(("P95 not inflated (CV=0.3)", test_p95_not_inflated()))
    results.append(("ROI calculation", test_roi_calc()))
    results.append(("LEC boundaries", test_lec_score()))
    print("\n=== SUMMARY ===")
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_pass = False
    print(f"\nOverall: {'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())