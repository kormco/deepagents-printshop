"""
Workflow Coordinator

Provides quality assessment and workflow summary utilities for the QA pipeline.
The LangGraph graph handles orchestration directly; this module supplies the
quality-gate evaluation helpers that nodes and routing functions call.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.qa_orchestrator.quality_gates import QualityGateManager, QualityAssessment
from agents.qa_orchestrator.pipeline_types import AgentResult, AgentType, WorkflowStage  # noqa: F401  -- re-exported
from tools.version_manager import VersionManager
from tools.change_tracker import ChangeTracker


class WorkflowCoordinator:
    """
    Quality assessment and summary utilities for the QA pipeline.

    The LangGraph graph owns orchestration; this class provides:
    - assess_workflow_quality()  -- build a QualityAssessment from raw agent result dicts
    - get_workflow_summary()     -- build a summary dict from PipelineState
    - quality_gate_manager       -- for gate evaluations in routing functions
    """

    def __init__(self, content_source: str = "research_report"):
        self.content_source = content_source
        self.version_manager = VersionManager()
        self.change_tracker = ChangeTracker()
        self.quality_gate_manager = QualityGateManager()

        # Set up paths based on content source
        self.content_dir = Path(f"artifacts/sample_content/{content_source}")
        self.output_filename = content_source

    def assess_workflow_quality(self, agent_results: List[Dict[str, Any]]) -> QualityAssessment:
        """
        Assess overall workflow quality based on agent result dicts.

        Args:
            agent_results: List of serialized AgentResult dicts from PipelineState.

        Returns:
            Comprehensive quality assessment.
        """
        assessment = QualityAssessment()

        for r in agent_results:
            ar = AgentResult.from_dict(r)

            if ar.agent_type == AgentType.CONTENT_EDITOR and ar.success:
                assessment.content_score = int(ar.quality_score) if ar.quality_score else None
                assessment.content_issues = ar.issues_found

            elif ar.agent_type == AgentType.LATEX_SPECIALIST and ar.success:
                assessment.latex_score = int(ar.quality_score) if ar.quality_score else None
                assessment.latex_issues = ar.issues_found

                if ar.metadata and "latex_analysis" in ar.metadata:
                    latex_analysis = ar.metadata["latex_analysis"]
                    assessment.latex_structure = latex_analysis.get("structure_score")
                    assessment.latex_typography = latex_analysis.get("typography_score")
                    assessment.latex_tables_figures = latex_analysis.get("tables_figures_score")
                    assessment.latex_best_practices = latex_analysis.get("best_practices_score")

            elif ar.agent_type == AgentType.VISUAL_QA and ar.success:
                if ar.quality_score is not None:
                    assessment.visual_qa_score = float(ar.quality_score)
                assessment.visual_qa_issues = ar.issues_found

        return assessment

    def get_workflow_summary(self, state: Dict[str, Any]) -> Dict:
        """
        Generate comprehensive workflow summary from PipelineState.

        Args:
            state: Final PipelineState dict.

        Returns:
            Workflow summary dictionary.
        """
        agent_results = [AgentResult.from_dict(r) for r in state.get("agent_results", [])]

        # Get final quality assessment
        quality_assessments = state.get("quality_assessments", [])
        final_assessment = quality_assessments[-1] if quality_assessments else None

        # Calculate agent performance
        agent_performance: Dict[str, Any] = {}
        for ar in agent_results:
            agent_name = ar.agent_type.value
            if agent_name not in agent_performance:
                agent_performance[agent_name] = {
                    "executions": 0,
                    "successes": 0,
                    "total_time": 0,
                    "quality_improvements": [],
                }

            perf = agent_performance[agent_name]
            perf["executions"] += 1
            if ar.success:
                perf["successes"] += 1
            perf["total_time"] += ar.processing_time
            if ar.quality_score:
                perf["quality_improvements"].append(ar.quality_score)

        return {
            "workflow_id": state.get("workflow_id", ""),
            "execution_summary": {
                "start_time": state.get("start_time"),
                "end_time": state.get("end_time"),
                "total_processing_time": state.get("total_processing_time"),
                "iterations_completed": state.get("iterations_completed", 0),
                "final_stage": state.get("current_stage", "unknown"),
                "success": state.get("success", False),
                "human_handoff": state.get("human_handoff", False),
                "escalated": state.get("escalated", False),
            },
            "version_progression": {
                "starting_version": agent_results[0].version_created if agent_results else None,
                "final_version": state.get("current_version"),
                "versions_created": [r.version_created for r in agent_results if r.success],
            },
            "quality_progression": {
                "final_assessment": final_assessment,
                "quality_evaluations": len(state.get("quality_evaluations", [])),
                "overall_score": final_assessment.get("overall_score") if final_assessment else None,
            },
            "agent_performance": agent_performance,
        }
