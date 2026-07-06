**App Name**: RiskQuant  
**Version**: 1.2 MVP (Updated with Prioritization Focus)  
**Owner/Stakeholder**: Peter Van Walsem (IT Risk Manager, Rotterdam CET; insurance/finance focus).  
**Business Goal**: SaaS/PWA tool to quantify IT/cyber risks into financial terms (e.g., € loss ranges, ROI for mitigations). Use FAIR model/Monte Carlo for probabilistic forecasts. Targets insurers/teams for audits/prioritization. Freemium (basic sims free; premium integrations $99/user/mo).  
**Target Users**: Risk managers (you), CISO teams, execs (financial narratives).  
**Platform/Scope**: Web PWA (desktop/mobile, offline sims). Host: GitHub Pages/AWS. Backend: Python/Flask for calcs (JS frontend). DB: Local/PostgreSQL for scenarios.  
**Assumptions**: FAIR framework base; open datasets (Verizon DBIR, MITRE); SME inputs via forms. EU GDPR compliant.  
**Constraints**: <5s sim runs; no real-time telemetry (MVP inputs); CET timezone.  

#### 1. Functional Requirements (Core Features)
Refined with CRQ/FAIR workflow and organizational prioritization: Quantify risks for processes/assets to rank scenarios (e.g., highest ALE first). Structured as user stories.

- **Must-Have (MVP Essentials—Build First)**:
  - **Step 1: Risk Scenario & Asset Identification**: As a risk manager, I want to define scenario (e.g., "malware compromising data integrity") and perform BIA (asset value, business purpose), so I frame context. (Forms for scenario description, asset financial value via SME estimates.)
  - **Step 2: Loss Event Frequency (LEF)**: As an analyst, I want TEF (attempts from SIEM/IDS/telemetry/threat intel) and Susceptibility (Threat Capability vs. Resistance Strength), so I calculate real frequency. (Inputs: TEF baseline from DBIR/MITRE; vuln = max(0, capability - resistance); integrate CSV for logs.)
  - **Data Ingestion and Integration**: As a risk manager, I want to input/upload data from SIEM/IDS/IAM/CMDB/financial records/threat intel (Verizon DBIR/MITRE/ISAC), including SME estimates, so I baseline threats/assets. (Forms for manual/CSV; API stubs for future integrations.)
  - **Step 3: Loss Magnitude (Financial Impact)**: As an exec, I want Primary (productivity/response/replacement) and Secondary (reputation/market loss/consumer churn/fines/judgments) losses, so I quantify fallout. (Breakdown: % allocation, e.g., 40% secondary; CI for ranges.)
  - **Risk Modeling Engine**: As an analyst, I want FAIR decomposition (LEF x LM) with Monte Carlo sims (BetaPERT/log-normal distributions), so I get probabilistic ranges (not point estimates). (JS/Python calc: ALE = incident cost x annual rate; Vulnerability = Threat Capability vs. Resistance Strength.)
  - **Step 4: Simulations for Uncertainty**: As a planner, I want Monte Carlo (1K-10K iterations) with probability distributions, so I handle variability. (Randomized LEF/LM; sorted for percentiles.)
  - **Financial Impact Assessment**: As an exec, I want categorization of Primary/Secondary losses with confidence intervals, so I see defensible € ranges. (Outputs: Lower/upper bounds, e.g., "€500K-2M at 95% CI".)
  - **Step 5: Executive Outputs**: As a decision-maker, I want ALE (annual expected loss, e.g., €1.4M-3M), LEC (prob > threshold), and ROI calculator (mit cost vs. avoided losses, e.g., 248% for €300K upgrade), so I communicate/prioritize. (What-if toggle for scenarios.)
  - **Scenario Analysis**: As a planner, I want "what-if" sims for attacks/breaches and ROI calcs (control cost vs. avoided losses), so I prioritize projects. (Dynamic register: Map tech risks to business impacts.)
  - **Organizational Prioritization**: As a CISO, I want a risk register that ranks scenarios by quantified metrics (e.g., ALE, ROI, P95 CI for processes/assets), so I focus on high-impact IT security first (e.g., sort by € exposure for CEO/CFO decisions). (Table view: Scenarios list, sortable by ALE/ROI; dollar figures for processes/assets key.)
  - **Reporting/Visualization**: As a decision-maker, I want Loss Exceedance Curve (LEC: prob losses > € thresholds), dashboards (qualitative to financial, trends, peer comparisons), so I communicate clearly. (Chart.js for LEC/curves; export PDF/CSV; prioritization dashboard with rankings.)

- **Should-Have (Enhance MVP—Phase 2)**:
  - **Automated Telemetry**: Integrate live feeds (SIEM logs) for real-time inputs.
  - **Advanced Sims**: Dynamic vulnerability derivation; industry benchmarks auto-pull.
  - **Risk Register**: Maintain/track scenarios over time with auto-ranking.

- **Could-Have (v1.5—Nice-to-Have)**:
  - **AI Assistance**: SME calibration via prompts; predictive trends.
  - **Collaboration**: Share sims (multi-user, comments).
  - **Compliance Ties**: Export for NIST/ISO audits.

- **Won't-Have (Out of v1.0 Scope)**:
  - Live integrations (manual/CSV only).
  - Blockchain/peer sharing.
  - Mobile-native (PWA suffices).

#### 2. Non-Functional Requirements (Quality Attributes)
- **Must-Have**:
  - **Usability**: Intuitive forms/dashboards; guided inputs (e.g., sliders for likelihood); responsive (desktop/mobile). Prioritization table sortable/filterable.
  - **Performance**: <5s for 1K sims; scalable to 10K (cloud optional).
  - **Accessibility**: WCAG AA (alt text/charts, keyboard nav).
  - **Security/Privacy**: Encrypt inputs; GDPR (no PII storage); audit logs.
  - **Reliability**: Offline calcs; error handling (e.g., invalid data).

- **Should-Have**:
  - **Compatibility**: Modern browsers; Python 3.10+ backend.
  - **Maintainability**: Modular code (FAIR lib reusable); GitHub repo.
  - **Scalability**: Handle 100 users/sim (serverless if needed).

- **Could-Have**:
  - **Analytics**: Usage tracking (anonymized).

#### 3. User Stories & Acceptance Criteria
- **Story 1 (Must: Scenario/BIA)**: As a manager, I want scenario definition/BIA, so context set. Criteria: Input "malware data integrity" → Asset value € estimate; business purpose dropdown.
- **Story 2 (Must: LEF/TEF/Susceptibility)**: As an analyst, I want TEF/Susceptibility, so frequency real. Criteria: Input capability/resistance → Vuln %; telemetry CSV parse.
- **Story 3 (Must: Ingestion)**: As a manager, I want data input from tools/SME, so baseline. Criteria: Upload CSV → Parses assets/threats; estimates validated (0-100% likelihood).
- **Story 4 (Must: Loss Magnitude)**: As an exec, I want Primary/Secondary breakdown, so fallout quantified. Criteria: % allocation (e.g., 40% reputation); CI shown.
- **Story 5 (Must: Simulations)**: As a planner, I want Monte Carlo/BetaPERT, so uncertainty handled. Criteria: 1K runs → Sorted percentiles; log-normal variation.
- **Story 6 (Must: Modeling)**: As an analyst, I want FAIR/Monte Carlo, so ranges output. Criteria: Input freq/mag → 1K sims; ALE calc; Vulnerability score (e.g., 0.7 = high).
- **Story 7 (Must: Impact)**: As an exec, I want primary/secondary losses with CI, so financial view. Criteria: Categorize (e.g., €1M fine secondary); 95% interval shown.
- **Story 8 (Must: Scenarios/ROI)**: As a planner, I want what-if/ROI, so prioritize. Criteria: Toggle controls → Re-sim; ROI = (avoided - cost)/cost >1.
- **Story 9 (Must: Outputs)**: As a decision-maker, I want ALE/LEC/ROI, so exec-ready. Criteria: ALE €1.4M-3M; LEC chart >€X prob; ROI 248% example.
- **Story 10 (Must: Reporting)**: As a decision-maker, I want LEC/dashboards/comparisons, so communicate. Criteria: Chart prob > €X; side-by-side inherent/residual risks.
- **Story 11 (Must: Prioritization)**: As a CISO, I want risk register ranking (by ALE/ROI/P95 for processes/assets), so I focus on top IT security scenarios first. Criteria: Add multiple scenarios → Sortable table (highest € exposure top); dollar figures for assets/processes.

#### 4. Risks & Mitigations
- **Risk**: Data inaccuracy (estimates). Mitigate: SME validation prompts; benchmarks.
- **Risk**: Compute heavy (sims). Mitigate: JS for MVP, Python offload.
- **Risk**: Scope creep (integrations). Mitigate: MVP manual only.
- **Success Metrics**: 90% stories pass; sim accuracy vs. FAIR examples; you approve dashboard; prioritization ranks 5+ scenarios correctly.

*Draft v1.2—Updated 2026-04-17 with prioritization (risk register ranking by ALE/ROI for IT security scenarios, € figures for processes/assets). Approved for MVP.*