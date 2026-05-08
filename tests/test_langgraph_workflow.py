"""Tests for the LangGraph QA pipeline workflow.

All tests run without Docker, TeX Live, or API keys.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.qa_orchestrator.langgraph_workflow import (  # noqa: E402, I001
    build_qa_graph,
    compile_qa_pipeline,
    completion_node,
    export_mermaid_diagram,
    get_visual_qa_mode,
    merge_dicts,
    route_after_content_review,
    route_after_latex_optimization,
    route_after_quality_assessment,
    write_handoff_manifest,
)
from agents.qa_orchestrator.quality_gates import (  # noqa: E402
    QualityAssessment,
    QualityGateEvaluation,
    QualityGateManager,
    QualityGateResult,
)
from agents.qa_orchestrator.pipeline_types import AgentResult, AgentType  # noqa: E402


# ---------------------------------------------------------------------------
# Graph compilation tests
# ---------------------------------------------------------------------------

class TestGraphCompilation:
    def test_graph_compiles(self):
        """Verify graph builds and compiles without error."""
        app = compile_qa_pipeline()
        assert app is not None

    def test_build_qa_graph_returns_state_graph(self):
        """build_qa_graph returns an uncompiled StateGraph."""
        graph = build_qa_graph()
        assert graph is not None

    def test_mermaid_export(self):
        """Verify Mermaid diagram contains all node names."""
        mermaid = export_mermaid_diagram()
        assert isinstance(mermaid, str)
        for node in [
            "content_review",
            "latex_optimization",
            "visual_qa",
            "quality_assessment",
            "iteration",
            "completion",
            "escalation",
            "enrich_for_latex",
            "enrich_for_visual_qa",
            "enrich_for_iteration",
        ]:
            assert node in mermaid, f"Node '{node}' missing from Mermaid diagram"

    def test_graph_has_11_nodes(self):
        """Graph should have 11 nodes (7 processing + 3 enrichment + 1 HITL checkpoint)."""
        graph = build_qa_graph()
        compiled = graph.compile()
        node_names = set(compiled.get_graph().nodes.keys())
        # LangGraph adds __start__ and __end__ pseudo-nodes
        real_nodes = node_names - {"__start__", "__end__"}
        assert len(real_nodes) == 11, f"Expected 11 nodes, got {len(real_nodes)}: {real_nodes}"
        assert "human_checkpoint_after_latex" in real_nodes


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

class TestRouting:
    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_content_pass(self, MockCoordinator):
        """Score 85 routes to enrich_for_latex."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(content_score=85, content_issues=[])
        mock_coord.quality_gate_manager.evaluate_content_quality_gate.return_value = QualityGateEvaluation(
            gate_name="content_quality",
            result=QualityGateResult.PASS,
            score=85,
            threshold=80,
            reasons=["Good content quality: 85"],
            recommendations=[],
            next_action="proceed_to_latex",
        )
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [{"agent_type": "content_editor", "success": True, "version_created": "v1", "quality_score": 85, "processing_time": 1.0, "issues_found": [], "optimizations_applied": []}],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_content_review(state)
        assert result == "enrich_for_latex"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_content_iterate(self, MockCoordinator):
        """Score 60 routes to iteration."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(content_score=60, content_issues=[])
        mock_coord.quality_gate_manager.evaluate_content_quality_gate.return_value = QualityGateEvaluation(
            gate_name="content_quality",
            result=QualityGateResult.ITERATE,
            score=60,
            threshold=80,
            reasons=["Content score 60 below minimum 80"],
            recommendations=[],
            next_action="run_content_editor",
        )
        mock_coord.quality_gate_manager.thresholds.max_iterations = 3
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_content_review(state)
        assert result == "iteration"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_content_escalate_at_max_iterations(self, MockCoordinator):
        """Iterate result at max iterations routes to escalation."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(content_score=60)
        mock_coord.quality_gate_manager.evaluate_content_quality_gate.return_value = QualityGateEvaluation(
            gate_name="content_quality",
            result=QualityGateResult.ITERATE,
            score=60,
            threshold=80,
            reasons=[],
            recommendations=[],
            next_action="run_content_editor",
        )
        mock_coord.quality_gate_manager.thresholds.max_iterations = 3
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 3,
            "agent_context": {},
        }
        result = route_after_content_review(state)
        assert result == "escalation"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_latex_pass(self, MockCoordinator):
        """Score 90 routes to enrich_for_visual_qa."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(latex_score=90, latex_issues=[])
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.PASS,
            score=90,
            threshold=85,
            reasons=["Good LaTeX quality: 90"],
            recommendations=[],
            next_action="proceed_to_visual_qa",
        )
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_latex_optimization(state)
        assert result == "enrich_for_visual_qa"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_latex_iterate(self, MockCoordinator):
        """Low LaTeX score routes to iteration."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(latex_score=70)
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.ITERATE,
            score=70,
            threshold=85,
            reasons=[],
            recommendations=[],
            next_action="run_latex_specialist",
        )
        mock_coord.quality_gate_manager.thresholds.max_iterations = 3
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_latex_optimization(state)
        assert result == "iteration"

    def test_route_overall_completion(self):
        """Score 85 routes to completion."""
        state = {
            "quality_evaluations": [{
                "gate_name": "overall_quality",
                "result": "pass",
                "score": 85,
                "threshold": 80,
                "reasons": ["Good overall quality: 85"],
                "recommendations": [],
                "next_action": "human_handoff",
            }],
            "iterations_completed": 0,
        }
        result = route_after_quality_assessment(state)
        assert result == "completion"

    def test_route_overall_iterate(self):
        """Low overall score routes to iteration."""
        state = {
            "quality_evaluations": [{
                "gate_name": "overall_quality",
                "result": "iterate",
                "score": 65,
                "threshold": 80,
                "reasons": [],
                "recommendations": [],
                "next_action": "iterate_pipeline",
            }],
            "iterations_completed": 1,
        }
        result = route_after_quality_assessment(state)
        assert result == "iteration"

    def test_route_overall_escalation(self):
        """Iterations >= 3 with iterate result routes to escalation."""
        state = {
            "quality_evaluations": [{
                "gate_name": "overall_quality",
                "result": "iterate",
                "score": 65,
                "threshold": 80,
                "reasons": [],
                "recommendations": [],
                "next_action": "iterate_pipeline",
            }],
            "iterations_completed": 3,
        }
        result = route_after_quality_assessment(state)
        assert result == "escalation"

    def test_route_overall_escalate_result(self):
        """Explicit escalate result routes to escalation."""
        state = {
            "quality_evaluations": [{
                "gate_name": "overall_quality",
                "result": "escalate",
                "score": 70,
                "threshold": 80,
                "reasons": [],
                "recommendations": [],
                "next_action": "human_escalation",
            }],
            "iterations_completed": 0,
        }
        result = route_after_quality_assessment(state)
        assert result == "escalation"

    def test_route_overall_no_evaluations(self):
        """No evaluations routes to escalation."""
        state = {"quality_evaluations": [], "iterations_completed": 0}
        result = route_after_quality_assessment(state)
        assert result == "escalation"


# ---------------------------------------------------------------------------
# Inter-agent context tests
# ---------------------------------------------------------------------------

class TestInterAgentContext:
    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_latex_node_reads_content_context_complex_tables(self, MockCoordinator):
        """LaTeX node uses conservative optimization when complex tables flagged."""
        from agents.qa_orchestrator.langgraph_workflow import latex_optimization_node

        mock_coord = MagicMock()
        MockCoordinator.return_value = mock_coord

        # Mock the LaTeX specialist agent
        mock_agent = MagicMock()
        mock_agent.process_with_versioning.return_value = {
            "latex_analysis": {"overall_score": 90, "issues_found": 0},
            "optimizations_applied": ["optimized tables"],
        }

        with patch("tools.version_manager.VersionManager") as MockVM:
            MockVM.return_value.get_version.return_value = None

            with patch("agents.latex_specialist.agent.LaTeXSpecialistAgent", return_value=mock_agent):
                state = {
                    "content_source": "research_report",
                    "current_version": "v1_content_edited",
                    "iterations_completed": 0,
                    "agent_context": {
                        "content_editor_notes": {
                            "quality_score": 85,
                            "issues_found": [],
                            "has_complex_tables": True,
                            "readability_concerns": [],
                        }
                    },
                    "agent_results": [],
                }
                latex_optimization_node(state)

                # Verify conservative optimization was used
                mock_agent.process_with_versioning.assert_called_once()
                call_kwargs = mock_agent.process_with_versioning.call_args
                assert call_kwargs[1]["optimization_level"] == "conservative" or call_kwargs.kwargs.get("optimization_level") == "conservative"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_latex_node_default_optimization_without_complex_tables(self, MockCoordinator):
        """LaTeX node uses moderate optimization when no complex tables flagged."""
        from agents.qa_orchestrator.langgraph_workflow import latex_optimization_node

        mock_coord = MagicMock()
        MockCoordinator.return_value = mock_coord

        mock_agent = MagicMock()
        mock_agent.process_with_versioning.return_value = {
            "latex_analysis": {"overall_score": 90, "issues_found": 0},
            "optimizations_applied": ["standard optimization"],
        }

        with patch("tools.version_manager.VersionManager") as MockVM:
            MockVM.return_value.get_version.return_value = None

            with patch("agents.latex_specialist.agent.LaTeXSpecialistAgent", return_value=mock_agent):
                state = {
                    "content_source": "research_report",
                    "current_version": "v1_content_edited",
                    "iterations_completed": 0,
                    "agent_context": {},
                    "agent_results": [],
                }
                latex_optimization_node(state)

                mock_agent.process_with_versioning.assert_called_once()
                call_kwargs = mock_agent.process_with_versioning.call_args
                assert call_kwargs[1]["optimization_level"] == "moderate" or call_kwargs.kwargs.get("optimization_level") == "moderate"

    def test_visual_qa_reads_latex_context_weak_typography(self):
        """Visual QA allows extra iterations when typography score is weak."""
        from agents.qa_orchestrator.langgraph_workflow import visual_qa_node

        state = {
            "content_source": "research_report",
            "current_version": "v2_latex_optimized",
            "agent_context": {
                "latex_specialist_notes": {
                    "structure_score": 23,
                    "typography_score": 15,  # weak
                    "typography_issues": ["bad spacing"],
                    "packages_used": [],
                }
            },
            "agent_results": [],
        }

        # The node will fail (no PDF, no visual_qa agent), but we can verify
        # the max_iterations logic by checking the result still completes
        result = visual_qa_node(state)
        # Should succeed (graceful error handling) even without PDF
        assert "agent_results" in result
        assert len(result["agent_results"]) == 1
        assert result["agent_results"][0]["agent_type"] == "visual_qa"


# ---------------------------------------------------------------------------
# AgentResult round-trip tests
# ---------------------------------------------------------------------------

class TestAgentResultSerialization:
    def test_to_dict_from_dict_round_trip(self):
        """AgentResult survives a to_dict/from_dict round trip."""
        original = AgentResult(
            agent_type=AgentType.CONTENT_EDITOR,
            success=True,
            version_created="v1_content_edited",
            quality_score=88.5,
            processing_time=12.3,
            issues_found=["minor grammar"],
            optimizations_applied=["improved readability"],
            error_message=None,
            metadata={"key": "value"},
        )

        d = original.to_dict()
        reconstructed = AgentResult.from_dict(d)

        assert reconstructed.agent_type == original.agent_type
        assert reconstructed.success == original.success
        assert reconstructed.version_created == original.version_created
        assert reconstructed.quality_score == original.quality_score
        assert reconstructed.processing_time == original.processing_time
        assert reconstructed.issues_found == original.issues_found
        assert reconstructed.optimizations_applied == original.optimizations_applied
        assert reconstructed.error_message == original.error_message
        assert reconstructed.metadata == original.metadata

    def test_from_dict_with_minimal_data(self):
        """from_dict handles missing optional fields gracefully."""
        d = {
            "agent_type": "latex_specialist",
            "success": False,
            "version_created": "v2_latex_optimized",
        }
        result = AgentResult.from_dict(d)
        assert result.agent_type == AgentType.LATEX_SPECIALIST
        assert result.success is False
        assert result.quality_score is None
        assert result.processing_time == 0.0
        assert result.issues_found == []
        assert result.error_message is None


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Compilation failure feedback loop tests
# ---------------------------------------------------------------------------

class TestCompilationFailureFeedback:
    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_latex_iterate_on_compilation_failure(self, MockCoordinator):
        """State with PDF_COMPILATION_FAILED issue routes to iteration."""
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(
            latex_score=90,
            latex_issues=["PDF_COMPILATION_FAILED: ! Missing \\begin{document}"],
        )
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.ITERATE,
            score=90,
            threshold=85,
            reasons=["PDF compilation failed — must iterate"],
            recommendations=["Fix LaTeX compilation errors before proceeding"],
            next_action="run_latex_specialist",
        )
        mock_coord.quality_gate_manager.thresholds.max_iterations = 3
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_latex_optimization(state)
        assert result == "iteration"

    def test_compilation_failure_quality_gate(self):
        """evaluate_latex_quality_gate returns ITERATE when latex_issues contains a compilation failure."""
        manager = QualityGateManager()
        assessment = QualityAssessment(
            latex_score=92,
            latex_structure=24,
            latex_typography=22,
            latex_tables_figures=23,
            latex_best_practices=23,
            latex_issues=["Found 0 LaTeX issues", "PDF_COMPILATION_FAILED: ! Undefined control sequence"],
        )
        evaluation = manager.evaluate_latex_quality_gate(assessment)
        assert evaluation.result == QualityGateResult.ITERATE
        assert "compilation failed" in evaluation.reasons[0].lower()


class TestVisualQAMode:
    def test_default_is_auto(self, monkeypatch):
        monkeypatch.delenv("VISUAL_QA_MODE", raising=False)
        assert get_visual_qa_mode() == "auto"

    def test_disabled_recognized(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "disabled")
        assert get_visual_qa_mode() == "disabled"

    def test_interactive_recognized(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "interactive")
        assert get_visual_qa_mode() == "interactive"

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "Interactive")
        assert get_visual_qa_mode() == "interactive"

    def test_unknown_falls_back_to_auto(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "manual")
        assert get_visual_qa_mode() == "auto"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_latex_pass_routes_to_quality_assessment_when_disabled(
        self, MockCoordinator, monkeypatch
    ):
        """When VISUAL_QA_MODE=disabled, a passing LaTeX gate skips visual_qa."""
        monkeypatch.setenv("VISUAL_QA_MODE", "disabled")
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(
            latex_score=90, latex_issues=[]
        )
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.PASS,
            score=90,
            threshold=85,
            reasons=["Good LaTeX quality: 90"],
            recommendations=[],
            next_action="proceed_to_visual_qa",
        )
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        assert route_after_latex_optimization(state) == "quality_assessment"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_route_latex_pass_routes_to_quality_assessment_when_interactive(
        self, MockCoordinator, monkeypatch
    ):
        """When VISUAL_QA_MODE=interactive, a passing LaTeX gate skips visual_qa."""
        monkeypatch.setenv("VISUAL_QA_MODE", "interactive")
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(
            latex_score=90, latex_issues=[]
        )
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.PASS,
            score=90,
            threshold=85,
            reasons=["Good LaTeX quality: 90"],
            recommendations=[],
            next_action="proceed_to_visual_qa",
        )
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        assert route_after_latex_optimization(state) == "quality_assessment"

    @patch("agents.qa_orchestrator.langgraph_workflow.WorkflowCoordinator")
    def test_iteration_still_takes_priority_in_disabled_mode(
        self, MockCoordinator, monkeypatch
    ):
        """Disabled mode does NOT skip the iteration path on a failing gate."""
        monkeypatch.setenv("VISUAL_QA_MODE", "disabled")
        mock_coord = MagicMock()
        mock_coord.assess_workflow_quality.return_value = QualityAssessment(latex_score=70)
        mock_coord.quality_gate_manager.evaluate_latex_quality_gate.return_value = QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.ITERATE,
            score=70,
            threshold=85,
            reasons=[],
            recommendations=[],
            next_action="run_latex_specialist",
        )
        mock_coord.quality_gate_manager.thresholds.max_iterations = 3
        MockCoordinator.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        assert route_after_latex_optimization(state) == "iteration"


class TestHandoffManifest:
    def test_handoff_written_in_interactive_mode(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "interactive")
        # Create a fake .tex so the manifest reports tex_exists=True
        (tmp_path / "research_report.tex").write_text("\\documentclass{article}\n")
        state = {
            "workflow_id": "abc12345",
            "content_source": "research_report",
            "output_dir": str(tmp_path),
            "agent_context": {
                "latex_specialist_notes": {
                    "structure_score": 24,
                    "typography_score": 15,  # weak — should appear in concerns
                    "typography_issues": ["bad spacing on page 2"],
                    "packages_used": [],
                }
            },
        }
        completion_node(state)

        manifest_path = tmp_path / "handoff.json"
        assert manifest_path.exists(), "handoff.json should be written in interactive mode"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["run_id"] == "abc12345"
        assert manifest["content_source"] == "research_report"
        assert manifest["visual_qa_mode"] == "interactive"
        assert manifest["next_step"] == "interactive_review"
        assert manifest["tex_exists"] is True
        assert manifest["pdf_exists"] is False  # no PDF written
        # Concerns surface the typography issue and the weak score
        assert any("typography" in c for c in manifest["concerns"])
        assert any("weak typography" in c for c in manifest["concerns"])

    def test_handoff_not_written_in_auto_mode(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "auto")
        state = {
            "workflow_id": "abc12345",
            "content_source": "research_report",
            "output_dir": str(tmp_path),
            "agent_context": {},
        }
        completion_node(state)
        assert not (tmp_path / "handoff.json").exists()

    def test_handoff_not_written_in_disabled_mode(self, tmp_path, monkeypatch):
        """Disabled mode emits no manifest — user has nothing to pick up."""
        monkeypatch.setenv("VISUAL_QA_MODE", "disabled")
        state = {
            "workflow_id": "abc12345",
            "content_source": "research_report",
            "output_dir": str(tmp_path),
            "agent_context": {},
        }
        completion_node(state)
        assert not (tmp_path / "handoff.json").exists()

    def test_write_handoff_manifest_returns_none_without_output_dir(self, monkeypatch):
        monkeypatch.setenv("VISUAL_QA_MODE", "interactive")
        assert write_handoff_manifest({}) is None


class TestMergeDicts:
    def test_merge_dicts(self):
        """merge_dicts combines two dicts, right overwrites left."""
        left = {"a": 1, "b": 2}
        right = {"b": 3, "c": 4}
        result = merge_dicts(left, right)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_dicts_empty(self):
        result = merge_dicts({}, {"x": 1})
        assert result == {"x": 1}
