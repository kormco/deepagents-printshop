"""JSON contract schemas and helpers for the printshop HITL CLI.

The CLI and any external driver (Claude Code plugin, regression harness)
exchange state via JSON files in the run directory:

* ``ask.json`` — engine → driver, present while the graph is paused at an
  interrupt; carries the payload the human should react to
* ``response.json`` — driver → engine, present briefly while ``resume`` runs;
  carries the human's decision
* ``done.json`` — engine → driver, present when the graph terminates cleanly
* ``error.json`` — engine → driver, present when a stage failed unrecoverably

All payloads carry ``schema_version`` so old drivers fail loud against new
engines instead of silently misinterpreting fields.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

SCHEMA_VERSION = "1"

# Canned response used by ``printshop start --auto-approve`` and regression
# tests. Mirrors the action vocabulary the LangGraph routing function expects.
AUTO_APPROVE_RESPONSE: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "action": "approve_all",
    "approved_proposal_ids": [],
    "rejected_proposal_ids": [],
    "additional_instructions": "",
    "human_score": None,
    "exit_after_apply": False,
}

VALID_ACTIONS = {
    "approve_all",
    "approve_subset",
    "edit",
    "describe",
    "rerun_stage",
    "skip_to_finalize",
    "abort",
}


def runs_dir() -> Path:
    """Resolve the directory that holds per-run state.

    Order: ``PRINTSHOP_RUNS_DIR`` env var → ``/runs`` (when present, the
    container bind-mount target) → ``~/.printshop/runs``.
    """
    env = os.environ.get("PRINTSHOP_RUNS_DIR")
    if env:
        return Path(env).expanduser()
    container_runs = Path("/runs")
    if container_runs.exists() and container_runs.is_dir():
        return container_runs
    return Path.home() / ".printshop" / "runs"


def run_dir(run_id: str) -> Path:
    """Path to a specific run's directory under the runs root."""
    return runs_dir() / run_id


def build_ask_envelope(run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a node-supplied interrupt payload with envelope fields.

    Node payloads carry stage-specific content (artifacts, scores, proposals,
    etc.). This helper adds ``schema_version`` and ``run_id`` so the file the
    driver reads is self-contained.
    """
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "asked_at": datetime.now().isoformat(timespec="seconds"),
    }
    envelope.update(payload or {})
    return envelope


def build_done_payload(
    run_id: str,
    final_state: Dict[str, Any],
    *,
    wallclock_seconds: Optional[float] = None,
    human_checkpoints: int = 0,
) -> Dict[str, Any]:
    """Build the done.json payload from the graph's final state."""
    output_dir = final_state.get("output_dir", "artifacts/output")
    content_source = final_state.get("content_source", "research_report")

    stages_completed = sorted({
        r.get("agent_type")
        for r in (final_state.get("agent_results") or [])
        if r.get("success")
    } - {None})

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "completed" if final_state.get("success") else "escalated",
        "final_artifacts": {
            "tex": f"{output_dir}/{content_source}.tex",
            "pdf": f"{output_dir}/{content_source}.pdf",
        },
        "stages_completed": stages_completed,
        "iterations_completed": final_state.get("iterations_completed", 0),
        "human_checkpoints": human_checkpoints,
        "escalated": bool(final_state.get("escalated")),
        "wallclock_seconds": wallclock_seconds,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }


def build_error_payload(
    run_id: str,
    error: BaseException,
    *,
    stage: Optional[str] = None,
    last_artifacts: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Build the error.json payload for an unrecoverable failure."""
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "failed",
        "stage": stage,
        "error_type": type(error).__name__,
        "error": str(error),
        "last_artifacts": last_artifacts or {},
        "failed_at": datetime.now().isoformat(timespec="seconds"),
    }


def is_valid_response(response: Dict[str, Any]) -> bool:
    """Quick shape check on a response payload before feeding it to the graph."""
    if not isinstance(response, dict):
        return False
    action = response.get("action")
    return action in VALID_ACTIONS
