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

---

## Architecture Roadmap: When to Outgrow Streamlit (added 2026-07-08)

**Context:** Peter asked whether the current technical architecture (Streamlit +
local JSON-file storage) is future-proof and the most efficient way to build/
maintain this tool. Honest assessment below, captured here as a documented
"later" item — **not urgent, not a request for immediate work.** Do not start
any of this until one of the trigger conditions below actually occurs.

### Current state (as of Phase 2, commit `d1f7cd8`)

- `engine.py` / `content.py` / `app.py` / `storage.py` split (Phase 1.5) is
  solid — pure calculation logic is isolated from UI and content, with real
  pytest coverage (`test_monte_carlo.py`, 16 tests) and a CI gate on every
  push. This is genuinely good practice and should stay as-is regardless of
  what happens to the UI layer.
- `shared/scenario.schema.json` validates built-in example scenarios in CI.
  Also worth keeping regardless of framework.
- UI is Streamlit, a single ~1000-line `app.py`, heavy `st.session_state`
  choreography across a 4-step stepper flow.
- Persistence (`storage.py`) is local JSON files on the server's disk —
  already documented in-app as ephemeral ("lost on redeploy/restart").
- No auth, no multi-tenancy, single implicit user.

### Is this future-proof? Verdict: fine for current scope, not beyond it

**Good enough as-is if:** this stays a personal/internal tool used by Peter
(+ maybe a couple of colleagues) occasionally, where a saved assessment
disappearing on redeploy is an acceptable inconvenience because the Markdown/
CSV export is the real "save" mechanism. Don't over-engineer for this case —
keep shipping Streamlit fixes as they come up (like the 2026-07-08 tab
bleed-through fix).

**Will become a real constraint if any of these happen:**
1. A second/third regular user needs the tool (Streamlit's session model and
   lack of auth start to hurt).
2. Someone loses a saved assessment they actually cared about (the local-disk
   storage limitation stops being a footnote and becomes a trust problem —
   especially awkward for a *risk management* tool).
3. The tool needs to be shown to / relied on by leadership as something more
   than a personal calculator (credibility of "data can vanish on redeploy"
   drops fast in that context).
4. `app.py` keeps growing and session-state bugs (like today's) start taking
   longer to diagnose — a sign the single-file/global-session-state approach
   is running out of runway.

### Recommended path, in order (only act on the first unmet trigger)

1. **Storage: JSON files -> SQLite.** Smallest possible fix for the biggest
   actual risk (data loss). Still a single file, zero extra ops/infra, but
   survives restarts and gives real querying. Estimated effort: half a day.
   **This is the first thing to do the moment trigger #2 above happens** —
   don't wait for a bigger rewrite to fix this specific risk.
2. **If multi-user/roles become real (trigger #1):** this is where Streamlit
   itself becomes the ceiling, not just the storage layer — its rerun-the-
   whole-script-on-every-interaction model and lack of real routing/auth
   primitives will fight every future request. At that point, evaluate a
   proper split: FastAPI (or similar) backend + a real frontend, keeping
   `engine.py`'s calculation logic reusable as-is since it was already built
   framework-agnostic.
3. **Do not pre-emptively rewrite.** No evidence yet of trigger #1 or #3.
   Rewriting now would trade a working, tested, actively-used tool for a
   speculative one — worse trade than the Streamlit limitations it would fix.

**Action right now: none.** This section is a placeholder for the next
person (or future Moshe) to check against before reaching for a rewrite, and
a trigger list so Peter doesn't have to re-litigate this assessment from
scratch when one of these conditions eventually shows up.
