# IT Risk Tool — Improvement Requirements (v2.0)

**Date**: 2026-05-20
**Owner**: Peter Van Walsem
**Status**: Backlog — ready for development
**Base version**: Phase 1.5 (deployed at https://it-risk-demo.onrender.com/)
**Goal**: Make the tool more polished and convincing for demos to colleagues and management, without a full rebuild.

---

## Context

The Phase 1.5 tool is functional and useful as a demo/conversation starter for management and colleagues. The improvements below are prioritized to increase demo quality, clarity, and professionalism — not to add complexity.

---

## Priority 1 — High Impact, Low Effort

### IMP-01: Pre-loaded Example Scenarios
**What**: Add 3–5 realistic, pre-loaded risk scenarios selectable from a dropdown.
**Why**: Avoids live typing during demos; scenarios resonate with insurance/IT risk audiences.
**Suggested scenarios**:
- 🔐 Ransomware Attack (medium enterprise)
- 💾 Data Breach / Insider Threat
- ☁️ Cloud Misconfiguration / Data Exposure
- 🏦 Third-Party Supplier Failure
- 🔒 Privileged Access Compromise

**Acceptance criteria**:
- Dropdown on the dashboard loads a scenario and pre-fills all input fields
- Each scenario includes a short 1–2 sentence description visible to the user
- User can still override any field after loading

---

### IMP-02: Export to PDF / Print Report
**What**: A "Generate Report" button that produces a clean, printable summary of the current scenario results.
**Why**: Management wants something to take away from a demo; a printed or PDF output adds credibility.

**Acceptance criteria**:
- Button triggers browser print dialog or generates a downloadable PDF
- Report includes: scenario name, all inputs, key outputs (ALE, P95, ROI, LEC score), and the charts
- Report has a clean, professional layout (no raw code/debug info visible)
- Optional: include company placeholder name / date / report ID for realism

---

### IMP-03: Inline Tooltips / FAIR Concept Explanations
**What**: Add (?) help icons next to each input field and key output metric with a short plain-English tooltip.
**Why**: Colleagues and management are not FAIR experts — tooltips reduce friction and make the tool self-explanatory in a demo.

**Examples**:
- LEF: "How often this type of incident is expected per year (e.g., 0.5 = once every 2 years)"
- LM: "The average financial damage per incident, including downtime, response costs, and fines"
- P95: "In 95% of simulated scenarios, losses will be below this number — the 'worst realistic case'"
- ROI: "Return on investment for the proposed control: positive means the control pays for itself"

**Acceptance criteria**:
- All 9 input fields and 4 output metrics have tooltips
- Tooltips are accessible on hover (desktop) and tap (mobile)
- Language is plain English, no jargon

---

## Priority 2 — Moderate Effort, High Demo Value

### IMP-04: Inherent vs. Residual Risk — Side-by-Side View
**What**: Show the risk picture both before controls (inherent risk) and after controls (residual risk) in a visual side-by-side comparison.
**Why**: This is the core value proposition in any board/management risk conversation — "here's where we are, here's where we'll be after investment."

**Acceptance criteria**:
- Two columns or a before/after toggle: Inherent (no controls) vs. Residual (with controls applied)
- Visual delta: show % reduction in ALE and P95 prominently
- LEC score also shown for both states
- Chart overlays both distributions on the same histogram for visual contrast

---

### IMP-05: Auto-Generated "So What" Narrative
**What**: Below the charts, auto-generate a short plain-English paragraph summarising the results.
**Why**: Not everyone reads numbers — a narrative summary makes the tool instantly usable in verbal presentations and board packs.

**Example output**:
> "This ransomware scenario carries an expected annual loss of €95,000, with a 5% chance of exceeding €148,000 in any given year. The proposed control (€50,000 investment) reduces expected losses by 47%, delivering a 150% ROI. Overall risk severity is rated Medium (LEC: 125)."

**Acceptance criteria**:
- Narrative auto-updates when "Calculate Risk" is run
- Figures are formatted in local currency (€) with thousand separators
- Severity label (Low / Medium / High) derived from LEC score is included
- Narrative is copyable to clipboard with one click

---

### IMP-06: Risk Register (Save & Compare Scenarios)
**What**: Allow users to save a scenario result and compare multiple scenarios in a table/summary view.
**Why**: In a real demo or workshop, you want to run 3–4 scenarios and compare them — "which risk do we tackle first?"

**Acceptance criteria**:
- "Save Scenario" button adds current result to an in-session register table
- Register shows: scenario name, ALE, P95, ROI, LEC, risk level
- Scenarios sortable by any column
- Register exportable to CSV
- Session-only (no server-side persistence needed for MVP)

---

## Priority 3 — Phase 2 (Bigger Lift, Future Sprint)

### IMP-07: CSV / Excel Data Ingestion
**What**: Upload a CSV with multiple risk scenarios and process them in batch.
**Why**: Power users (analysts) want to import their existing risk register rather than type each scenario.

---

### IMP-08: Authentication & User Profiles
**What**: Simple login so the tool can be shared internally without being fully public.
**Why**: Required before any real sensitive data is entered.

---

### IMP-09: Threat Modeling Canvas (React App)
**What**: Complete the drag-and-drop threat canvas (STRIDE-based) that feeds into the dashboard.
**Why**: Connects threat identification → risk quantification in one workflow.
**Status**: Skeleton exists in `/threat-app`; not yet functional.

---

## Summary Table

| ID | Description | Priority | Effort | Demo Value |
|----|-------------|----------|--------|------------|
| IMP-01 | Pre-loaded scenarios | 🔴 High | Low | ⭐⭐⭐⭐⭐ |
| IMP-02 | Export to PDF/print | 🔴 High | Low | ⭐⭐⭐⭐⭐ |
| IMP-03 | Inline tooltips | 🔴 High | Low | ⭐⭐⭐⭐ |
| IMP-04 | Inherent vs residual view | 🟡 Medium | Medium | ⭐⭐⭐⭐⭐ |
| IMP-05 | Auto narrative summary | 🟡 Medium | Medium | ⭐⭐⭐⭐⭐ |
| IMP-06 | Risk register (session) | 🟡 Medium | Medium | ⭐⭐⭐⭐ |
| IMP-07 | CSV ingestion | 🟢 Low | High | ⭐⭐⭐ |
| IMP-08 | Auth / user profiles | 🟢 Low | High | ⭐⭐ |
| IMP-09 | Threat modeling canvas | 🟢 Low | Very High | ⭐⭐⭐ |

---

*Written by Moshe (AI Assistant) — 2026-05-20. Approved by: Peter Van Walsem (pending).*
