# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepAgents PrintShop is a document generation system that produces professional LaTeX documents with comprehensive formatting, citations, tables, images, and diagrams. It uses LangGraph for pipeline orchestration, the Anthropic SDK for Claude calls, and runs in Docker with TeX Live for PDF compilation.

**Important: Do not hardcode LaTeX output into deterministic Python logic.** Rendering behavior is controlled by natural language instructions in `content_types/*/type.md` files, which the LaTeX agent reads at generation time. To change how a document looks (disclaimers, footers, spacing, section formatting), edit the type.md rendering instructions — not the Python code.

## Common Commands

### Running the Pipeline
```bash
# Full QA pipeline (content editing → LaTeX generation → Visual QA)
python agents/qa_orchestrator/agent.py

# Run individual agents
python agents/content_editor/versioned_agent.py
python agents/latex_specialist/agent.py
python agents/visual_qa/agent.py

# Run tests
python -m pytest tests/ -v
```

### Development Environment
```bash
# Build and run Docker container
docker-compose build
docker-compose run --rm deepagents-printshop

# Run the QA pipeline inside Docker
docker-compose run --rm deepagents-printshop python agents/qa_orchestrator/agent.py

# Access container shell
docker-compose run --rm deepagents-printshop bash
```

### LaTeX/PDF Operations
```bash
# Manual PDF compilation (requires texlive)
pdflatex artifacts/output/research_report.tex

# Test LaTeX generator import
python -c "from tools.latex_generator import LaTeXGenerator; print('LaTeX generator loaded')"

# Test PDF compiler
python -c "from tools.pdf_compiler import PDFCompiler; PDFCompiler().compile_pdf('artifacts/output/research_report.tex')"
```

## Prerequisites

**LaTeX Distribution Required**: PDF compilation requires a LaTeX distribution. The Docker container includes TeX Live, but if running outside Docker:
- **Windows**: [MiKTeX](https://miktex.org/)
- **macOS**: [MacTeX](https://www.tug.org/mactex/) or `brew install --cask mactex`
- **Linux**: TeX Live via `apt install texlive-full` or equivalent

Without a LaTeX distribution, the system can generate `.tex` files but cannot compile them to PDF.

## Architecture

### Pipeline (LangGraph StateGraph)

The QA orchestrator (`agents/qa_orchestrator/agent.py`) runs a LangGraph StateGraph with three processing stages and three context enrichment nodes. Each processing stage is gated by a quality threshold:

1. **Content Editor** (gate: 80) — Reviews markdown for grammar, academic tone, readability. Iterates up to 4 times.
2. **LaTeX Specialist** (gate: 85) — Converts edited markdown to `.tex` using config manifest and content type instructions. Applies automated optimizations.
3. **Visual QA** (gate: 80) — Compiles PDF, renders pages as images, uses Claude vision to find formatting issues, applies fixes. Iterates up to 3 times.

Between each processing stage, a **context enrichment node** uses a lightweight LLM call (Haiku) to synthesize upstream results, pattern memory, and content type constraints into targeted instructions for the downstream agent. The flow is: `content_review → enrich_for_latex → latex_optimization → enrich_for_visual_qa → visual_qa → quality_assessment`. On iteration: `iteration → enrich_for_iteration → content_review`.

Each stage creates versioned artifacts in `artifacts/reviewed_content/` (e.g., `v0_original`, `v1_content_edited`, `v2_latex_optimized`, `v3_visual_qa`). Pipeline reports are saved to `artifacts/agent_reports/`.

### Core Components

**agents/qa_orchestrator/agent.py**: Main pipeline entry point. Orchestrates the LangGraph workflow with quality gates and iteration limits.

**agents/qa_orchestrator/langgraph_workflow.py**: LangGraph StateGraph definition with conditional edges for quality gate decisions.

**agents/qa_orchestrator/context_enrichment.py**: Three enrichment node functions (`enrich_for_latex_node`, `enrich_for_visual_qa_node`, `enrich_for_iteration_node`) that use Claude Haiku to synthesize context between pipeline stages.

**agents/content_editor/versioned_agent.py**: Content editing agent that reviews and improves markdown files using Claude. Scores content on grammar, readability (Flesch Reading Ease), and academic tone.

**agents/latex_specialist/latex_optimizer.py**: Core LaTeX generation logic. Converts markdown to LaTeX using LLM, processes inline references (`<!-- IMAGE: -->`, `<!-- CSV_TABLE: -->`, `<!-- TIKZ: -->`), sanitizes Unicode for pdflatex, and applies automated optimizations. This is where most LaTeX logic lives.

**agents/visual_qa/agent.py**: Compiles PDF, renders pages to images, inspects with Claude vision, and applies targeted LaTeX fixes.

**tools/latex_generator.py**: LaTeXGenerator class with DocumentConfig for building LaTeX document structure (preamble, sections, tables, figures).

**tools/pdf_compiler.py**: PDFCompiler class for LaTeX-to-PDF conversion with multi-pass compilation.

**tools/content_type_loader.py**: Loads content type definitions from `content_types/` directory.

### Content Types

Content type definitions live in `content_types/<type_id>/type.md`. Each file contains:
- **Type metadata**: document class, font size, paper size
- **Rendering instructions**: Natural language instructions that the LaTeX agent follows when generating the document (disclaimers, headers/footers, typography, table formatting, figure placement, citation style, etc.)
- **LaTeX requirements**: Required packages and preamble configuration
- **Structure rules**: Constraints for valid output

To change how a document renders, edit the rendering instructions in the appropriate type.md file. The LaTeX agent reads these at generation time.

### Multi-Theme Content Types

Some content types support multiple visual themes that share the same macro contract but swap palette, typography, and layout primitives. The pattern (introduced by `content_types/resume/type.md`):

1. The `type.md` includes a **Theme Definitions** section listing each theme's palette and layout deltas
2. The `config.md` for a given sample selects a theme via a `theme:` field (e.g., `theme: architect`)
3. A `palette_preview.pdf` (and accompanying `.tex` source) lives next to `type.md` as a visual design reference for users picking a theme
4. The macro signatures (`\resumeheader`, `\resumesection`, etc.) stay constant across themes; only their internal rendering changes

When adding a new theme to an existing multi-theme content type, update both the **Theme Definitions** section and the per-theme color/macro override notes in `type.md`, then re-render `palette_preview.pdf` so the design reference stays in sync.

### Sample Content Structure

Each sample content directory (`artifacts/sample_content/<type_id>/`) contains:
- **config.md**: Document metadata (title, author, abstract) and a content manifest listing sections in order
- **Section files**: Markdown files referenced by the manifest (e.g., `introduction.md`, `results.md`)
- **images/** *(optional)*: Images referenced by inline `<!-- IMAGE: -->` comments — only present if the content type uses figures
- **data/** *(optional)*: CSV files referenced by inline `<!-- CSV_TABLE: -->` comments — only present if the content type uses tables
- **Sidecar deliverables** *(optional)*: Some content types pair with an adjacent deliverable. For example, `artifacts/sample_content/resume/cover_letter.md` ships next to the resume sections; the LaTeX agent renders it with the matched theme via the `resume_cover_letter` content type.

### Inline Reference Syntax

Markdown content files use HTML comments to reference external assets. The LaTeX optimizer processes these into proper LaTeX:

```markdown
<!-- IMAGE: path=images/chart.png, caption=Performance Chart, label=fig:chart -->

<!-- CSV_TABLE: path=data/results.csv, caption=Model Results, label=tab:results -->

<!-- TIKZ:
caption: Neural Network Architecture
label: fig:neural_net
code:
\node[circle, draw] (input) at (0,0) {Input};
\node[circle, draw] (output) at (3,0) {Output};
\draw[->] (input) -- (output);
-->
```

### Data Flow

1. Orchestrator loads content from `artifacts/sample_content/<type_id>/`
2. Content editor iteratively improves markdown files, saving versions to `artifacts/reviewed_content/`
3. LaTeX specialist reads the final edited markdown + config manifest + content type instructions, generates `.tex`
4. LaTeX optimizer processes inline references (images, CSV tables, TikZ), sanitizes Unicode, applies formatting fixes
5. Visual QA compiles PDF, inspects rendered pages, applies fixes, recompiles
6. Final output saved to `artifacts/output/<run_id>/`

### Memory System

DeepAgents persistent memory stored in `.deepagents/`:

**Research Agent** (`.deepagents/research_agent/memories/`):
- `latex_knowledge.md`: LaTeX best practices and patterns
- `report_structure.md`: Research report structure templates
- `artifacts_tracking.md`: Artifact and content management

**Content Editor Agent** (`.deepagents/content_editor/memories/`):
- `grammar_rules.md`: Grammar and style correction rules
- `readability_patterns.md`: Readability improvement patterns
- `quality_metrics.md`: Content quality scoring criteria

### Configuration

**DocumentConfig** (tools/latex_generator.py): Controls document class, formatting, headers/footers, bibliography, and layout options.

**Environment**: Uses `.env` file for ANTHROPIC_API_KEY, Docker volumes for persistence.

### LangSmith Tracing (optional)

When `LANGCHAIN_TRACING_V2=true` is set (plus `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT`), every pipeline run is traced to LangSmith. Cost, per-node latency, prompts, and model usage are all visible per run.

LangGraph nodes auto-instrument. Direct `anthropic.Anthropic()` clients do not — `tools/tracing.py` wraps them via `maybe_wrap_anthropic()` so their `messages.create` calls also appear in the trace tree. Tracing is fully opt-in: with the env var unset, `maybe_wrap_anthropic` returns the client unchanged and `langsmith` isn't even imported.

When adding a new direct `anthropic.Anthropic(...)` instantiation, wrap it with `maybe_wrap_anthropic(...)` so it shows up in traces when tracing is enabled. `langchain-anthropic`'s `ChatAnthropic` is already auto-instrumented and needs no wrapping.

### Visual QA Modes

`VISUAL_QA_MODE` (env var, default `auto`) controls whether the pipeline runs the autonomous visual QA stage:

| Mode | Pipeline behavior | Visual QA |
|------|-------------------|-----------|
| `auto` | Runs all three stages | Claude vision, automated, gated |
| `disabled` | Stops after LaTeX gen, emits PDF + report | Skipped |
| `interactive` | Stops after LaTeX gen, writes `handoff.json` | Skipped — user runs `/printshop-review` in Claude Code to drive a human-in-the-loop review |

In `interactive` mode the orchestrator writes `artifacts/output/<run_id>/handoff.json` listing the .tex/PDF paths, page count, and any concerns the LaTeX-specialist stage flagged. The `.claude/skills/printshop-review/` skill picks that up. Recompilation after a fix goes through `python -m tools.recompile <run_id>`, which wraps `PDFCompiler` so multi-pass + regex fixes still apply.

Routing for `disabled`/`interactive` skips both `enrich_for_visual_qa` and `visual_qa`; `iteration` and `escalation` still apply when the LaTeX gate fails (e.g., compilation errors), so the only change is the post-pass branch.

## Development Patterns

### Adding New Content Types
1. Create `content_types/<type_id>/type.md` with metadata, rendering instructions, and LaTeX requirements
2. Create `artifacts/sample_content/<type_id>/` with `config.md` and section markdown files
3. Add images to `artifacts/sample_content/<type_id>/images/` and CSV data to `data/`
4. Reference assets from markdown using inline `<!-- IMAGE: -->`, `<!-- CSV_TABLE: -->`, or `<!-- TIKZ: -->` comments

### Changing Document Appearance
- Edit `content_types/<type_id>/type.md` rendering instructions (preferred — changes are picked up by the LLM at generation time)
- For structural changes to inline reference processing: edit `agents/latex_specialist/latex_optimizer.py`
- For changes to the LaTeX document builder: edit `tools/latex_generator.py`
- Add new LaTeX packages to Dockerfile if needed

### Quality Tuning
- Quality gate thresholds: `agents/qa_orchestrator/quality_gates.py`
- Content scoring (Flesch readability, grammar): `agents/content_editor/content_reviewer.py`
- LaTeX scoring (structure, typography, tables/figures, best practices): `agents/latex_specialist/latex_optimizer.py`
- Iteration limits: `agents/qa_orchestrator/langgraph_workflow.py`

### Pipeline Status Reporting
- **Completed / Human Handoff Ready**: All quality gates passed. Report as "completed successfully."
- **Escalated**: Pipeline hit iteration limits or quality gates were not met. Report as "completed with issues" and note what failed (e.g., visual QA score plateaued below threshold). Do NOT call this a successful run.
- **Failed**: A stage crashed or errored out. Report as "failed" with the error.

### Known Gotchas
- **Flesch readability vs. academic tone**: The content editor may lower scores on first pass by making prose more academic. Dense sentences score poorly on Flesch Reading Ease. If content consistently fails the gate, simplify sentence structure in the source markdown rather than lowering thresholds.
- **Unicode in LaTeX**: pdflatex cannot handle Unicode math symbols (superscripts, subscripts like `⁻`, `²`). The `_sanitize_unicode_for_latex()` method in latex_optimizer.py handles known cases, but new Unicode characters from LLM output may need to be added to the replacement map.
- **Duplicate figure labels**: If images appear both via inline `<!-- IMAGE: -->` comments and via a separate image-walking step, you get duplicate `\label{}` errors. All images should be referenced inline from markdown — there is no separate image directory scan.

### Conventions

These cross-content-type patterns are followed across the codebase. New content types should adopt them.

- **AI-disclosure footer**: Every rendered document includes a single italic gray line — *"Drafted with AI assistance via DeepAgents PrintShop."* — at ~7pt in the bottom-right of the last page (or every page for multi-page deliverables). Implemented via `\AddToShipoutPictureFG{}` from `eso-pic`, or `\vfill\hfill\textit{...}` immediately before `\end{document}`. This establishes a clear, non-removable AI-content disclosure.
- **Demo content banner**: When a sample's biographical or factual content is invented for demonstration (e.g., the parody resume), prepend a small framed banner at the top of page 1 noting *"Sample output --- fictitious content."* This makes the demo nature obvious to anyone viewing a rendered sample.
- **Multi-theme content types**: See *Multi-Theme Content Types* above. Use the `theme:` config field plus a `palette_preview.pdf` design reference rather than forking the content type for each visual variant.

## GitHub Issues

When creating GitHub issues with `gh issue create`, always apply a label:
- **bug** — Something is broken
- **enhancement** — New feature or improvement request
- **question** — Needs discussion or clarification

Example: `gh issue create --title "..." --body "..." --label "bug"`

## Dependencies

Python packages (requirements.txt):
- anthropic, openai: LLM APIs
- langchain, langchain-anthropic, langchain-openai: LLM orchestration
- langgraph: Pipeline state graph orchestration
- pandas: Data processing
- pillow, matplotlib: Image handling

System dependencies (Dockerfile):
- texlive-latex-base, texlive-latex-extra: LaTeX distribution
- texlive-fonts-recommended, texlive-science: LaTeX packages
- ghostscript, imagemagick: Image processing
