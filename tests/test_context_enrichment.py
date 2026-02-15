"""Tests for context enrichment nodes.

All tests mock the Anthropic client so they run without API keys.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.qa_orchestrator.context_enrichment import (
    enrich_for_iteration_node,
    enrich_for_latex_node,
    enrich_for_visual_qa_node,
    _format_dict,
    _summarize_quality_evaluations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(response_text: str = "1. Do something\n2. Do something else"):
    """Create a mock Anthropic client that returns the given text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_client.messages.create.return_value = mock_response
    return mock_client


def _base_state(**overrides):
    """Create a minimal pipeline state for testing."""
    state = {
        "content_source": "research_report",
        "iterations_completed": 0,
        "agent_context": {},
        "agent_results": [],
        "quality_evaluations": [],
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# enrich_for_latex_node tests
# ---------------------------------------------------------------------------

class TestEnrichForLatex:
    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_enriched_instructions(self, mock_get_client):
        """Enrichment node returns instructions in agent_context."""
        mock_get_client.return_value = _make_mock_client("1. Use booktabs\n2. Fix spacing")
        state = _base_state(agent_context={
            "content_editor_notes": {"quality_score": 85, "has_complex_tables": True}
        })
        result = enrich_for_latex_node(state)

        assert "agent_context" in result
        assert "enriched_latex_instructions" in result["agent_context"]
        assert "booktabs" in result["agent_context"]["enriched_latex_instructions"]

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_no_api_key(self, mock_get_client):
        """Returns empty dict when no API key is available."""
        mock_get_client.return_value = None
        result = enrich_for_latex_node(_base_state())
        assert result == {}

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_llm_error(self, mock_get_client):
        """Returns empty dict when the LLM call fails."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API error")
        mock_get_client.return_value = mock_client

        result = enrich_for_latex_node(_base_state())
        assert result == {}

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_includes_quality_progression_on_iteration(self, mock_get_client):
        """Includes quality progression when iterations > 0."""
        mock_client = _make_mock_client("1. Focus on tables")
        mock_get_client.return_value = mock_client

        state = _base_state(
            iterations_completed=1,
            quality_evaluations=[{"gate_name": "content_quality", "score": 75, "result": "iterate"}],
        )
        result = enrich_for_latex_node(state)

        assert "agent_context" in result
        # Verify the LLM was called (prompt should include quality info)
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert "iteration 2" in prompt.lower()

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_handles_empty_state_gracefully(self, mock_get_client):
        """Handles a minimal state without errors."""
        mock_get_client.return_value = _make_mock_client("1. Default guidance")
        result = enrich_for_latex_node(_base_state())
        assert "agent_context" in result


# ---------------------------------------------------------------------------
# enrich_for_visual_qa_node tests
# ---------------------------------------------------------------------------

class TestEnrichForVisualQA:
    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_enriched_instructions(self, mock_get_client):
        """Enrichment node returns focus areas in agent_context."""
        mock_get_client.return_value = _make_mock_client("1. Check table alignment\n2. Verify margins")
        state = _base_state(agent_context={
            "latex_specialist_notes": {"typography_score": 18, "typography_issues": ["bad spacing"]},
            "content_editor_notes": {"quality_score": 82},
        })
        result = enrich_for_visual_qa_node(state)

        assert "agent_context" in result
        assert "enriched_visual_qa_instructions" in result["agent_context"]

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_no_api_key(self, mock_get_client):
        mock_get_client.return_value = None
        result = enrich_for_visual_qa_node(_base_state())
        assert result == {}

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_llm_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("timeout")
        mock_get_client.return_value = mock_client

        result = enrich_for_visual_qa_node(_base_state())
        assert result == {}


# ---------------------------------------------------------------------------
# enrich_for_iteration_node tests
# ---------------------------------------------------------------------------

class TestEnrichForIteration:
    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_iteration_strategy(self, mock_get_client):
        """Enrichment node returns strategy in agent_context."""
        mock_get_client.return_value = _make_mock_client(
            "Content editor: simplify sentences\nLaTeX: fix tables\nVisual QA: check margins"
        )
        state = _base_state(
            iterations_completed=1,
            quality_evaluations=[
                {"gate_name": "overall", "score": 72, "result": "iterate"},
            ],
            agent_results=[
                {"agent_type": "content_editor", "quality_score": 80, "issues_found": ["long sentences"]},
                {"agent_type": "latex_specialist", "quality_score": 85, "issues_found": []},
            ],
        )
        result = enrich_for_iteration_node(state)

        assert "agent_context" in result
        assert "enriched_iteration_strategy" in result["agent_context"]

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_no_api_key(self, mock_get_client):
        mock_get_client.return_value = None
        result = enrich_for_iteration_node(_base_state())
        assert result == {}

    @patch("agents.qa_orchestrator.context_enrichment._get_anthropic_client")
    def test_returns_empty_on_llm_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API error")
        mock_get_client.return_value = mock_client
        result = enrich_for_iteration_node(_base_state())
        assert result == {}


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_format_dict_with_dict(self):
        result = _format_dict({"score": 85, "issues": ["a", "b"]})
        assert "score: 85" in result
        assert "issues:" in result

    def test_format_dict_with_string(self):
        result = _format_dict("hello")
        assert result == "hello"

    def test_format_dict_empty(self):
        result = _format_dict({})
        assert result == ""

    def test_summarize_quality_evaluations_empty(self):
        result = _summarize_quality_evaluations([])
        assert "No quality" in result

    def test_summarize_quality_evaluations_with_data(self):
        evals = [
            {"gate_name": "content_quality", "score": 75, "result": "iterate"},
            {"gate_name": "overall", "score": 82, "result": "pass"},
        ]
        result = _summarize_quality_evaluations(evals)
        assert "content_quality" in result
        assert "75" in result
        assert "overall" in result
        assert "82" in result
