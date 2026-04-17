**App Name**: RiskQuant  
**Version**: 1.0 MVP  
**Owner/Stakeholder**: Peter Van Walsem (IT Risk Manager, Rotterdam CET; insurance/finance focus).  
**Business Goal**: SaaS/PWA tool to quantify IT/cyber risks into financial terms (e.g., € loss ranges, ROI for mitigations). Use FAIR model/Monte Carlo for probabilistic forecasts. Targets insurers/teams for audits/prioritization. Freemium (basic sims free; premium integrations $99/user/mo).  
**Target Users**: Risk managers (you), CISO teams, execs (financial narratives).  
**Platform/Scope**: Web PWA (desktop/mobile, offline sims). Host: GitHub Pages/AWS. Backend: Python/Flask for calcs (JS frontend). DB: Local/PostgreSQL for scenarios.  
**Assumptions**: FAIR framework base; open datasets (Verizon DBIR, MITRE); SME inputs via forms. EU GDPR compliant.  
**Constraints**: <5s sim runs; no real-time telemetry (MVP inputs); CET timezone.  

#### 1. Functional Requirements (Core Features)
From provided specs—structured as user stories: "As [user], I want [feature] so that [benefit]."

- **Must-Have (MVP Essentials—Build First)**:
  - **Data Ingestion and Integration**: As a risk manager, I want to input/upload data from SIEM/IDS/IAM/CMDB/financial records/threat intel (Verizon DBIR/MITRE/ISAC), including SME estimates, so I baseline threats/assets. (Forms for manual/CSV; API stubs for future integrations.)
  - **Risk Modeling Engine**: As an analyst, I want FAIR decomposition (Loss Event Frequency x Magnitude) with Monte Carlo sims (BetaPERT/log-normal distributions), so I get probabilistic ranges (not point estimates). (JS/Python calc: ALE = incident cost x annual rate; Vulnerability = Threat Capability vs. Resistance Strength.)
  - **Financial Impact Assessment**: As an exec, I want categorization of Primary (response/asset/prod losses) and Secondary (fines/legal/reputation/churn) losses with confidence intervals, so I see defensible € ranges. (Outputs: Lower/upper bounds, e.g., "€500K-2M at 95% CI".)
  - **Scenario Analysis**: As a planner, I want "what-if" sims for attacks/breaches and ROI calcs (control cost vs. avoided losses), so I prioritize projects. (Dynamic register: Map tech risks to business impacts.)
  - **Reporting/Visualization**: As a decision-maker, I want Loss Exceedance Curve (LEC: prob losses > € thresholds), dashboards (qualitative to financial, trends, peer comparisons), so I communicate clearly. (Chart.js for LEC/curves; export PDF/CSV.)

- **Should-Have (Enhance MVP—Phase 2)**:
  - **Automated Telemetry**: Integrate live feeds (SIEM logs) for real-time inputs.
  - **Advanced Sims**: Dynamic vulnerability derivation; industry benchmarks auto-pull.
  - **Risk Register**: Maintain/track scenarios over time.

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
  - **Usability**: Intuitive forms/dashboards; guided inputs (e.g., sliders for likelihood); responsive (desktop/mobile).
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
- **Story 1 (Must: Ingestion)**: As a manager, I want data input from tools/SME, so I baseline. Criteria: Upload CSV → Parses assets/threats; estimates validated (e.g., 0-100% likelihood).
- **Story 2 (Must: Modeling)**: As an analyst, I want FAIR/Monte Carlo, so ranges output. Criteria: Input freq/mag → 1K sims; ALE calc; Vulnerability score (e.g., 0.7 = high).
- **Story 3 (Must: Impact)**: As an exec, I want primary/secondary losses with CI, so financial view. Criteria: Categorize (e.g., €1M fine secondary); 95% interval shown.
- **Story 4 (Must: Scenarios)**: As a planner, I want what-if/ROI, so prioritize. Criteria: Change control strength → Re-sim; ROI = (avoided - cost)/cost >1.
- **Story 5 (Must: Reporting)**: As a decision-maker, I want LEC/dashboards/comparisons, so communicate. Criteria: Chart prob > €X; side-by-side inherent/residual risks.

#### 4. Risks & Mitigations
- **Risk**: Data inaccuracy (estimates). Mitigate: SME validation prompts; benchmarks.
- **Risk**: Compute heavy (sims). Mitigate: JS for MVP, Python offload.
- **Risk**: Scope creep (integrations). Mitigate: MVP manual only.
- **Success Metrics**: 90% stories pass; sim accuracy vs. FAIR examples; you approve dashboard.

*Draft v0.1—From Peter 2026-04-16. Approved 2026-04-17. MVP Phase 1 live.*