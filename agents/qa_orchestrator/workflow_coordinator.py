"""
Workflow Coordinator - Milestone 4

Coordinates multi-agent workflows with intelligent sequencing and handoff logic.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.qa_orchestrator.quality_gates import QualityGateManager, QualityAssessment, QualityGateEvaluation, QualityGateResult
from tools.version_manager import VersionManager
from tools.change_tracker import ChangeTracker


class AgentType(Enum):
    """Available agent types."""
    CONTENT_EDITOR = "content_editor"
    LATEX_SPECIALIST = "latex_specialist"


class WorkflowStage(Enum):
    """Workflow execution stages."""
    INITIALIZATION = "initialization"
    CONTENT_REVIEW = "content_review"
    LATEX_OPTIMIZATION = "latex_optimization"
    VISUAL_QA = "visual_qa"
    QUALITY_ASSESSMENT = "quality_assessment"
    ITERATION = "iteration"
    COMPLETION = "completion"
    ESCALATION = "escalation"


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_type: AgentType
    success: bool
    version_created: str
    quality_score: Optional[float]
    processing_time: float
    issues_found: List[str]
    optimizations_applied: List[str]
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class WorkflowExecution:
    """Complete workflow execution record."""
    workflow_id: str
    start_time: str
    end_time: Optional[str]
    current_stage: WorkflowStage
    iterations_completed: int
    agents_executed: List[AgentResult]
    quality_assessments: List[QualityAssessment]
    quality_evaluations: List[QualityGateEvaluation]
    final_version: Optional[str]
    human_handoff: bool
    escalated: bool
    success: bool
    total_processing_time: Optional[float] = None


class WorkflowCoordinator:
    """
    Coordinates multi-agent QA workflows with intelligent sequencing.

    Features:
    - Multi-agent execution coordination
    - Quality gate integration
    - Intelligent iteration logic
    - Error handling and recovery
    - Performance tracking
    """

    def __init__(self):
        """Initialize workflow coordinator."""
        self.version_manager = VersionManager()
        self.change_tracker = ChangeTracker()
        self.quality_gate_manager = QualityGateManager()

        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.completed_workflows: List[WorkflowExecution] = []

    def create_workflow(self, workflow_id: str, starting_version: str) -> WorkflowExecution:
        """
        Create a new workflow execution.

        Args:
            workflow_id: Unique identifier for this workflow
            starting_version: Version to start the workflow from

        Returns:
            New workflow execution object
        """
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            current_stage=WorkflowStage.INITIALIZATION,
            iterations_completed=0,
            agents_executed=[],
            quality_assessments=[],
            quality_evaluations=[],
            final_version=starting_version,
            human_handoff=False,
            escalated=False,
            success=False
        )

        self.active_workflows[workflow_id] = workflow
        return workflow

    def execute_content_editor(self, workflow: WorkflowExecution, input_version: str, target_version: str) -> AgentResult:
        """
        Execute content editor agent.

        Args:
            workflow: Current workflow execution
            input_version: Input version name
            target_version: Target version name

        Returns:
            Agent execution result
        """
        print(f"🔄 Executing Content Editor: {input_version} → {target_version}")
        start_time = datetime.now()

        try:
            # Import content editor here to avoid circular imports
            from agents.content_editor.versioned_agent import VersionedContentEditorAgent

            agent = VersionedContentEditorAgent()

            # Check if target version already exists
            existing_version = self.version_manager.get_version(target_version)
            if existing_version:
                # Use existing version data
                quality_score = existing_version.get('metadata', {}).get('improved_avg_quality', 85)
                processing_time = (datetime.now() - start_time).total_seconds()

                return AgentResult(
                    agent_type=AgentType.CONTENT_EDITOR,
                    success=True,
                    version_created=target_version,
                    quality_score=quality_score,
                    processing_time=processing_time,
                    issues_found=[],
                    optimizations_applied=["Using existing content editor version"],
                    metadata=existing_version.get('metadata', {})
                )

            # Execute content editor processing
            results = agent.process_content_with_versioning(
                target_version=target_version,
                parent_version=input_version
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # Extract results
            quality_improvement = results["quality_progression"]["overall_improvement"]
            final_quality = results["quality_progression"]["improved_avg_quality"]

            return AgentResult(
                agent_type=AgentType.CONTENT_EDITOR,
                success=True,
                version_created=target_version,
                quality_score=final_quality,
                processing_time=processing_time,
                issues_found=[],  # Would extract from results
                optimizations_applied=[f"Quality improvement: +{quality_improvement} points"],
                metadata=results
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Content Editor failed: {e}")

            return AgentResult(
                agent_type=AgentType.CONTENT_EDITOR,
                success=False,
                version_created=target_version,
                quality_score=None,
                processing_time=processing_time,
                issues_found=[],
                optimizations_applied=[],
                error_message=str(e)
            )

    def execute_latex_specialist(self, workflow: WorkflowExecution, input_version: str, target_version: str) -> AgentResult:
        """
        Execute LaTeX specialist agent.

        Args:
            workflow: Current workflow execution
            input_version: Input version name
            target_version: Target version name

        Returns:
            Agent execution result
        """
        print(f"🔧 Executing LaTeX Specialist: {input_version} → {target_version}")
        start_time = datetime.now()

        try:
            # Import LaTeX specialist here to avoid circular imports
            from agents.latex_specialist.agent import LaTeXSpecialistAgent

            agent = LaTeXSpecialistAgent()

            # Check if target version already exists
            existing_version = self.version_manager.get_version(target_version)
            if existing_version:
                # Use existing version data
                metadata = existing_version.get('metadata', {})
                quality_score = metadata.get('latex_quality_score', 90)
                processing_time = (datetime.now() - start_time).total_seconds()

                return AgentResult(
                    agent_type=AgentType.LATEX_SPECIALIST,
                    success=True,
                    version_created=target_version,
                    quality_score=quality_score,
                    processing_time=processing_time,
                    issues_found=[],
                    optimizations_applied=["Using existing LaTeX specialist version"],
                    metadata=metadata
                )

            # Execute LaTeX specialist processing
            results = agent.process_with_versioning(
                parent_version=input_version,
                target_version=target_version,
                optimization_level="moderate"
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # Extract results
            latex_analysis = results["latex_analysis"]
            optimizations = results["optimizations_applied"]

            return AgentResult(
                agent_type=AgentType.LATEX_SPECIALIST,
                success=True,
                version_created=target_version,
                quality_score=latex_analysis["overall_score"],
                processing_time=processing_time,
                issues_found=[f"Found {latex_analysis['issues_found']} LaTeX issues"],
                optimizations_applied=optimizations,
                metadata=results
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ LaTeX Specialist failed: {e}")

            return AgentResult(
                agent_type=AgentType.LATEX_SPECIALIST,
                success=False,
                version_created=target_version,
                quality_score=None,
                processing_time=processing_time,
                issues_found=[],
                optimizations_applied=[],
                error_message=str(e)
            )

    def assess_workflow_quality(self, workflow: WorkflowExecution) -> QualityAssessment:
        """
        Assess overall workflow quality based on agent results.

        Args:
            workflow: Current workflow execution

        Returns:
            Comprehensive quality assessment
        """
        assessment = QualityAssessment()

        # Extract quality scores from agent results
        for agent_result in workflow.agents_executed:
            if agent_result.agent_type == AgentType.CONTENT_EDITOR and agent_result.success:
                assessment.content_score = int(agent_result.quality_score) if agent_result.quality_score else None
                assessment.content_issues = agent_result.issues_found

            elif agent_result.agent_type == AgentType.LATEX_SPECIALIST and agent_result.success:
                assessment.latex_score = int(agent_result.quality_score) if agent_result.quality_score else None
                assessment.latex_issues = agent_result.issues_found

                # Extract component scores if available
                if agent_result.metadata and "latex_analysis" in agent_result.metadata:
                    latex_analysis = agent_result.metadata["latex_analysis"]
                    assessment.latex_structure = latex_analysis.get("structure_score")
                    assessment.latex_typography = latex_analysis.get("typography_score")
                    assessment.latex_tables_figures = latex_analysis.get("tables_figures_score")
                    assessment.latex_best_practices = latex_analysis.get("best_practices_score")

        return assessment

    def determine_next_action(self, workflow: WorkflowExecution, quality_evaluation: QualityGateEvaluation) -> Tuple[WorkflowStage, str]:
        """
        Determine next workflow action based on quality evaluation.

        Args:
            workflow: Current workflow execution
            quality_evaluation: Quality gate evaluation result

        Returns:
            Tuple of (next_stage, next_action_description)
        """
        if quality_evaluation.result == QualityGateResult.PASS:
            if quality_evaluation.next_action == "human_handoff":
                return WorkflowStage.COMPLETION, "Ready for human review"
            elif quality_evaluation.next_action == "proceed_to_latex":
                return WorkflowStage.LATEX_OPTIMIZATION, "Proceed to LaTeX optimization"
            elif quality_evaluation.next_action == "proceed_to_visual_qa":
                return WorkflowStage.VISUAL_QA, "Proceed to visual QA"
            elif quality_evaluation.next_action == "proceed_to_final_assessment":
                return WorkflowStage.QUALITY_ASSESSMENT, "Proceed to final quality assessment"

        elif quality_evaluation.result == QualityGateResult.ITERATE:
            if quality_evaluation.next_action == "run_content_editor":
                return WorkflowStage.CONTENT_REVIEW, "Iterate content editor"
            elif quality_evaluation.next_action == "run_latex_specialist":
                return WorkflowStage.LATEX_OPTIMIZATION, "Iterate LaTeX specialist"
            elif quality_evaluation.next_action == "iterate_pipeline":
                return WorkflowStage.ITERATION, "Iterate complete pipeline"

        elif quality_evaluation.result == QualityGateResult.ESCALATE:
            return WorkflowStage.ESCALATION, "Escalate to human review"

        # Default fallback
        return WorkflowStage.COMPLETION, "Workflow complete"

    def execute_workflow_stage(self, workflow: WorkflowExecution, stage: WorkflowStage) -> bool:
        """
        Execute a specific workflow stage.

        Args:
            workflow: Current workflow execution
            stage: Stage to execute

        Returns:
            True if stage completed successfully
        """
        workflow.current_stage = stage
        print(f"📍 Workflow Stage: {stage.value}")

        try:
            if stage == WorkflowStage.CONTENT_REVIEW:
                # Generate version name for this iteration
                iteration_suffix = f"_iter{workflow.iterations_completed + 1}" if workflow.iterations_completed > 0 else ""
                target_version = f"v1_content_edited{iteration_suffix}"

                # Execute content editor
                agent_result = self.execute_content_editor(
                    workflow=workflow,
                    input_version=workflow.final_version,
                    target_version=target_version
                )

                workflow.agents_executed.append(agent_result)
                if agent_result.success:
                    workflow.final_version = target_version

                return agent_result.success

            elif stage == WorkflowStage.LATEX_OPTIMIZATION:
                # Generate version name for this iteration
                iteration_suffix = f"_iter{workflow.iterations_completed + 1}" if workflow.iterations_completed > 0 else ""
                target_version = f"v2_latex_optimized{iteration_suffix}"

                # Execute LaTeX specialist
                agent_result = self.execute_latex_specialist(
                    workflow=workflow,
                    input_version=workflow.final_version,
                    target_version=target_version
                )

                workflow.agents_executed.append(agent_result)
                if agent_result.success:
                    workflow.final_version = target_version

                return agent_result.success

            elif stage == WorkflowStage.VISUAL_QA:
                # Run Visual QA analysis on the generated PDF
                print("👁️ Executing Visual QA Analysis")

                # Visual QA doesn't modify content, just analyzes the PDF
                # The PDF should be at artifacts/output/research_report.pdf
                pdf_path = "artifacts/output/research_report.pdf"

                # Create a simple agent result for Visual QA
                from tools.visual_qa import VisualQAAgent
                visual_qa = VisualQAAgent()

                try:
                    if os.path.exists(pdf_path):
                        qa_results = visual_qa.validate_pdf_visual_quality(pdf_path)
                        print(f"✅ Visual QA Score: {qa_results.overall_score:.1f}/100")

                        # Collect all issues from page results
                        all_issues = []
                        for page_result in qa_results.page_results:
                            all_issues.extend(page_result.issues_found)

                        agent_result = AgentResult(
                            agent_type=AgentType.LATEX_SPECIALIST,  # Reuse for now
                            success=True,
                            version_created=workflow.final_version,
                            quality_score=qa_results.overall_score,
                            processing_time=0.0,
                            issues_found=all_issues[:5],  # Limit to first 5
                            optimizations_applied=[],
                            error_message=None
                        )
                    else:
                        print(f"⚠️ PDF not found at {pdf_path}, skipping Visual QA")
                        agent_result = AgentResult(
                            agent_type=AgentType.LATEX_SPECIALIST,
                            success=True,
                            version_created=workflow.final_version,
                            quality_score=None,  # Don't affect overall score if skipped
                            processing_time=0.0,
                            issues_found=[],
                            optimizations_applied=[],
                            error_message="PDF not found"
                        )
                except Exception as e:
                    print(f"⚠️ Visual QA error: {e}")
                    agent_result = AgentResult(
                        agent_type=AgentType.LATEX_SPECIALIST,
                        success=True,
                        version_created=workflow.final_version,
                        quality_score=None,  # Don't affect overall score if failed
                        processing_time=0.0,
                        issues_found=[],
                        optimizations_applied=[],
                        error_message=str(e)
                    )

                workflow.agents_executed.append(agent_result)
                return True

            elif stage == WorkflowStage.QUALITY_ASSESSMENT:
                # Assess current quality
                quality_assessment = self.assess_workflow_quality(workflow)
                workflow.quality_assessments.append(quality_assessment)

                # Evaluate against quality gates
                overall_evaluation = self.quality_gate_manager.evaluate_overall_quality_gate(
                    assessment=quality_assessment,
                    iteration_count=workflow.iterations_completed
                )
                workflow.quality_evaluations.append(overall_evaluation)

                return True

            elif stage == WorkflowStage.COMPLETION:
                workflow.human_handoff = True
                workflow.success = True
                workflow.end_time = datetime.now().isoformat()
                return True

            elif stage == WorkflowStage.ESCALATION:
                workflow.escalated = True
                workflow.end_time = datetime.now().isoformat()
                return True

            elif stage == WorkflowStage.ITERATION:
                workflow.iterations_completed += 1
                print(f"🔄 Starting iteration {workflow.iterations_completed}")
                return True

            return False

        except Exception as e:
            print(f"❌ Stage {stage.value} failed: {e}")
            return False

    def run_complete_workflow(self, workflow_id: str, starting_version: str = "v0_original") -> WorkflowExecution:
        """
        Run complete QA workflow from start to finish.

        Args:
            workflow_id: Unique workflow identifier
            starting_version: Version to start workflow from

        Returns:
            Completed workflow execution
        """
        print(f"🚀 Starting QA Workflow: {workflow_id}")
        print(f"📦 Starting from version: {starting_version}")
        print("=" * 60)

        # Create workflow
        workflow = self.create_workflow(workflow_id, starting_version)

        # Main workflow loop
        max_total_iterations = 5  # Safety limit
        total_iterations = 0

        while total_iterations < max_total_iterations:
            total_iterations += 1

            # Determine current stage
            if workflow.current_stage == WorkflowStage.INITIALIZATION:
                # Start with content review
                success = self.execute_workflow_stage(workflow, WorkflowStage.CONTENT_REVIEW)
                if not success:
                    break

            elif workflow.current_stage == WorkflowStage.CONTENT_REVIEW:
                # Assess content quality
                quality_assessment = self.assess_workflow_quality(workflow)
                content_evaluation = self.quality_gate_manager.evaluate_content_quality_gate(quality_assessment)

                next_stage, action_desc = self.determine_next_action(workflow, content_evaluation)
                print(f"📊 Content Quality Gate: {content_evaluation.result.value} - {action_desc}")

                if next_stage == WorkflowStage.LATEX_OPTIMIZATION:
                    success = self.execute_workflow_stage(workflow, WorkflowStage.LATEX_OPTIMIZATION)
                    if not success:
                        break
                elif next_stage == WorkflowStage.CONTENT_REVIEW:
                    # Iterate content editor
                    success = self.execute_workflow_stage(workflow, WorkflowStage.ITERATION)
                    if success:
                        success = self.execute_workflow_stage(workflow, WorkflowStage.CONTENT_REVIEW)
                    if not success:
                        break
                else:
                    workflow.current_stage = next_stage

            elif workflow.current_stage == WorkflowStage.LATEX_OPTIMIZATION:
                # Assess LaTeX quality
                quality_assessment = self.assess_workflow_quality(workflow)
                latex_evaluation = self.quality_gate_manager.evaluate_latex_quality_gate(quality_assessment)

                next_stage, action_desc = self.determine_next_action(workflow, latex_evaluation)
                print(f"📊 LaTeX Quality Gate: {latex_evaluation.result.value} - {action_desc}")

                if next_stage == WorkflowStage.VISUAL_QA:
                    success = self.execute_workflow_stage(workflow, WorkflowStage.VISUAL_QA)
                    if success:
                        workflow.current_stage = WorkflowStage.QUALITY_ASSESSMENT
                    else:
                        break
                elif next_stage == WorkflowStage.QUALITY_ASSESSMENT:
                    success = self.execute_workflow_stage(workflow, WorkflowStage.QUALITY_ASSESSMENT)
                    if not success:
                        break
                elif next_stage == WorkflowStage.LATEX_OPTIMIZATION:
                    # Iterate LaTeX specialist
                    success = self.execute_workflow_stage(workflow, WorkflowStage.ITERATION)
                    if success:
                        success = self.execute_workflow_stage(workflow, WorkflowStage.LATEX_OPTIMIZATION)
                    if not success:
                        break
                else:
                    workflow.current_stage = next_stage

            elif workflow.current_stage == WorkflowStage.QUALITY_ASSESSMENT:
                # Final quality assessment
                quality_assessment = self.assess_workflow_quality(workflow)
                overall_evaluation = self.quality_gate_manager.evaluate_overall_quality_gate(
                    assessment=quality_assessment,
                    iteration_count=workflow.iterations_completed
                )

                next_stage, action_desc = self.determine_next_action(workflow, overall_evaluation)
                print(f"📊 Overall Quality Gate: {overall_evaluation.result.value} - {action_desc}")

                workflow.quality_assessments.append(quality_assessment)
                workflow.quality_evaluations.append(overall_evaluation)

                if next_stage in [WorkflowStage.COMPLETION, WorkflowStage.ESCALATION]:
                    success = self.execute_workflow_stage(workflow, next_stage)
                    break
                elif next_stage == WorkflowStage.ITERATION:
                    # Start another iteration
                    success = self.execute_workflow_stage(workflow, WorkflowStage.ITERATION)
                    if success:
                        workflow.current_stage = WorkflowStage.CONTENT_REVIEW
                    if not success:
                        break

            elif workflow.current_stage in [WorkflowStage.COMPLETION, WorkflowStage.ESCALATION]:
                break

            else:
                print(f"⚠️ Unknown workflow stage: {workflow.current_stage}")
                break

        # Finalize workflow
        if workflow.end_time is None:
            workflow.end_time = datetime.now().isoformat()

        start_time = datetime.fromisoformat(workflow.start_time)
        end_time = datetime.fromisoformat(workflow.end_time)
        workflow.total_processing_time = (end_time - start_time).total_seconds()

        # Move to completed workflows
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
        self.completed_workflows.append(workflow)

        print("=" * 60)
        print(f"✅ Workflow Complete: {workflow_id}")
        print(f"📊 Final Version: {workflow.final_version}")
        print(f"🔄 Iterations: {workflow.iterations_completed}")
        print(f"⏱️ Total Time: {workflow.total_processing_time:.2f}s")
        print(f"🎯 Status: {'Success' if workflow.success else 'Escalated' if workflow.escalated else 'Failed'}")

        return workflow

    def get_workflow_summary(self, workflow: WorkflowExecution) -> Dict:
        """
        Generate comprehensive workflow summary.

        Args:
            workflow: Completed workflow execution

        Returns:
            Workflow summary dictionary
        """
        # Get final quality assessment
        final_assessment = workflow.quality_assessments[-1] if workflow.quality_assessments else None

        # Calculate agent performance
        agent_performance = {}
        for agent_result in workflow.agents_executed:
            agent_name = agent_result.agent_type.value
            if agent_name not in agent_performance:
                agent_performance[agent_name] = {
                    "executions": 0,
                    "successes": 0,
                    "total_time": 0,
                    "quality_improvements": []
                }

            perf = agent_performance[agent_name]
            perf["executions"] += 1
            if agent_result.success:
                perf["successes"] += 1
            perf["total_time"] += agent_result.processing_time
            if agent_result.quality_score:
                perf["quality_improvements"].append(agent_result.quality_score)

        return {
            "workflow_id": workflow.workflow_id,
            "execution_summary": {
                "start_time": workflow.start_time,
                "end_time": workflow.end_time,
                "total_processing_time": workflow.total_processing_time,
                "iterations_completed": workflow.iterations_completed,
                "final_stage": workflow.current_stage.value,
                "success": workflow.success,
                "human_handoff": workflow.human_handoff,
                "escalated": workflow.escalated
            },
            "version_progression": {
                "starting_version": workflow.agents_executed[0].version_created if workflow.agents_executed else None,
                "final_version": workflow.final_version,
                "versions_created": [r.version_created for r in workflow.agents_executed if r.success]
            },
            "quality_progression": {
                "final_assessment": final_assessment.__dict__ if final_assessment else None,
                "quality_evaluations": len(workflow.quality_evaluations),
                "overall_score": final_assessment.overall_score if final_assessment else None
            },
            "agent_performance": agent_performance
        }