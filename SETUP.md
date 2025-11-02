# DeepAgent Scribe Setup Guide

This guide will help you set up and run the DeepAgent Scribe research agent.

## Prerequisites

- Docker Desktop (installed and running)
- Anthropic API key (get one at https://console.anthropic.com/)

## Quick Start

### 1. Configure API Keys

Create a `.env` file with your API keys:

```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 2. Build the Docker Container

```bash
docker-compose build
```

This will:
- Install Python 3.11
- Install TeX Live (for LaTeX/PDF generation)
- Install deepagents-cli and all dependencies
- Set up the project structure

### 3. Run the Agent

#### Option A: Interactive Mode

```bash
docker-compose run --rm deepagent-scribe python agents/research_agent/agent.py
```

Then use the interactive commands:
- `generate` - Generate a sample research report
- `help` - Show agent capabilities
- `exit` - Exit the agent

#### Option B: Direct Generation

```bash
docker-compose run --rm deepagent-scribe python agents/research_agent/agent.py generate
```

This will immediately generate a LaTeX report and compile it to PDF.

#### Option C: Using the run script

```bash
docker-compose run --rm deepagent-scribe bash run_agent.sh generate
```

### 4. View the Output

Generated files will be in `artifacts/output/`:
- `research_report.tex` - LaTeX source file
- `research_report.pdf` - Compiled PDF document

## Project Structure

```
deepagent-scribe/
├── agents/
│   └── research_agent/
│       ├── agent.py              # Main agent with DeepAgents integration
│       └── report_generator.py   # LaTeX report generation logic
├── tools/
│   ├── latex_generator.py        # LaTeX document builder
│   └── pdf_compiler.py           # PDF compilation tool
├── artifacts/
│   ├── sample_content/           # Markdown content files
│   │   ├── introduction.md
│   │   ├── methodology.md
│   │   └── results.md
│   ├── data/                     # CSV data files
│   │   ├── model_performance.csv
│   │   └── training_metrics.csv
│   ├── images/                   # Image assets
│   └── output/                   # Generated files (LaTeX & PDF)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env                          # Your API keys (create from .env.example)
```

## Agent Capabilities

The DeepAgent Scribe can generate LaTeX reports with:

1. **Document Structure**
   - Customizable document classes (article, report, book)
   - Automatic table of contents
   - Headers and footers
   - Title page with author and date

2. **Content Formatting**
   - Convert markdown to LaTeX
   - Bold, italic, and code formatting
   - Bulleted and numbered lists
   - Section and subsection hierarchy

3. **Tables and Data**
   - Manual tables with booktabs styling
   - Tables from CSV files with headers
   - Proper captioning and labeling

4. **Figures and Graphics**
   - Image inclusion (JPG/PNG)
   - Text-wrapped figures
   - Vector diagrams with TikZ
   - Figure captions and references

5. **Citations and References**
   - Bibliography management
   - Inline citations
   - Hyperlinks to external resources

6. **PDF Compilation**
   - Automatic compilation with pdflatex
   - Multiple runs for proper cross-references
   - Clean auxiliary files

## Customizing the Report

### Adding Your Own Content

1. Add markdown files to `artifacts/sample_content/`
2. Add CSV data to `artifacts/data/`
3. Add images to `artifacts/images/`
4. Modify `agents/research_agent/report_generator.py` to use your content

### Changing Document Style

Edit the `DocumentConfig` in `report_generator.py`:

```python
config = DocumentConfig(
    doc_class="article",     # or "report", "book"
    font_size="12pt",        # or "10pt", "11pt"
    paper_size="letterpaper",# or "a4paper"
    title="Your Title",
    author="Your Name",
    # ... more options
)
```

## Troubleshooting

### Docker Build Issues

If the build fails, try:
```bash
docker-compose build --no-cache
```

### LaTeX Compilation Errors

If PDF compilation fails:
1. Check the `.tex` file in `artifacts/output/`
2. Look for syntax errors in the LaTeX code
3. Manually compile to see detailed errors:
   ```bash
   docker-compose run --rm deepagent-scribe pdflatex artifacts/output/research_report.tex
   ```

### Missing API Key

If you get authentication errors:
1. Make sure `.env` file exists
2. Verify your `ANTHROPIC_API_KEY` is correct
3. Restart the container after changing `.env`

## Advanced Usage

### Running with DeepAgents CLI

Once inside the container, you can use the full DeepAgents CLI:

```bash
docker-compose run --rm deepagent-scribe bash
# Inside container:
deepagents --agent research-scribe
```

### Inspecting Agent Memory

Agent memories are stored in `.deepagents/research_agent/memories/`:
- `latex_knowledge.md` - LaTeX best practices
- `report_structure.md` - Research report structure
- `artifacts_tracking.md` - Artifact management
- `generation_log.md` - Report generation history

### Creating Custom Tools

Add new tools to the `tools/` directory and import them in your agent:

```python
from tools.my_custom_tool import MyTool

tool = MyTool()
result = tool.process()
```

## Next Steps

1. Customize the sample content with your own research
2. Add your own images and diagrams
3. Modify the report structure and styling
4. Extend the agent with additional tools
5. Train the agent on specific LaTeX patterns for your field

## Resources

- DeepAgents Documentation: https://docs.langchain.com/oss/python/deepagents
- LaTeX Documentation: https://www.latex-project.org/help/documentation/
- TikZ Examples: https://texample.net/tikz/
- Anthropic API: https://docs.anthropic.com/

## License

MIT
