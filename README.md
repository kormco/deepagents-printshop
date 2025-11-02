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
- **🆕 Multi-agent quality assurance system** for professional-grade outputs
- **🆕 Iterative content review** with specialized grammar, LaTeX, and visual QA agents
- **🆕 Quality scoring and automated refinement** before human handoff

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

3. Inside the container, run the research agent:
   ```bash
   python agents/research_agent/agent.py
   ```

### Quality Assurance Workflow (🆕 Milestone 1)

4. Run content quality review before LaTeX generation:
   ```bash
   python agents/content_editor/agent.py
   ```

5. View quality improvements:
   ```bash
   cat artifacts/quality_reports/content_review_report.md
   ```

## Project Structure

```
deepagent-scribe/
├── agents/
│   ├── research_agent/       # Research agent implementation
│   └── content_editor/       # 🆕 Content quality assurance agent
├── tools/                     # Custom tools for the agent
│   ├── latex_generator.py    # LaTeX document generation
│   └── pdf_compiler.py       # PDF compilation
├── artifacts/                 # Sample content and outputs
│   ├── sample_content/       # Markdown and text content
│   ├── reviewed_content/     # 🆕 LLM-improved content versions
│   ├── quality_reports/      # 🆕 Quality analysis reports
│   ├── images/               # JPG/PNG images
│   ├── data/                 # CSV data files
│   └── output/               # Generated LaTeX and PDF files
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Usage

### Standard Workflow
The agent will generate LaTeX reports based on your research content, automatically handling:
- Document structure and layout
- Content conversion from markdown
- Table and figure placement
- Citation formatting
- PDF compilation

### Quality Assurance Workflow (🆕 Milestone 1)

**Step 1: Content Quality Review**
```bash
python agents/content_editor/agent.py
```
This will:
- Review grammar, spelling, and readability
- Improve sentence structure and flow
- Generate quality scores and improvement reports
- Save polished content to `artifacts/reviewed_content/`

**Step 2: Generate LaTeX from Improved Content**
```bash
python agents/research_agent/agent.py
```

**Quality Metrics:**
- Grammar and spelling corrections
- Readability improvements (Flesch Reading Ease)
- Academic writing style optimization
- Before/after quality scoring (0-100 scale)

**Future Milestones:**
- Milestone 2: File versioning and iteration tracking
- Milestone 3: LaTeX specialist agent
- Milestone 4: QA orchestration and automation
- Milestone 5: Visual PDF quality analysis

## Development Milestones

- **✅ Milestone 1**: Content Editor Agent - Grammar, readability, and style improvements
- **🔄 Milestone 2**: File Organization & Versioning - Track content iterations
- **📋 Milestone 3**: LaTeX Specialist Agent - Typography and formatting optimization
- **🔗 Milestone 4**: QA Orchestration - Automated multi-agent workflow
- **👁️ Milestone 5**: Visual QA Agent - PDF layout and design validation

See `MILESTONE_1_README.md` for detailed implementation guide.

## License

MIT
