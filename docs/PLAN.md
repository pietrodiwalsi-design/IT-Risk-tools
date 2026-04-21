# Development Plan: Step-by-Step Approach

Based on agile MVP for Core Threat Modeling App + Risk Quantification Dashboard. Timelines: 4-8 weeks assuming 10-20 hrs/week. Track progress in GitHub Issues/Milestones.

## Phase 1: Research & Planning (Week 1)
- [ ] Gather requirements: User stories (e.g., "As risk manager, drag threats to visualize").
- [ ] Wireframe MVP: Figma sketches for canvas/forms/charts.
- [ ] Setup repo: Folders created; install guides in README.
- [ ] Risk assessment: List dev risks (e.g., auth bugs).
- Output: PLAN.md (this file), wireframes in `/docs/wireframes`.

## Phase 2: Prototyping (Weeks 2-4)
- Threat App:
  - [ ] Basic canvas: React Flow for nodes/edges.
  - [ ] Scoring/notes: Dropdowns, text inputs.
  - [ ] Collab/export: Firebase + JSON/PNG.
- Dashboard:
  - [ ] Inputs/sims: Streamlit forms, Monte Carlo (NumPy).
  - [ ] Viz: Plotly charts, JSON import.
  - [ ] Tie-in: Parse threat exports.
- Output: Runnable prototypes; deploy links.

## Phase 3: Polish & Testing (Weeks 5-6)
- [ ] UI tweaks: Responsive, themes.
- [ ] Tests: Unit (Jest/pytest), user mocks.
- [ ] Security: Auth, audits.
- Output: Beta version.

## Phase 4: Iteration (Ongoing)
- [ ] Feedback loops: Share demos, prioritize adds (e.g., voice-to-text).
- [ ] Enhancements: Gamification, integrations.

## Phase 5: Launch
- [ ] Deploy: Vercel/Streamlit.
- [ ] Monetize: Freemium setup.
- Output: Live apps.

## Tools & Best Practices
- Agile: Weekly check-ins.
- No-Code Alt: Bubble for app if low-code.
- Metrics: Time to first demo (<3 weeks).

Update this file as we progress. Next: Wireframes?
