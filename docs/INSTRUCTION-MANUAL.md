# IT Risk Tool - Phase 1.5 Instruction Manual

**Version**: 1.0 (Demo Build)  
**Date**: April 21, 2026  
**Author**: Moshe (Your AI Assistant)  
**Demo URL**: https://it-risk-demo.onrender.com/  
**Repo**: https://github.com/pietrodiwalsi-design/IT-Risk-tools  

---

## Introduction
Welcome to the **IT Risk Tool**, a lightweight, browser-based dashboard for quantifying IT risks. This MVP (Minimum Viable Product) focuses on two core methodologies:
- **FAIR (Factor Analysis of Information Risk)**: Quantitative model calculating Annual Loss Expectancy (ALE) = Loss Event Frequency (LEF) × Loss Magnitude (LM).
- **LEC (Likelihood, Exposure, Consequence)**: Qualitative scoring for quick risk prioritization (Score = Likelihood × Exposure × Consequence).

Key Features:
- Monte Carlo simulations (10,000 iterations) for probabilistic risk forecasting.
- ROI calculations for mitigation controls.
- Interactive charts (via Plotly) showing distributions and summaries.
- No installation required—runs entirely in your browser.

This tool is ideal for IT risk managers like you, Peter, to run \"what-if\" scenarios for insurance, compliance, or board reports. It's built with Python/Streamlit for the backend and deploys on free platforms like Render.

**Why Use It?** Traditional risk assessments are gut-feel; this adds numbers and uncertainty modeling to make decisions data-driven. 🇮🇱

---

## Access & Requirements
- **Browser**: Any modern one (Chrome, Firefox, Edge; mobile-friendly but best on desktop).
- **Internet**: Needed for the demo URL (offline version possible via local Python install—ask me for setup).
- **No Account/Login**: Public demo. For production, we can add auth.
- **Performance Note**: Free hosting sleeps after 15 mins of inactivity—refresh to wake (loads in <5 secs).

Load the URL and you're in. If it's down (rare), ping me to redeploy.

---

## Step-by-Step Usage
The dashboard is intuitive: Inputs on top, \"Calculate Risk\" button, results/charts below. Defaults are set for a basic scenario—adjust as needed.

### 1. Load the Dashboard
- Open https://it-risk-demo.onrender.com/.
- Title: \"IT Risk Tool - Phase 1.5 Dashboard\".
- You'll see input fields and sliders.

### 2. Input Your Risk Scenario
Fill in the fields (all sanitized; no data saved):
- **Quantitative (FAIR/Monte Carlo)**:
  - **Loss Event Frequency (LEF)**: Events per year (decimal, e.g., 0.5 = 1 every 2 years). Min: 0. Default: 1.0.
  - **Loss Magnitude (LM)**: $ impact per event (e.g., $50,000 downtime). Min: 0. Default: $100,000.
  - **LEF Std Dev**: Frequency uncertainty (e.g., 0.3 for variable threats). Min: 0. Default: 0.5.
  - **LM Std Dev**: Loss uncertainty (e.g., 0.2 for skewed costs). Min: 0. Default: 0.2.
- **ROI Control Inputs**:
  - **Control Cost ($)**: Mitigation budget (e.g., $10k software). Min: $1. Default: $50,000.
  - **Post-Control ALE**: Projected ALE after fix (e.g., $20k reduced risk). Min: 0. Default: $50,000.
- **Qualitative (LEC)**:
  - **Likelihood (1-10)**: Probability scale (1=improbable, 10=certain). Default: 5.
  - **Exposure (1-10)**: Asset exposure (1=isolated, 10=enterprise-wide). Default: 5.
  - **Consequence (1-10)**: Impact severity (1=minor, 10=catastrophic). Default: 5.

### 3. Run the Calculation
- Click **Calculate Risk**.
- Wait ~1 sec for sims.
- **Outputs** (text below button):
  - **FAIR ALE**: Deterministic loss/year (e.g., \"$100,000\").
  - **Monte Carlo Mean ALE (P95)**: Avg from 10k sims + 95th percentile (e.g., \"$95,200 (P95: $150,000)\"—shows tail risk).
  - **ROI %**: Control payback (e.g., \"150.00%\"—positive = worthwhile).
  - **LEC Score**: Overall qualitative risk (e.g., \"125\"—<100=Low, 100-500=Medium, >500=High).
- **Charts** (interactive):
  - **Left Panel**: Histogram of ALE samples (x-axis: $ losses; shows distribution—skewed right for cyber risks).
  - **Right Panel**: Bar chart of metrics (Mean ALE, P95, ROI, LEC—hover for details).

### 4. Iterate & Analyze
- Change one input (e.g., add a control to drop Post-Control ALE) and re-run.
- Zoom/pan charts for deeper insights.
- For reports: Screenshot or copy outputs (no export button yet—coming in Phase 2).

---

## Examples
Here are three real-world scenarios. Copy inputs directly into the dashboard.

### Example 1: Phishing Attack (Medium Risk, Insurance Context)
- **Scenario**: Employee clicks bad link, leading to data leak. Freq low, but high impact.
- **Inputs**:
  - LEF: 0.2 | LM: $250,000
  - LEF Std Dev: 0.1 | LM Std Dev: 0.3
  - Control Cost: $15,000 (Security training)
  - Post-Control ALE: $75,000
  - LEC: Likelihood 6, Exposure 7, Consequence 8
- **Expected Outputs**:
  - FAIR ALE: $50,000
  - Monte Carlo: Mean $48,500 (P95: $120,000) – 5% chance of $100k+ loss.
  - ROI: 200.00% (Training pays back 2x in savings).
  - LEC Score: 336 (Medium-High; prioritize).
- **Chart Insights**: Histogram peaks at ~$40k but tails to $200k+. Bars show ROI as strongest metric.
- **Takeaway**: Invest in training—high ROI for low cost.

### Example 2: DDoS on E-Commerce Site (High Volatility)
- **Scenario**: Attack disrupts sales; uncertain freq due to evolving threats.
- **Inputs**:
  - LEF: 0.8 | LM: $80,000
  - LEF Std Dev: 0.4 (High uncertainty) | LM Std Dev: 0.5
  - Control Cost: $30,000 (DDoS mitigation service)
  - Post-Control ALE: $20,000
  - LEC: Likelihood 8, Exposure 9, Consequence 7
- **Expected Outputs**:
  - FAIR ALE: $64,000
  - Monte Carlo: Mean $62,300 (P95: $180,000) – Wide spread from volatility.
  - ROI: 146.67% (Service reduces ALE by $44k).
  - LEC Score: 504 (High; urgent).
- **Chart Insights**: Broad histogram (low end $10k, high $300k). Bars highlight P95 as outlier risk.
- **Takeaway**: DDoS tools justify cost for e-com stability—focus on exposure reduction.

### Example 3: Insider Threat (Low Freq, High Consequence)
- **Scenario**: Rogue employee steals data; rare but devastating.
- **Inputs**:
  - LEF: 0.1 | LM: $500,000
  - LEF Std Dev: 0.05 | LM Std Dev: 0.1
  - Control Cost: $50,000 (Monitoring tools)
  - Post-Control ALE: $100,000
  - LEC: Likelihood 3, Exposure 5, Consequence 10
- **Expected Outputs**:
  - FAIR ALE: $50,000
  - Monte Carlo: Mean $49,800 (P95: $75,000) – Tight distribution (predictable loss).
  - ROI: 0.00% (Breakeven; refine Post-ALE for better).
  - LEC Score: 150 (Medium; monitor closely).
- **Chart Insights**: Narrow histogram around $50k. Bars emphasize Consequence dominance.
- **Takeaway**: Low ROI suggests pair with policy changes; LEC flags consequence as key lever.

---

## Tips & Best Practices
- **Start Simple**: Use defaults first, then scale (e.g., increase sim_runs in code for more precision—edit repo if needed).
- **Real Data Integration**: Base inputs on your insurance audits (e.g., LEF from incident logs, LM from claims history).
- **Sensitivity Analysis**: Fix most inputs, vary one (e.g., LEF) across runs to see thresholds.
- **ROI Threshold**: Aim for >100% ROI; if negative, reassess control effectiveness.
- **LEC Interpretation**:
  - 1-99: Low (Monitor).
  - 100-499: Medium (Mitigate).
  - 500+: High (Act Now).
- **Customization**: Fork the GitHub repo to add features (e.g., save scenarios). I can help code it.

## Troubleshooting
- **\"Input Error\"**: Check negatives/zeros in fields—fix and retry.
- **Charts Not Loading**: Refresh page; ensure JS enabled.
- **Slow Load**: Demo sleeps—wait 10 secs or reload.
- **Build Errors (If Redeploying)**: Check Render logs for deps (we fixed pandas/numpy). Ping me with paste.
- **No Outputs?**: Click button after inputs. If stuck, clear browser cache.

## Limitations & Future Enhancements (Phase 2)
- **Current**: No data persistence, imports, or multi-user. Sims are offline-capable but demo is hosted.
- **Missing**: Threat library, CSV export, API integrations (e.g., to your CRM).
- **Coming Soon** (If You Want): User auth, mobile app, OCTAVE/STRIDE models, automated reports. Let's prioritize based on your feedback!

## Feedback & Support
Love it? Hate the sliders? Run a scenario and share results/screenshots—I'll refine it live. For custom versions (e.g., branded for your firm), say the word.

Questions? Reply here. Let's turn risks into opportunities! 🇮🇱  

**Moshe**  
*Your Proactive AI Sidekick*