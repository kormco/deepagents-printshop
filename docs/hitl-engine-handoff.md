# HITL Engine — Handoff

**Branch:** `feature/hitl-engine-cli` (`8bedf6e`, pushed to origin)
**Status:** First commit landed; smoke-tested end-to-end on Windows + MiKTeX with a real `research_report` run.
**Created:** 2026-05-08

## Why this exists

The autonomous QA pipeline (LangGraph StateGraph in `agents/qa_orchestrator/langgraph_workflow.py`) made every quality decision itself: gate thresholds, iteration caps, when to escalate. In practice the user reviews every output anyway, and the most common failure mode is "score plateaued below threshold → escalated." A human-in-the-loop variant fixes that — the human becomes the gate, the engine just runs stages.

The longer-term goal is to ship the engine as a Docker container and the user-facing flow as a Claude Code plugin (`/printshop`, `/printshop-iterate`). This branch is **only the engine half** — the CLI contract that the plugin will eventually drive. No plugin manifest, no Docker image yet.

The full design discussion that led here is in conversation; the short version: we chose **LangGraph drives, Claude is the UI** (Option 2) over **Claude drives, calls LangGraph subgraphs** (Option 1) because the user wants the engine in Docker so end users don't install Python, TeX Live, etc.

## What's in the commit

Two commits on the branch:

```
8bedf6e Force UTF-8 stdio in printshop CLI to survive Windows cp1252
1a760be Add HITL engine CLI scaffolding behind HITL_MODE flag
```

### New code

- `printshop/__init__.py` — public re-exports
- `printshop/__main__.py` — `python -m printshop` entry
- `printshop/cli.py` — `start`, `resume`, `status`, `list`, `abort`, `logs`
- `printshop/contracts.py` — `SCHEMA_VERSION`, payload builders, `runs_dir()` resolution

### Modified

- `agents/qa_orchestrator/langgraph_workflow.py`
  - `get_hitl_mode()` — reads `HITL_MODE` env var (default off)
  - `human_checkpoint_after_latex_node()` — calls `interrupt()` with an ask payload
  - `route_after_latex_optimization_or_hitl()` — wraps existing routing; only diverts to checkpoint when flag on AND latex stage succeeded (compilation failures still drive auto-retry)
  - `route_after_human_checkpoint()` — branches on response action

### Tests

48 new tests in `tests/test_hitl_cli.py` covering: HITL flag parsing, routing in both modes, ask-payload shape, response validation, contract envelope helpers, CLI status/list/abort against a tmp runs dir, argparse wiring.

Existing `test_graph_has_10_nodes` bumped to 11 — the new `human_checkpoint_after_latex` node is always present in the graph (orphan when HITL is off) so a single graph definition serves both modes.

**137 total tests pass.** Autonomous behavior is byte-identical when `HITL_MODE=off`.

## How it works at runtime

```
$ python -m printshop start <run_id> --content-type research_report

  ┌────────────────────────────────────────────────────────────┐
  │ 1. CLI sets HITL_MODE=on (idempotent), creates run dir,    │
  │    builds initial PipelineState, opens SqliteSaver         │
  │ 2. graph.invoke() runs content_review → enrich → latex     │
  │ 3. Latex stage succeeds → router returns                   │
  │    "human_checkpoint_after_latex"                          │
  │ 4. Node calls interrupt(payload) — graph pauses,           │
  │    state persisted to checkpoint.sqlite                    │
  │ 5. CLI extracts result["__interrupt__"][0].value,          │
  │    wraps it in build_ask_envelope, writes ask.json         │
  │ 6. CLI exits 0 — the run is paused                         │
  └────────────────────────────────────────────────────────────┘

$ python -m printshop resume <run_id> --response response.json

  ┌────────────────────────────────────────────────────────────┐
  │ 7. CLI loads response.json, validates action vocabulary    │
  │ 8. Clears stale ask.json, opens SqliteSaver                │
  │ 9. graph.invoke(Command(resume=response)) — interrupt()    │
  │    inside the node returns the response value              │
  │ 10. Node stores response in agent_context;                 │
  │     route_after_human_checkpoint reads action and routes   │
  │ 11. Graph runs to END → CLI writes done.json               │
  └────────────────────────────────────────────────────────────┘
```

`/loop /printshop-iterate` (future plugin work) wraps this by polling `printshop status` between fires.

## JSON contracts (the actual cross-system interface)

`schema_version: "1"` everywhere. Files appear in `~/.printshop/runs/<run_id>/` (override with `PRINTSHOP_RUNS_DIR`).

### `ask.json` (engine → driver, present while paused)

```json
{
  "schema_version": "1",
  "run_id": "d4e2aac2",
  "asked_at": "2026-05-08T13:59:03",
  "stage": "latex_optimization",
  "iteration": 1,
  "summary": "LaTeX stage complete (score 93).",
  "scores": {
    "agent": {"value": 93, "rationale": "LaTeX specialist quality score"},
    "thresholds": {"minimum": 80, "good": 85, "excellent": 90}
  },
  "artifacts": {"tex": "...", "pdf": "..."},
  "notes": {"structure_score": 20, "typography_score": 24, "typography_issues": [], "compilation_success": false},
  "question": "Review the compiled output...",
  "valid_actions": ["approve_all", "approve_subset", "edit", "describe", "rerun_stage", "skip_to_finalize", "abort"]
}
```

### `response.json` (driver → engine, present briefly during resume)

```json
{
  "schema_version": "1",
  "action": "approve_all",
  "approved_proposal_ids": [],
  "rejected_proposal_ids": [],
  "additional_instructions": "",
  "human_score": 93,
  "exit_after_apply": false
}
```

### `done.json` / `error.json` (terminal)

```json
{
  "schema_version": "1",
  "run_id": "d4e2aac2",
  "status": "completed",   // or "escalated" / "failed" / "aborted"
  "final_artifacts": {"tex": "...", "pdf": "..."},
  "stages_completed": ["content_editor", "latex_specialist", "visual_qa"],
  "iterations_completed": 1,
  "human_checkpoints": 1,
  "wallclock_seconds": 152.48,
  "completed_at": "2026-05-08T14:35:07"
}
```

`SCHEMA_VERSION` is `"1"`. Any future field shape change bumps it; drivers should refuse runs they don't recognize.

## Smoke test results (run `d4e2aac2`)

| Phase | Time | What happened |
|---|---|---|
| `start` | 13:57 | Content edit (iterated 79→80), LaTeX gen, PDF compile to 3 pages |
| Paused | 13:59 | `ask.json` written with score 93/100, .tex/.pdf paths, valid_actions |
| `resume` | 14:32 | `approve_all`, ran visual QA |
| Completed | 14:35 | `done.json` written, `human_checkpoints: 1`, 152s wall-clock |

Final `done.json` status was `"escalated"` because visual QA scored 43/100 — it judged the output didn't match research-report specs. That's honest: with HITL, you'd have used `"action": "skip_to_finalize"` at the LaTeX checkpoint to ship without visual QA running. That's the use case HITL exists for.

## Known issues surfaced (pre-existing, not HITL bugs)

1. **`compilation_success: false` in ask.json `notes` when PDF clearly compiled.** When the LLM-fix branch in `latex_optimization_node` (lines ~507-538 of `langgraph_workflow.py`) succeeds, it doesn't update `agent_context["latex_specialist_notes"]["compilation_success"]`. Cosmetic but misleading. Small, isolated fix.
2. **Visual QA "Version v3_visual_qa_iter1 already exists"** during resume. Pre-existing version-manager interaction in `agents/visual_qa/agent.py`. Didn't crash the run; the run still completed. Worth filing as a separate bug.
3. **Windows UTF-8 console** — fixed in `8bedf6e`. The autonomous CLI worked around this via `run_agent.py`; the new entry point now handles it itself.

## Try it yourself

Prerequisites: `pip install -e ".[dev]"` (or use the `.venv-regression/` venv we set up locally), MiKTeX/TeX Live for PDF compilation, `ANTHROPIC_API_KEY` in `.env`.

```powershell
# Auto-approve mode — drives the run end-to-end with canned approvals
python -m printshop start abc12345 --content-type research_report --auto-approve

# Manual HITL — pauses at each checkpoint, you craft response.json
python -m printshop start xyz99999 --content-type research_report
python -m printshop status xyz99999          # → state: "paused"
cat ~/.printshop/runs/xyz99999/ask.json      # → score, paths, valid_actions

# Write response.json with {"action": "approve_all", "schema_version": "1"}
python -m printshop resume xyz99999 --response ~/.printshop/runs/xyz99999/response.json
python -m printshop logs xyz99999            # → all events
```

Other commands: `printshop list`, `printshop abort <id>`.

## Roadmap (priority order)

1. ~~**Push branch + open draft PR**~~ — pushed; draft PR optional.
2. **Add interrupts at content_review and visual_qa stages.** Currently only LaTeX has a HITL pause. The user should be able to steer all three stages. Pattern is established — copy the `human_checkpoint_after_latex_node` shape, parameterize by stage. ~30 lines per stage + tests.
3. **Fix `compilation_success` reporting in `latex_optimization_node`.** Small, isolated. While we're touching that node, also fix the visual_qa version collision (item 2 in known issues).
4. **Build Docker engine image.** Move the runtime into a container; expose CLI via `docker exec`. Bind mount `~/.printshop/runs/` so artifacts are visible on host.
5. **Sketch the Claude Code plugin.** `commands/printshop.md`, `commands/printshop-iterate.md`, `commands/printshop-resume.md`, content-type-* skills (Claude-side, for input prep). The earlier sketch in conversation is the starting point.
6. **`/loop /printshop-iterate` polling.** The plugin uses `/loop` to poll `printshop status` between human turns; only summons the human when `state == "paused"`.

## What's intentionally NOT in this commit

- No Docker engine yet — engine still runs in-process via local Python.
- No Claude Code plugin manifest, commands, or skills.
- No `printshop-engine` console script — invocation is `python -m printshop` to avoid colliding with the existing `printshop` script that points at `agents.qa_orchestrator.agent:main` (the autonomous CLI).
- Only one HITL pause point (post-LaTeX). Pre-LaTeX content review and post-visual-QA checkpoints come incrementally.
- No surgical-diff LLM call yet for `additional_instructions`. The `approve_all` and `abort` paths work; `approve_subset` and `describe` ride through routing today but don't actually apply additional_instructions until that LLM call lands. Worth doing alongside item 2.

## Files to know

| File | Purpose |
|---|---|
| `printshop/cli.py` | Entry point, subcommand dispatch, JSON I/O |
| `printshop/contracts.py` | Schema, payload builders, `runs_dir()` |
| `agents/qa_orchestrator/langgraph_workflow.py` | HITL flag, interrupt node, routing wrapper |
| `tests/test_hitl_cli.py` | 48 tests for everything HITL-specific |
| `~/.printshop/runs/<id>/` | Per-run state (configurable via `PRINTSHOP_RUNS_DIR`) |
