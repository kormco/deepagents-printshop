"""Tests for quality gate decision logic.

All tests run without Docker, TeX Live, or API keys.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.qa_orchestrator.quality_gates import (  # noqa: E402
    QualityAssessment,
    QualityGateResult,
)


class TestContentQualityGate:
    def test_pass_excellent(self, gate_manager):
        """Score >= content_excellent passes."""
        assessment = QualityAssessment(content_score=92, content_issues=[])
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.PASS
        assert result.score == 92

    def test_pass_good(self, gate_manager):
        """Score >= content_good passes."""
        assessment = QualityAssessment(content_score=86, content_issues=[])
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.PASS

    def test_pass_minimum(self, gate_manager):
        """Score == content_minimum passes."""
        assessment = QualityAssessment(content_score=80, content_issues=[])
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.PASS

    def test_iterate_below_minimum(self, gate_manager):
        """Score < content_minimum iterates."""
        assessment = QualityAssessment(content_score=75, content_issues=[])
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.ITERATE

    def test_iterate_too_many_issues(self, gate_manager):
        """Too many content issues triggers iterate even if score passes."""
        issues = [f"issue_{i}" for i in range(10)]
        assessment = QualityAssessment(content_score=85, content_issues=issues)
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.ITERATE

    def test_fail_no_score(self, gate_manager):
        """Missing content score fails."""
        assessment = QualityAssessment(content_score=None)
        result = gate_manager.evaluate_content_quality_gate(assessment)
        assert result.result == QualityGateResult.FAIL


class TestLatexQualityGate:
    def test_pass_excellent(self, gate_manager):
        """Score >= latex_excellent passes."""
        assessment = QualityAssessment(
            latex_score=96,
            latex_structure=24, latex_typography=23,
            latex_tables_figures=24, latex_best_practices=25,
            latex_issues=[],
        )
        result = gate_manager.evaluate_latex_quality_gate(assessment)
        assert result.result == QualityGateResult.PASS

    def test_pass_minimum(self, gate_manager):
        """Score at latex_minimum with good components passes."""
        assessment = QualityAssessment(
            latex_score=85,
            latex_structure=22, latex_typography=20,
            latex_tables_figures=21, latex_best_practices=22,
            latex_issues=[],
        )
        result = gate_manager.evaluate_latex_quality_gate(assessment)
        assert result.result == QualityGateResult.PASS

    def test_iterate_below_minimum(self, gate_manager):
        """Score < latex_minimum iterates."""
        assessment = QualityAssessment(latex_score=70, latex_issues=[])
        result = gate_manager.evaluate_latex_quality_gate(assessment)
        assert result.result == QualityGateResult.ITERATE

    def test_iterate_component_below_minimum(self, gate_manager):
        """Component score below minimum triggers iterate."""
        assessment = QualityAssessment(
            latex_score=88,
            latex_structure=15,  # below 22 minimum
            latex_typography=22,
            latex_tables_figures=22,
            latex_best_practices=22,
            latex_issues=[],
        )
        result = gate_manager.evaluate_latex_quality_gate(assessment)
        assert result.result == QualityGateResult.ITERATE

    def test_fail_no_score(self, gate_manager):
        """Missing LaTeX score fails."""
        assessment = QualityAssessment(latex_score=None)
        result = gate_manager.evaluate_latex_quality_gate(assessment)
        assert result.result == QualityGateResult.FAIL


class TestOverallQualityGate:
    def test_pass_above_handoff(self, gate_manager, high_overall_assessment):
        """Score >= human_handoff_threshold passes."""
        result = gate_manager.evaluate_overall_quality_gate(high_overall_assessment, iteration_count=0)
        assert result.result == QualityGateResult.PASS

    def test_pass_above_target(self, gate_manager):
        """Score >= overall_target but below handoff passes."""
        assessment = QualityAssessment(content_score=82, latex_score=82)
        result = gate_manager.evaluate_overall_quality_gate(assessment, iteration_count=0)
        assert result.result == QualityGateResult.PASS

    def test_iterate_below_target(self, gate_manager, low_overall_assessment):
        """Score < overall_target with iterations remaining iterates."""
        result = gate_manager.evaluate_overall_quality_gate(low_overall_assessment, iteration_count=0)
        assert result.result == QualityGateResult.ITERATE

    def test_escalate_at_max_iterations(self, gate_manager, low_overall_assessment):
        """Max iterations reached escalates."""
        result = gate_manager.evaluate_overall_quality_gate(low_overall_assessment, iteration_count=3)
        assert result.result == QualityGateResult.ESCALATE

    def test_escalate_max_iterations_good_score(self, gate_manager):
        """Max iterations with good score still escalates (but with different recommendation)."""
        assessment = QualityAssessment(content_score=85, latex_score=85)
        result = gate_manager.evaluate_overall_quality_gate(assessment, iteration_count=3)
        assert result.result == QualityGateResult.ESCALATE

    def test_fail_no_scores(self, gate_manager):
        """No scores at all fails."""
        assessment = QualityAssessment()
        result = gate_manager.evaluate_overall_quality_gate(assessment, iteration_count=0)
        assert result.result == QualityGateResult.FAIL


class TestConvergence:
    def test_no_convergence_on_first_iteration(self, gate_manager):
        """First iteration (no previous) never converges."""
        current = QualityAssessment(overall_score=85)
        converged, improvement = gate_manager.check_improvement_convergence(current, None)
        assert converged is False

    def test_convergence_detected(self, gate_manager):
        """Small improvement triggers convergence."""
        previous = QualityAssessment(overall_score=84)
        current = QualityAssessment(overall_score=85)
        converged, improvement = gate_manager.check_improvement_convergence(current, previous)
        assert converged is True
        assert improvement == 1

    def test_no_convergence_with_large_improvement(self, gate_manager):
        """Large improvement does not trigger convergence."""
        previous = QualityAssessment(overall_score=70)
        current = QualityAssessment(overall_score=85)
        converged, improvement = gate_manager.check_improvement_convergence(current, previous)
        assert converged is False
        assert improvement == 15
