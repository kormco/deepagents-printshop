"""Shared test fixtures for the QA pipeline test suite."""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so imports work without pip install
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.qa_orchestrator.quality_gates import (  # noqa: E402
    QualityAssessment,
    QualityGateManager,
    QualityThresholds,
)


@pytest.fixture
def default_thresholds():
    """Return default QualityThresholds."""
    return QualityThresholds()


@pytest.fixture
def gate_manager(default_thresholds):
    """Return a QualityGateManager with default thresholds."""
    return QualityGateManager(thresholds=default_thresholds)


@pytest.fixture
def passing_content_assessment():
    """QualityAssessment with a content score that passes the gate."""
    return QualityAssessment(
        content_score=85,
        content_issues=["minor style issue"],
    )


@pytest.fixture
def failing_content_assessment():
    """QualityAssessment with a content score below minimum."""
    return QualityAssessment(
        content_score=60,
        content_issues=["grammar", "readability", "structure"],
    )


@pytest.fixture
def passing_latex_assessment():
    """QualityAssessment with a LaTeX score that passes the gate."""
    return QualityAssessment(
        latex_score=90,
        latex_structure=23,
        latex_typography=22,
        latex_tables_figures=22,
        latex_best_practices=23,
        latex_issues=[],
    )


@pytest.fixture
def failing_latex_assessment():
    """QualityAssessment with a LaTeX score below minimum."""
    return QualityAssessment(
        latex_score=70,
        latex_structure=18,
        latex_typography=15,
        latex_tables_figures=18,
        latex_best_practices=19,
        latex_issues=["bad spacing", "wrong font", "missing packages", "broken table"],
    )


@pytest.fixture
def high_overall_assessment():
    """QualityAssessment that should pass the overall gate."""
    return QualityAssessment(
        content_score=90,
        latex_score=88,
        visual_qa_score=85.0,
        content_issues=[],
        latex_issues=[],
        visual_qa_issues=[],
    )


@pytest.fixture
def low_overall_assessment():
    """QualityAssessment that should trigger iteration."""
    return QualityAssessment(
        content_score=70,
        latex_score=65,
        content_issues=["many issues"],
        latex_issues=["many issues"],
    )


@pytest.fixture
def sample_initial_state():
    """A minimal PipelineState dict for testing graph invocation."""
    return {
        "workflow_id": "test_pipeline",
        "content_source": "research_report",
        "starting_version": "v0_original",
        "current_version": "v0_original",
        "current_stage": "initialization",
        "iterations_completed": 0,
        "success": False,
        "human_handoff": False,
        "escalated": False,
        "start_time": "2025-01-01T00:00:00",
        "end_time": None,
        "total_processing_time": None,
        "agent_results": [],
        "quality_assessments": [],
        "quality_evaluations": [],
        "agent_context": {},
    }
