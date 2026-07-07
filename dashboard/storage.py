"""
Saved-assessment persistence layer.

Simple JSON-file-per-assessment storage under `dashboard/saved_assessments/`.
No database dependency — keeps the app deployable as a single Streamlit
service (Render free/starter tier, no attached DB).

Known limitation (documented, not hidden): on platforms with an ephemeral
filesystem (e.g. Render web services without a persistent disk), saved
assessments do NOT survive a redeploy or dyno/container restart. This is
acceptable for the tool's current use case (within-session and
short/medium-term board-report history) but is NOT a durable audit trail.
If long-term persistence across redeploys is needed later, this module is
the single place to swap in a real database or object storage backend —
the public functions (`list_assessments`, `save_assessment`,
`delete_assessment`) are the seam to do that behind.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORAGE_DIR = Path(__file__).parent / "saved_assessments"

# Result keys that hold raw, non-serialisable simulation data (e.g. numpy
# arrays of Monte Carlo samples) that is only needed transiently to draw
# the chart in Step 3 -- summary stats (mean/std/p95) already live
# alongside it in the same dict and are what a saved-assessment dashboard
# card actually needs to display.
_NON_SERIALISABLE_NESTED_KEYS = {"sim": {"samples"}}


def _ensure_dir() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _json_safe_results(results: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-ish copy of `results` with known non-serialisable
    fields stripped, plus a defensive `default=str` fallback in the actual
    json.dumps call for anything unexpected (e.g. a stray numpy scalar)."""
    clean: dict[str, Any] = {}
    for key, value in results.items():
        if key in _NON_SERIALISABLE_NESTED_KEYS and isinstance(value, dict):
            clean[key] = {k: v for k, v in value.items() if k not in _NON_SERIALISABLE_NESTED_KEYS[key]}
        else:
            clean[key] = value
    return clean


def save_assessment(scenario_name: str, method: str, results: dict[str, Any],
                     currency_label: str) -> str:
    """Persist one assessment as a JSON file. Returns the new assessment id."""
    _ensure_dir()
    assessment_id = str(uuid.uuid4())
    record = {
        "id": assessment_id,
        "scenario_name": scenario_name,
        "method": method,
        "currency_label": currency_label,
        "results": _json_safe_results(results),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    path = STORAGE_DIR / f"{assessment_id}.json"
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    return assessment_id


def list_assessments() -> list[dict[str, Any]]:
    """Return all saved assessments, newest first. Corrupt files are skipped."""
    _ensure_dir()
    records = []
    for path in STORAGE_DIR.glob("*.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    records.sort(key=lambda r: r.get("saved_at", ""), reverse=True)
    return records


def delete_assessment(assessment_id: str) -> bool:
    """Delete one saved assessment by id. Returns True if a file was removed."""
    _ensure_dir()
    path = STORAGE_DIR / f"{assessment_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def get_assessment(assessment_id: str) -> dict[str, Any] | None:
    _ensure_dir()
    path = STORAGE_DIR / f"{assessment_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
