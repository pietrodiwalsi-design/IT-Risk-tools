# IT Risk Tools - Threat Modeling App & Risk Quantification Dashboard

## Project Overview
This repo is for developing two interconnected IT Risk tools:
1. **Core Threat Modeling App**: A collaborative web app for team-based threat modeling sessions (drag-and-drop canvas, STRIDE-based, real-time collab, exports).
2. **Risk Quantification Dashboard**: A Python-based dashboard for simulating financial impacts of risks (Monte Carlo sims, visualizations, imports from threat app).

Inspired by discussions with Peter Van Walsem (2026-04-16). Focus: Practical for insurance/IT Risk pros—quantify threats, comply, mitigate.

## Setup
- **Tech Stack**:
  - Threat App: React (frontend), Firebase (collab/auth), Node.js.
  - Dashboard: Python/Streamlit, NumPy/Plotly for sims.
  - Shared: Git for version control; Vercel/Streamlit Cloud for deploy.
- **Local Dev**:
  1. Clone: `git clone https://github.com/pietrodiwalsi-design/IT-Risk-tools.git`
  2. Threat App: `cd threat-app && npm install && npm start`
  3. Dashboard: `cd dashboard && pip install -r requirements.txt && streamlit run app.py`
- **Requirements**: Node.js 18+, Python 3.10+, Git.

## Structure
- `/threat-app`: React source for canvas.
- `/dashboard`: Streamlit/Python for quant sims.
- `/docs`: Ideas, plans, wireframes.
- `/shared`: Common utils (e.g., JSON schemas for exports).

## Phases (Agile MVP)
See `docs/PLAN.md` for step-by-step roadmap.

## Contributing
- Branch: `feat/[feature]` (e.g., `feat/canvas-basic`).
- Commit: Conventional (e.g., "feat: add drag-drop").
- Issues: Track bugs/features here.

*Started: 2026-04-16 | Owner: Peter Van Walsem*
