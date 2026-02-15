"""
Context Enrichment Nodes for the LangGraph QA Pipeline.

Lightweight LLM calls that synthesize cross-agent context between processing
nodes. Each enrichment node reads the current run state, pattern memory,
content type constraints, and quality progression, then writes targeted
instructions for the downstream agent into ``agent_context``.

Enrichment is additive -- if the LLM call fails, the node returns an empty
dict and the downstream agent proceeds without enriched guidance.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure project root is importable
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENRICHMENT_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1024


def _get_anthropic_client():
    """Return an Anthropic client or None if the key is missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    from anthropic import Anthropic
    return Anthropic(api_key=api_key)


def _load_pattern_context(content_source: str) -> Dict[str, str]:
    """Load pattern injector context for a content source.

    Returns a dict with keys for each agent context getter that has content.
    """
    result: Dict[str, str] = {}
    try:
        from tools.pattern_injector import PatternInjector
        injector = PatternInjector(document_type=content_source)
        for key, method in [
            ("latex_specialist", injector.get_context_for_latex_specialist),
            ("visual_qa", injector.get_context_for_visual_qa),
            ("content_editor", injector.get_context_for_content_editor),
            ("agent_memory_latex", lambda: injector.get_agent_memory_context("latex_specialist")),
        ]:
            ctx = method()
            if ctx:
                result[key] = ctx
    except Exception:
        pass
    return result


def _load_rendering_instructions(content_source: str) -> str:
    """Load the rendering instructions for a content type."""
    try:
        from tools.content_type_loader import ContentTypeLoader
        loader = ContentTypeLoader()
        ct = loader.load_type(content_source)
        return ct.rendering_instructions or ""
    except Exception:
        return ""


def _summarize_quality_evaluations(evaluations: list) -> str:
    """Build a compact summary of quality score progression."""
    if not evaluations:
        return "No quality evaluations yet."
    lines = []
    for i, ev in enumerate(evaluations):
        score = ev.get("score", "?")
        result = ev.get("result", "?")
        gate = ev.get("gate_name", "unknown")
        lines.append(f"  Eval {i + 1}: {gate} = {score} ({result})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Enrichment node functions
# ---------------------------------------------------------------------------

def enrich_for_latex_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize context for the LaTeX specialist from upstream signals.

    Reads content editor notes, quality evaluations, pattern memory, and
    content type rendering instructions, then asks the LLM to generate
    3-5 specific instructions for the LaTeX specialist.
    """
    client = _get_anthropic_client()
    if client is None:
        return {}

    try:
        content_source = state.get("content_source", "research_report")
        agent_ctx = state.get("agent_context", {})
        content_notes = agent_ctx.get("content_editor_notes", {})
        iterations = state.get("iterations_completed", 0)
        evaluations = state.get("quality_evaluations", [])

        # Load external context
        patterns = _load_pattern_context(content_source)
        rendering = _load_rendering_instructions(content_source)

        # Assemble prompt inputs
        prompt_parts = [
            "You are a pipeline orchestrator. Based on the information below, "
            "generate 3-5 specific, actionable instructions for the LaTeX specialist "
            "agent that will convert edited markdown into a professional LaTeX document. "
            "Be concise. Output ONLY the numbered instructions, nothing else."
        ]

        if content_notes:
            prompt_parts.append(f"\n## Content Editor Findings\n{_format_dict(content_notes)}")

        if iterations > 0:
            prompt_parts.append(f"\nThis is iteration {iterations + 1}.")
            quality_summary = _summarize_quality_evaluations(evaluations)
            prompt_parts.append(f"\n## Quality Progression\n{quality_summary}")

        if patterns.get("latex_specialist"):
            prompt_parts.append(f"\n## Historical Patterns\n{patterns['latex_specialist'][:800]}")

        if rendering:
            prompt_parts.append(f"\n## Document Type Rendering Rules\n{rendering[:800]}")

        response = client.messages.create(
            model=_ENRICHMENT_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
        )
        instructions = response.content[0].text.strip()

        return {
            "agent_context": {"enriched_latex_instructions": instructions},
        }
    except Exception as e:
        print(f"   [Enrichment] enrich_for_latex failed (non-blocking): {e}")
        return {}


def enrich_for_visual_qa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize context for Visual QA from upstream signals.

    Reads LaTeX specialist notes, content editor notes, quality evaluations,
    pattern memory, and rendering instructions, then generates specific
    focus areas for the visual QA agent.
    """
    client = _get_anthropic_client()
    if client is None:
        return {}

    try:
        content_source = state.get("content_source", "research_report")
        agent_ctx = state.get("agent_context", {})
        latex_notes = agent_ctx.get("latex_specialist_notes", {})
        content_notes = agent_ctx.get("content_editor_notes", {})
        evaluations = state.get("quality_evaluations", [])

        patterns = _load_pattern_context(content_source)
        rendering = _load_rendering_instructions(content_source)

        prompt_parts = [
            "You are a pipeline orchestrator. Based on the information below, "
            "generate 3-5 specific focus areas for the Visual QA agent that will "
            "inspect a rendered PDF for formatting defects. Distinguish between "
            "intentional formatting (from the document type rules) and actual defects. "
            "Be concise. Output ONLY the numbered focus areas, nothing else."
        ]

        if latex_notes:
            prompt_parts.append(f"\n## LaTeX Specialist Analysis\n{_format_dict(latex_notes)}")

        if content_notes:
            prompt_parts.append(f"\n## Content Editor Notes\n{_format_dict(content_notes)}")

        if evaluations:
            quality_summary = _summarize_quality_evaluations(evaluations)
            prompt_parts.append(f"\n## Quality Progression\n{quality_summary}")

        if patterns.get("visual_qa"):
            prompt_parts.append(f"\n## Historical Visual Patterns\n{patterns['visual_qa'][:800]}")

        if rendering:
            prompt_parts.append(
                f"\n## Document Type Rendering Rules (intentional formatting -- not defects)\n{rendering[:800]}"
            )

        response = client.messages.create(
            model=_ENRICHMENT_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
        )
        instructions = response.content[0].text.strip()

        return {
            "agent_context": {"enriched_visual_qa_instructions": instructions},
        }
    except Exception as e:
        print(f"   [Enrichment] enrich_for_visual_qa failed (non-blocking): {e}")
        return {}


def enrich_for_iteration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize an adjusted strategy for the next pipeline iteration.

    Reads the full quality evaluation progression, all agent results, and
    pattern memory to generate guidance on what each agent should prioritize
    differently in the next iteration.
    """
    client = _get_anthropic_client()
    if client is None:
        return {}

    try:
        content_source = state.get("content_source", "research_report")
        evaluations = state.get("quality_evaluations", [])
        agent_results = state.get("agent_results", [])
        agent_ctx = state.get("agent_context", {})
        iterations = state.get("iterations_completed", 0)

        patterns = _load_pattern_context(content_source)

        prompt_parts = [
            "You are a pipeline orchestrator. The QA pipeline is about to start "
            f"iteration {iterations + 1}. Based on the quality progression and agent "
            "results below, generate an adjusted strategy for the next iteration. "
            "For each agent (content editor, LaTeX specialist, visual QA), state what "
            "it should prioritize differently. Be concise. Output ONLY the strategy."
        ]

        quality_summary = _summarize_quality_evaluations(evaluations)
        prompt_parts.append(f"\n## Quality Score Progression\n{quality_summary}")

        # Summarize agent results compactly
        if agent_results:
            results_summary = []
            for r in agent_results[-6:]:  # Last 6 results (2 iterations worth)
                agent = r.get("agent_type", "?")
                score = r.get("quality_score", "?")
                issues = r.get("issues_found", [])
                issues_str = "; ".join(issues[:3]) if issues else "none"
                results_summary.append(f"  {agent}: score={score}, issues=[{issues_str}]")
            prompt_parts.append(f"\n## Recent Agent Results\n" + "\n".join(results_summary))

        # Include any existing context notes
        for key in ["content_editor_notes", "latex_specialist_notes", "compilation_errors"]:
            if key in agent_ctx:
                prompt_parts.append(f"\n## {key}\n{_format_dict(agent_ctx[key])}")

        if patterns.get("content_editor"):
            prompt_parts.append(f"\n## Content Patterns\n{patterns['content_editor'][:500]}")

        response = client.messages.create(
            model=_ENRICHMENT_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
        )
        strategy = response.content[0].text.strip()

        return {
            "agent_context": {"enriched_iteration_strategy": strategy},
        }
    except Exception as e:
        print(f"   [Enrichment] enrich_for_iteration failed (non-blocking): {e}")
        return {}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_dict(d: Any) -> str:
    """Format a dict or value as a compact string for LLM prompts."""
    if isinstance(d, dict):
        lines = []
        for k, v in d.items():
            if isinstance(v, list):
                v_str = ", ".join(str(item) for item in v[:5])
                lines.append(f"- {k}: [{v_str}]")
            else:
                lines.append(f"- {k}: {v}")
        return "\n".join(lines)
    return str(d)
