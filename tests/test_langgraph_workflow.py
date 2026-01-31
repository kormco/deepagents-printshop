"""Tests for the LangGraph QA pipeline workflow.

All tests run without Docker, TeX Live, or API keys.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.qa_orchestrator.langgraph_workflow import (  # noqa: E402, I001
    build_qa_graph,
    compile_qa_pipeline,
    export_mermaid_diagram,
    merge_dicts,
    route_after_content_review,
    route_after_latex_optimization,
    route_after_quality_assessment,
    state_to_workflow_execution,
)
from agents.qa_orchestrator.quality_gates import (  # noqa: E402
    QualityAssessment,
    QualityGateEvaluation,
    QualityGateResult,
)
from agents.qa_orchestrator.workflow_coordinator import WorkflowExecution, WorkflowStage  # noqa: E402


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
        ]:
            assert node in mermaid, f"Node '{node}' missing from Mermaid diagram"


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

class TestRouting:
    @patch("agents.qa_orchestrator.langgraph_workflow._build_coordinator")
    def test_route_content_pass(self, mock_build):
        """Score 85 routes to latex_optimization."""
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
        mock_build.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [{"agent_type": "content_editor", "success": True, "version_created": "v1", "quality_score": 85, "processing_time": 1.0, "issues_found": [], "optimizations_applied": []}],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_content_review(state)
        assert result == "latex_optimization"

    @patch("agents.qa_orchestrator.langgraph_workflow._build_coordinator")
    def test_route_content_iterate(self, mock_build):
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
        mock_build.return_value = mock_coord

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

    @patch("agents.qa_orchestrator.langgraph_workflow._build_coordinator")
    def test_route_content_escalate_at_max_iterations(self, mock_build):
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
        mock_build.return_value = mock_coord

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

    @patch("agents.qa_orchestrator.langgraph_workflow._build_coordinator")
    def test_route_latex_pass(self, mock_build):
        """Score 90 routes to visual_qa."""
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
        mock_build.return_value = mock_coord

        state = {
            "content_source": "research_report",
            "agent_results": [],
            "quality_assessments": [],
            "quality_evaluations": [],
            "iterations_completed": 0,
            "agent_context": {},
        }
        result = route_after_latex_optimization(state)
        assert result == "visual_qa"

    @patch("agents.qa_orchestrator.langgraph_workflow._build_coordinator")
    def test_route_latex_iterate(self, mock_build):
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
        mock_build.return_value = mock_coord

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
# State conversion tests
# ---------------------------------------------------------------------------

class TestStateConversion:
    def test_state_to_workflow_execution(self, sample_initial_state):
        """Round-trip PipelineState -> WorkflowExecution."""
        state = sample_initial_state.copy()
        state["current_version"] = "v2_latex_optimized"
        state["success"] = True
        state["human_handoff"] = True
        state["iterations_completed"] = 1
        state["current_stage"] = "completion"
        state["end_time"] = "2025-01-01T01:00:00"
        state["agent_results"] = [
            {
                "agent_type": "content_editor",
                "success": True,
                "version_created": "v1_content_edited",
                "quality_score": 88,
                "processing_time": 10.5,
                "issues_found": [],
                "optimizations_applied": ["improved grammar"],
                "error_message": None,
                "metadata": None,
            }
        ]
        state["quality_assessments"] = [
            {"content_score": 88, "latex_score": 90, "overall_score": 89}
        ]

        wf = state_to_workflow_execution(state)

        assert isinstance(wf, WorkflowExecution)
        assert wf.workflow_id == "test_pipeline"
        assert wf.success is True
        assert wf.human_handoff is True
        assert wf.iterations_completed == 1
        assert wf.final_version == "v2_latex_optimized"
        assert wf.current_stage == WorkflowStage.COMPLETION
        assert len(wf.agents_executed) == 1
        assert wf.agents_executed[0].agent_type.value == "content_editor"
        assert wf.agents_executed[0].quality_score == 88
        assert len(wf.quality_assessments) == 1
        assert wf.total_processing_time == 3600.0  # 1 hour

    def test_state_to_workflow_empty(self, sample_initial_state):
        """Conversion works with an empty initial state."""
        wf = state_to_workflow_execution(sample_initial_state)
        assert isinstance(wf, WorkflowExecution)
        assert wf.success is False
        assert wf.agents_executed == []


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

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
