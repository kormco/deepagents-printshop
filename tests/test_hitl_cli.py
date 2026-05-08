"""Tests for the HITL engine CLI and its LangGraph wiring.

No Docker, TeX Live, or API keys required. The graph itself is exercised
elsewhere (test_langgraph_workflow.py); these tests cover only the
HITL-specific additions: the HITL_MODE flag, the human-checkpoint node and
its routing, the JSON contracts, and the CLI's filesystem-only subcommands.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Project root on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.qa_orchestrator.langgraph_workflow import (  # noqa: E402, I001
    _build_latex_checkpoint_payload,
    build_qa_graph,
    get_hitl_mode,
    route_after_human_checkpoint,
    route_after_latex_optimization_or_hitl,
)
from agents.qa_orchestrator.quality_gates import (  # noqa: E402
    QualityAssessment,
    QualityGateEvaluation,
    QualityGateResult,
)
from printshop.cli import (  # noqa: E402, I001
    _build_initial_state,
    _build_parser,
    _extract_interrupt_payload,
    cmd_abort,
    cmd_list,
    cmd_status,
)
from printshop.contracts import (  # noqa: E402
    AUTO_APPROVE_RESPONSE,
    SCHEMA_VERSION,
    build_ask_envelope,
    build_done_payload,
    build_error_payload,
    is_valid_response,
    run_dir,
    runs_dir,
)


# ---------------------------------------------------------------------------
# HITL flag
# ---------------------------------------------------------------------------

class TestHitlFlag:
    def test_default_is_off(self, monkeypatch):
        monkeypatch.delenv("HITL_MODE", raising=False)
        assert get_hitl_mode() is False

    def test_on_lowercase(self, monkeypatch):
        monkeypatch.setenv("HITL_MODE", "on")
        assert get_hitl_mode() is True

    def test_on_mixed_case(self, monkeypatch):
        monkeypatch.setenv("HITL_MODE", "ON")
        assert get_hitl_mode() is True

    def test_on_with_whitespace(self, monkeypatch):
        monkeypatch.setenv("HITL_MODE", "  on  ")
        assert get_hitl_mode() is True

    def test_garbage_is_off(self, monkeypatch):
        monkeypatch.setenv("HITL_MODE", "yes")
        assert get_hitl_mode() is False


# ---------------------------------------------------------------------------
# Routing: HITL on
# ---------------------------------------------------------------------------

def _state_with_latex_result(*, success: bool, score: int = 90):
    return {
        "content_source": "research_report",
        "agent_results": [{
            "agent_type": "latex_specialist",
            "success": success,
            "version_created": "v2_latex_optimized",
            "quality_score": score if success else None,
            "processing_time": 1.0,
            "issues_found": [] if success else ["PDF_COMPILATION_FAILED: oops"],
            "optimizations_applied": [],
        }],
        "quality_assessments": [],
        "quality_evaluations": [],
        "iterations_completed": 0,
        "agent_context": {},
    }


class TestRouteAfterLatexOrHitl:
    def test_hitl_off_defers_to_existing_routing(self, monkeypatch):
        """With HITL off, the wrapper must delegate to route_after_latex_optimization."""
        monkeypatch.delenv("HITL_MODE", raising=False)
        with patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator") as MockCoord:
            mock = MagicMock()
            mock.assess_workflow_quality.return_value = QualityAssessment(latex_score=90)
            mock.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
                gate_name="latex_quality", result=QualityGateResult.PASS, score=90, threshold=85,
                reasons=[], recommendations=[], next_action="proceed_to_visual_qa",
            )
            MockCoord.return_value = mock
            assert route_after_latex_optimization_or_hitl(_state_with_latex_result(success=True)) == "enrich_for_visual_qa"

    def test_hitl_on_with_success_routes_to_checkpoint(self, monkeypatch):
        monkeypatch.setenv("HITL_MODE", "on")
        result = route_after_latex_optimization_or_hitl(_state_with_latex_result(success=True))
        assert result == "human_checkpoint_after_latex"

    def test_hitl_on_with_failure_defers(self, monkeypatch):
        """Compilation failure should still drive the auto-retry path even when HITL is on."""
        monkeypatch.setenv("HITL_MODE", "on")
        with patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator") as MockCoord:
            mock = MagicMock()
            mock.assess_workflow_quality.return_value = QualityAssessment(latex_score=50)
            mock.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
                gate_name="latex_quality", result=QualityGateResult.ITERATE, score=50, threshold=85,
                reasons=[], recommendations=[], next_action="run_latex_specialist",
            )
            mock.quality_gate_manager.thresholds.max_iterations = 3
            MockCoord.return_value = mock
            result = route_after_latex_optimization_or_hitl(_state_with_latex_result(success=False))
            assert result in ("iteration", "escalation")
            assert result != "human_checkpoint_after_latex"

    def test_hitl_on_no_latex_results_defers(self, monkeypatch):
        """Edge: if no latex_specialist result is present, defer to autonomous routing."""
        monkeypatch.setenv("HITL_MODE", "on")
        with patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator") as MockCoord:
            mock = MagicMock()
            mock.assess_workflow_quality.return_value = QualityAssessment(latex_score=0)
            mock.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
                gate_name="latex_quality", result=QualityGateResult.ITERATE, score=0, threshold=85,
                reasons=[], recommendations=[], next_action="run_latex_specialist",
            )
            mock.quality_gate_manager.thresholds.max_iterations = 3
            MockCoord.return_value = mock
            state = _state_with_latex_result(success=True)
            state["agent_results"] = []
            result = route_after_latex_optimization_or_hitl(state)
            assert result != "human_checkpoint_after_latex"


# ---------------------------------------------------------------------------
# Routing: from human checkpoint
# ---------------------------------------------------------------------------

def _state_with_response(action: str):
    return {
        "content_source": "research_report",
        "agent_context": {"human_response_after_latex": {"action": action}},
        "agent_results": [],
        "quality_assessments": [],
        "quality_evaluations": [],
        "iterations_completed": 0,
    }


class TestRouteAfterHumanCheckpoint:
    def test_abort_routes_to_escalation(self):
        assert route_after_human_checkpoint(_state_with_response("abort")) == "escalation"

    def test_rerun_stage_routes_to_iteration(self):
        assert route_after_human_checkpoint(_state_with_response("rerun_stage")) == "iteration"

    def test_skip_to_finalize_routes_to_completion(self):
        assert route_after_human_checkpoint(_state_with_response("skip_to_finalize")) == "completion"

    def test_approve_all_routes_to_visual_qa_when_auto(self, monkeypatch):
        monkeypatch.delenv("VISUAL_QA_MODE", raising=False)
        assert route_after_human_checkpoint(_state_with_response("approve_all")) == "enrich_for_visual_qa"

    def test_approve_all_skips_visual_qa_when_disabled(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "disabled")
        assert route_after_human_checkpoint(_state_with_response("approve_all")) == "quality_assessment"

    def test_unknown_action_falls_through(self, monkeypatch):
        monkeypatch.delenv("VISUAL_QA_MODE", raising=False)
        assert route_after_human_checkpoint(_state_with_response("nonsense")) == "enrich_for_visual_qa"

    def test_missing_response_defaults_to_proceed(self, monkeypatch):
        monkeypatch.delenv("VISUAL_QA_MODE", raising=False)
        state = {"agent_context": {}, "iterations_completed": 0}
        assert route_after_human_checkpoint(state) == "enrich_for_visual_qa"


# ---------------------------------------------------------------------------
# Ask payload
# ---------------------------------------------------------------------------

class TestLatexCheckpointPayload:
    def test_payload_shape(self):
        state = {
            "content_source": "research_report",
            "output_dir": "/tmp/out",
            "iterations_completed": 1,
            "agent_results": [{
                "agent_type": "latex_specialist",
                "success": True,
                "version_created": "v2_latex_optimized",
                "quality_score": 88,
                "processing_time": 1.0,
                "issues_found": [],
                "optimizations_applied": [],
            }],
            "agent_context": {
                "latex_specialist_notes": {
                    "structure_score": 23,
                    "typography_score": 22,
                    "typography_issues": ["minor: heading spacing"],
                    "compilation_success": True,
                },
            },
        }
        p = _build_latex_checkpoint_payload(state)
        assert p["stage"] == "latex_optimization"
        assert p["iteration"] == 1
        assert p["scores"]["agent"]["value"] == 88
        assert p["artifacts"]["pdf"] == "/tmp/out/research_report.pdf"
        assert p["artifacts"]["tex"] == "/tmp/out/research_report.tex"
        assert "approve_all" in p["valid_actions"]
        assert p["notes"]["typography_issues"] == ["minor: heading spacing"]


# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

class TestGraphIncludesCheckpoint:
    def test_human_checkpoint_node_present(self):
        graph = build_qa_graph()
        compiled = graph.compile()
        assert "human_checkpoint_after_latex" in compiled.get_graph().nodes


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_auto_approve_shape(self):
        assert AUTO_APPROVE_RESPONSE["action"] == "approve_all"
        assert AUTO_APPROVE_RESPONSE["schema_version"] == SCHEMA_VERSION
        assert is_valid_response(AUTO_APPROVE_RESPONSE)

    def test_is_valid_response_rejects_unknown_action(self):
        assert not is_valid_response({"action": "nuke_it"})

    def test_is_valid_response_rejects_missing_action(self):
        assert not is_valid_response({})

    def test_is_valid_response_rejects_non_dict(self):
        assert not is_valid_response("approve_all")

    def test_build_ask_envelope_adds_metadata(self):
        env = build_ask_envelope("abc12345", {"stage": "latex_optimization", "question": "?"})
        assert env["schema_version"] == SCHEMA_VERSION
        assert env["run_id"] == "abc12345"
        assert env["stage"] == "latex_optimization"
        assert "asked_at" in env

    def test_build_done_payload_basic(self):
        final = {
            "content_source": "research_report",
            "output_dir": "/tmp/out",
            "success": True,
            "iterations_completed": 2,
            "agent_results": [
                {"agent_type": "content_editor", "success": True},
                {"agent_type": "latex_specialist", "success": True},
            ],
        }
        d = build_done_payload("xyz", final, wallclock_seconds=10.5, human_checkpoints=2)
        assert d["status"] == "completed"
        assert d["run_id"] == "xyz"
        assert d["wallclock_seconds"] == 10.5
        assert d["human_checkpoints"] == 2
        assert "content_editor" in d["stages_completed"]
        assert "latex_specialist" in d["stages_completed"]
        assert d["final_artifacts"]["pdf"] == "/tmp/out/research_report.pdf"

    def test_build_done_payload_escalated(self):
        d = build_done_payload("xyz", {"escalated": True, "success": False}, human_checkpoints=0)
        assert d["status"] == "escalated"
        assert d["escalated"] is True

    def test_build_error_payload(self):
        e = build_error_payload("xyz", ValueError("boom"), stage="latex_optimization")
        assert e["status"] == "failed"
        assert e["stage"] == "latex_optimization"
        assert e["error_type"] == "ValueError"
        assert e["error"] == "boom"


# ---------------------------------------------------------------------------
# Initial state builder
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_initial_state_shape(self, tmp_path):
        s = _build_initial_state("abc", "research_report", tmp_path)
        assert s["workflow_id"] == "abc"
        assert s["content_source"] == "research_report"
        assert s["starting_version"] == "v0_original"
        assert s["iterations_completed"] == 0
        assert s["agent_results"] == []
        assert s["agent_context"] == {}
        assert s["output_dir"] == str(tmp_path)


# ---------------------------------------------------------------------------
# Interrupt payload extraction
# ---------------------------------------------------------------------------

class TestExtractInterruptPayload:
    def test_no_interrupt(self):
        assert _extract_interrupt_payload({"foo": "bar"}) is None

    def test_empty_interrupt_list(self):
        assert _extract_interrupt_payload({"__interrupt__": []}) is None

    def test_extracts_value_attribute(self):
        class FakeInterrupt:
            value = {"stage": "latex_optimization", "question": "?"}
        result = _extract_interrupt_payload({"__interrupt__": [FakeInterrupt()]})
        assert result == {"stage": "latex_optimization", "question": "?"}

    def test_non_dict_result_returns_none(self):
        assert _extract_interrupt_payload("not a dict") is None


# ---------------------------------------------------------------------------
# CLI argparse
# ---------------------------------------------------------------------------

class TestParser:
    def test_start_requires_content_type(self):
        parser = _build_parser()
        # Missing --content-type should error
        with patch("sys.stderr"):
            try:
                parser.parse_args(["start", "abc"])
            except SystemExit as e:
                assert e.code != 0

    def test_start_with_auto_approve(self):
        args = _build_parser().parse_args(["start", "abc", "--content-type", "research_report", "--auto-approve"])
        assert args.cmd == "start"
        assert args.run_id == "abc"
        assert args.content_type == "research_report"
        assert args.auto_approve is True
        assert args.auto_approve_max_steps == 20

    def test_resume_requires_response(self):
        parser = _build_parser()
        with patch("sys.stderr"):
            try:
                parser.parse_args(["resume", "abc"])
            except SystemExit as e:
                assert e.code != 0

    def test_status_minimal(self):
        args = _build_parser().parse_args(["status", "abc"])
        assert args.cmd == "status"
        assert args.run_id == "abc"


# ---------------------------------------------------------------------------
# CLI status/list/abort against tmp runs dir
# ---------------------------------------------------------------------------

def _make_run(root: Path, name: str, *, ask=False, done=False, error=False):
    rd = root / name
    rd.mkdir(parents=True, exist_ok=True)
    if ask:
        (rd / "ask.json").write_text("{}", encoding="utf-8")
    if done:
        (rd / "done.json").write_text("{}", encoding="utf-8")
    if error:
        (rd / "error.json").write_text("{}", encoding="utf-8")
    return rd


class TestCliStatusListAbort:
    def test_status_running(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "run1")
        rc = cmd_status(MagicMock(run_id="run1"))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "running"

    def test_status_paused(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "run1", ask=True)
        cmd_status(MagicMock(run_id="run1"))
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "paused"
        assert out["ask_path"] is not None

    def test_status_completed(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "run1", done=True)
        cmd_status(MagicMock(run_id="run1"))
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "completed"
        assert out["done_path"] is not None

    def test_status_failed(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "run1", error=True)
        cmd_status(MagicMock(run_id="run1"))
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "failed"

    def test_status_failed_takes_precedence_over_done(self, tmp_path, monkeypatch, capsys):
        """If both error.json and done.json exist (shouldn't normally), error wins."""
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "run1", done=True, error=True)
        cmd_status(MagicMock(run_id="run1"))
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "failed"

    def test_status_not_found(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        rc = cmd_status(MagicMock(run_id="nope"))
        assert rc == 3
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "not_found"

    def test_list_empty(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        rc = cmd_list(MagicMock())
        assert rc == 0
        assert "no runs" in capsys.readouterr().out

    def test_list_with_runs(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        _make_run(tmp_path, "alpha", ask=True)
        _make_run(tmp_path, "beta", done=True)
        cmd_list(MagicMock())
        out = capsys.readouterr().out
        assert "alpha" in out and "paused" in out
        assert "beta" in out and "completed" in out

    def test_abort_marks_failed(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        rd = _make_run(tmp_path, "run1", ask=True)
        rc = cmd_abort(MagicMock(run_id="run1"))
        assert rc == 0
        assert (rd / "error.json").exists()
        assert not (rd / "ask.json").exists()
        err = json.loads((rd / "error.json").read_text())
        assert err["status"] == "aborted"

    def test_abort_unknown_run(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        with patch("sys.stderr"):
            assert cmd_abort(MagicMock(run_id="nope")) == 3


# ---------------------------------------------------------------------------
# Runs dir resolution
# ---------------------------------------------------------------------------

class TestRunsDir:
    def test_env_var_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        assert runs_dir() == tmp_path

    def test_run_dir_joins_run_id(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PRINTSHOP_RUNS_DIR", str(tmp_path))
        assert run_dir("abc12345") == tmp_path / "abc12345"

    def test_default_falls_back_to_home(self, monkeypatch):
        monkeypatch.delenv("PRINTSHOP_RUNS_DIR", raising=False)
        # Patch /runs check to fail
        with patch("printshop.contracts.Path") as MockPath:
            # When called as Path("/runs"), return a fake that doesn't exist
            def path_factory(arg):
                if arg == "/runs":
                    fake = MagicMock()
                    fake.exists.return_value = False
                    return fake
                return Path(arg)
            MockPath.side_effect = path_factory
            MockPath.home.return_value = Path("/fake/home")
            result = runs_dir()
            assert ".printshop" in str(result) and "runs" in str(result)
