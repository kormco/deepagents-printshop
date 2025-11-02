# DeepAgent Scribe - LaTeX Research Report Generator

A specialized DeepAgent that generates professional LaTeX research reports with comprehensive formatting, citations, tables, images, and diagrams.

## Features

- Generate professional LaTeX reports with customizable document structure
- Support for multiple document classes (article, book, report)
- Automatic table of contents generation
- Citation management and in-line references
- Data tables from CSV files
- Image placement with text wrapping
- Vector diagrams (EPS/SVG)
- Hyperlink support
- PDF compilation with pdflatex
- Multi-agent quality assurance system for professional-grade outputs
- Iterative content review with specialized grammar, LaTeX, and visual QA agents
- Quality scoring and automated refinement before human handoff
- File versioning and change tracking
- Automated QA workflow orchestration

## Prerequisites

- Docker Desktop (installed and running)
- Anthropic API key (for Claude)

## Quick Start

1. Copy the environment file and add your API keys:
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and add your `ANTHROPIC_API_KEY`

2. Build and run the Docker container:
   ```bash
   docker-compose build
   docker-compose run --rm deepagent-scribe
   ```

3. Inside the container, run the QA orchestrator for automated workflow:
   ```bash
   python agents/qa_orchestrator/agent.py
   ```

   Or run individual agents:
   ```bash
   # Content quality review
   python agents/content_editor/agent.py

   # LaTeX generation
   python agents/research_agent/agent.py

   # LaTeX optimization
   python agents/latex_specialist/agent.py
   ```

## Project Structure

```
deepagent-scribe/
├── agents/
│   ├── research_agent/       # LaTeX report generation
│   ├── content_editor/       # Content quality review and improvement
│   ├── latex_specialist/     # LaTeX formatting and typography optimization
│   └── qa_orchestrator/      # Multi-agent workflow coordination
├── tools/                     # Custom tools and utilities
│   ├── latex_generator.py    # LaTeX document generation
│   ├── pdf_compiler.py       # PDF compilation with pdflatex
│   ├── visual_qa.py          # Visual quality analysis
│   ├── visual_qa_agent.py    # Visual QA agent implementation
│   ├── version_manager.py    # File versioning system
│   └── change_tracker.py     # Content change tracking
├── artifacts/                 # Sample content and outputs
│   ├── sample_content/       # Source markdown, images, and CSV data
│   ├── reviewed_content/     # LLM-improved content versions
│   ├── quality_reports/      # Content quality analysis reports
│   ├── qa_reports/           # QA orchestration reports
│   ├── visual_qa/            # Visual quality analysis outputs
│   └── output/               # Generated LaTeX and PDF files
├── .deepagents/              # Persistent agent memory storage
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Usage

### Automated Workflow (Recommended)

Run the QA orchestrator for a fully automated multi-agent workflow:

```bash
python agents/qa_orchestrator/agent.py
```

This orchestrates the complete pipeline:
1. Content quality review and improvement (Content Editor)
2. LaTeX document generation (Research Agent)
3. LaTeX formatting optimization (LaTeX Specialist)
4. Visual PDF quality analysis (Visual QA)
5. Quality gate validation and reporting

### Manual Workflow

Run individual agents for granular control:

**Step 1: Content Quality Review**
```bash
python agents/content_editor/agent.py
```
- Reviews grammar, spelling, and readability
- Improves sentence structure and flow
- Generates quality scores and improvement reports
- Saves polished content to `artifacts/reviewed_content/`

**Step 2: Generate LaTeX Document**
```bash
python agents/research_agent/agent.py
```
- Converts markdown content to LaTeX
- Creates tables from CSV data
- Places images and figures
- Handles citations and references
- Compiles PDF with pdflatex

**Step 3: LaTeX Optimization**
```bash
python agents/latex_specialist/agent.py
```
- Optimizes LaTeX formatting and typography
- Fixes compilation warnings and errors
- Improves document structure
- Ensures professional layout

**Step 4: Visual Quality Analysis**
```bash
python tools/visual_qa_agent.py
```
- Analyzes PDF layout and design quality
- Checks typography and spacing
- Validates figure placement and quality
- Generates visual quality report
- Saves analysis to `artifacts/visual_qa/`

### Quality Metrics

The system tracks comprehensive quality metrics:
- **Content**: Grammar, spelling, readability (Flesch Reading Ease)
- **LaTeX**: Compilation success, warning count, formatting quality
- **Visual**: Layout analysis, typography, figure quality
- **Overall**: Before/after quality scoring (0-100 scale)

## Multi-Agent Architecture

DeepAgent Scribe implements a sophisticated multi-agent system with specialized agents:

- **Content Editor Agent**: Reviews and improves content quality (grammar, readability, style)
- **Research Agent**: Generates LaTeX documents from markdown, CSV, and images
- **LaTeX Specialist Agent**: Optimizes LaTeX formatting and typography
- **QA Orchestrator**: Coordinates the complete workflow with quality gates
- **Visual QA**: Analyzes PDF layout and design quality

Each agent maintains persistent memory using the DeepAgents framework, allowing them to learn from previous iterations and improve over time.

## License

MIT
