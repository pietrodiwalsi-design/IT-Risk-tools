# IT Risk Quantification Dashboard — UX Review & Improvement Plan

**Scope:** `dashboard/app.py` (Streamlit, 834 lines, main branch) · Review date 2026-07-06 · Reviewer: Fable
**Peter's complaint:** "the tool works, but the GUI and user flow are not intuitive." Confirmed — and the causes are specific and fixable.

---

## 1. What is already good (keep)

The quantification substance is genuinely strong: correct lognormal parameterisation (CV-based, recently fixed), input validation with hard limits, honest help-texts with rules of thumb, "What does this mean?" explainers per method, example scenarios, executive summary generator, CSV export, and an inherent-vs-residual comparison. **The problem is not content — it is sequencing and state.**

## 2. Findings (ranked by UX damage)

### F1 — Results vanish on any interaction (CRITICAL, the "not intuitive" root cause)
All results render inside `if calculate:` (line 467) with no `session_state`. Streamlit reruns the whole script on every widget event, so: user clicks Calculate → scrolls results → nudges one slider to compare → **everything disappears**. Worse: the CSV `download_button` sits inside the same block — clicking Download triggers a rerun and *wipes the results the user just exported*. This single defect explains most of the "flow feels broken" experience.
**Fix:** store computed results in `st.session_state["results"]`; render whenever present; add a visible "inputs changed since last calculation" warning instead of deleting output. (~1 h)

### F2 — One endless page doing three jobs (HIGH)
Tab 1 stacks: intro → example loader → 2×3 input groups (FAIR/MC, ROI, LEC) → button → KPI row → 4 method sections → charts → inherent/residual → executive summary → scenario summary → CSV. That's ~12 scroll-screens. The user's actual mental model is sequential: *describe scenario → see exposure → evaluate control → take away report*. The UI presents everything in parallel and buries the payoff below the fold.
**Fix:** restructure into a stepper (see §3, Phase 2). Cheap first step: after Calculate, auto-scroll/anchor to results and collapse the input area into an expander showing a one-line summary of the loaded scenario.

### F3 — Statistician's vocabulary as field labels (HIGH)
First-contact labels include "LEF std", "Loss Magnitude CV — coefficient of variation (uncertainty as % of mean)", "lognormal". The target user (IT risk professional, possibly demoing to a CISO) shouldn't need distribution theory to enter a scenario. The excellent explanations exist but hide in tooltips.
**Fix:** plain-language primary labels with the technical term secondary: "Hoe onzeker is je frequentie-schatting? (LEF σ)". Replace the two CV/σ number fields with a 3-position choice — Low / Medium / High uncertainty (mapped to 0.1/0.3/0.5) — plus an "Advanced" expander exposing the raw numbers for power users. Nothing is lost; the entry barrier drops dramatically.

### F4 — Example-loader state confusion (MEDIUM)
The selectbox auto-fills defaults via `val()`, but once a user edits any field the dropdown still displays the example name — the UI now lies about what's loaded. There is also no way back to "my own values".
**Fix:** on example change, write values into `session_state` once (explicit "Load" action), then set the selector to "Custom (edited)" the moment any field diverges. Add a "Reset inputs" button.

### F5 — LEC mixed into the same form (MEDIUM)
LEC ("quick prioritisation *without* dollar values") sits beside FAIR inputs that demand dollar values — two different maturity levels of the same question, presented as one form. Users doing a quick triage still face the full FAIR form.
**Fix:** make the method a choice, not a pile: "Quick scan (LEC, 3 sliders, 30 sec)" vs. "Full quantification (FAIR + Monte Carlo)". LEC results can end with "ready for the next step? quantify in €".

### F6 — Sidebar is a theory library, not navigation (MEDIUM)
The sidebar holds four methodology expanders and no controls. Prime navigation real estate spent on reference material, while the actual mode/tabs live in the main area.
**Fix:** sidebar = scenario management (loaded scenario, method choice, Reset, Export); move methodology explainers to the "How to Use" tab where they belong.

### F7 — Report is copy-paste, not artifact (LOW)
Executive summary ends with "Select all and copy the text above." For a tool whose audience is boards/CISOs, the takeaway should be one click.
**Fix:** `st.download_button` for a Markdown/HTML one-pager (summary + KPIs + both charts); keep CSV for the analysts. (Charts export via Plotly `to_image` needs kaleido — acceptable dependency, or ship HTML.)

### F8 — No persistence of user scenarios (LOW, quick win)
Examples are hardcoded; user scenarios die with the browser tab. A JSON "save scenario / load scenario" (download/upload) costs ~30 lines and enables the STRIDE-import path later (review §5: threat model → quantification is this repo's differentiator).

### F9 — Currency inconsistency (COSMETIC)
Inputs are labeled `($)` for a Dutch insurance context. Make currency configurable (€ default) — stakeholder reports in the wrong currency undermine credibility disproportionately.

### F10 — 834-line single file (MAINTAINABILITY)
Calculator class + UI + copy in one file makes every UX iteration risky. Split: `engine.py` (pure, already tested), `content.py` (examples + explainer texts), `app.py` (UI only). Enables the existing test suite to stay green through UI changes.

## 3. Improvement plan

### Phase 1 — Stop the bleeding (½ day, no redesign)
1. F1: session_state for results + "inputs changed" warning + download outside the gate.
2. F2 (cheap part): anchor to results after Calculate; collapse inputs post-calculation.
3. F4: explicit Load button + "Custom (edited)" state + Reset.
4. F9: currency select (€/$/£) applied to labels and outputs.
**Exit criteria:** calculate → adjust a slider → results remain visible with a stale-warning; CSV download does not destroy the view; example state never lies.

### Phase 2 — Flow redesign (2–3 days)
Restructure Tab 1 as a 4-step stepper (Streamlit-native, no new framework):
1. **Scenario** — name, description, example/JSON load, method choice (Quick scan | Full quantification) [F5, F8]
2. **Inputs** — only the fields for the chosen method; plain-language labels with Low/Med/High uncertainty presets; Advanced expander for σ/CV [F3]
3. **Results** — KPI row pinned on top, then per-method detail cards; inherent vs. residual as toggle rather than second table
4. **Report** — executive summary + one-click Markdown/HTML download + CSV [F7]
Sidebar becomes scenario/session management [F6]. Refactor into engine/content/app modules [F10] — do this first within the phase, it de-risks the rest.
**Exit criteria:** a first-time user completes quick scan in <1 min and full quantification in <5 min without opening a single tooltip; Peter approves the flow on a colleague-demo.

### Phase 3 — The differentiator (later, after stride consolidation ADR)
Import STRIDE-tool JSON export → pre-filled scenarios per threat → portfolio view (aggregate LEC/ALE over all threats). This is the "threat model → quantified exposure" integration the portfolio review called the genuinely valuable piece. Depends on the consolidation decision (stride repo = modeling, this repo = quantification).

## 4. Execution proposal

Phase 1 is small and safe enough for a single Moshe mandate with the existing test suite as regression gate (`test_monte_carlo.py` must stay green — engine untouched). Phase 2 gets its own mandate after Peter approves this plan and the stepper sketch; Fable reviews the PR against the exit criteria. Phase 3 waits for the consolidation ADR.
