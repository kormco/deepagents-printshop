"""
LangGraph QA Pipeline Workflow

Declarative StateGraph that orchestrates the QA pipeline. Node functions invoke
downstream agents directly -- no WorkflowExecution object, no glue code.
PipelineState is the single source of truth.
"""

import operator
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv

load_dotenv()

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
from agents.qa_orchestrator.pipeline_types import AgentResult, AgentType  # noqa: E402, I001
from agents.qa_orchestrator.workflow_coordinator import WorkflowCoordinator  # noqa: E402, I001


# ---------------------------------------------------------------------------
# LLM-based LaTeX error fixer (second-tier, after PDFCompiler regex fixes)
# ---------------------------------------------------------------------------

def _llm_fix_latex(tex_content: str, error_log: str, attempt: int) -> Optional[str]:
    """Ask Claude to fix LaTeX compilation errors.

    Returns corrected .tex content, or None on failure.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": (
                    f"The following LaTeX document failed to compile (attempt {attempt}). "
                    "Fix the errors and return ONLY the corrected .tex content with no explanation.\n"
                    "IMPORTANT: Preserve ALL \\includegraphics commands, \\begin{figure} environments, "
                    "and disclaimer sections exactly as they appear. Do not remove any images or figures.\n\n"
                    f"=== ERRORS ===\n{error_log[:3000]}\n\n"
                    f"=== DOCUMENT ===\n{tex_content}"
                ),
            }],
        )
        fixed = response.content[0].text.strip()
        if fixed and "\\begin{document}" in fixed:
            return fixed
        return None
    except Exception as e:
        print(f"   [LangGraph] LLM LaTeX fix attempt {attempt} failed: {e}")
        return None


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

    # --- output directory (set by orchestrator) ---
    output_dir: str

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

    # --- inter-agent communication ---
    agent_context: Annotated[Dict[str, Any], merge_dicts]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def content_review_node(state: PipelineState) -> Dict[str, Any]:
    """Run the content editor agent directly."""
    content_source = state.get("content_source", "research_report")
    iteration = state.get("iterations_completed", 0)
    iteration_suffix = f"_iter{iteration + 1}" if iteration > 0 else ""
    target_version = f"v1_content_edited{iteration_suffix}"
    input_version = state.get("current_version", state.get("starting_version", "v0_original"))

    start_time = datetime.now()

    try:
        from agents.content_editor.versioned_agent import VersionedContentEditorAgent
        from tools.version_manager import VersionManager

        version_manager = VersionManager()
        existing_version = version_manager.get_version(target_version)

        if existing_version:
            quality_score = existing_version.get("metadata", {}).get("improved_avg_quality", 85)
            processing_time = (datetime.now() - start_time).total_seconds()
            result = AgentResult(
                agent_type=AgentType.CONTENT_EDITOR,
                success=True,
                version_created=target_version,
                quality_score=quality_score,
                processing_time=processing_time,
                issues_found=[],
                optimizations_applied=["Using existing content editor version"],
                metadata=existing_version.get("metadata", {}),
            )
        else:
            agent = VersionedContentEditorAgent(content_source=content_source)
            results = agent.process_content_with_versioning(
                target_version=target_version,
                parent_version=input_version,
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            quality_improvement = results["quality_progression"]["overall_improvement"]
            final_quality = results["quality_progression"]["improved_avg_quality"]

            result = AgentResult(
                agent_type=AgentType.CONTENT_EDITOR,
                success=True,
                version_created=target_version,
                quality_score=final_quality,
                processing_time=processing_time,
                issues_found=[],
                optimizations_applied=[f"Quality improvement: +{quality_improvement} points"],
                metadata=results,
            )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"Content Editor failed: {e}")
        result = AgentResult(
            agent_type=AgentType.CONTENT_EDITOR,
            success=False,
            version_created=target_version,
            quality_score=None,
            processing_time=processing_time,
            issues_found=[],
            optimizations_applied=[],
            error_message=str(e),
        )

    new_version = target_version if result.success else state.get("current_version", state.get("starting_version"))

    # Populate inter-agent context with actionable notes
    context_update: Dict[str, Any] = {}
    if result.success:
        has_complex_tables = bool(result.metadata and result.metadata.get("has_complex_tables"))
        readability_concerns = result.metadata.get("readability_concerns", []) if result.metadata else []
        context_update["content_editor_notes"] = {
            "quality_score": result.quality_score,
            "issues_found": result.issues_found,
            "has_complex_tables": has_complex_tables,
            "readability_concerns": readability_concerns,
        }

    return {
        "current_version": new_version,
        "current_stage": "content_review",
        "agent_results": [result.to_dict()],
        "agent_context": context_update,
    }


def latex_optimization_node(state: PipelineState) -> Dict[str, Any]:
    """Run the LaTeX specialist agent directly."""
    content_source = state.get("content_source", "research_report")
    iteration = state.get("iterations_completed", 0)
    iteration_suffix = f"_iter{iteration + 1}" if iteration > 0 else ""
    target_version = f"v2_latex_optimized{iteration_suffix}"
    input_version = state.get("current_version", "v1_content_edited")

    # Read upstream context to adjust optimization
    agent_ctx = state.get("agent_context", {})
    content_notes = agent_ctx.get("content_editor_notes", {})

    optimization_level = "moderate"
    if content_notes.get("has_complex_tables"):
        optimization_level = "conservative"
        print("   [LangGraph] LaTeX node: upstream flagged complex tables — using conservative optimization")

    start_time = datetime.now()

    try:
        from agents.latex_specialist.agent import LaTeXSpecialistAgent
        from tools.version_manager import VersionManager

        version_manager = VersionManager()
        existing_version = version_manager.get_version(target_version)

        if existing_version:
            metadata = existing_version.get("metadata", {})
            quality_score = metadata.get("latex_quality_score", 90)
            processing_time = (datetime.now() - start_time).total_seconds()
            result = AgentResult(
                agent_type=AgentType.LATEX_SPECIALIST,
                success=True,
                version_created=target_version,
                quality_score=quality_score,
                processing_time=processing_time,
                issues_found=[],
                optimizations_applied=["Using existing LaTeX specialist version"],
                metadata=metadata,
            )
        else:
            agent = LaTeXSpecialistAgent(content_source=content_source)
            results = agent.process_with_versioning(
                parent_version=input_version,
                target_version=target_version,
                optimization_level=optimization_level,
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            latex_analysis = results["latex_analysis"]
            optimizations = results["optimizations_applied"]

            result = AgentResult(
                agent_type=AgentType.LATEX_SPECIALIST,
                success=True,
                version_created=target_version,
                quality_score=latex_analysis["overall_score"],
                processing_time=processing_time,
                issues_found=[f"Found {latex_analysis['issues_found']} LaTeX issues"],
                optimizations_applied=optimizations,
                metadata=results,
            )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"LaTeX Specialist failed: {e}")
        result = AgentResult(
            agent_type=AgentType.LATEX_SPECIALIST,
            success=False,
            version_created=target_version,
            quality_score=None,
            processing_time=processing_time,
            issues_found=[],
            optimizations_applied=[],
            error_message=str(e),
        )

    new_version = target_version if result.success else state.get("current_version")

    # Compile .tex to PDF so Visual QA can analyze it
    compilation_success = False
    compilation_error: Optional[str] = None

    if result.success:
        try:
            from tools.version_manager import VersionManager as _VM
            from tools.pdf_compiler import PDFCompiler

            vm = _VM()
            version_content = vm.get_version_content(target_version)
            output_dir = Path(state.get("output_dir", "artifacts/output"))
            output_dir.mkdir(parents=True, exist_ok=True)

            tex_filename = f"{content_source}.tex"
            # Find the .tex file in the version (may be named research_report.tex)
            tex_content = None
            for fname, content in version_content.items():
                if fname.endswith(".tex"):
                    tex_content = content
                    break

            if tex_content:
                tex_path = output_dir / tex_filename
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(tex_content)

                compiler = PDFCompiler(output_dir=str(output_dir))
                success, msg = compiler.compile(str(tex_path))

                if success:
                    compilation_success = True
                    print(f"   [LangGraph] PDF compiled: {output_dir / content_source}.pdf")
                else:
                    # PDFCompiler regex fixes failed — try LLM-based fixes
                    print(f"   [LangGraph] PDF compilation failed, attempting LLM fix: {msg}")
                    compilation_error = msg
                    for llm_attempt in range(1, 3):  # up to 2 LLM fix attempts
                        fixed_tex = _llm_fix_latex(tex_content, msg, llm_attempt)
                        if fixed_tex:
                            tex_content = fixed_tex
                            with open(tex_path, "w", encoding="utf-8") as f:
                                f.write(tex_content)
                            success, msg = compiler.compile(str(tex_path))
                            if success:
                                compilation_success = True
                                compilation_error = None
                                print(f"   [LangGraph] PDF compiled after LLM fix attempt {llm_attempt}")
                                break
                            else:
                                compilation_error = msg
                                print(f"   [LangGraph] LLM fix attempt {llm_attempt} did not resolve compilation: {msg}")
                        else:
                            print(f"   [LangGraph] LLM fix attempt {llm_attempt} returned no result")
                            break
            else:
                compilation_error = "No .tex file found in version content"
                print(f"   [LangGraph] {compilation_error}")
        except Exception as e:
            compilation_error = str(e)
            print(f"   [LangGraph] PDF compilation error: {e}")

    # If compilation failed, record it as an issue so the quality gate can react
    if result.success and not compilation_success and compilation_error:
        truncated = compilation_error[:300]
        result.issues_found.append(f"PDF_COMPILATION_FAILED: {truncated}")

    # Write downstream context for Visual QA
    context_update: Dict[str, Any] = {}
    if result.success and result.metadata:
        latex_analysis = result.metadata.get("latex_analysis", {})
        context_update["latex_specialist_notes"] = {
            "structure_score": latex_analysis.get("structure_score"),
            "typography_score": latex_analysis.get("typography_score"),
            "typography_issues": latex_analysis.get("typography_issues", []),
            "packages_used": latex_analysis.get("packages_used", []),
            "compilation_success": compilation_success,
        }
        if compilation_error:
            context_update["compilation_errors"] = {
                "message": compilation_error[:500],
                "iteration": iteration,
            }

    return {
        "current_version": new_version,
        "current_stage": "latex_optimization",
        "agent_results": [result.to_dict()],
        "agent_context": context_update,
    }


def visual_qa_node(state: PipelineState) -> Dict[str, Any]:
    """Run visual QA analysis on the generated PDF."""
    content_source = state.get("content_source", "research_report")
    current_version = state.get("current_version")
    output_dir = state.get("output_dir", "artifacts/output")
    pdf_path = f"{output_dir}/{content_source}.pdf"

    # Read upstream context to decide iteration budget
    agent_ctx = state.get("agent_context", {})
    latex_notes = agent_ctx.get("latex_specialist_notes", {})

    max_iterations = 2
    typography_score = latex_notes.get("typography_score")
    if typography_score is not None and typography_score < 20:
        max_iterations = 3
        print("   [LangGraph] Visual QA node: weak typography score — allowing extra iteration")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "visual_qa"))
        from agent import VisualQAFeedbackAgent

        visual_qa_feedback = VisualQAFeedbackAgent(content_source=content_source)

        if os.path.exists(pdf_path):
            final_pdf, improvements, final_version = visual_qa_feedback.analyze_and_improve(
                pdf_path, max_iterations=max_iterations
            )

            # Copy the final improved PDF and .tex back to the canonical output dir
            if final_pdf and final_pdf != pdf_path and os.path.exists(final_pdf):
                import shutil
                shutil.copy(final_pdf, pdf_path)
                print(f"   [LangGraph] Copied final Visual QA PDF to {pdf_path}")

                # Also copy the improved .tex if it exists
                improved_tex = os.path.join(output_dir, f"{content_source}_improved.tex")
                canonical_tex = os.path.join(output_dir, f"{content_source}.tex")
                if os.path.exists(improved_tex):
                    shutil.copy(improved_tex, canonical_tex)
                    print(f"   [LangGraph] Copied improved .tex to {canonical_tex}")

            from tools.visual_qa import VisualQAAgent
            visual_qa = VisualQAAgent(content_source=content_source)
            qa_results = visual_qa.validate_pdf_visual_quality(final_pdf)

            print(f"Visual QA Score: {qa_results.overall_score:.1f}/100")
            if improvements:
                print(f"Applied {len(improvements)} improvements")

            all_issues = []
            for page_result in qa_results.page_results:
                all_issues.extend(page_result.issues_found)

            new_version = final_version if final_version else current_version

            result = AgentResult(
                agent_type=AgentType.VISUAL_QA,
                success=True,
                version_created=new_version,
                quality_score=qa_results.overall_score,
                processing_time=0.0,
                issues_found=all_issues[:5],
                optimizations_applied=improvements,
            )
        else:
            print(f"PDF not found at {pdf_path}, skipping Visual QA")
            new_version = current_version
            result = AgentResult(
                agent_type=AgentType.VISUAL_QA,
                success=True,
                version_created=current_version,
                quality_score=None,
                processing_time=0.0,
                issues_found=[],
                optimizations_applied=[],
                error_message="PDF not found",
            )
    except Exception as e:
        print(f"Visual QA error: {e}")
        new_version = current_version
        result = AgentResult(
            agent_type=AgentType.VISUAL_QA,
            success=True,
            version_created=current_version,
            quality_score=None,
            processing_time=0.0,
            issues_found=[],
            optimizations_applied=[],
            error_message=str(e),
        )

    return {
        "current_version": new_version,
        "current_stage": "visual_qa",
        "agent_results": [result.to_dict()],
    }


def quality_assessment_node(state: PipelineState) -> Dict[str, Any]:
    """Assess overall workflow quality from accumulated agent results."""
    coordinator = WorkflowCoordinator(
        content_source=state.get("content_source", "research_report")
    )
    assessment = coordinator.assess_workflow_quality(state.get("agent_results", []))

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
    coordinator = WorkflowCoordinator(
        content_source=state.get("content_source", "research_report")
    )
    assessment = coordinator.assess_workflow_quality(state.get("agent_results", []))
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
    coordinator = WorkflowCoordinator(
        content_source=state.get("content_source", "research_report")
    )
    assessment = coordinator.assess_workflow_quality(state.get("agent_results", []))
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
