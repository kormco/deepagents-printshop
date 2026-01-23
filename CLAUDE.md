# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepAgents PrintShop is a document generation system that produces professional LaTeX documents with comprehensive formatting, citations, tables, images, and diagrams. It uses the DeepAgents CLI framework and runs in Docker with TeX Live for PDF compilation.

Do not hardcode LaTeX output into deterministic logic, primarily make updates to natural language instruction for the LaTeX agent where possible.

## Common Commands

### Development Environment
```bash
# Build and run Docker container
docker-compose build
docker-compose run --rm deepagents-printshop

# Run the research agent interactively
docker-compose run --rm deepagents-printshop python agents/research_agent/agent.py

# Run agent with direct generation
docker-compose run --rm deepagents-printshop python agents/research_agent/agent.py generate

# Use convenience script
docker-compose run --rm deepagents-printshop bash run_agent.sh generate

# Quality Assurance Workflow (Milestone 1+)
docker-compose run --rm deepagents-printshop python agents/content_editor/agent.py
docker-compose run --rm deepagents-printshop cat artifacts/agent_reports/quality/content_review_report.md

# Access container shell
docker-compose run --rm deepagents-printshop bash
```

### LaTeX/PDF Operations
```bash
# Manual PDF compilation (inside container)
pdflatex artifacts/output/research_report.tex

# Check LaTeX syntax
python -c "from tools.latex_generator import LaTeXGenerator; print('LaTeX generator loaded')"

# Test PDF compiler
python -c "from tools.pdf_compiler import PDFCompiler; PDFCompiler().compile_pdf('artifacts/output/research_report.tex')"
```


## Prerequisites

**LaTeX Distribution Required**: PDF compilation requires a LaTeX distribution installed on your system. The Docker container includes TeX Live, but if running outside Docker you must install one of:
- **Windows**: [MiKTeX](https://miktex.org/) - includes pdflatex and automatic package installation
- **macOS**: [MacTeX](https://www.tug.org/mactex/) or `brew install --cask mactex`
- **Linux**: TeX Live via `apt install texlive-full` or equivalent

Without a LaTeX distribution, the system can generate `.tex` files but cannot compile them to PDF.

### Testing and Validation
No formal test suite exists. Validation is done by:
1. Running agent.py to generate sample reports
2. Verifying PDF compilation succeeds
3. Checking LaTeX syntax in generated .tex files

### Quality Assurance Testing (Milestone 1+)
```bash
# Test content editor agent
docker-compose run --rm deepagents-printshop python agents/content_editor/simple_test.py

# Run full content quality review
docker-compose run --rm deepagents-printshop python agents/content_editor/agent.py

# Check quality improvements
docker-compose run --rm deepagents-printshop ls -la artifacts/reviewed_content/
docker-compose run --rm deepagents-printshop cat artifacts/agent_reports/quality/content_review_report.md
```

## Architecture

### Core Components

**agents/research_agent/agent.py**: Main DeepAgent with persistent memory management. Implements ResearchAgent class with memory tracking for LaTeX generation patterns, report structures, and artifact management.

**agents/research_agent/report_generator.py**: ResearchReportGenerator class that orchestrates LaTeX document creation from markdown content, CSV data, and images.

**agents/content_editor/agent.py**: Quality assurance agent (Milestone 1+) that reviews and improves content before LaTeX generation. Implements ContentEditorAgent class with memory for grammar rules, style guidelines, and quality metrics.

**agents/content_editor/content_reviewer.py**: ContentReviewer tool that uses Claude API for intelligent content analysis, grammar correction, readability improvement, and quality scoring.

**tools/latex_generator.py**: LaTeXGenerator class with DocumentConfig for creating professional LaTeX documents. Handles document structure, formatting, tables, figures, and citations.

**tools/pdf_compiler.py**: PDFCompiler class for converting LaTeX to PDF using pdflatex with proper error handling and multi-pass compilation.

### Data Flow

**Standard Workflow:**
1. Agent loads content from `artifacts/sample_content/` (markdown files)
2. Data tables from `artifacts/data/` (CSV files)
3. Images from `artifacts/images/` (JPG/PNG)
4. LaTeXGenerator creates .tex document with proper formatting
5. PDFCompiler runs pdflatex to generate final PDF
6. Output saved to `artifacts/output/`

**Quality Assurance Workflow (Milestone 1+):**
1. ContentEditorAgent loads original content from `artifacts/sample_content/`
2. ContentReviewer analyzes grammar, readability, and style
3. Claude API improves content quality and fixes issues
4. Improved content saved to `artifacts/reviewed_content/v1_content_edited/`
5. Quality reports generated in `artifacts/agent_reports/quality/`
6. ResearchAgent uses improved content for LaTeX generation

### Memory System

DeepAgents persistent memory stored in `.deepagents/`:

**Research Agent** (`.deepagents/research_agent/memories/`):
- `latex_knowledge.md`: LaTeX best practices and patterns
- `report_structure.md`: Research report structure templates
- `artifacts_tracking.md`: Artifact and content management
- `generation_log.md`: Report generation history

**Content Editor Agent** (`.deepagents/content_editor/memories/`):
- `grammar_rules.md`: Grammar and style correction rules
- `readability_patterns.md`: Readability improvement patterns
- `quality_metrics.md`: Content quality scoring criteria

### Configuration

**DocumentConfig** (tools/latex_generator.py): Controls document class, formatting, headers/footers, bibliography, and layout options.

**Environment**: Uses `.env` file for ANTHROPIC_API_KEY, Docker volumes for persistence.

## Development Patterns

### Adding New Content
- Markdown files: `artifacts/sample_content/`
- CSV data: `artifacts/data/`
- Images: `artifacts/images/`
- Modify report_generator.py to incorporate new content

### Quality Assurance Development
- Content rules: Edit `.deepagents/content_editor/memories/grammar_rules.md`
- Quality metrics: Modify ContentReviewer.calculate_quality_score()
- Review prompts: Update ContentReviewer.review_text() prompts
- Add new QA agents: Follow `agents/content_editor/` pattern

### LaTeX Customization
- Edit DocumentConfig in report_generator.py
- Extend LaTeXGenerator for new formatting features
- Add new LaTeX packages to Dockerfile if needed

### Tool Extension
- Add new tools to `tools/` directory
- Import in agent.py or report_generator.py
- Follow existing patterns for error handling and configuration

### Multi-Agent Development
- Create new agents in `agents/[agent_name]/` directories
- Follow ContentEditorAgent pattern for memory management
- Use DeepAgents CLI framework for persistent memory
- Implement quality scoring and reporting capabilities

## Dependencies

Python packages (requirements.txt):
- deepagents-cli: Core agent framework
- anthropic, openai: LLM APIs
- langchain, langchain-anthropic, langchain-openai: LLM orchestration
- pandas: Data processing
- pillow, matplotlib: Image handling

System dependencies (Dockerfile):
- texlive-latex-base, texlive-latex-extra: LaTeX distribution
- texlive-fonts-recommended, texlive-science: LaTeX packages
- ghostscript, imagemagick: Image processing