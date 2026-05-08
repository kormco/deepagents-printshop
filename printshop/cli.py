"""HITL-capable engine CLI.

Usage::

    python -m printshop start <run_id> --content-type research_report [--auto-approve]
    python -m printshop resume <run_id> --response <path-to-response.json>
    python -m printshop status <run_id>
    python -m printshop list
    python -m printshop abort <run_id>
    python -m printshop logs <run_id>

Each ``start`` and ``resume`` invocation runs the LangGraph QA pipeline until
it pauses at an ``interrupt()`` or completes. State persists in
``<runs_dir>/<run_id>/checkpoint.sqlite``; the CLI is stateless across calls.
Marker files (``ask.json``, ``done.json``, ``error.json``) are the single
source of truth for "what should the driver do next".

Exit codes:
* ``0`` paused at interrupt (success, awaiting human) OR completed
* ``1`` engine error / unrecoverable failure
* ``2`` invalid arguments
* ``3`` run not found
* ``4`` run not in a resumable state
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is importable when invoked via ``python -m printshop``
# from inside the container or via the source tree.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from printshop.contracts import (  # noqa: E402, I001
    AUTO_APPROVE_RESPONSE,
    SCHEMA_VERSION,
    build_ask_envelope,
    build_done_payload,
    build_error_payload,
    is_valid_response,
)
from printshop.contracts import run_dir as _run_dir  # noqa: E402
from printshop.contracts import runs_dir as _runs_dir  # noqa: E402


# ---------------------------------------------------------------------------
# JSON I/O helpers
# ---------------------------------------------------------------------------

def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON via temp+rename so a partial write never confuses a poller."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _append_event(run_dir: Path, event: str, **fields: Any) -> None:
    """Append a single line to the run's events.log."""
    run_dir.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **fields},
        default=str,
    )
    with open(run_dir / "events.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _clear_markers(run_dir: Path, *, keep: tuple = ()) -> None:
    """Remove ask/response/done/error markers (selectively) before the next step."""
    for name in ("ask.json", "response.json", "done.json", "error.json"):
        if name in keep:
            continue
        marker = run_dir / name
        marker.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def _build_initial_state(run_id: str, content_type: str, output_dir: Path) -> Dict[str, Any]:
    """Build the PipelineState dict the graph expects for a fresh run."""
    return {
        "workflow_id": run_id,
        "content_source": content_type,
        "starting_version": "v0_original",
        "current_version": "v0_original",
        "current_stage": "initialization",
        "iterations_completed": 0,
        "success": False,
        "human_handoff": False,
        "escalated": False,
        "start_time": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "agent_results": [],
        "quality_assessments": [],
        "quality_evaluations": [],
        "agent_context": {},
    }


# ---------------------------------------------------------------------------
# Graph compilation + invocation
# ---------------------------------------------------------------------------

def _ensure_hitl_on() -> None:
    """Set HITL_MODE=on for the duration of this process if not already set.

    The CLI is the contract between the human and the graph; without HITL
    mode the graph would skip the interrupt nodes and run autonomously,
    defeating the purpose of going through start/resume.
    """
    if (os.environ.get("HITL_MODE") or "").strip().lower() != "on":
        os.environ["HITL_MODE"] = "on"


def _extract_interrupt_payload(result: Any) -> Optional[Dict[str, Any]]:
    """Pull the first pending interrupt's payload out of an invoke() result.

    LangGraph 1.x surfaces pending interrupts as ``result["__interrupt__"]``
    (a list of ``Interrupt`` objects with ``.value``). Returns ``None`` if no
    interrupts are pending — meaning the graph reached an END node.
    """
    if not isinstance(result, dict):
        return None
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    first = interrupts[0]
    value = getattr(first, "value", None)
    if isinstance(value, dict):
        return value
    if value is None and isinstance(first, dict):
        return first.get("value") if isinstance(first.get("value"), dict) else first
    return None


def _invoke_graph(run_id: str, run_dir: Path, command_or_state: Any) -> int:
    """Compile the graph with a SQLite checkpoint and invoke once.

    Writes ask.json/done.json/error.json based on the outcome and returns the
    matching exit code.
    """
    _ensure_hitl_on()

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        from agents.qa_orchestrator.langgraph_workflow import build_qa_graph
    except Exception as exc:
        _append_event(run_dir, "engine_import_failed", error=str(exc))
        _write_json_atomic(run_dir / "error.json", build_error_payload(run_id, exc, stage="bootstrap"))
        return 1

    checkpoint_path = run_dir / "checkpoint.sqlite"
    config = {"configurable": {"thread_id": run_id}}
    started_at = time.monotonic()

    try:
        with SqliteSaver.from_conn_string(str(checkpoint_path)) as saver:
            graph = build_qa_graph().compile(checkpointer=saver)
            result = graph.invoke(command_or_state, config=config)
    except BaseException as exc:  # pragma: no cover - defensive
        _append_event(run_dir, "engine_invoke_failed", error=str(exc))
        _write_json_atomic(run_dir / "error.json", build_error_payload(run_id, exc))
        return 1

    elapsed = time.monotonic() - started_at
    payload = _extract_interrupt_payload(result)

    if payload is not None:
        envelope = build_ask_envelope(run_id, payload)
        _write_json_atomic(run_dir / "ask.json", envelope)
        _append_event(run_dir, "paused", stage=payload.get("stage"))
        return 0

    # Graph ran to END — completion or escalation, both terminal.
    human_checkpoints = sum(
        1 for line in _read_events(run_dir) if line.get("event") == "paused"
    )
    done = build_done_payload(
        run_id,
        result if isinstance(result, dict) else {},
        wallclock_seconds=elapsed,
        human_checkpoints=human_checkpoints,
    )
    _write_json_atomic(run_dir / "done.json", done)
    _append_event(run_dir, "completed", elapsed=round(elapsed, 2))
    return 0


def _read_events(run_dir: Path) -> List[Dict[str, Any]]:
    """Return all events from events.log; tolerates a missing file."""
    log = run_dir / "events.log"
    if not log.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_start(args: argparse.Namespace) -> int:
    rd = _run_dir(args.run_id)
    if rd.exists():
        print(f"error: run {args.run_id!r} already exists at {rd}", file=sys.stderr)
        return 2

    rd.mkdir(parents=True, exist_ok=False)
    output_dir = Path(args.output_dir) if args.output_dir else rd / "artifacts" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    state = _build_initial_state(args.run_id, args.content_type, output_dir)
    _append_event(rd, "started", content_type=args.content_type, schema_version=SCHEMA_VERSION)

    rc = _invoke_graph(args.run_id, rd, state)

    if args.auto_approve:
        return _auto_approve_until_done(args.run_id, rd, rc, max_steps=args.auto_approve_max_steps)
    return rc


def cmd_resume(args: argparse.Namespace) -> int:
    rd = _run_dir(args.run_id)
    if not rd.exists():
        print(f"error: run {args.run_id!r} not found at {rd}", file=sys.stderr)
        return 3

    if (rd / "done.json").exists() or (rd / "error.json").exists():
        print(f"error: run {args.run_id!r} is not in a resumable state", file=sys.stderr)
        return 4

    response_path = Path(args.response).expanduser()
    if not response_path.exists():
        print(f"error: response file not found: {response_path}", file=sys.stderr)
        return 2

    response = _read_json(response_path)
    if not is_valid_response(response):
        print("error: response.json missing/invalid 'action' (expected one of approve_all/etc.)", file=sys.stderr)
        return 2

    # Clear stale markers BEFORE invoking so a poll mid-resume sees no
    # ask.json (i.e., state == running).
    _clear_markers(rd, keep=())
    _append_event(rd, "resumed", action=response.get("action"))

    from langgraph.types import Command
    return _invoke_graph(args.run_id, rd, Command(resume=response))


def cmd_status(args: argparse.Namespace) -> int:
    rd = _run_dir(args.run_id)
    if not rd.exists():
        print(json.dumps({"run_id": args.run_id, "state": "not_found"}))
        return 3

    if (rd / "error.json").exists():
        state = "failed"
    elif (rd / "done.json").exists():
        state = "completed"
    elif (rd / "ask.json").exists():
        state = "paused"
    else:
        state = "running"

    last_mtime: Optional[str] = None
    try:
        latest = max(
            (p for p in rd.iterdir() if p.is_file()),
            key=lambda p: p.stat().st_mtime,
            default=None,
        )
        if latest is not None:
            last_mtime = datetime.fromtimestamp(latest.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        pass

    print(json.dumps({
        "run_id": args.run_id,
        "state": state,
        "last_event_at": last_mtime,
        "ask_path": str(rd / "ask.json") if state == "paused" else None,
        "done_path": str(rd / "done.json") if state == "completed" else None,
        "error_path": str(rd / "error.json") if state == "failed" else None,
    }))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = _runs_dir()
    if not root.exists():
        print("(no runs)")
        return 0
    rows = []
    for rd in sorted(root.iterdir()):
        if not rd.is_dir():
            continue
        if (rd / "error.json").exists():
            state = "failed"
        elif (rd / "done.json").exists():
            state = "completed"
        elif (rd / "ask.json").exists():
            state = "paused"
        else:
            state = "running"
        try:
            mtime = datetime.fromtimestamp(rd.stat().st_mtime).isoformat(timespec="seconds")
        except OSError:
            mtime = "?"
        rows.append((rd.name, state, mtime))
    if not rows:
        print("(no runs)")
        return 0
    width = max(len(r[0]) for r in rows)
    for name, state, mtime in rows:
        print(f"{name:<{width}}  {state:<10}  {mtime}")
    return 0


def cmd_abort(args: argparse.Namespace) -> int:
    rd = _run_dir(args.run_id)
    if not rd.exists():
        print(f"error: run {args.run_id!r} not found", file=sys.stderr)
        return 3
    err = build_error_payload(args.run_id, RuntimeError("aborted by user"), stage="abort")
    err["status"] = "aborted"
    _write_json_atomic(rd / "error.json", err)
    _clear_markers(rd, keep=("error.json",))
    _append_event(rd, "aborted")
    print(json.dumps({"run_id": args.run_id, "state": "aborted"}))
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    rd = _run_dir(args.run_id)
    if not rd.exists():
        print(f"error: run {args.run_id!r} not found", file=sys.stderr)
        return 3
    log = rd / "events.log"
    if not log.exists():
        return 0
    text = log.read_text(encoding="utf-8")
    if args.tail:
        lines = text.splitlines()[-args.tail:]
        text = "\n".join(lines)
    print(text)
    return 0


# ---------------------------------------------------------------------------
# --auto-approve helper
# ---------------------------------------------------------------------------

def _auto_approve_until_done(run_id: str, rd: Path, initial_rc: int, *, max_steps: int) -> int:
    """Repeatedly resume with AUTO_APPROVE_RESPONSE until done/error/limit.

    Used by ``printshop start --auto-approve`` and by regression tests so a
    fresh run can complete end-to-end without a human in the loop.
    """
    rc = initial_rc
    steps = 0
    while rc == 0 and (rd / "ask.json").exists() and steps < max_steps:
        steps += 1
        response_path = rd / "_auto_approve_response.json"
        _write_json_atomic(response_path, AUTO_APPROVE_RESPONSE)

        ns = argparse.Namespace(run_id=run_id, response=str(response_path))
        rc = cmd_resume(ns)
        response_path.unlink(missing_ok=True)

    if rc == 0 and (rd / "ask.json").exists():
        # Hit the step cap with a pending interrupt — surface as escalation
        # rather than silently leaving the run paused forever.
        msg = f"--auto-approve hit max_steps={max_steps} with the run still paused"
        _append_event(rd, "auto_approve_capped", steps=steps)
        _write_json_atomic(rd / "error.json", build_error_payload(run_id, RuntimeError(msg), stage="auto_approve"))
        _clear_markers(rd, keep=("error.json",))
        return 1
    return rc


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="printshop", description="HITL engine CLI for deepagents-printshop.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("start", help="Start a new run; advance to first interrupt or completion.")
    s.add_argument("run_id")
    s.add_argument("--content-type", required=True, dest="content_type")
    s.add_argument("--output-dir", dest="output_dir", default=None)
    s.add_argument("--auto-approve", action="store_true", dest="auto_approve",
                   help="Drive the run end-to-end with canned approve_all responses (regression mode).")
    s.add_argument("--auto-approve-max-steps", type=int, default=20, dest="auto_approve_max_steps")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("resume", help="Resume a paused run with a response.json.")
    s.add_argument("run_id")
    s.add_argument("--response", required=True)
    s.set_defaults(func=cmd_resume)

    s = sub.add_parser("status", help="Print current state of a run as JSON.")
    s.add_argument("run_id")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("list", help="List all runs in the runs directory.")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("abort", help="Mark a run as failed/aborted.")
    s.add_argument("run_id")
    s.set_defaults(func=cmd_abort)

    s = sub.add_parser("logs", help="Print a run's event log.")
    s.add_argument("run_id")
    s.add_argument("--tail", type=int, default=None)
    s.set_defaults(func=cmd_logs)

    return p


def _force_utf8_stdio() -> None:
    """Force UTF-8 on stdout/stderr so emoji and Unicode in agent ``print``
    calls don't crash the run on Windows under cp1252.

    Mirrors the wrapper in ``run_agent.py``. Idempotent and a no-op when
    streams are already UTF-8.
    """
    import io

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    if sys.platform != "win32":
        return
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        encoding = (getattr(stream, "encoding", "") or "").lower()
        if "utf" in encoding:
            continue
        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue
        setattr(sys, name, io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"))


def main(argv: Optional[List[str]] = None) -> int:
    _force_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
