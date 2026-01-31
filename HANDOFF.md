# Handoff: LangGraph Migration, Packaging & Promotion

**Branch**: `feature/langgraph-migration` (off `main`)
**Last updated**: 2026-01-30

---

## Plan Overview

Migrate the QA orchestrator from a manual state machine to a LangGraph StateGraph, add inter-agent communication, package for PyPI, and prepare for open-source promotion.

Four phases:
1. **LangGraph StateGraph Migration** — replace the `while` loop in `workflow_coordinator.py` with a declarative graph
2. **Inter-Agent Communication** — `agent_context` dict flows upstream notes between nodes
3. **Python Package** — `pyproject.toml`, tests, CI
4. **Promotion Prep** — `llms.txt`, README updates, badges

---

## Current Progress

### DONE

| # | Item | Status |
|---|------|--------|
| 1 | `requirements.txt` — add `langgraph` | Done |
| 2 | `agents/qa_orchestrator/langgraph_workflow.py` — StateGraph, nodes, conditional edges, inter-agent context | Done |
| 3 | `agents/qa_orchestrator/agent.py` — `orchestrate_qa_pipeline()` now uses `compile_qa_pipeline()` + `app.invoke()` | Done |
| 4 | `tests/__init__.py`, `conftest.py`, `test_langgraph_workflow.py`, `test_quality_gates.py` — 37 tests, all passing | Done |
| 5 | `pyproject.toml` — hatchling build, `printshop` entry point, `[dev]` extras | Done |
| 6 | `.github/workflows/ci.yml` — ruff + pytest on push/PR | Done |
| 7 | `SYSTEM_DEPS.md` — system dependency install docs | Done |
| 8 | `llms.txt` — AI-discoverable project summary | Done |
| 9 | `README.md` — badges, gallery, Mermaid diagram, PyPI install, GitHub topics | Done |

### NOT YET COMMITTED

All changes are staged but not committed. Run:
```bash
git add ... && git commit
```

### NOT YET DONE

| Item | Notes |
|------|-------|
| Push to remote | Branch exists locally only |
| Create PR | After push |
| `pip install -e .` verification | Works locally but not formally tested in CI yet |
| Docker build verification | Needs `docker-compose build` — not run yet |
| Full pipeline E2E test | Requires API key + Docker/TeX Live |
| PyPI publish | Not in scope yet — `pyproject.toml` is ready |

---

## Key Architecture Decisions

### LangGraph integration is additive, not destructive
- `workflow_coordinator.py` and `quality_gates.py` are **untouched**
- Node functions in `langgraph_workflow.py` are thin wrappers that call existing `WorkflowCoordinator` methods
- `state_to_workflow_execution()` converts the final LangGraph state back to `WorkflowExecution` so all existing reporting works

### Inter-agent communication (Phase 2)
- `agent_context` field in `PipelineState` uses a custom `merge_dicts` reducer
- Content editor writes `content_editor_notes` (quality_score, issues, has_complex_tables)
- LaTeX specialist reads those notes and writes `latex_specialist_notes` (structure_score, typography_issues, packages_used)
- Visual QA reads both upstream note sets for prioritization

### Graph structure
```
START → content_review
content_review → [latex_optimization | iteration | escalation]
latex_optimization → [visual_qa | iteration | escalation]
visual_qa → quality_assessment
quality_assessment → [completion | iteration | escalation]
iteration → content_review (back-edge)
completion → END
escalation → END
```

Recursion limit: 30. Checkpointer: `MemorySaver` (in-memory, per invocation).

---

## Files Changed/Created

| File | Action |
|------|--------|
| `requirements.txt` | Modified — added `langgraph` |
| `agents/qa_orchestrator/langgraph_workflow.py` | **New** — ~300 lines |
| `agents/qa_orchestrator/agent.py` | Modified — new `orchestrate_qa_pipeline()` using LangGraph |
| `tests/__init__.py` | **New** — empty |
| `tests/conftest.py` | **New** — fixtures |
| `tests/test_langgraph_workflow.py` | **New** — 17 tests |
| `tests/test_quality_gates.py` | **New** — 20 tests |
| `pyproject.toml` | **New** — package config |
| `.github/workflows/ci.yml` | **New** — CI |
| `SYSTEM_DEPS.md` | **New** — system deps docs |
| `llms.txt` | **New** — AI discoverability |
| `README.md` | Modified — badges, gallery, install, architecture |

---

## Verification Checklist

- [x] `pytest tests/ -v` — 37/37 passing
- [x] `ruff check` on new files — clean
- [x] `python -c "from agents.qa_orchestrator.langgraph_workflow import export_mermaid_diagram; print(export_mermaid_diagram())"` — valid Mermaid output
- [ ] `pip install -e .` — editable install
- [ ] `docker-compose build` — Docker still works
- [ ] `printshop --content research_report` — CLI entry point
- [ ] Full pipeline E2E with API key
