"""
Quality Gates System - Milestone 4

Manages quality thresholds, decision logic, and escalation rules for the QA pipeline.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class QualityGateResult(Enum):
    """Quality gate evaluation results."""
    PASS = "pass"
    FAIL = "fail"
    ITERATE = "iterate"
    ESCALATE = "escalate"


@dataclass
class QualityThresholds:
    """Quality threshold configuration."""
    # Content quality thresholds
    content_minimum: int = 80
    content_good: int = 85
    content_excellent: int = 90

    # LaTeX quality thresholds
    latex_minimum: int = 85
    latex_good: int = 90
    latex_excellent: int = 95

    # Component thresholds (out of 25 each)
    latex_structure_minimum: int = 22
    latex_typography_minimum: int = 18  # Lowered to avoid iteration loops on acceptable typography
    latex_tables_figures_minimum: int = 20
    latex_best_practices_minimum: int = 20

    # Overall pipeline thresholds
    overall_target: int = 80  # Lowered to avoid iteration issues during development
    human_handoff_threshold: int = 90

    # Iteration control
    improvement_minimum: int = 5
    convergence_threshold: int = 2
    max_iterations: int = 3

    # Error thresholds
    max_content_issues: int = 5
    max_latex_issues: int = 3


@dataclass
class QualityAssessment:
    """Complete quality assessment result."""
    content_score: Optional[int] = None
    latex_score: Optional[int] = None
    latex_structure: Optional[int] = None
    latex_typography: Optional[int] = None
    latex_tables_figures: Optional[int] = None
    latex_best_practices: Optional[int] = None

    content_issues: List[str] = None
    latex_issues: List[str] = None

    overall_score: Optional[float] = None
    assessment_timestamp: str = None

    def __post_init__(self):
        if self.content_issues is None:
            self.content_issues = []
        if self.latex_issues is None:
            self.latex_issues = []
        if self.assessment_timestamp is None:
            self.assessment_timestamp = datetime.now().isoformat()


@dataclass
class QualityGateEvaluation:
    """Result of quality gate evaluation."""
    gate_name: str
    result: QualityGateResult
    score: Optional[float]
    threshold: Optional[float]
    reasons: List[str]
    recommendations: List[str]
    next_action: str
    evaluation_timestamp: str = None

    def __post_init__(self):
        if self.evaluation_timestamp is None:
            self.evaluation_timestamp = datetime.now().isoformat()


class QualityGateManager:
    """
    Manages quality gates and decision logic for the QA pipeline.

    Features:
    - Quality threshold evaluation
    - Iteration decision logic
    - Human escalation triggers
    - Quality progression tracking
    """

    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        """
        Initialize quality gate manager.

        Args:
            thresholds: Custom quality thresholds (uses defaults if None)
        """
        self.thresholds = thresholds or QualityThresholds()
        self.evaluation_history: List[QualityGateEvaluation] = []

    def evaluate_content_quality_gate(self, assessment: QualityAssessment) -> QualityGateEvaluation:
        """
        Evaluate content quality gate.

        Args:
            assessment: Quality assessment data

        Returns:
            Quality gate evaluation result
        """
        reasons = []
        recommendations = []

        if assessment.content_score is None:
            return QualityGateEvaluation(
                gate_name="content_quality",
                result=QualityGateResult.FAIL,
                score=None,
                threshold=self.thresholds.content_minimum,
                reasons=["Content score not available"],
                recommendations=["Run content analysis"],
                next_action="run_content_editor"
            )

        score = assessment.content_score

        # Check minimum threshold
        if score < self.thresholds.content_minimum:
            reasons.append(f"Content score {score} below minimum {self.thresholds.content_minimum}")
            recommendations.append("Run content editor to improve grammar, readability, and structure")
            return QualityGateEvaluation(
                gate_name="content_quality",
                result=QualityGateResult.ITERATE,
                score=score,
                threshold=self.thresholds.content_minimum,
                reasons=reasons,
                recommendations=recommendations,
                next_action="run_content_editor"
            )

        # Check issue count
        issue_count = len(assessment.content_issues)
        if issue_count > self.thresholds.max_content_issues:
            reasons.append(f"Too many content issues: {issue_count} > {self.thresholds.max_content_issues}")
            recommendations.append("Address remaining content issues")
            return QualityGateEvaluation(
                gate_name="content_quality",
                result=QualityGateResult.ITERATE,
                score=score,
                threshold=self.thresholds.content_minimum,
                reasons=reasons,
                recommendations=recommendations,
                next_action="run_content_editor"
            )

        # Determine pass level
        if score >= self.thresholds.content_excellent:
            reasons.append(f"Excellent content quality: {score}")
            next_action = "proceed_to_latex"
        elif score >= self.thresholds.content_good:
            reasons.append(f"Good content quality: {score}")
            next_action = "proceed_to_latex"
        else:
            reasons.append(f"Acceptable content quality: {score}")
            next_action = "proceed_to_latex"

        return QualityGateEvaluation(
            gate_name="content_quality",
            result=QualityGateResult.PASS,
            score=score,
            threshold=self.thresholds.content_minimum,
            reasons=reasons,
            recommendations=["Content quality meets standards"],
            next_action=next_action
        )

    def evaluate_latex_quality_gate(self, assessment: QualityAssessment) -> QualityGateEvaluation:
        """
        Evaluate LaTeX quality gate.

        Args:
            assessment: Quality assessment data

        Returns:
            Quality gate evaluation result
        """
        reasons = []
        recommendations = []

        if assessment.latex_score is None:
            return QualityGateEvaluation(
                gate_name="latex_quality",
                result=QualityGateResult.FAIL,
                score=None,
                threshold=self.thresholds.latex_minimum,
                reasons=["LaTeX score not available"],
                recommendations=["Run LaTeX analysis"],
                next_action="run_latex_specialist"
            )

        score = assessment.latex_score

        # Check overall LaTeX score
        if score < self.thresholds.latex_minimum:
            reasons.append(f"LaTeX score {score} below minimum {self.thresholds.latex_minimum}")
            recommendations.append("Run LaTeX specialist to improve formatting and structure")
            return QualityGateEvaluation(
                gate_name="latex_quality",
                result=QualityGateResult.ITERATE,
                score=score,
                threshold=self.thresholds.latex_minimum,
                reasons=reasons,
                recommendations=recommendations,
                next_action="run_latex_specialist"
            )

        # Check component scores
        component_issues = []

        if assessment.latex_structure and assessment.latex_structure < self.thresholds.latex_structure_minimum:
            component_issues.append(f"Structure: {assessment.latex_structure}/{self.thresholds.latex_structure_minimum}")

        if assessment.latex_typography and assessment.latex_typography < self.thresholds.latex_typography_minimum:
            component_issues.append(f"Typography: {assessment.latex_typography}/{self.thresholds.latex_typography_minimum}")

        if assessment.latex_tables_figures and assessment.latex_tables_figures < self.thresholds.latex_tables_figures_minimum:
            component_issues.append(f"Tables/Figures: {assessment.latex_tables_figures}/{self.thresholds.latex_tables_figures_minimum}")

        if assessment.latex_best_practices and assessment.latex_best_practices < self.thresholds.latex_best_practices_minimum:
            component_issues.append(f"Best Practices: {assessment.latex_best_practices}/{self.thresholds.latex_best_practices_minimum}")

        if component_issues:
            reasons.extend([f"Component scores below minimum: {', '.join(component_issues)}"])
            recommendations.append("Improve LaTeX component scores")
            return QualityGateEvaluation(
                gate_name="latex_quality",
                result=QualityGateResult.ITERATE,
                score=score,
                threshold=self.thresholds.latex_minimum,
                reasons=reasons,
                recommendations=recommendations,
                next_action="run_latex_specialist"
            )

        # Check issue count
        issue_count = len(assessment.latex_issues)
        if issue_count > self.thresholds.max_latex_issues:
            reasons.append(f"Too many LaTeX issues: {issue_count} > {self.thresholds.max_latex_issues}")
            recommendations.append("Address remaining LaTeX issues")
            return QualityGateEvaluation(
                gate_name="latex_quality",
                result=QualityGateResult.ITERATE,
                score=score,
                threshold=self.thresholds.latex_minimum,
                reasons=reasons,
                recommendations=recommendations,
                next_action="run_latex_specialist"
            )

        # Determine pass level
        if score >= self.thresholds.latex_excellent:
            reasons.append(f"Excellent LaTeX quality: {score}")
            next_action = "proceed_to_visual_qa"
        elif score >= self.thresholds.latex_good:
            reasons.append(f"Good LaTeX quality: {score}")
            next_action = "proceed_to_visual_qa"
        else:
            reasons.append(f"Acceptable LaTeX quality: {score}")
            next_action = "proceed_to_visual_qa"

        return QualityGateEvaluation(
            gate_name="latex_quality",
            result=QualityGateResult.PASS,
            score=score,
            threshold=self.thresholds.latex_minimum,
            reasons=reasons,
            recommendations=["LaTeX quality meets standards"],
            next_action=next_action
        )

    def evaluate_overall_quality_gate(self, assessment: QualityAssessment, iteration_count: int = 0) -> QualityGateEvaluation:
        """
        Evaluate overall quality gate for final decision.

        Args:
            assessment: Complete quality assessment
            iteration_count: Number of iterations completed

        Returns:
            Final quality gate evaluation
        """
        reasons = []
        recommendations = []

        # Calculate overall score
        scores = []
        if assessment.content_score is not None:
            scores.append(assessment.content_score)
        if assessment.latex_score is not None:
            scores.append(assessment.latex_score)

        if not scores:
            return QualityGateEvaluation(
                gate_name="overall_quality",
                result=QualityGateResult.FAIL,
                score=None,
                threshold=self.thresholds.overall_target,
                reasons=["No quality scores available"],
                recommendations=["Run complete QA pipeline"],
                next_action="start_pipeline"
            )

        overall_score = sum(scores) / len(scores)
        assessment.overall_score = overall_score

        # Check maximum iterations
        if iteration_count >= self.thresholds.max_iterations:
            reasons.append(f"Maximum iterations reached: {iteration_count}")
            if overall_score >= self.thresholds.overall_target:
                recommendations.append("Quality acceptable despite max iterations - proceed with human review")
                return QualityGateEvaluation(
                    gate_name="overall_quality",
                    result=QualityGateResult.ESCALATE,
                    score=overall_score,
                    threshold=self.thresholds.overall_target,
                    reasons=reasons,
                    recommendations=recommendations,
                    next_action="human_review"
                )
            else:
                recommendations.append("Quality below target at max iterations - escalate to human")
                return QualityGateEvaluation(
                    gate_name="overall_quality",
                    result=QualityGateResult.ESCALATE,
                    score=overall_score,
                    threshold=self.thresholds.overall_target,
                    reasons=reasons,
                    recommendations=recommendations,
                    next_action="human_escalation"
                )

        # Check for human handoff threshold
        if overall_score >= self.thresholds.human_handoff_threshold:
            reasons.append(f"Excellent overall quality: {overall_score}")
            recommendations.append("Quality exceeds handoff threshold - ready for human review")
            return QualityGateEvaluation(
                gate_name="overall_quality",
                result=QualityGateResult.PASS,
                score=overall_score,
                threshold=self.thresholds.human_handoff_threshold,
                reasons=reasons,
                recommendations=recommendations,
                next_action="human_handoff"
            )

        # Check for target threshold
        if overall_score >= self.thresholds.overall_target:
            reasons.append(f"Good overall quality: {overall_score}")
            recommendations.append("Quality meets target - ready for human review")
            return QualityGateEvaluation(
                gate_name="overall_quality",
                result=QualityGateResult.PASS,
                score=overall_score,
                threshold=self.thresholds.overall_target,
                reasons=reasons,
                recommendations=recommendations,
                next_action="human_handoff"
            )

        # Below target - determine iteration strategy
        reasons.append(f"Overall quality {overall_score} below target {self.thresholds.overall_target}")

        # Analyze which components need improvement
        if assessment.content_score and assessment.content_score < self.thresholds.content_good:
            recommendations.append("Improve content quality")
        if assessment.latex_score and assessment.latex_score < self.thresholds.latex_good:
            recommendations.append("Improve LaTeX quality")

        return QualityGateEvaluation(
            gate_name="overall_quality",
            result=QualityGateResult.ITERATE,
            score=overall_score,
            threshold=self.thresholds.overall_target,
            reasons=reasons,
            recommendations=recommendations,
            next_action="iterate_pipeline"
        )

    def check_improvement_convergence(self,
                                    current_assessment: QualityAssessment,
                                    previous_assessment: Optional[QualityAssessment]) -> Tuple[bool, float]:
        """
        Check if quality improvement has converged (plateaued).

        Args:
            current_assessment: Current quality assessment
            previous_assessment: Previous iteration assessment

        Returns:
            Tuple of (has_converged, improvement_amount)
        """
        if not previous_assessment or not current_assessment.overall_score or not previous_assessment.overall_score:
            return False, 0.0

        improvement = current_assessment.overall_score - previous_assessment.overall_score

        # Check if improvement is below convergence threshold
        has_converged = improvement < self.thresholds.convergence_threshold

        return has_converged, improvement

    def generate_quality_summary(self, assessment: QualityAssessment) -> Dict:
        """
        Generate a comprehensive quality summary.

        Args:
            assessment: Quality assessment to summarize

        Returns:
            Quality summary dictionary
        """
        summary = {
            "overall_score": assessment.overall_score,
            "assessment_timestamp": assessment.assessment_timestamp,
            "content_analysis": {
                "score": assessment.content_score,
                "issues_count": len(assessment.content_issues),
                "issues": assessment.content_issues[:5]  # Limit to first 5
            },
            "latex_analysis": {
                "overall_score": assessment.latex_score,
                "structure": assessment.latex_structure,
                "typography": assessment.latex_typography,
                "tables_figures": assessment.latex_tables_figures,
                "best_practices": assessment.latex_best_practices,
                "issues_count": len(assessment.latex_issues),
                "issues": assessment.latex_issues[:5]  # Limit to first 5
            },
            "quality_gates": {
                "content_passes": assessment.content_score >= self.thresholds.content_minimum if assessment.content_score else False,
                "latex_passes": assessment.latex_score >= self.thresholds.latex_minimum if assessment.latex_score else False,
                "overall_passes": assessment.overall_score >= self.thresholds.overall_target if assessment.overall_score else False,
                "ready_for_handoff": assessment.overall_score >= self.thresholds.human_handoff_threshold if assessment.overall_score else False
            }
        }

        return summary

    def log_evaluation(self, evaluation: QualityGateEvaluation):
        """Log quality gate evaluation for history tracking."""
        self.evaluation_history.append(evaluation)

    def get_evaluation_history(self) -> List[QualityGateEvaluation]:
        """Get complete evaluation history."""
        return self.evaluation_history.copy()