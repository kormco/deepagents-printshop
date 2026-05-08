"""HITL-capable engine CLI for deepagents-printshop.

Wraps the LangGraph QA pipeline with start/resume/status commands. Each run
lives in a directory under ``PRINTSHOP_RUNS_DIR`` (defaults to
``~/.printshop/runs``) and is paused/resumed via JSON marker files plus a
LangGraph SQLite checkpoint.

Activated by setting ``HITL_MODE=on`` in the engine environment; with the
flag off, the pipeline runs autonomously as before.
"""

from printshop.contracts import (
    AUTO_APPROVE_RESPONSE,
    SCHEMA_VERSION,
    build_ask_envelope,
    build_done_payload,
    build_error_payload,
    runs_dir,
)

__all__ = [
    "AUTO_APPROVE_RESPONSE",
    "SCHEMA_VERSION",
    "build_ask_envelope",
    "build_done_payload",
    "build_error_payload",
    "runs_dir",
]
