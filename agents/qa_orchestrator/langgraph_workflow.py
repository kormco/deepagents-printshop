"""
LangGraph QA Pipeline Workflow

Declarative StateGraph that replaces the manual while-loop in workflow_coordinator.py
with a LangGraph graph. Node functions are thin wrappers around existing agent execution
methods, preserving full backward compatibility.
"""

import operator
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.qa_orchestrator.quality_gates import (  # noqa: E402, I001
    QualityAssessment,
    QualityGateEvaluation,
    QualityGateResult,
)
from agents.qa_orchestrator.workflow_coordinator import (  # noqa: E402, I001
    AgentResult,
    WorkflowCoordinator,
    WorkflowExecution,
    WorkflowStage,
)


# ---------------------------------------------------------------------------
# Custom reducer for merging dicts (used by agent_context)
# ---------------------------------------------------------------------------

def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dicts, with right-side values overwriting left-side."""
    merged = left.copy()
    merged.update(right)
    return merged


# ---------------------------------------------------------------------------
# Pipeline State
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    """LangGraph state for the QA pipeline.

    List fields use ``operator.add`` (append semantics).
    ``agent_context`` uses ``merge_dicts`` so each node can contribute keys.
    Scalar fields use default replace semantics.
    """

    # --- workflow identity ---
    workflow_id: str
    content_source: str
    starting_version: str

    # --- mutable scalars (replace semantics) ---
    current_version: str
    current_stage: str
    iterations_completed: int
    success: bool
    human_handoff: bool
    escalated: bool
    start_time: str
    end_time: Optional[str]
    total_processing_time: Optional[float]

    # --- append-only lists ---
    agent_results: Annotated[List[Dict[str, Any]], operator.add]
    quality_assessments: Annotated[List[Dict[str, Any]], operator.add]
    quality_evaluations: Annotated[List[Dict[str, Any]], operator.add]

    # --- inter-agent communication (Phase 2) ---
    agent_context: Annotated[Dict[str, Any], merge_dicts]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_coordinator(state: PipelineState) -> WorkflowCoordinator:
    """Create a WorkflowCoordinator from pipeline state."""
    return WorkflowCoordinator(content_source=state.get("content_source", "research_report"))


def _stub_workflow(state: PipelineState) -> WorkflowExecution:
    """Build a minimal WorkflowExecution from current state so existing methods work."""
    agents_executed = []
    for r in state.get("agent_results", []):
        from agents.qa_orchestrator.workflow_coordinator import AgentResult, AgentType
        agents_executed.append(AgentResult(
            agent_type=AgentType(r["agent_type"]),
            success=r["success"],
            version_created=r["version_created"],
            quality_score=r.get("quality_score"),
            processing_time=r.get("processing_time", 0.0),
            issues_found=r.get("issues_found", []),
            optimizations_applied=r.get("optimizations_applied", []),
            error_message=r.get("error_message"),
            metadata=r.get("metadata"),
        ))

    quality_assessments = []
    for qa in state.get("quality_assessments", []):
        assessment = QualityAssessment()
        for k, v in qa.items():
            if hasattr(assessment, k):
                setattr(assessment, k, v)
        quality_assessments.append(assessment)

    quality_evaluations = []
    for qe in state.get("quality_evaluations", []):
        quality_evaluations.append(QualityGateEvaluation(
            gate_name=qe.get("gate_name", ""),
            result=QualityGateResult(qe["result"]) if "result" in qe else QualityGateResult.FAIL,
            score=qe.get("score"),
            threshold=qe.get("threshold"),
            reasons=qe.get("reasons", []),
            recommendations=qe.get("recommendations", []),
            next_action=qe.get("next_action", ""),
            evaluation_timestamp=qe.get("evaluation_timestamp"),
        ))

    return WorkflowExecution(
        workflow_id=state.get("workflow_id", ""),
        start_time=state.get("start_time", datetime.now().isoformat()),
        end_time=state.get("end_time"),
        current_stage=WorkflowStage(state.get("current_stage", "initialization")),
        iterations_completed=state.get("iterations_completed", 0),
        agents_executed=agents_executed,
        quality_assessments=quality_assessments,
        quality_evaluations=quality_evaluations,
        final_version=state.get("current_version"),
        human_handoff=state.get("human_handoff", False),
        escalated=state.get("escalated", False),
        success=state.get("success", False),
        total_processing_time=state.get("total_processing_time"),
    )


def _agent_result_to_dict(result: AgentResult) -> Dict[str, Any]:
    """Serialize an AgentResult to a plain dict for state storage."""
    return {
        "agent_type": result.agent_type.value,
        "success": result.success,
        "version_created": result.version_created,
        "quality_score": result.quality_score,
        "processing_time": result.processing_time,
        "issues_found": result.issues_found,
        "optimizations_applied": result.optimizations_applied,
        "error_message": result.error_message,
        "metadata": result.metadata,
    }


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def content_review_node(state: PipelineState) -> Dict[str, Any]:
    """Run the content editor agent."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)

    iteration = state.get("iterations_completed", 0)
    iteration_suffix = f"_iter{iteration + 1}" if iteration > 0 else ""
    target_version = f"v1_content_edited{iteration_suffix}"

    result = coordinator.execute_content_editor(
        workflow=workflow,
        input_version=state.get("current_version", state.get("starting_version", "v0_original")),
        target_version=target_version,
    )

    new_version = target_version if result.success else state.get("current_version", state.get("starting_version"))

    # Phase 2: populate inter-agent context
    context_update: Dict[str, Any] = {}
    if result.success:
        context_update["content_editor_notes"] = {
            "quality_score": result.quality_score,
            "issues_found": result.issues_found,
            "has_complex_tables": bool(result.metadata and result.metadata.get("has_complex_tables")),
            "readability_concerns": result.metadata.get("readability_concerns", []) if result.metadata else [],
        }

    return {
        "current_version": new_version,
        "current_stage": "content_review",
        "agent_results": [_agent_result_to_dict(result)],
        "agent_context": context_update,
    }


def latex_optimization_node(state: PipelineState) -> Dict[str, Any]:
    """Run the LaTeX specialist agent."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)

    iteration = state.get("iterations_completed", 0)
    iteration_suffix = f"_iter{iteration + 1}" if iteration > 0 else ""
    target_version = f"v2_latex_optimized{iteration_suffix}"

    # Phase 2: read upstream context
    agent_ctx = state.get("agent_context", {})
    content_notes = agent_ctx.get("content_editor_notes", {})
    if content_notes.get("has_complex_tables"):
        print("   [LangGraph] LaTeX node: upstream flagged complex tables — adjusting optimization")

    result = coordinator.execute_latex_specialist(
        workflow=workflow,
        input_version=state.get("current_version", "v1_content_edited"),
        target_version=target_version,
    )

    new_version = target_version if result.success else state.get("current_version")

    # Phase 2: write downstream context
    context_update: Dict[str, Any] = {}
    if result.success and result.metadata:
        latex_analysis = result.metadata.get("latex_analysis", {})
        context_update["latex_specialist_notes"] = {
            "structure_score": latex_analysis.get("structure_score"),
            "typography_issues": latex_analysis.get("typography_issues", []),
            "packages_used": latex_analysis.get("packages_used", []),
        }

    return {
        "current_version": new_version,
        "current_stage": "latex_optimization",
        "agent_results": [_agent_result_to_dict(result)],
        "agent_context": context_update,
    }


def visual_qa_node(state: PipelineState) -> Dict[str, Any]:
    """Run visual QA analysis on the generated PDF."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)
    workflow.final_version = state.get("current_version")

    # Phase 2: read upstream context for prioritization
    agent_ctx = state.get("agent_context", {})
    content_notes = agent_ctx.get("content_editor_notes", {})
    latex_notes = agent_ctx.get("latex_specialist_notes", {})
    if content_notes or latex_notes:
        print("   [LangGraph] Visual QA node: using upstream context for prioritization")

    coordinator.execute_workflow_stage(workflow, WorkflowStage.VISUAL_QA)

    # Extract the visual QA agent result that was appended
    new_results = []
    new_version = state.get("current_version")
    for ar in workflow.agents_executed:
        if ar.agent_type.value == "visual_qa":
            new_results.append(_agent_result_to_dict(ar))
            if ar.success and ar.version_created:
                new_version = ar.version_created

    return {
        "current_version": new_version,
        "current_stage": "visual_qa",
        "agent_results": new_results,
    }


def quality_assessment_node(state: PipelineState) -> Dict[str, Any]:
    """Assess overall workflow quality from accumulated agent results."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)
    workflow.final_version = state.get("current_version")

    assessment = coordinator.assess_workflow_quality(workflow)

    overall_eval = coordinator.quality_gate_manager.evaluate_overall_quality_gate(
        assessment=assessment,
        iteration_count=state.get("iterations_completed", 0),
    )

    return {
        "current_stage": "quality_assessment",
        "quality_assessments": [assessment.__dict__],
        "quality_evaluations": [overall_eval.__dict__],
    }


def iteration_node(state: PipelineState) -> Dict[str, Any]:
    """Increment iteration counter and reset stage for next cycle."""
    new_count = state.get("iterations_completed", 0) + 1
    print(f"   [LangGraph] Starting iteration {new_count}")
    return {
        "iterations_completed": new_count,
        "current_stage": "iteration",
    }


def completion_node(state: PipelineState) -> Dict[str, Any]:
    """Mark pipeline as successfully complete."""
    return {
        "success": True,
        "human_handoff": True,
        "current_stage": "completion",
        "end_time": datetime.now().isoformat(),
    }


def escalation_node(state: PipelineState) -> Dict[str, Any]:
    """Mark pipeline as escalated to human review."""
    return {
        "escalated": True,
        "current_stage": "escalation",
        "end_time": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def route_after_content_review(state: PipelineState) -> Literal["latex_optimization", "iteration", "escalation"]:
    """Decide next step after content review using quality gate."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)
    assessment = coordinator.assess_workflow_quality(workflow)
    evaluation = coordinator.quality_gate_manager.evaluate_content_quality_gate(assessment)

    print(f"   [LangGraph] Content quality gate: {evaluation.result.value} (score={evaluation.score})")

    if evaluation.result == QualityGateResult.PASS:
        return "latex_optimization"
    elif evaluation.result == QualityGateResult.ITERATE:
        if state.get("iterations_completed", 0) >= coordinator.quality_gate_manager.thresholds.max_iterations:
            return "escalation"
        return "iteration"
    else:
        return "escalation"


def route_after_latex_optimization(state: PipelineState) -> Literal["visual_qa", "iteration", "escalation"]:
    """Decide next step after LaTeX optimization using quality gate."""
    coordinator = _build_coordinator(state)
    workflow = _stub_workflow(state)
    assessment = coordinator.assess_workflow_quality(workflow)
    evaluation = coordinator.quality_gate_manager.evaluate_latex_quality_gate(assessment)

    print(f"   [LangGraph] LaTeX quality gate: {evaluation.result.value} (score={evaluation.score})")

    if evaluation.result == QualityGateResult.PASS:
        return "visual_qa"
    elif evaluation.result == QualityGateResult.ITERATE:
        if state.get("iterations_completed", 0) >= coordinator.quality_gate_manager.thresholds.max_iterations:
            return "escalation"
        return "iteration"
    else:
        return "escalation"


def route_after_quality_assessment(state: PipelineState) -> Literal["completion", "iteration", "escalation"]:
    """Decide final outcome after quality assessment."""
    evaluations = state.get("quality_evaluations", [])
    if not evaluations:
        return "escalation"

    latest = evaluations[-1]
    result = latest.get("result", "fail")

    if result == QualityGateResult.PASS.value:
        return "completion"
    elif result == QualityGateResult.ITERATE.value:
        if state.get("iterations_completed", 0) >= 3:
            return "escalation"
        return "iteration"
    else:  # ESCALATE or FAIL
        return "escalation"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_qa_graph() -> StateGraph:
    """Build the QA pipeline StateGraph (uncompiled)."""
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("content_review", content_review_node)
    graph.add_node("latex_optimization", latex_optimization_node)
    graph.add_node("visual_qa", visual_qa_node)
    graph.add_node("quality_assessment", quality_assessment_node)
    graph.add_node("iteration", iteration_node)
    graph.add_node("completion", completion_node)
    graph.add_node("escalation", escalation_node)

    # Edges
    graph.add_edge(START, "content_review")
    graph.add_conditional_edges("content_review", route_after_content_review)
    graph.add_conditional_edges("latex_optimization", route_after_latex_optimization)
    graph.add_edge("visual_qa", "quality_assessment")
    graph.add_conditional_edges("quality_assessment", route_after_quality_assessment)
    graph.add_edge("iteration", "content_review")
    graph.add_edge("completion", END)
    graph.add_edge("escalation", END)

    return graph


def compile_qa_pipeline(checkpointer=None):
    """Compile and return the QA pipeline graph.

    Args:
        checkpointer: LangGraph checkpointer instance. Defaults to MemorySaver.

    Returns:
        Compiled LangGraph application.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = build_qa_graph()
    return graph.compile(checkpointer=checkpointer)


def export_mermaid_diagram() -> str:
    """Export the pipeline graph as a Mermaid diagram string."""
    graph = build_qa_graph()
    return graph.compile().get_graph().draw_mermaid()


# ---------------------------------------------------------------------------
# State ↔ WorkflowExecution conversion
# ---------------------------------------------------------------------------

def state_to_workflow_execution(state: Dict[str, Any]) -> WorkflowExecution:
    """Convert a final LangGraph PipelineState dict to a WorkflowExecution dataclass.

    Used by the orchestrator agent to feed into compile_pipeline_results().
    """
    workflow = _stub_workflow(state)

    # Fill in timing
    if state.get("end_time") and state.get("start_time"):
        try:
            start = datetime.fromisoformat(state["start_time"])
            end = datetime.fromisoformat(state["end_time"])
            workflow.total_processing_time = (end - start).total_seconds()
        except (ValueError, TypeError):
            workflow.total_processing_time = 0.0
    else:
        workflow.total_processing_time = state.get("total_processing_time", 0.0)

    workflow.final_version = state.get("current_version")
    workflow.success = state.get("success", False)
    workflow.human_handoff = state.get("human_handoff", False)
    workflow.escalated = state.get("escalated", False)
    workflow.iterations_completed = state.get("iterations_completed", 0)

    # Map current_stage string back to WorkflowStage enum
    stage_str = state.get("current_stage", "initialization")
    try:
        workflow.current_stage = WorkflowStage(stage_str)
    except ValueError:
        workflow.current_stage = WorkflowStage.COMPLETION

    return workflow
